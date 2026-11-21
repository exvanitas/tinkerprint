"""Review round 3: git priors (S2), clones (4), history (5), audit (6), comparison (7), exact shares (8),
paths (9), unassigned and guards (10), and the P3s (11)."""
import io
import json
import math
import ntpath
import os
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
from helpers import commit, edit, profile, project, run, session, stat
from tinkerprint.build import build
from tinkerprint.demo import RepoWriter, git_env
from tinkerprint.profile import ProfileError, load_profile

UTC = ZoneInfo("UTC")
ME = ("Ida Fenwick", "ida@fenwick.example.test")
TS = "2026-03-02T10:00:00+00:00"
L = math.log1p


def git(cwd, *args, check=True, when=TS):
    env = dict(git_env(), GIT_AUTHOR_NAME=ME[0], GIT_AUTHOR_EMAIL=ME[1], GIT_COMMITTER_NAME=ME[0],
               GIT_COMMITTER_EMAIL=ME[1], GIT_AUTHOR_DATE=when, GIT_COMMITTER_DATE=when)
    return subprocess.run(["git", "-C", cwd, *args], capture_output=True, text=True, env=env, check=check)


def write_profile(path, projects, extra=""):
    with open(path, "w", encoding="utf-8") as f:
        f.write(f'name = "Ida"\n{extra}\n[identity]\nemails = ["{ME[1]}"]\n[harnesses]\nclaude = false\ncodex = false\n')
        for name, roots in projects:
            f.write(f'[[project]]\nname = "{name}"\nroots = {json.dumps(roots)}\n')
    return load_profile(path)


class Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def go(self, prof, out="out", **kw):
        kw.setdefault("home", os.path.join(self.t, "data"))
        return build(prof, os.path.join(self.t, out), **kw)


class S2PriorsFromGit(Tmp):
    def test_checkout_state_does_not_change_a_historical_sheet(self):
        root = os.path.join(self.t, "repo")
        r = RepoWriter(root)
        r.touch(datetime(2026, 1, 5, 10, tzinfo=UTC), ME, {"train.py": 3})
        r.touch(datetime(2026, 2, 5, 10, tzinfo=UTC), ME, {"requirements.txt": 1})
        r.write()
        with open(os.path.join(root, "requirements.txt"), "w") as f:
            f.write("numpy\n")
        git(root, "commit", "-qam", "plain deps", when="2026-02-05T11:00:00+00:00")
        prof = write_profile(os.path.join(self.t, "p.toml"), [("A", [root])])
        jan = self.go(prof, "o1", as_of=date(2026, 1, 31))["sheet"]["class"]["name"]
        with open(os.path.join(root, "requirements.txt"), "w") as f:
            f.write("torch\n")  # uncommitted
        self.assertEqual(self.go(prof, "o2", as_of=date(2026, 1, 31))["sheet"]["class"]["name"], jan)
        self.assertEqual(jan, "Sage")


