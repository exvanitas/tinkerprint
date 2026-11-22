"""0.2.0 review, part 2: the sheet's HTML, parts, small fixes and shallow clones.
Every name, path and email here is invented."""
import json
import os
import subprocess
import tempfile
import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
from tinkerprint.demo import RepoWriter, git_env
from tinkerprint.render_html import _changes
from tinkerprint.score import compare


def sheet_like():
    return {"method": 3, "profile": {"set": "builder"}, "history": {"points": 9, "level": 3},
            "stats": [{"key": "Logic", "share": 1.0}], "party": [{"harness": "claude", "name": "Claude Code",
                                                                  "sessions": 4}],
            "achievements": [], "class": None}


class SavedHistory(unittest.TestCase):
    """A saved sheet that was damaged or edited never breaks a build or puts markup on the page."""

    BAD = "<script>alert(1)</script>"

    def test_text_where_numbers_go(self):
        prev = {"method": 3, "profile": {"set": "builder"},
                "history": {"points": "12; DROP", "level": self.BAD},
                "stats": [{"key": "Logic", "share": "most"}, "junk", {"share": 1}],
                "party": [{"harness": "claude", "sessions": "many"}, {"no": "harness"}],
                "achievements": [{"id": 5}, "x"], "class": {"kind": self.BAD}}
        ch = compare(sheet_like(), prev, "2026-03-01")
        self.assertIsNone(ch["level_from"])
        self.assertEqual(ch["points_since"], 9)
        self.assertEqual(ch["class_from"], "Unclassed")
        html = _changes(ch)
        self.assertNotIn("<script", html)
        self.assertIn("+9 points.", html)

    def test_wrong_shapes_never_raise(self):
        for prev in ({"method": 3, "history": [], "profile": "x", "stats": {}, "party": "x", "achievements": 3},
                     {"method": 3, "history": {"level": True, "points": 1.5}},
                     {"method": [self.BAD]}):
            with self.subTest(prev=prev):
                ch = compare(sheet_like(), prev, "2026-03-01")
                self.assertNotIn("<script", _changes(ch))

    def test_the_panel_escapes_what_it_is_handed(self):
        ch = {"against": "2026-03-01", "points_since": 2, "level_from": self.BAD, "level_to": 3,
              "set_changed": False, "new_class": False, "class_to": "Sage", "drift": [],
              "party_sessions": [{"name": "Claude Code", "sessions_since": self.BAD}]}
        html = _changes(ch)
        self.assertNotIn("<script", html)
        self.assertIn("Claude Code: +0 sessions.", html)


