"""0.2.0 review, part 2: the cache upgrade, locks, git, paths from logs and malformed records.
Every name, path and email here is invented."""
import io
import json
import ntpath
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from unittest import mock
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
from tinkerprint.build import CACHE_VERSION, _cached, new_report
from tinkerprint.demo import RepoWriter, git_env
from tinkerprint.readers import claude
from tinkerprint.readers import git as git_mod
from tinkerprint.readers.git import Identity, read_git


def write_lines(path, records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write((r if isinstance(r, str) else json.dumps(r)) + "\n")
    return path


def claude_record(sid, day="2026-03-02", cwd="/w/a"):
    return {"type": "user", "sessionId": sid, "timestamp": f"{day}T10:00:00Z", "cwd": cwd, "version": "2.1.4",
            "message": {"role": "user", "content": "invented"}}


class Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = os.path.realpath(self.tmp.name)
        self.base = os.path.join(self.t, "logs")
        self.cache = os.path.join(self.t, "data", "cache", "claude.json")

    def tearDown(self):
        self.tmp.cleanup()

    def read(self, files):
        rep = new_report()
        return _cached(files, claude.read_file, self.cache, self.base, rep), rep

    def entries(self):
        with open(self.cache, encoding="utf-8") as f:
            return json.load(f)


class CacheFrom01(Tmp):
    """A 0.1 cache (version 4) never marked an entry gone. Its events are still valid."""

    def v4_cache(self, files):
        os.makedirs(os.path.dirname(self.cache), exist_ok=True)
        with open(self.cache, "w", encoding="utf-8") as f:
            json.dump({"v": 4, "files": files}, f)

    def event(self, session):
        return {"ts": "2025-11-05T10:00:00+00:00", "source": "claude", "kind": "session", "path": "/w/a",
                "session": session, "harness": "claude", "model": "", "actor": "agent", "origin": "",
                "commit": "", "status": "", "added": 0, "op": ""}

    def test_a_log_gone_since_01_keeps_its_events(self):
        live = write_lines(os.path.join(self.base, "p", "live.jsonl"), [claude_record("now")])
        gone = os.path.join(self.base, "p", "gone.jsonl")
        with open(live, "rb") as f:
            raw = f.read()
        import hashlib
        st = os.stat(live)
        self.v4_cache({
            gone: {"stat": None, "sha256": "1" * 64, "size": 10, "events": [self.event("rotated")]},
            # The 0.1 entry of a live log matches it exactly, yet it is read again.
            live: {"stat": [st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_ino],
                   "sha256": hashlib.sha256(raw).hexdigest(), "size": len(raw), "events": [self.event("stale")]},
        })
        evs, rep = self.read([live])
        self.assertEqual({e.session for e in evs}, {"now", "rotated"})
        self.assertEqual((rep["kept_files"], rep["kept_sessions"]), (1, 1))
        saved = self.entries()
        self.assertEqual(saved["v"], CACHE_VERSION)
        self.assertTrue(saved["files"][gone]["gone"])
        self.assertNotIn("gone", saved["files"][live])
        # And the next build still counts it.
        evs, rep = self.read([live])
        self.assertEqual({e.session for e in evs}, {"now", "rotated"})

    def test_an_unknown_version_keeps_only_what_it_marked_gone(self):
        gone = os.path.join(self.base, "p", "gone.jsonl")
        os.makedirs(os.path.dirname(self.cache), exist_ok=True)
        with open(self.cache, "w", encoding="utf-8") as f:
            json.dump({"v": 99, "files": {gone: {"events": [self.event("x")]}}}, f)
        evs, _ = self.read([])
        self.assertEqual(evs, [])


HOLD = """
import sys, time
sys.path.insert(0, sys.argv[1])
from tinkerprint.datadir import data_lock
with data_lock(sys.argv[2]):
    print("held", flush=True)
    sys.stdin.readline()
"""


class Locks(Tmp):
    """Builds and forget take the data folder's lock around shared state, and wait for each other."""

    def setUp(self):
        super().setUp()
        self.data = os.path.join(self.t, "data")
        from tinkerprint.datadir import claim_home
        claim_home(self.data)

    def hold(self):
        """Another process holds the lock until the test releases it."""
        child = subprocess.Popen([sys.executable, "-c", HOLD, helpers.SRC, self.data], stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, text=True)
        self.addCleanup(child.wait)
        self.addCleanup(child.stdin.close)
        self.addCleanup(child.stdout.close)
        self.assertEqual(child.stdout.readline().strip(), "held")
        return child

    def release(self, child):
        child.stdin.write("\n")
        child.stdin.flush()
        child.wait()

    def profile(self):
        from tinkerprint.profile import load_profile
        p = os.path.join(self.t, "p.toml")
        logs = os.path.join(self.t, "logs")
        os.makedirs(logs, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(f'name = "Ida"\n[identity]\nemails = ["ida@fenwick.example.test"]\n[harnesses]\n'
                    f'claude = true\ncodex = false\nclaude_dir = "{logs}"\n[[project]]\nname = "P"\n'
                    f'root = "{os.path.join(self.t, "nowhere")}"\n')
        return load_profile(p)

    def in_thread(self, fn):
        import threading
        done = []
        th = threading.Thread(target=lambda: done.append(fn()), daemon=True)
        th.start()
        return th, done

    def test_the_cache_waits_for_the_lock_and_says_so(self):
        from tinkerprint import datadir
        from tinkerprint.build import gather
        prof = self.profile()
        child = self.hold()
        err = io.StringIO()
        with mock.patch.object(datadir, "NOTICE_AFTER", 0.1), mock.patch.object(sys, "stderr", err):
            th, done = self.in_thread(lambda: gather(prof, self.data))
            th.join(0.6)
            self.assertTrue(th.is_alive())
            self.assertFalse(os.path.exists(os.path.join(self.data, "cache")))
            self.release(child)
            th.join(10)
        self.assertFalse(th.is_alive())
        self.assertIn("waiting for another tinkerprint run...", err.getvalue())
        self.assertTrue(os.path.exists(os.path.join(self.data, "cache", "claude.json")))

    def test_the_profile_list_waits_for_the_lock(self):
        from tinkerprint.keys import adopt, read_registry
        prof = self.profile()
        child = self.hold()
        adopt(self.data, prof, write=False)  # a read never waits
        th, _ = self.in_thread(lambda: adopt(self.data, prof))
        th.join(0.3)
        self.assertTrue(th.is_alive())
        self.assertEqual(read_registry(self.data), {})
        self.release(child)
        th.join(10)
        self.assertEqual(len(read_registry(self.data)), 1)

    def test_forget_waits_for_a_build(self):
        from tinkerprint.cli import main
        os.makedirs(os.path.join(self.data, "cache"))
        with open(os.path.join(self.data, "cache", "claude.json"), "w") as f:
            f.write("{}")
        child = self.hold()
        out = io.StringIO()
        th, done = self.in_thread(lambda: main(["forget", "--all", "--yes", "--data-dir", self.data]))
        with redirect_stdout(out):
            th.join(0.3)
            self.assertTrue(th.is_alive())
            self.assertTrue(os.path.exists(os.path.join(self.data, "cache", "claude.json")))
            self.release(child)
            th.join(10)
        self.assertEqual(done, [0])
        self.assertFalse(os.path.exists(self.data))

    def test_a_run_that_waited_while_forget_deleted_the_folder_stops(self):
        from tinkerprint.datadir import Gone, data_lock
        from tinkerprint.forget import forget_all
        result = []

        def waiter():
            try:
                with data_lock(self.data, claimed=True):
                    result.append("wrote")
            except Gone as e:
                result.append(str(e))
        import threading
        with data_lock(self.data) as lock:
            th = threading.Thread(target=waiter, daemon=True)
            th.start()
            th.join(0.2)
            self.assertTrue(th.is_alive())
            lines = forget_all(self.data, True)  # the same thread holds the lock, so this nests
            self.assertIn("Deleted", lines[-1])
            self.assertTrue(lock.drop)
        th.join(10)
        self.assertEqual(len(result), 1)
        self.assertIn("was deleted while this run waited", result[0])
        self.assertFalse(os.path.exists(self.data))

    def test_the_lock_nests_in_its_thread_and_forget_all_leaves_nothing(self):
        from tinkerprint.cli import main
        from tinkerprint.datadir import LOCK, data_lock
        with data_lock(self.data):
            with data_lock(self.data):  # the same thread never waits on itself
                pass
        self.assertTrue(os.path.exists(os.path.join(self.data, LOCK)))
        os.makedirs(os.path.join(self.data, "cache"))
        with open(os.path.join(self.data, "cache", "claude.json"), "w") as f:
            f.write("{}")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["forget", "--all", "--yes", "--data-dir", self.data]), 0)
        self.assertFalse(os.path.exists(self.data))

    def test_another_thread_waits(self):
        from tinkerprint.datadir import data_lock
        order = []
        with data_lock(self.data):
            th, _ = self.in_thread(lambda: data_lock(self.data).__enter__() and order.append("other"))
            th.join(0.3)
            self.assertTrue(th.is_alive())
            order.append("first")
        th.join(10)
        self.assertEqual(order, ["first", "other"])

    def test_a_file_system_without_locking_warns_once_and_goes_on(self):
        import errno
        from tinkerprint import datadir
        opened, closed = [], []
        real_open, real_close = os.open, os.close

        def track_open(*a, **k):
            fd = real_open(*a, **k)
            opened.append(fd)
            return fd

        def track_close(fd):
            closed.append(fd)
            return real_close(fd)
        err = io.StringIO()
        fail = OSError(errno.ENOLCK, "No locks available")
        with mock.patch.object(datadir, "_try_lock", side_effect=datadir._NoLocking(fail.errno, fail.strerror)), \
                mock.patch.object(datadir.os, "open", track_open), mock.patch.object(datadir.os, "close", track_close), \
                mock.patch.object(datadir, "_warned", []), mock.patch.object(sys, "stderr", err):
            for _ in range(2):
                with datadir.data_lock(self.data) as lock:
                    self.assertIsNone(lock.fd)
        self.assertEqual(err.getvalue().count("cannot lock files"), 1)
        self.assertEqual(sorted(opened), sorted(closed))

    def test_an_error_while_locking_closes_the_file(self):
        from tinkerprint import datadir
        opened, closed = [], []
        real_open, real_close = os.open, os.close

        def track_open(*a, **k):
            fd = real_open(*a, **k)
            opened.append(fd)
            return fd

        def track_close(fd):
            closed.append(fd)
            return real_close(fd)
        with mock.patch.object(datadir, "_try_lock", side_effect=OSError(5, "I/O error")), \
                mock.patch.object(datadir.os, "open", track_open), mock.patch.object(datadir.os, "close", track_close):
            with self.assertRaises(OSError):
                with datadir.data_lock(self.data):
                    pass
        self.assertEqual(len(opened), 1)
        self.assertEqual(opened, closed)

    def test_a_released_lock_is_free(self):
        from tinkerprint.datadir import data_lock
        self.release(self.hold())
        with data_lock(self.data):
            pass