class Item04CloneKeys(Tmp):
    def test_roots_at_different_depths_share_file_keys(self):
        a = os.path.join(self.t, "clone1")
        r = RepoWriter(a)
        r.touch(datetime(2026, 3, 2, 10, tzinfo=UTC), ME, {"sub/x.py": 3})
        r.write()
        b = os.path.join(self.t, "clone2")
        subprocess.run(["git", "clone", "-q", a, b], check=True, env=git_env())
        other = os.path.join(self.t, "other")
        r = RepoWriter(other)
        r.touch(datetime(2026, 3, 2, 10, tzinfo=UTC), ME, {"y.py": 1})
        r.write()
        prof = write_profile(os.path.join(self.t, "p.toml"), [("A", [a, os.path.join(b, "sub")]), ("B", [other])])
        from tinkerprint.build import gather
        from tinkerprint.events import Inputs
        from tinkerprint.score import score_core
        inp = gather(prof, os.path.join(self.t, "data"))
        evs = list(inp.events) + [edit("2026-03-02T12:00:00+00:00", os.path.join(os.path.realpath(b), "sub", "x.py"))]
        sheet, _ = score_core(Inputs(events=evs, commits=inp.commits, root_ids=inp.root_ids), prof, {})
        self.assertAlmostEqual(project(sheet, "A")["points"], 0.5, places=5)

    def full_and_shallow(self, names=("a-shallow", "z-full"), history=True):
        full = os.path.join(self.t, names[1])
        r = RepoWriter(full)
        r.touch(datetime(2026, 3, 1, 10, tzinfo=UTC), ME, {"old.md": 2})
        if history:
            r.touch(datetime(2026, 3, 2, 10, tzinfo=UTC), ME, {"x.py": 2})
        r.write()
        shallow = os.path.join(self.t, names[0])
        subprocess.run(["git", "clone", "-q", "--depth", "1", "file://" + full, shallow], check=True,
                       env=git_env(), capture_output=True)
        return full, shallow

    def test_complete_copy_supplies_the_diff(self):
        full, shallow = self.full_and_shallow()
        prof = write_profile(os.path.join(self.t, "p.toml"), [("A", [shallow, full])])
        sheet = self.go(prof, season=(date(2026, 3, 2), date(2026, 3, 2)))["sheet"]
        self.assertAlmostEqual(stat(sheet, "Logic")["share"], 1.0)

    def test_complete_copy_proves_the_first_commit(self):
        full, shallow = self.full_and_shallow(history=False)
        r = RepoWriter(full)  # add later history to the full copy only
        git(full, "commit", "-q", "--allow-empty", "-m", "later", when="2026-03-05T10:00:00+00:00")
        prof = write_profile(os.path.join(self.t, "p.toml"), [("A", [shallow, full])])
        sheet = self.go(prof)["sheet"]
        self.assertIn("founder", [a["id"] for a in sheet["achievements"]])


class Item05History(Tmp):
    def repo(self, days):
        root = os.path.join(self.t, "repo")
        r = RepoWriter(root)
        for d in days:
            r.touch(datetime(2026, 3, d, 10, tzinfo=UTC), ME, {f"f{d}.py": 2})
        r.write()
        return write_profile(os.path.join(self.t, "p.toml"), [("A", [root])])

    def test_failed_bookkeeping_saves_no_history(self):
        prof = self.repo([1, 2, 3])
        os.makedirs(os.path.join(self.t, "data"))
        open(os.path.join(self.t, "data", "last-build"), "w").close()
        with self.assertRaises(Exception):
            self.go(prof, as_of=date(2026, 3, 1))
        os.remove(os.path.join(self.t, "data", "last-build"))
        res = self.go(prof, as_of=date(2026, 3, 3))
        self.assertIsNone(res["changes"]["against"])

    def test_default_date_covers_future_events(self):
        prof = self.repo([1, 5])
        self.go(prof, "o1", today=date(2026, 3, 1))
        res = self.go(prof, "o2", as_of=date(2026, 3, 2))
        self.assertIsNone(res["changes"]["against"])


class Item06AuditParsesXml(Tmp):
    def audit(self, svg):
        from tinkerprint.audit import audit_card
        out = os.path.join(self.t, "card")
        os.makedirs(out, exist_ok=True)
        with open(os.path.join(out, "card.svg"), "w") as f:
            f.write(svg)
        return "\n".join(audit_card(out, profile([("A", "/w/a", None)])))

    def test_cdata_and_single_quotes(self):
        text = self.audit("<svg xmlns='http://www.w3.org/2000/svg' aria-label='Private label'>"
                          "<text><![CDATA[Private note]]></text><desc>Desc text</desc></svg>")
        for s in ("Private label", "Private note", "Desc text"):
            self.assertIn(s, text)

    def test_malformed_is_not_certified(self):
        text = self.audit("<svg><text>open")
        self.assertIn("not valid", text)
        self.assertNotIn("nothing else", text)