class PartsStayInside(unittest.TestCase):
    """A part is a folder inside its project's root. Nothing outside the root is ever read."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = os.path.realpath(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def parse(self, part):
        from helpers import profile
        return profile([("P", os.path.join(self.t, "root"), {"part": [{"path": part}]})])

    def test_a_part_that_leaves_its_root_is_refused(self):
        from tinkerprint.profile import ProfileError
        for part in ("../other", "..", "web/../../other", ".", "web/..", "C:/other", "c:other"):
            with self.subTest(part=part):
                with self.assertRaises(ProfileError) as cm:
                    self.parse(part)
                self.assertIn("inside the project's root", str(cm.exception))
        self.assertEqual(self.parse("web/./api/").projects[0].parts[0].path, "web/api")
        self.assertEqual(self.parse("web/../api").projects[0].parts[0].path, "api")

    def test_a_linked_part_is_not_read(self):
        from tinkerprint.projects import scan_priors
        root, other = os.path.join(self.t, "root"), os.path.join(self.t, "other")
        os.makedirs(root)
        os.makedirs(other)
        with open(os.path.join(other, "package.json"), "w") as f:
            json.dump({"name": "x", "bin": {"x": "x.js"}}, f)
        with open(os.path.join(other, "requirements.txt"), "w") as f:
            f.write("torch\n")
        os.symlink(other, os.path.join(root, "web"))
        os.makedirs(os.path.join(root, "api"))
        os.symlink(os.path.join(other, "package.json"), os.path.join(root, "api", "package.json"))
        from helpers import profile
        prof = profile([("P", root, {"part": [{"path": "web"}, {"path": "api"}]})])
        self.assertEqual(scan_priors(prof.projects)["P"], {})


class SmallOnes(unittest.TestCase):
    def test_list_unassigned_prints_at_most_n_once_each(self):
        from tinkerprint.cli import unassigned_lines
        sheet = {"unassigned": {"sessions": 3, "folders": 4, "edits": 3}}
        local = {"unassigned_folders": [("/w/a", 2), ("/w/b", 1)],
                 "unassigned_edit_folders": ["/w/a", "/w/c", "/w/c", "/w/d"]}
        one = unassigned_lines(sheet, local, 1)
        self.assertEqual(one[1:], ["     2  /w/a", "  ... 3 more. Use --list-unassigned N to see them."])
        three = unassigned_lines(sheet, local, 3)
        self.assertEqual(three[1:], ["     2  /w/a", "     1  /w/b", "        /w/c",
                                     "  ... 1 more. Use --list-unassigned N to see them."])
        every = unassigned_lines(sheet, local, 10)
        self.assertEqual(every[1:], ["     2  /w/a", "     1  /w/b", "        /w/c", "        /w/d"])
        self.assertIn("Use --list-unassigned N", unassigned_lines(sheet, local, 0)[0])

    def test_a_project_name_must_be_text(self):
        from helpers import profile
        from tinkerprint.profile import ProfileError
        for name in (False, 0, "", ["x"]):
            with self.subTest(name=name):
                with self.assertRaises(ProfileError) as cm:
                    profile([("P", "/w", None)], project=[{"name": name, "root": "/w"}])
                self.assertIn("name must be", str(cm.exception))
        prof = profile([("P", "/w", None)], project=[{"root": "/w"}])
        self.assertEqual(prof.projects[0].name, "Project 1")


class SameInputsSameSheet(unittest.TestCase):
    """The footer says the build's as-of date, so a fixed --as-of gives the same sheet.html."""

    def test_two_builds_minutes_apart_are_identical(self):
        import io
        from contextlib import redirect_stdout
        from datetime import datetime as real_dt, timedelta
        from unittest import mock
        from zoneinfo import ZoneInfo
        from tinkerprint import cli
        from tinkerprint.demo import RepoWriter
        ticks = iter(range(100))

        class Clock(real_dt):
            @classmethod
            def now(cls, tz=None):
                return real_dt(2026, 11, 23, 10, next(ticks), tzinfo=tz or ZoneInfo("UTC"))

        with tempfile.TemporaryDirectory() as t:
            t = os.path.realpath(t)
            root = os.path.join(t, "repo")
            r = RepoWriter(root)
            r.touch(real_dt(2026, 3, 2, 10, tzinfo=ZoneInfo("UTC")), ("Ida", "ida@fenwick.example.test"), {"a.py": 2})
            r.write()
            path = os.path.join(t, "p.toml")
            with open(path, "w", encoding="utf-8") as f:
                f.write('name = "Ida"\n[identity]\nemails = ["ida@fenwick.example.test"]\n[harnesses]\n'
                        f'claude = false\ncodex = false\n[[project]]\nname = "P"\nroot = "{root}"\n')
            pages = []
            for out in ("o1", "o2"):
                with mock.patch.object(cli, "datetime", Clock), redirect_stdout(io.StringIO()):
                    self.assertEqual(cli.main(["build", "--profile", path, "--data-dir", os.path.join(t, "data"),
                                               "--out", os.path.join(t, out), "--as-of", "2026-09-15"]), 0)
                with open(os.path.join(t, out, "sheet.html"), "rb") as f:
                    pages.append(f.read())
        self.assertEqual(pages[0], pages[1])
        self.assertIn(b"As of Sep 15, 2026.", pages[0])