UTC = ZoneInfo("UTC")
ME = ("Ida Fenwick", "ida@fenwick.example.test")


def git(cwd, *args, env=None):
    return subprocess.run(["git", "-C", cwd, *args], check=True, capture_output=True,
                          env=dict(env or git_env(), GIT_AUTHOR_NAME=ME[0], GIT_AUTHOR_EMAIL=ME[1],
                                   GIT_COMMITTER_NAME=ME[0], GIT_COMMITTER_EMAIL=ME[1]))


class GitCalls(Tmp):
    """Every git call starts from an environment with no GIT_* variable and runs no other program."""

    def repo(self, name, files):
        path = os.path.join(self.t, name)
        r = RepoWriter(path)
        r.touch(datetime(2026, 3, 2, 10, tzinfo=UTC), ME, files)
        r.write()
        return path

    def test_git_variables_from_outside_never_pick_the_repo(self):
        real = self.repo("real", {"a.py": 2})
        decoy = self.repo("decoy", {"b.py": 2, "c.py": 2})
        env = {"GIT_DIR": os.path.join(decoy, ".git"), "GIT_WORK_TREE": decoy, "GIT_ALLOW_PROTOCOL": "file",
               "git_ceiling_directories": "/"}
        with mock.patch.dict(os.environ, env):
            res = read_git([real], Identity([ME[1]], []))
            sent = git_mod._env()
        self.assertEqual({os.path.basename(e.path) for e in res.events}, {"a.py"})
        self.assertEqual(sent["GIT_ALLOW_PROTOCOL"], "")
        self.assertEqual(sent["GIT_NO_LAZY_FETCH"], "1")
        self.assertEqual({k for k in sent if k.upper().startswith("GIT_")},
                         {"GIT_TERMINAL_PROMPT", "GIT_OPTIONAL_LOCKS", "GIT_PAGER", "GIT_NO_LAZY_FETCH",
                          "GIT_ALLOW_PROTOCOL"})

    def test_no_transport_even_when_the_repo_allows_one(self):
        src = self.repo("src", {"a.py": 2})
        clone = os.path.join(self.t, "clone")
        subprocess.run(["git", "clone", "-q", "file://" + src, clone], check=True, capture_output=True,
                       env=dict(git_env(), GIT_ALLOW_PROTOCOL="file"))
        git(clone, "config", "protocol.file.allow", "always")
        self.assertIsNone(git_mod.git_text(["fetch", "-q", "origin"], clone))
        self.assertIsNotNone(git_mod.git_text(["rev-parse", "HEAD"], clone))

    @unittest.skipUnless(os.name == "posix", "the stand-in programs are shell scripts")
    def test_a_repo_config_starts_no_program(self):
        root = self.repo("signed", {"a.py": 2})
        marker = os.path.join(self.t, "ran")
        prog = os.path.join(self.t, "prog.sh")
        with open(prog, "w") as f:
            f.write(f'#!/bin/sh\necho "$*" >> "{marker}"\n'
                    'case "$*" in *-bsau*) cat >/dev/null; echo "[GNUPG:] SIG_CREATED " >&2; '
                    "printf -- '-----BEGIN PGP SIGNATURE-----\\n\\nZmFrZQ==\\n-----END PGP SIGNATURE-----\\n';; "
                    '*) cat "$1" 2>/dev/null;; esac\nexit 0\n')
        os.chmod(prog, 0o755)
        with open(os.path.join(root, ".gitattributes"), "w") as f:
            f.write("*.py diff=conv\n")
        with open(os.path.join(root, "a.py"), "a") as f:
            f.write("more\n")
        git(root, "add", ".")
        git(root, "-c", f"gpg.program={prog}", "commit", "-q", "-S", "-m", "signed")
        os.remove(marker)
        for key, value in (("log.showSignature", "true"), ("gpg.program", prog), ("diff.conv.textconv", prog),
                           ("diff.external", prog), ("diff.conv.command", prog), ("core.pager", prog),
                           ("core.fsmonitor", prog)):
            git(root, "config", key, value)
        res = read_git([root], Identity([ME[1]], []))
        self.assertEqual(len([c for c in res.commits if c.mine]), 2)
        from tinkerprint.projects import scan_priors
        from helpers import profile
        scan_priors(profile([("P", root, None)]).projects)
        self.assertFalse(os.path.exists(marker))