class Item07Comparison(unittest.TestCase):
    def test_first_class_is_new(self):
        from tinkerprint.score import compare
        prof = profile([("A", "/w/a", None)])
        before, _ = run(prof, [session(TS, "/w/a")])
        after, _ = run(prof, [session(TS, "/w/a"), commit(TS, "/w/a/x.py")])
        ch = compare(after, before, "2026-03-01")
        self.assertTrue(ch["new_class"])
        self.assertEqual(ch["class_from"], "Unclassed")

    def test_set_change_still_compares_points(self):
        from tinkerprint.score import compare
        before, _ = run(profile([("A", "/w/a", None)]), [commit(TS, "/w/a/x.py")])
        after, _ = run(profile([("A", "/w/a", None)], set="tinkerer"),
                       [commit(TS, "/w/a/x.py"), commit("2026-03-03T10:00:00+00:00", "/w/a/y.py")])
        ch = compare(after, before, "2026-03-02")
        self.assertEqual(ch["against"], "2026-03-02")
        self.assertEqual(ch["points_since"], 1)
        self.assertTrue(ch["set_changed"])


class Item08ExactShares(unittest.TestCase):
    def test_equal_points_tie_by_set_order(self):
        prof = profile([("A", "/w/a", None)])
        evs = []
        for i, (ui, lo) in enumerate([(1, 3), (1, 1), (1, 0), (0, 1), (3, 1)]):
            day = f"2026-03-{i + 1:02d}T10:00:00+00:00"
            evs += [commit(day, f"/w/a/ui{i}_{k}.tsx", h=f"u{i}{k}") for k in range(ui)]
            evs += [commit(day, f"/w/a/lo{i}_{k}.py", h=f"l{i}{k}") for k in range(lo)]
        sheet, _ = run(prof, evs)
        self.assertEqual(sheet["class"]["name"], "Illusionist")

    def test_thresholds_are_exact(self):
        from tinkerprint.classes import raw_class
        cls = raw_class({"Logic": 0.4999999999995, "Interface": 0.31, "Tests": 0.1900000000005}, "builder")
        self.assertEqual(cls["kind"], "pair")


class Item09Paths(unittest.TestCase):
    def test_windows_containment(self):
        from tinkerprint.projects import Resolver
        prof = profile([("A", "/w/a", None)])
        prof.projects[0].roots = ["C:\\repo"]
        r = Resolver(prof.projects, pathmod=ntpath)
        hit = r.resolve_root("C:\\repo\\src\\x.py")
        self.assertEqual(hit[2], "src/x.py")

    def test_profile_root_with_nul_is_refused(self):
        with self.assertRaises(ProfileError):
            profile([("A", "/w/a\u0000b", None)])


class Item10UnassignedAndGuards(Tmp):
    def test_cli_and_sheet_share_totals(self):
        from tinkerprint.cli import unassigned_lines
        prof = profile([("A", "/w/a", None)])
        evs = [session(TS, "/w/out-a", sid="s1"), session("2026-03-02T11:00:00+00:00", "/w/out-b", sid="s1"),
               commit(TS, "/w/out-c/z.py")]
        sheet, local = run(prof, evs)
        self.assertEqual(sheet["unassigned"]["sessions"], 1)
        self.assertEqual(sheet["unassigned"]["folders"], 3)
        self.assertIn("1 session in 3 folders", "\n".join(unassigned_lines(sheet, local, 10)))

    def test_undecodable_manifest_is_skipped_with_an_alias(self):
        root = os.path.join(self.t, "secret-folder")
        os.makedirs(root)
        with open(os.path.join(root, "requirements.txt"), "wb") as f:
            f.write(b"\x80\x81\xfe torch\n")
        prof = write_profile(os.path.join(self.t, "p.toml"), [("Alias A", [root])])
        res = self.go(prof)
        text = "\n".join(res["warnings"])
        self.assertIn("Alias A", text)
        self.assertNotIn("secret-folder", text)

    def test_guard_checks_final_folders(self):
        root = os.path.join(self.t, "repo")
        r = RepoWriter(root)
        r.touch(datetime(2026, 3, 2, 10, tzinfo=UTC), ME, {"x.py": 1})
        r.write()
        prof = write_profile(os.path.join(self.t, "p.toml"), [("A", [root])])
        home = os.path.join(self.t, "safe")
        os.makedirs(os.path.join(home, "history"))
        os.symlink(root, os.path.join(home, "history", prof.id))
        with self.assertRaises(ValueError):
            self.go(prof, home=home)