class ShallowClones(unittest.TestCase):
    """A shallow clone's boundary commits show their whole tree as added, so they never decide scope,
    and a shallow repo never proves a first commit."""

    ME = ("Ida Fenwick", "ida@fenwick.example.test")
    UTC = ZoneInfo("UTC")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = os.path.realpath(self.tmp.name)
        self.data = os.path.join(self.t, "data")

    def tearDown(self):
        self.tmp.cleanup()

    def git(self, cwd, *args, when="2026-03-05T10:00:00+00:00"):
        env = dict(git_env(), GIT_AUTHOR_NAME=self.ME[0], GIT_AUTHOR_EMAIL=self.ME[1], GIT_COMMITTER_NAME=self.ME[0],
                   GIT_COMMITTER_EMAIL=self.ME[1], GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when,
                   GIT_ALLOW_PROTOCOL="file")
        return subprocess.run(["git", "-C", cwd, *args], check=True, capture_output=True, env=env).stdout

    def profile(self, root):
        from tinkerprint.profile import load_profile
        path = os.path.join(self.t, "p.toml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f'name = "Ida"\n[identity]\nemails = ["{self.ME[1]}"]\n[harnesses]\nclaude = false\n'
                    f'codex = false\n[[project]]\nname = "Kite"\nroot = "{root}"\n')
        return load_profile(path)

    def build(self, prof):
        from tinkerprint.build import build
        return build(prof, os.path.join(self.t, "out"), home=self.data, today=date(2026, 11, 1))

    def test_a_boundary_commit_never_puts_a_tag_in_scope(self):
        full = os.path.join(self.t, "full")
        r = RepoWriter(full)
        r.touch(datetime(2026, 3, 1, 10, tzinfo=self.UTC), self.ME, {"sub/x.py": 2, "other/y.py": 2})
        r.touch(datetime(2026, 3, 2, 10, tzinfo=self.UTC), self.ME, {"other/y.py": 2}, tag="v1.0.0")
        r.write()
        shallow = os.path.join(self.t, "shallow")
        self.git(self.t, "clone", "-q", "--depth", "1", "file://" + full, shallow)
        res = self.build(self.profile(os.path.join(shallow, "sub")))
        ids = [a["id"] for a in res["sheet"]["achievements"]]
        self.assertNotIn("shipwright", ids)
        self.assertNotIn("founder", ids)
        shallow_lines = [w for w in res["warnings"] if "shallow" in w]
        self.assertEqual(len(shallow_lines), 1)
        self.assertTrue(shallow_lines[0].startswith("Kite: "), shallow_lines[0])
        self.assertNotIn(shallow, shallow_lines[0])
        # The same history, complete, puts the tag out of scope too: it touched only other/.
        res = self.build(self.profile(os.path.join(full, "sub")))
        self.assertNotIn("shipwright", [a["id"] for a in res["sheet"]["achievements"]])
        self.assertFalse([w for w in res["warnings"] if "shallow" in w])

    def test_a_shallow_repo_never_earns_founder(self):
        full = os.path.join(self.t, "full")
        r = RepoWriter(full)
        r.touch(datetime(2026, 3, 1, 10, tzinfo=self.UTC), self.ME, {"a.py": 2})
        r.touch(datetime(2026, 3, 2, 10, tzinfo=self.UTC), self.ME, {"a.py": 2})
        r.touch(datetime(2026, 3, 3, 10, tzinfo=self.UTC), self.ME, {"a.py": 2})
        r.write()
        tree = self.git(full, "rev-parse", "HEAD^{tree}").decode().strip()
        side = self.git(full, "commit-tree", tree, "-m", "side", when="2026-02-01T10:00:00+00:00").decode().strip()
        self.git(full, "update-ref", "refs/heads/side", side)
        shallow = os.path.join(self.t, "shallow")
        # At depth 2 the side branch's root is whole, not cut off: no parents, and not a boundary.
        self.git(self.t, "clone", "-q", "--depth", "2", "--no-single-branch", "file://" + full, shallow)
        with open(os.path.join(shallow, ".git", "shallow")) as f:
            self.assertNotIn(side, f.read())
        res = self.build(self.profile(shallow))
        self.assertNotIn("founder", [a["id"] for a in res["sheet"]["achievements"]])
        self.assertTrue(any(w.startswith("Kite: ") and "shallow" in w for w in res["warnings"]))
        res = self.build(self.profile(full))
        self.assertIn("founder", [a["id"] for a in res["sheet"]["achievements"]])


if __name__ == "__main__":
    unittest.main()