class DemoRepos(Tmp):
    """The demo writes only repos inside its own folder, whatever GIT_* variables say."""

    def victim(self):
        path = os.path.join(self.t, "checkout")
        os.makedirs(path)
        git(path, "init", "-q", "-b", "trunk")
        with open(os.path.join(path, "work.txt"), "w") as f:
            f.write("committed\n")
        git(path, "add", ".")
        git(path, "commit", "-q", "-m", "x")
        with open(os.path.join(path, "work.txt"), "w") as f:
            f.write("unsaved work\n")
        return path

    def test_git_dir_from_outside_never_reaches_a_checkout(self):
        victim = self.victim()
        demo = os.path.join(self.t, "demo")
        with mock.patch.dict(os.environ, {"GIT_DIR": os.path.join(victim, ".git"), "GIT_WORK_TREE": victim}):
            r = RepoWriter(os.path.join(demo, "repo"), within=demo)
            r.touch(datetime(2026, 3, 2, 10, tzinfo=UTC), ME, {"a.py": 2})
            r.write()
        with open(os.path.join(victim, "work.txt")) as f:
            self.assertEqual(f.read(), "unsaved work\n")
        branches = git(victim, "branch", "--format=%(refname:short)").stdout.decode().split()
        self.assertEqual(branches, ["trunk"])
        self.assertTrue(os.path.isfile(os.path.join(demo, "repo", "a.py")))

    def test_a_repo_outside_the_demo_folder_is_refused_before_any_write(self):
        demo = os.path.join(self.t, "demo")
        outside = os.path.join(self.t, "elsewhere")
        r = RepoWriter(outside, within=demo)
        r.touch(datetime(2026, 3, 2, 10, tzinfo=UTC), ME, {"a.py": 2})
        with self.assertRaises(ValueError):
            r.write()
        self.assertFalse(os.path.exists(outside))

    def test_a_dot_git_file_is_refused(self):
        demo = os.path.join(self.t, "demo")
        path = os.path.join(demo, "repo")
        os.makedirs(path)
        victim = self.victim()
        with open(os.path.join(path, ".git"), "w") as f:
            f.write(f"gitdir: {os.path.join(victim, '.git')}\n")
        r = RepoWriter(path, within=demo)
        r.touch(datetime(2026, 3, 2, 10, tzinfo=UTC), ME, {"a.py": 2})
        with self.assertRaises(ValueError):
            r.write()
        self.assertEqual(git(victim, "branch", "--format=%(refname:short)").stdout.decode().split(), ["trunk"])