class Item11P3(Tmp):
    def test_record_separator_in_a_file_name(self):
        root = os.path.join(self.t, "repo")
        os.makedirs(root)
        git(root, "init", "-q", "-b", "main")
        with open(os.path.join(root, "before\x1eafter.py"), "w") as f:
            f.write("x\n")
        git(root, "add", ".")
        git(root, "commit", "-qm", "x")
        from tinkerprint.readers.git import Identity, read_git
        res = read_git([root], Identity([ME[1]], []))
        self.assertEqual([os.path.basename(e.path) for e in res.events], ["before\x1eafter.py"])

    def test_card_class_lines_fit(self):
        from tinkerprint.render_card import render_card
        prof = profile([("A", "/w/a", {"stats": {"Infra": 40, "Tools": 21, "Data": 20, "Tests": 10, "Docs": 9}})])
        sheet, _ = run(prof, [commit(TS, "/w/a/x.py")])
        svg = render_card(sheet["card"])
        self.assertIn(sheet["class"]["display"], svg)
        self.assertIn(sheet["multiclass"]["display"], svg)
        self.assertNotIn("\u2026", svg)

    def test_necromancer_needs_180_quiet_days(self):
        def ach(gap):
            evs = [commit("2025-01-01T10:00:00+00:00", "/w/a/x.py", h="a"),
                   commit(f"{date(2025, 1, 1) + timedelta(days=gap)}T10:00:00+00:00", "/w/a/x.py", h="b")]
            from tinkerprint.events import Commit
            commits = [Commit(ts=e.ts, hash=e.commit, repo="r", top="/w/a", mine=True, bot=False, root=False)
                       for e in evs]
            return [a["id"] for a in run(profile([("A", "/w/a", None)]), evs, commits=commits)[0]["achievements"]]
        self.assertNotIn("necromancer", ach(180))
        self.assertIn("necromancer", ach(181))

    def test_polyglot_needs_past_1000(self):
        def ach(n):
            evs = [commit(f"2026-01-0{i + 1}T10:00:00+00:00", f"/w/a/f.{x}", h=f"p{i}", status="A", added=n)
                   for i, x in enumerate(("py", "ts", "go", "rs", "sql"))]
            return [a["id"] for a in run(profile([("A", "/w/a", None)]), evs)[0]["achievements"]]
        self.assertNotIn("polyglot", ach(1000))
        self.assertIn("polyglot", ach(1001))

    def test_seasons_turn_needs_no_consecutive_quarters(self):
        evs = []
        for year, month in ((2024, 1), (2024, 7), (2025, 1), (2025, 10)):
            evs += [commit(f"{date(year, month, 1) + timedelta(days=k)}T10:00:00+00:00", "/w/a/x.py",
                           h=f"{year}{month}{k}") for k in range(10)]
        self.assertIn("seasons-turn", [a["id"] for a in run(profile([("A", "/w/a", None)]), evs)[0]["achievements"]])

    def test_audit_out_without_a_usable_profile(self):
        from tinkerprint.cli import main
        out = os.path.join(self.t, "card")
        os.makedirs(out)
        with open(os.path.join(out, "card.svg"), "w") as f:
            f.write("<svg xmlns='http://www.w3.org/2000/svg'><text>Hello card</text></svg>")
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(["audit", "--profile", os.path.join(self.t, "missing.toml"), "--out", out])
        self.assertIn("Hello card", buf.getvalue())


class Item01CardFloor(unittest.TestCase):
    def test_shares_under_five_percent_stay_off_the_card(self):
        prof = profile([("A", "/w/a", None)])
        evs = [commit(f"{date(2026, 1, 1) + timedelta(days=k)}T10:00:00+00:00", "/w/a/x.py", h=f"l{k}") for k in range(20)]
        evs += [commit(f"{date(2026, 2, 1) + timedelta(days=k)}T10:00:00+00:00", "/w/a/README.md", h=f"d{k}")
                for k in range(4)]
        evs.append(commit("2026-03-01T10:00:00+00:00", "/w/a/tests/test_x.py", h="t"))
        sheet, _ = run(prof, evs)
        pct = {s["stat"]: s["pct"] for s in sheet["card"]["stats"]}
        self.assertEqual(pct["Tests"], 0)
        self.assertEqual(sheet["card"]["chart"], "bars")


if __name__ == "__main__":
    unittest.main()
