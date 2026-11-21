"""Review round 2, git and build items. Each test reproduces a reported case. All data is invented."""
import copy
import io
import json
import math
import os
import sqlite3
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, datetime
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
from helpers import commit, edit, profile, project, run, session
from tinkerprint.demo import RepoWriter, git_env, write_agy_db
from tinkerprint.profile import ProfileError, load_profile, parse_profile
from tinkerprint.readers import agy, claude, codex

UTC = ZoneInfo("UTC")
ME = ("Ida Fenwick", "ida@fenwick.example.test")
MATE = ("Oren Pell", "oren@fenwick.example.test")
TS = "2026-03-02T10:00:00+00:00"
L = math.log1p
SECRET = "FUZZSECRET"
WRONG = ({"message": SECRET}, [SECRET], 7, None, True)


def write_lines(path, records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write((r if isinstance(r, str) else json.dumps(r)) + "\n")
    return path


def key_paths(obj, prefix=()):
    """Every key path in a JSON value, sorted, so the fuzz is deterministic."""
    out = []
    if isinstance(obj, dict):
        for k in sorted(obj):
            out.append(prefix + (k,))
            out += key_paths(obj[k], prefix + (k,))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.append(prefix + (i,))
            out += key_paths(v, prefix + (i,))
    return out


def mutated(records, index, path, value):
    recs = copy.deepcopy(records)
    target = recs[index]
    for k in path[:-1]:
        target = target[k]
    target[path[-1]] = copy.deepcopy(value)
    return recs


def stringified(evs):
    """Event string fields that look like a printed dict or list, or carry the planted text."""
    bad = []
    for e in evs:
        for k, v in e.to_dict().items():
            if isinstance(v, str) and (SECRET in v or v.startswith(("{", "[")) or "{'" in v or "['" in v):
                bad.append((k, v))
    return bad


CLAUDE_FIXTURE = [
    {"type": "user", "sessionId": "cs1", "timestamp": "2026-03-02T10:00:00Z", "cwd": "/w/a",
     "message": {"role": "user", "content": "invented"}},
    {"type": "assistant", "sessionId": "cs1", "timestamp": "2026-03-02T10:01:00Z", "cwd": "/w/a",
     "message": {"role": "assistant", "model": "m-1", "content": [
         {"type": "tool_use", "id": "t1", "name": "Edit", "input": {"file_path": "/w/a/x.py"}}]}},
    {"type": "user", "sessionId": "cs1", "timestamp": "2026-03-02T10:01:05Z", "cwd": "/w/a",
     "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]}},
]
CODEX_FIXTURE = [
    {"timestamp": "2026-03-02T10:00:00Z", "type": "session_meta",
     "payload": {"id": "s1", "timestamp": "2026-03-02T10:00:00Z", "cwd": "/w/a", "originator": "codex_exec"}},
    {"timestamp": "2026-03-02T10:00:01Z", "type": "turn_context", "payload": {"model": "m-2", "cwd": "/w/a"}},
    {"timestamp": "2026-03-02T10:02:00Z", "type": "event_msg", "payload": {"type": "item_completed", "item": {
        "type": "FileChange", "id": "fc1", "status": "completed", "changes": {"/w/a/x.py": {"type": "update"}}}}},
    {"timestamp": "2026-03-02T10:03:00Z", "type": "event_msg", "payload": {
        "type": "patch_apply_end", "call_id": "c9", "success": True, "changes": {"/w/a/y.py": {"type": "add"}}}},
]




class Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()


def git(cwd, *args, check=True):
    env = dict(git_env(), GIT_AUTHOR_NAME=ME[0], GIT_AUTHOR_EMAIL=ME[1], GIT_COMMITTER_NAME=ME[0],
               GIT_COMMITTER_EMAIL=ME[1], GIT_AUTHOR_DATE=TS, GIT_COMMITTER_DATE=TS)
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, env=env, check=check)


def write_profile(path, projects, extra=""):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f'name = "Ida"\n{extra}\n[identity]\nemails = ["{ME[1]}"]\n[harnesses]\nclaude = false\ncodex = false\n')
        for name, roots in projects:
            f.write(f'[[project]]\nname = "{name}"\nroots = {json.dumps(roots)}\n')
    return load_profile(path)