class WindowsLogPaths(Tmp):
    """A path from a log that names a share or a device never reaches the file system, on Windows
    rules (ntpath) on any OS."""

    LOCAL = r"C:\w\kite"
    SHARE = r"\\server\share\kite"

    def setUp(self):
        super().setUp()
        from tinkerprint.readers import _common
        patch = mock.patch.object(_common, "PATHMOD", ntpath)
        patch.start()
        self.addCleanup(patch.stop)

    def claude_file(self, cwd, edits):
        recs = [claude_record("s1", cwd=cwd)]
        for i, p in enumerate(edits):
            recs.append({"type": "assistant", "sessionId": "s1", "timestamp": "2026-03-02T10:01:00Z", "cwd": cwd,
                         "message": {"role": "assistant", "model": "m-1", "content": [
                             {"type": "tool_use", "id": f"t{i}", "name": "Edit", "input": {"file_path": p}}]}})
            recs.append({"type": "user", "sessionId": "s1", "timestamp": "2026-03-02T10:01:05Z", "cwd": cwd,
                         "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": f"t{i}"}]}})
        return write_lines(os.path.join(self.base, "p", "s1.jsonl"), recs)

    def test_claude_keeps_only_drive_paths(self):
        path = self.claude_file(self.LOCAL, [self.LOCAL + r"\a.py", self.SHARE + r"\b.py", "//server/share/c.py",
                                             r"\\?\C:\w\d.py", r"\\.\pipe\e", r"C:\w\NUL", "f.py"])
        evs = claude.read_file(path)
        edits = sorted(e.path for e in evs if e.kind == "edit")
        self.assertEqual(edits, [self.LOCAL + r"\a.py", self.LOCAL + r"\f.py"])

    def test_claude_drops_a_share_as_the_folder(self):
        path = self.claude_file(self.SHARE, ["g.py"])
        evs = claude.read_file(path)
        self.assertEqual([e.path for e in evs if e.kind == "edit"], ["g.py"])  # relative: unassigned
        self.assertEqual({e.path for e in evs if e.kind == "session"}, {""})

    def test_codex_keeps_only_drive_paths(self):
        from tinkerprint.readers import codex
        recs = [{"type": "session_meta", "timestamp": "2026-03-02T10:00:00Z",
                 "payload": {"id": "c1", "cwd": self.SHARE, "timestamp": "2026-03-02T10:00:00Z"}},
                {"type": "turn_context", "timestamp": "2026-03-02T10:00:01Z", "payload": {"model": "m-1",
                                                                                        "cwd": self.LOCAL}},
                {"type": "event_msg", "timestamp": "2026-03-02T10:00:02Z", "payload": {
                    "type": "patch_apply_end", "success": True, "call_id": "k1",
                    "changes": {self.LOCAL + r"\a.py": {}, self.SHARE + r"\b.py": {}, "c.py": {},
                                r"\\?\UNC\server\share\d.py": {}}}}]
        path = write_lines(os.path.join(self.base, "rollout-1.jsonl"), recs)
        evs = codex.read_file(path)
        self.assertEqual(sorted(e.path for e in evs if e.kind == "edit"),
                         [self.LOCAL + r"\a.py", self.LOCAL + r"\c.py"])
        self.assertNotIn(self.SHARE, {e.path for e in evs})

    def test_agy_refuses_a_share_in_the_path(self):
        from tinkerprint.readers.agy import _uri_path
        for uri in ("file:////server/share/kite", "file:///%5C%5Cserver%5Cshare%5Ckite", "file:///C:/w/CON",
                    "file:////%3F/C:/kite", "file:///%2F%2Fserver/share"):
            with self.subTest(uri=uri):
                self.assertIsNone(_uri_path(uri, ntpath))
        self.assertEqual(_uri_path("file:///C:/w/kite", ntpath), self.LOCAL)

    def test_the_resolver_never_resolves_a_share(self):
        from helpers import profile
        from tinkerprint.projects import Resolver
        prof = profile([("P", "/w", None)])
        prof.projects[0].roots[:] = [self.SHARE]
        res = Resolver(prof.projects, ntpath)
        self.assertIsNone(res.resolve_root(self.SHARE + r"\x.py"))  # as an older cache may hold


