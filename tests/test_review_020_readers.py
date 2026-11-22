"""0.2.0 review, part 2: the cache upgrade, locks, git, paths from logs and malformed records.
Every name, path and email here is invented."""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

import helpers  # noqa: F401
from tinkerprint.build import CACHE_VERSION, _cached, new_report
from tinkerprint.readers import claude


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
    """Builds and forget take the data folder's lock around shared state, and give up in time."""

    def setUp(self):
        super().setUp()
        self.data = os.path.join(self.t, "data")
        os.makedirs(self.data)
        from tinkerprint import datadir
        self.wait = mock.patch.object(datadir, "LOCK_WAIT", 0.3)
        self.wait.start()

    def tearDown(self):
        self.wait.stop()
        super().tearDown()

    def hold(self):
        """Another process holds the lock until the test ends."""
        child = subprocess.Popen([sys.executable, "-c", HOLD, helpers.SRC, self.data], stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, text=True)
        self.addCleanup(child.wait)
        self.addCleanup(child.stdin.close)
        self.addCleanup(child.stdout.close)
        self.assertEqual(child.stdout.readline().strip(), "held")
        return child

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

    def test_the_cache_waits_for_the_lock(self):
        from tinkerprint.build import gather
        from tinkerprint.datadir import Busy
        prof = self.profile()
        self.hold()
        with self.assertRaises(Busy) as cm:
            gather(prof, self.data)
        self.assertIn("another tinkerprint run is using", str(cm.exception))
        self.assertFalse(os.path.exists(os.path.join(self.data, "cache")))

    def test_the_profile_list_waits_for_the_lock(self):
        from tinkerprint.datadir import Busy
        from tinkerprint.keys import adopt, read_registry
        prof = self.profile()
        self.hold()
        with self.assertRaises(Busy):
            adopt(self.data, prof)
        self.assertEqual(read_registry(self.data), {})
        adopt(self.data, prof, write=False)  # a read never waits

    def test_forget_waits_and_says_so(self):
        from tinkerprint.cli import main
        from tinkerprint.datadir import mark_home
        mark_home(self.data)
        os.makedirs(os.path.join(self.data, "cache"))
        with open(os.path.join(self.data, "cache", "claude.json"), "w") as f:
            f.write("{}")
        self.hold()
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            code = main(["forget", "--all", "--yes", "--data-dir", self.data])
        self.assertEqual(code, 2)
        self.assertIn("another tinkerprint run is using", err.getvalue())
        self.assertTrue(os.path.exists(os.path.join(self.data, "cache", "claude.json")))

    def test_the_lock_nests_and_forget_all_leaves_nothing(self):
        from tinkerprint.cli import main
        from tinkerprint.datadir import LOCK, data_lock, mark_home
        mark_home(self.data)
        with data_lock(self.data):
            with data_lock(self.data):  # the same process never waits on itself
                pass
        self.assertTrue(os.path.exists(os.path.join(self.data, LOCK)))
        os.makedirs(os.path.join(self.data, "cache"))
        with open(os.path.join(self.data, "cache", "claude.json"), "w") as f:
            f.write("{}")
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["forget", "--all", "--yes", "--data-dir", self.data]), 0)
        self.assertFalse(os.path.exists(self.data))

    def test_a_released_lock_is_free(self):
        from tinkerprint.datadir import data_lock
        child = self.hold()
        child.stdin.write("\n")
        child.stdin.flush()
        child.wait()
        with data_lock(self.data, wait=5):
            pass


if __name__ == "__main__":
    unittest.main()
