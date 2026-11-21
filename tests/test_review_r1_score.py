"""Review round 1: scoring findings."""
import math
import unittest
from datetime import date

import helpers  # noqa: F401
from helpers import commit, edit, profile, project, run, session, stat

L = math.log1p
TS = "2026-03-02T10:00:00+00:00"


class Item13BulkIsPerCommit(unittest.TestCase):
    def test_threshold_counts_the_whole_commit(self):
        prof = profile([("A", "/w/a", None), ("B", "/w/b", None)])
        evs = [commit(TS, f"/w/a/img{i}.png", h="big", status="A") for i in range(101)]
        evs += [commit(TS, f"/w/b/img{i}.png", h="big", status="A") for i in range(100)]
        sheet, _ = run(prof, evs)
        a, b = L(101 / 201), L(100 / 201)
        self.assertAlmostEqual(project(sheet, "A")["points"], a / (a + b), places=5)

    def test_bulk_keeps_unclassified_share_and_same_day_edits(self):
        prof = profile([("A", "/w/a", None)])
        evs = [commit(TS, f"/w/a/notes{i}.md", h="big", status="A") for i in range(101)]
        evs += [commit(TS, f"/w/a/img{i}.png", h="big", status="A") for i in range(100)]
        sheet, _ = run(prof, evs)
        docs, other = L(101 / 201), L(100 / 201)
        self.assertAlmostEqual(stat(sheet, "Docs")["points"], docs / (docs + other), places=5)
        self.assertGreater(sheet["season_totals"]["unclassified"], 0.4)
        with_edit, _ = run(prof, evs + [edit("2026-03-02T12:00:00+00:00", "/w/a/img0.png")])
        self.assertGreater(with_edit["season_totals"]["unclassified"], sheet["season_totals"]["unclassified"])


class Item16PartyStaysInsideRootsAndSeason(unittest.TestCase):
    def test_outside_presence_adds_no_days(self):
        prof = profile([("A", "/w/a", None)])
        evs = [session("2026-03-14T10:00:00+00:00", "/elsewhere", sid="s1"),
               edit("2026-03-17T10:00:00+00:00", "/w/a/x.py", session="s1")]
        sheet, _ = run(prof, evs)
        self.assertEqual(sheet["party"][0]["days_together"], 1)

    def test_models_follow_the_season(self):
        prof = profile([("A", "/w/a", None)])
        evs = [session("2026-03-14T10:00:00+00:00", "/w/a", sid="s1", model="m-old"),
               session("2026-03-17T10:00:00+00:00", "/w/a", sid="s1", model="m-new")]
        sheet, _ = run(prof, evs, season=(date(2026, 3, 17), date(2026, 3, 17)))
        self.assertEqual(sheet["party"][0]["models"], ["m-new"])


class Item18MulticlassHold(unittest.TestCase):
    def test_secondary_class_waits_for_two_points(self):
        def sheet_for(tests, docs, prev=None):
            w = f"{{ Logic = 35, Interface = 25, Data = 16, Tests = {tests}, Docs = {docs} }}"
            import tomllib
            prof = profile([("A", "/w/a", {"stats": tomllib.loads("s = " + w)["s"]})])
            return run(prof, [commit(TS, "/w/a/x.py")], prev=prev)[0]
        first = sheet_for(12.5, 11.5)
        self.assertEqual(first["multiclass"]["stats"], ["Data", "Tests"])
        second = sheet_for(11.5, 12.5, prev=first)
        self.assertEqual(second["multiclass"]["stats"], ["Data", "Tests"])
        self.assertTrue(second["multiclass"]["held"])


class Item20FullPrecisionRanking(unittest.TestCase):
    def test_tiny_lead_is_not_a_tie(self):
        prof = profile([("A", "/w/a", {"stats": {"Interface": 1, "Logic": 1.000001}})])
        sheet, _ = run(prof, [commit(TS, "/w/a/x.py")])
        self.assertEqual(sheet["class"]["name"], "Sage")


class Item21UnassignedFollowsSeason(unittest.TestCase):
    def test_edits_outside_season_are_not_counted(self):
        prof = profile([("A", "/w/a", None)])
        evs = [edit("2026-02-02T10:00:00+00:00", "/elsewhere/x.txt", session="s9"),
               commit("2026-03-02T10:00:00+00:00", "/w/a/x.py")]
        sheet, local = run(prof, evs, season=(date(2026, 3, 1), None))
        self.assertEqual(sheet["unassigned"]["edits"], 0)
        self.assertEqual(local["unassigned_edit_folders"], [])

    def test_cli_lists_edit_folders(self):
        from tinkerprint.cli import unassigned_lines
        prof = profile([("A", "/w/a", None)])
        evs = [session(TS, "/w/a", sid="s1"), edit(TS, "/elsewhere/notes/x.txt", session="s1")]
        _, local = run(prof, evs)
        self.assertIn("/elsewhere/notes", "\n".join(unassigned_lines(local, 10)))


if __name__ == "__main__":
    unittest.main()
