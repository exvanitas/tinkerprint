"""Review round 1: git reader findings. All repos and identities are invented."""
import os
import subprocess
import tempfile
import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
from helpers import commit, profile, project, run
from tinkerprint.build import build, gather
from tinkerprint.demo import RepoWriter, git_env
from tinkerprint.profile import load_profile
from tinkerprint.readers.git import Identity, read_git

UTC = ZoneInfo("UTC")
ME = ("Ida Fenwick", "ida@fenwick.example.test")
WHO = f"{ME[0]} <{ME[1]}>"


def git(cwd, *args, check=True):
    env = dict(git_env(), GIT_AUTHOR_NAME=ME[0], GIT_AUTHOR_EMAIL=ME[1], GIT_COMMITTER_NAME=ME[0],
               GIT_COMMITTER_EMAIL=ME[1], GIT_AUTHOR_DATE="2026-03-02T10:00:00+00:00",
               GIT_COMMITTER_DATE="2026-03-02T10:00:00+00:00")
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, env=env, check=check)


def write_profile(path, roots):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f'name = "Ida"\n[identity]\nemails = ["{ME[1]}"]\n[harnesses]\nclaude = false\ncodex = false\n')
        for i, root in enumerate(roots):
            if isinstance(root, list):
                f.write(f'[[project]]\nname = "P{i}"\nroots = {root!r}\n'.replace("'", '"'))
            else:
                f.write(f'[[project]]\nname = "P{i}"\nroot = "{root}"\n')
    return path


class Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()


class Item07NoFetchInPartialClones(Tmp):
    def test_partial_clone_reads_without_fetching(self):
        src = os.path.join(self.t, "src")
        r = RepoWriter(src)
        for d in range(3):
            r.touch(datetime(2026, 3, 2 + d, 10, tzinfo=UTC), ME, {"a.py": 5, f"b{d}.py": 3})
        r.write()
        git(src, "config", "uploadpack.allowFilter", "true")
        clone = os.path.join(self.t, "clone")
        subprocess.run(["git", "clone", "-q", "--filter=blob:none", "file://" + src, clone], check=True,
                       env=git_env(), capture_output=True)

        def missing():
            out = git(clone, "rev-list", "--objects", "--all", "--missing=print").stdout
            return sum(1 for line in out.splitlines() if line.startswith("?"))

        before = missing()
        self.assertGreater(before, 0)
        res = read_git([clone], Identity([ME[1]], []))
        self.assertEqual(missing(), before)
        self.assertEqual(len([c for c in res.commits if c.mine]), 3)
        self.assertTrue(any("incomplete local history" in w for w in res.warnings))


class Item12CloneChoiceFollowsRoots(Tmp):
    def test_assigned_clone_wins(self):
        a = os.path.join(self.t, "aa")
        r = RepoWriter(a)
        r.touch(datetime(2026, 3, 2, 10, tzinfo=UTC), ME, {"back/service.py": 3, "front/app.py": 1})
        r.write()
        b = os.path.join(self.t, "bb")
        subprocess.run(["git", "clone", "-q", a, b], check=True, env=git_env())
        prof = load_profile(write_profile(os.path.join(self.t, "p.toml"),
                                          [os.path.join(a, "front"), os.path.join(b, "back")]))
        sheet = build(prof, os.path.join(self.t, "out"), home=os.path.join(self.t, "data"))["sheet"]
        names = sorted(p["name"] for p in sheet["projects"])
        self.assertEqual(names, ["P0", "P1"])


class Item14RootsKeepSeparateFileKeys(Tmp):
    def test_two_roots_of_one_project(self):
        front, server, other = (os.path.join(self.t, n) for n in ("front", "server", "other"))
        for root, files in ((front, {"main.py": 2}), (server, {"main.py": 3}), (other, {"x.py": 1})):
            r = RepoWriter(root)
            r.touch(datetime(2026, 3, 2, 10, tzinfo=UTC), ME, files)
            r.write()
        prof = load_profile(write_profile(os.path.join(self.t, "p.toml"), [[front, server], other]))
        sheet = build(prof, os.path.join(self.t, "out"), home=os.path.join(self.t, "data"))["sheet"]
        L = __import__("math").log1p
        self.assertAlmostEqual(project(sheet, "P0")["points"], L(2) / (L(2) + L(1)), places=5)

    def test_clone_and_worktree_of_one_repo_still_count_once(self):
        main = os.path.join(self.t, "main")
        r = RepoWriter(main)
        r.touch(datetime(2026, 3, 2, 10, tzinfo=UTC), ME, {"a.py": 2})
        r.write()
        wt = os.path.join(self.t, "wt")
        git(main, "worktree", "add", "-q", wt)
        prof = load_profile(write_profile(os.path.join(self.t, "p.toml"), [[main, wt]]))
        inputs = gather(prof, os.path.join(self.t, "data"))
        evs = list(inputs.events) + [commit("2026-03-02T11:00:00+00:00", os.path.join(wt, "a.py"), h="x")]
        from tinkerprint.events import Inputs
        from tinkerprint.score import score_core
        core, _ = score_core(Inputs(events=evs, commits=inputs.commits, root_ids=inputs.root_ids), prof, {})
        self.assertEqual(core["inputs"]["commits"], 2)
        self.assertEqual(len(core["projects"]), 1)


class Item15MergeResolutions(Tmp):
    def test_conflict_resolution_counts(self):
        root = os.path.join(self.t, "repo")
        os.makedirs(root)
        git(root, "init", "-q", "-b", "main")
        with open(os.path.join(root, "f.py"), "w") as f:
            f.write("a\nb\nc\n")
        git(root, "add", ".")
        git(root, "commit", "-qm", "base")
        git(root, "checkout", "-qb", "side")
        with open(os.path.join(root, "f.py"), "w") as f:
            f.write("a\nSIDE\nc\n")
        with open(os.path.join(root, "clean.py"), "w") as f:
            f.write("x\n")
        git(root, "add", ".")
        git(root, "commit", "-qm", "side")
        git(root, "checkout", "-q", "main")
        with open(os.path.join(root, "f.py"), "w") as f:
            f.write("a\nMAIN\nc\n")
        git(root, "commit", "-qam", "main")
        git(root, "merge", "-q", "side", check=False)
        with open(os.path.join(root, "f.py"), "w") as f:
            f.write("a\nRESOLVED\nc\n")
        git(root, "add", ".")
        env_date = "2026-03-09T10:00:00+00:00"
        subprocess.run(["git", "-C", root, "commit", "-qm", "merge"], check=True, capture_output=True,
                       env=dict(git_env(), GIT_AUTHOR_NAME=ME[0], GIT_AUTHOR_EMAIL=ME[1], GIT_COMMITTER_NAME=ME[0],
                                GIT_COMMITTER_EMAIL=ME[1], GIT_AUTHOR_DATE=env_date, GIT_COMMITTER_DATE=env_date))
        res = read_git([root], Identity([ME[1]], []))
        merge_files = sorted(os.path.basename(e.path) for e in res.events if e.ts.startswith("2026-03-09"))
        self.assertEqual(merge_files, ["f.py"])
        self.assertTrue(all(e.added == 0 for e in res.events if e.ts.startswith("2026-03-09")))


if __name__ == "__main__":
    unittest.main()
