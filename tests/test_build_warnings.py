"""A build says why it may have found less than expected, and lists unassigned folders only on request.
Every name, path and email here is invented."""
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, datetime
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
from helpers import profile, run, session
from tinkerprint.build import build, setup_warnings
from tinkerprint.cli import main, unassigned_lines
from tinkerprint.demo import RepoWriter, write_claude_session
from tinkerprint.events import Inputs
from tinkerprint.profile import load_profile

UTC = ZoneInfo("UTC")
ME = ("Ida Fenwick", "ida@fenwick.example.test")
NOREPLY = ("Ida Fenwick", "4242+ida@users.noreply.example.test")
MATE = ("Oren Pell", "oren@fenwick.example.test")
BOT = ("renovate[bot]", "bot@renovate.example.test")


class Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = os.path.realpath(self.tmp.name)
        self.claude = os.path.join(self.t, "logs", "claude")
        self.codex = os.path.join(self.t, "logs", "codex")

    def tearDown(self):
        self.tmp.cleanup()

    def repo(self, name, authors):
        root = os.path.join(self.t, name)
        r = RepoWriter(root)
        for k, who in enumerate(authors):
            r.touch(datetime(2026, 3, 2 + k, 10, tzinfo=UTC), who, {f"f{k}.py": 2})
        r.write()
        return root

    def profile(self, projects, harnesses="claude = false\ncodex = false\n"):
        path = os.path.join(self.t, "p.toml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f'name = "Ida"\n[identity]\nemails = ["{ME[1]}"]\n[harnesses]\n{harnesses}')
            for name, roots in projects:
                f.write(f'[[project]]\nname = "{name}"\nroots = {json.dumps(roots)}\n')
        return load_profile(path)

    def build(self, prof):
        return build(prof, os.path.join(self.t, "out"), home=os.path.join(self.t, "data"), today=date(2026, 11, 1))


class RootWarnings(Tmp):
    def test_missing_root_named_by_project_not_path(self):
        prof = self.profile([("Kite", [os.path.join(self.t, "secret-missing")]),
                             ("Loom", [self.repo("loom", [ME]), os.path.join(self.t, "gone-too")])])
        res = self.build(prof)
        text = "\n".join(res["warnings"])
        self.assertIn("Kite: its root does not exist", text)
        self.assertIn("Loom: root 2 of 2 does not exist", text)
        self.assertNotIn("secret-missing", text)
        self.assertEqual(res["local"]["warnings"], res["warnings"])
        self.assertNotIn("does not exist", json.dumps(res["sheet"]))

    def test_no_matching_commits_lists_authors(self):
        root = self.repo("kite", [NOREPLY] * 3 + [MATE] + [BOT] * 2)
        res = self.build(self.profile([("Kite", [root])]))
        text = "\n".join(res["warnings"])
        self.assertIn("Kite: 6 commits in the repo, none by the emails or names under [identity]", text)
        self.assertIn(f"{NOREPLY[0]} <{NOREPLY[1]}> (3), {MATE[0]} <{MATE[1]}> (1)", text)
        self.assertNotIn("renovate", text)
        self.assertNotIn(self.t, text)
        self.assertNotIn("Warning", json.dumps(res["sheet"]))

    def test_at_most_five_authors(self):
        people = [(f"Person {k}", f"p{k}@example.test") for k in range(7)]
        root = self.repo("kite", people + [people[0]])
        text = "\n".join(self.build(self.profile([("Kite", [root])]))["warnings"])
        self.assertIn("Person 0 <p0@example.test> (2)", text)
        self.assertEqual(text.count("@example.test>"), 5)

    def test_quiet_when_commits_match(self):
        root = self.repo("kite", [ME, MATE])
        self.assertEqual(self.build(self.profile([("Kite", [root])]))["warnings"], [])

    def test_folder_of_repos_as_root(self):
        self.repo(os.path.join("code", "a"), [ME])
        self.repo(os.path.join("code", "b"), [ME])
        text = "\n".join(self.build(self.profile([("Kite", [os.path.join(self.t, "code")])]))["warnings"])
        self.assertIn("Kite: its root is not a git repo, but 2 folders in it are", text)

    def test_cli_prints_warnings(self):
        prof = self.profile([("Kite", [os.path.join(self.t, "missing")])])
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            code = main(["build", "--profile", os.path.join(self.t, "p.toml"), "--data-dir",
                         os.path.join(self.t, "data")])
        self.assertEqual(code, 0)
        self.assertIn("Warning: Kite: its root does not exist", out.getvalue())
        self.assertTrue(prof)

    def test_no_git_on_path(self):
        prof = profile([("A", "/w/a", None)])
        text = "\n".join(setup_warnings(prof, Inputs(setup={"git": False, "roots": {}, "repos": {}})))
        self.assertIn("git was not found", text)


class HarnessWarnings(Tmp):
    def harnesses(self):
        return (f'claude = true\ncodex = true\nagy = true\nclaude_dir = "{self.claude}"\n'
                f'codex_dir = "{self.codex}"\nagy_db = "{os.path.join(self.t, "logs", "agy.db")}"\n')

    def test_missing_folders(self):
        res = self.build(self.profile([("Kite", [self.repo("kite", [ME])])], self.harnesses()))
        text = "\n".join(res["warnings"])
        self.assertIn(f"Claude Code is on, but {self.claude} does not exist. Set claude = false", text)
        self.assertIn("Codex is on, but", text)
        self.assertIn("Antigravity is on, but", text)

    def test_present_but_empty(self):
        os.makedirs(self.claude)
        os.makedirs(self.codex)
        text = "\n".join(self.build(self.profile([("Kite", [self.repo("kite", [ME])])], self.harnesses()))["warnings"])
        self.assertIn(f"Claude Code is on, but no sessions were read from {self.claude}", text)
        self.assertIn(f"Codex is on, but no sessions were read from {self.codex}", text)

    def test_quiet_with_sessions(self):
        import random
        root = self.repo("kite", [ME])
        write_claude_session(self.claude, root, datetime(2026, 3, 2, 10, tzinfo=UTC), "model-x",
                             [(datetime(2026, 3, 2, 10, 5, tzinfo=UTC), os.path.join(root, "f0.py"), "Edit")],
                             random.Random(1))
        text = "\n".join(self.build(self.profile([("Kite", [root])],
                                                 f'claude = true\ncodex = false\nclaude_dir = "{self.claude}"\n'))
                         ["warnings"])
        self.assertNotIn("Claude Code", text)

    def test_tilde(self):
        from tinkerprint.build import _tilde
        home = os.path.expanduser("~")
        self.assertEqual(_tilde(os.path.join(home, ".codex", "sessions")), os.path.join("~", ".codex", "sessions"))
        self.assertEqual(_tilde(home + "x"), home + "x")


class Unassigned(unittest.TestCase):
    def sheet(self):
        prof = profile([("A", "/w/a", None)])
        evs = [session("2026-03-02T10:00:00+00:00", "/w/out-a", sid="s1"),
               session("2026-03-02T11:00:00+00:00", "/w/out-b", sid="s2")]
        return run(prof, evs)

    def test_totals_only_by_default(self):
        sheet, local = self.sheet()
        lines = unassigned_lines(sheet, local)
        self.assertEqual(len(lines), 1)
        self.assertIn("2 sessions in 2 folders", lines[0])
        self.assertIn("--list-unassigned N", lines[0])
        self.assertNotIn("/w/out", "\n".join(lines))

    def test_listing_on_request(self):
        sheet, local = self.sheet()
        text = "\n".join(unassigned_lines(sheet, local, 1))
        self.assertIn("/w/out-a", text)
        self.assertNotIn("/w/out-b", text)
        self.assertIn("1 more", text)
        text = "\n".join(unassigned_lines(sheet, local, 5))
        self.assertIn("/w/out-b", text)
        self.assertNotIn("more", text)

    def test_cli_default_is_zero(self):
        from tinkerprint.cli import parser
        args = parser().parse_args(["build", "--profile", "x.toml"])
        self.assertEqual(args.list_unassigned, 0)


if __name__ == "__main__":
    unittest.main()