DEEP = '{"type": "user", "sessionId": "deep", "message": ' + "[" * 200000 + "]" * 200000 + "}"


class MalformedRecords(Tmp):
    """A record that will not decode, nests too deep or runs too long is skipped and counted. The
    rest of the log still counts."""

    def test_claude_skips_a_record_nested_too_deep(self):
        path = write_lines(os.path.join(self.base, "p", "s.jsonl"),
                           [claude_record("before"), DEEP, '{"type": "user", "broken', claude_record("after")])
        evs, rep = self.read([path])
        self.assertEqual({e.session for e in evs}, {"before", "after"})
        self.assertEqual((rep["records"], rep["rejected"]), (2, 2))

    def test_codex_skips_a_record_nested_too_deep(self):
        from tinkerprint.readers import codex
        recs = [{"type": "session_meta", "timestamp": "2026-03-02T10:00:00Z",
                 "payload": {"id": "c1", "cwd": "/w/a", "timestamp": "2026-03-02T10:00:00Z"}},
                '{"type": "event_msg", "payload": ' + "[" * 200000 + "]" * 200000 + "}",
                {"type": "turn_context", "timestamp": "2026-03-03T10:00:00Z", "payload": {"model": "m-1"}}]
        path = write_lines(os.path.join(self.base, "rollout-1.jsonl"), recs)
        from tinkerprint.readers._common import new_health
        hc = new_health()
        evs = codex.read_file(path, health=hc)
        self.assertEqual({e.ts[:10] for e in evs}, {"2026-03-02", "2026-03-03"})
        self.assertEqual((hc["records"], hc["rejected"]), (2, 1))

    def test_agy_skips_a_folder_list_nested_too_deep_or_too_long(self):
        from tinkerprint.demo import write_agy_db
        from tinkerprint.readers import _common, agy
        db = os.path.join(self.t, "agy.db")
        write_agy_db(db, [("a1", ["/w/a"], datetime(2026, 3, 2, 10, tzinfo=UTC)),
                          ("a2", ["/w/b"], datetime(2026, 3, 3, 10, tzinfo=UTC)),
                          ("a3", ["/w/c" + "x" * 300], datetime(2026, 3, 4, 10, tzinfo=UTC))])
        import sqlite3
        con = sqlite3.connect(db)
        con.execute("update conversation_summaries set workspace_uris = ? where conversation_id = 'a1'",
                    ("[" * 200000,))
        con.commit()
        con.close()
        with mock.patch.object(_common, "MAX_RECORD", 200):
            hc = _common.new_health()
            evs = agy.read_db(db, hc)
        self.assertEqual(sorted((e.session, e.path) for e in evs), [("a1", ""), ("a2", "/w/b"), ("a3", "")])
        self.assertEqual(hc["rejected"], 2)

    def test_a_line_too_long_is_skipped_but_hashed(self):
        from tinkerprint.readers import _common
        long_rec = dict(claude_record("long"), message={"role": "user", "content": "y" * 5000})
        path = write_lines(os.path.join(self.base, "p", "s.jsonl"), [long_rec, claude_record("short")])
        with mock.patch.object(_common, "MAX_RECORD", 1000):
            evs, rep = self.read([path])
        self.assertEqual({e.session for e in evs}, {"short"})
        self.assertEqual(rep["rejected"], 1)
        entry = self.entries()["files"][path]
        self.assertEqual(entry["size"], os.path.getsize(path))
        self.assertIsNotNone(entry["stat"])

    def test_a_time_at_the_edge_of_the_calendar_is_no_time(self):
        path = write_lines(os.path.join(self.base, "p", "s.jsonl"), [
            dict(claude_record("edge"), timestamp="0001-01-01T00:00:00+01:00"),
            dict(claude_record("edge2"), timestamp="9999-12-31T23:59:59-05:00"), claude_record("fine")])
        evs, _ = self.read([path])
        self.assertEqual({e.session for e in evs}, {"fine"})

    def test_the_health_line_counts_them(self):
        from tinkerprint.build import health_lines
        from tinkerprint.events import Inputs
        from helpers import profile
        path = write_lines(os.path.join(self.base, "p", "s.jsonl"), [claude_record("a"), DEEP])
        _, rep = self.read([path])
        line = health_lines(profile([("P", "/w", None)]), Inputs(setup={"health": {"claude": rep}}))[0]
        self.assertIn("1 malformed record skipped", line)


if __name__ == "__main__":
    unittest.main()