class GitItems(Tmp):
    def repo(self, name, files=None, when=None, tag=""):
        root = os.path.join(self.t, name)
        r = RepoWriter(root)
        r.touch(when or datetime(2026, 3, 2, 10, tzinfo=UTC), ME, files or {"x.py": 3}, tag=tag)
        r.write()
        return root

    def build(self, prof, out="out"):
        from tinkerprint.build import build
        return build(prof, os.path.join(self.t, out), home=os.path.join(self.t, "data"), today=date(2026, 11, 1))

    def test_item07_warnings_use_aliases(self):
        src = os.path.join(self.t, "client-secret-src")
        r = RepoWriter(src)
        for d in range(3):
            r.touch(datetime(2026, 3, 2 + d, 10, tzinfo=UTC), ME, {"a.py": 5, f"b{d}.py": 2})
        r.write()
        git(src, "config", "uploadpack.allowFilter", "true")
        clone = os.path.join(self.t, "client-secret")
        subprocess.run(["git", "clone", "-q", "--filter=blob:none", "file://" + src, clone], check=True,
                       env=git_env(), capture_output=True)
        res = self.build(write_profile(os.path.join(self.t, "p.toml"), [("Project A", [clone])]))
        text = "\n".join(res["warnings"])
        self.assertIn("Project A", text)
        self.assertNotIn("client-secret", text)

    def test_item08_symlinked_root(self):
        real = self.repo("physical")
        link = os.path.join(self.t, "link")
        os.symlink(real, link)
        res = self.build(write_profile(os.path.join(self.t, "p.toml"), [("A", [link])]))
        self.assertEqual(res["sheet"]["history"]["points"], 1)

    def test_item09_tags_dedupe_across_clones(self):
        a = os.path.join(self.t, "a")
        r = RepoWriter(a)
        r.touch(datetime(2026, 3, 2, 10, tzinfo=UTC), ME, {"x.py": 3}, tag="v1.0.0")
        r.write()
        b = os.path.join(self.t, "b")
        subprocess.run(["git", "clone", "-q", a, b], check=True, env=git_env())
        res = self.build(write_profile(os.path.join(self.t, "p.toml"), [("A", [a, b])]))
        ship = [x for x in res["sheet"]["achievements"] if x["id"] == "shipwright"]
        self.assertEqual(ship[0]["count"], 1)

    def test_item11_lightweight_tag_on_your_commit_is_not_yours(self):
        root = self.repo("repo")
        git(root, "tag", "v1.0.0")
        res = self.build(write_profile(os.path.join(self.t, "p.toml"), [("A", [root])]))
        self.assertNotIn("shipwright", [x["id"] for x in res["sheet"]["achievements"]])

    def test_item11_priors_follow_their_own_root(self):
        torch = self.repo("trainer", {"pyproject.toml": 1})
        with open(os.path.join(torch, "pyproject.toml"), "w") as f:
            f.write('[project]\nname = "t"\ndependencies = ["torch"]\n')
        cli = self.repo("cli", {"main.py": 2})
        with open(os.path.join(cli, "package.json"), "w") as f:
            f.write('{"name": "c", "bin": {"c": "main.py"}}')
        for order in ([torch, cli], [cli, torch]):
            prof = write_profile(os.path.join(self.t, "p.toml"), [("A", order)])
            from tinkerprint.projects import scan_priors
            priors = scan_priors(prof.projects)
            sheet, _ = run(prof, [commit(TS, os.path.join(os.path.realpath(cli), "main.py"))], priors=priors)
            self.assertEqual(sheet["class"]["name"], "Artificer", order)

    def test_item11_unicode_names_stay_distinct(self):
        root = os.path.join(self.t, "uni")
        os.makedirs(root)
        git(root, "init", "-q", "-b", "main")
        for name in ('café".py', 'cafè".py'):
            with open(os.path.join(root, name), "w") as f:
                f.write("x\n")
        git(root, "add", ".")
        git(root, "commit", "-qm", "x")
        from tinkerprint.readers.git import Identity, read_git
        res = read_git([root], Identity([ME[1]], []))
        self.assertEqual(len({e.path for e in res.events}), 2)

    def test_item11_shallow_clone_shares_identity(self):
        full = os.path.join(self.t, "full")
        r = RepoWriter(full)
        r.touch(datetime(2026, 3, 1, 10, tzinfo=UTC), ME, {"base.py": 2})
        r.touch(datetime(2026, 3, 2, 10, tzinfo=UTC), ME, {"x.py": 2})
        r.write()
        shallow = os.path.join(self.t, "shallow")
        subprocess.run(["git", "clone", "-q", "--depth", "1", "file://" + full, shallow], check=True,
                       env=git_env(), capture_output=True)
        other = self.repo("other", {"y.py": 1})
        prof = write_profile(os.path.join(self.t, "p.toml"), [("A", [full, shallow]), ("B", [other])])
        from tinkerprint.build import gather
        from tinkerprint.events import Inputs
        from tinkerprint.score import score_core
        inp = gather(prof, os.path.join(self.t, "data"))
        evs = [e for e in inp.events] + [edit("2026-03-02T12:00:00+00:00", os.path.join(os.path.realpath(shallow), "x.py"))]
        sheet, _ = score_core(Inputs(events=evs, commits=inp.commits, root_ids=inp.root_ids), prof, {},
                              (date(2026, 3, 2), date(2026, 3, 2)))
        self.assertAlmostEqual(project(sheet, "A")["points"], 0.5, places=5)
        founders = [x for x in sheet["achievements"] if x["id"] == "founder"]
        self.assertEqual(founders[0]["count"], 2)  # full and other. The shallow boundary is no root.

    def test_item11_audit_uses_the_last_build(self):
        from tinkerprint.cli import main
        root = self.repo("repo")
        p = os.path.join(self.t, "p.toml")
        write_profile(p, [("A", [root])])
        data = os.path.join(self.t, "data")
        with redirect_stdout(io.StringIO()):
            main(["build", "--profile", p, "--data-dir", data])
            main(["build", "--profile", p, "--data-dir", data, "--out", os.path.join(self.t, "export")])
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(["audit", "--profile", p, "--data-dir", data])
        self.assertIn(os.path.join(self.t, "export"), buf.getvalue())

    def test_item11_data_guard_bare_repo_and_symlinked_cache(self):
        from tinkerprint.build import build
        root = self.repo("repo")
        prof = write_profile(os.path.join(self.t, "p.toml"), [("A", [root])])
        bare = os.path.join(self.t, "archive.git")
        subprocess.run(["git", "init", "-q", "--bare", bare], check=True, env=git_env())
        with self.assertRaises(ValueError):
            build(prof, os.path.join(self.t, "o1"), home=os.path.join(bare, "data"))
        home = os.path.join(self.t, "safe")
        os.makedirs(home)
        os.symlink(root, os.path.join(home, "cache"))
        with self.assertRaises(ValueError):
            build(prof, os.path.join(self.t, "o2"), home=home)


if __name__ == "__main__":
    unittest.main()
