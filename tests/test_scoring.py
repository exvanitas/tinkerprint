import math
import unittest

import helpers  # noqa: F401
from helpers import commit, edit, profile, project, run, session, stat

L = math.log1p


class ProjectsAndDays(unittest.TestCase):
    def test_monorepo_parts_count_as_one_project(self):
        prof = profile([("Mono", "/w/mono", {"part": ["a", "b", "c", "d"]}), ("Other", "/w/other", None)])
        evs = [commit("2026-03-02T12:00:00+00:00", f"/w/mono/{p}/f.py") for p in "abcd"]
        evs.append(commit("2026-03-02T12:00:00+00:00", "/w/other/g.py", h="c2"))
        sheet, _ = run(prof, evs)
        self.assertEqual(sheet["history"]["points"], 1)
        self.assertEqual(len(sheet["projects"]), 2)
        self.assertAlmostEqual(project(sheet, "Mono")["points"], L(4) / (L(4) + L(1)), places=5)

    def test_commit_and_agent_edit_of_same_file_count_once(self):
        prof = profile([("A", "/w/a", None), ("B", "/w/b", None)])
        evs = [commit("2026-03-02T10:00:00+00:00", "/w/a/x.py"),
               edit("2026-03-02T15:00:00+00:00", "/w/a/x.py"),
               commit("2026-03-02T11:00:00+00:00", "/w/b/y.py", h="c2")]
        sheet, _ = run(prof, evs)
        self.assertAlmostEqual(project(sheet, "A")["points"], 0.5, places=6)

    def test_session_outside_every_root_is_unassigned(self):
        prof = profile([("A", "/w/a", None)])
        evs = [session("2026-03-02T10:00:00+00:00", "/elsewhere/notes", sid="out"),
               edit("2026-03-02T10:05:00+00:00", "/elsewhere/notes/todo.txt", session="out"),
               commit("2026-03-02T11:00:00+00:00", "/w/a/x.py")]
        sheet, local = run(prof, evs)
        self.assertEqual(sheet["unassigned"], {"sessions": 1, "folders": 1, "edits": 1})
        self.assertEqual(sheet["party"], [])
        self.assertEqual(local["unassigned_folders"], [("/elsewhere/notes", 1)])
        self.assertEqual(sheet["history"]["points"], 1)

    def test_session_inside_a_root_joins_the_party_and_earns_nothing(self):
        prof = profile([("A", "/w/a", None)])
        sheet, _ = run(prof, [session("2026-03-02T10:00:00+00:00", "/w/a")])
        self.assertEqual(sheet["history"]["points"], 0)
        self.assertEqual(sheet["party"][0]["harness"], "claude")
        self.assertEqual(sheet["party"][0]["days_together"], 1)

    def test_day_rollover_one_am_counts_toward_previous_day(self):
        prof = profile([("A", "/w/a", None)], tz="+02:00", rollover=4)
        # 01:00 local on Mar 3 is 23:00 UTC on Mar 2.
        sheet, _ = run(prof, [commit("2026-03-02T23:00:00+00:00", "/w/a/x.py")])
        self.assertEqual(sheet["history"]["first_day"], "2026-03-02")
        # 04:00 local on Mar 3 starts Mar 3.
        sheet, _ = run(prof, [commit("2026-03-03T02:00:00+00:00", "/w/a/x.py")])
        self.assertEqual(sheet["history"]["first_day"], "2026-03-03")

    def test_agent_edit_without_commit_makes_an_active_day(self):
        prof = profile([("A", "/w/a", None)])
        sheet, _ = run(prof, [edit("2026-03-04T10:00:00+00:00", "/w/a/x.py")])
        self.assertEqual(sheet["history"]["points"], 1)
        self.assertEqual(sheet["party"][0]["edit_sessions"], 1)

    def test_longest_root_wins(self):
        prof = profile([("Outer", "/w/outer", None), ("Inner", "/w/outer/inner", None)])
        sheet, _ = run(prof, [commit("2026-03-02T10:00:00+00:00", "/w/outer/inner/x.py")])
        self.assertEqual([p["name"] for p in sheet["projects"]], ["Inner"])


class Splits(unittest.TestCase):
    def test_log_one_plus_files_splits_projects_and_stats(self):
        prof = profile([("A", "/w/a", None), ("B", "/w/b", None)])
        ts = "2026-03-02T10:00:00+00:00"
        evs = [commit(ts, "/w/a/x.py"), commit(ts, "/w/a/y.py"), commit(ts, "/w/a/README.md"),
               commit(ts, "/w/b/z.py", h="c2")]
        sheet, _ = run(prof, evs)
        a = L(3) / (L(3) + L(1))
        self.assertAlmostEqual(project(sheet, "A")["points"], a, places=5)
        logic_from_a = a * L(2) / (L(2) + L(1))
        self.assertAlmostEqual(stat(sheet, "Logic")["points"], logic_from_a + (1 - a), places=5)
        self.assertAlmostEqual(stat(sheet, "Docs")["points"], a * L(1) / (L(2) + L(1)), places=5)

    def test_unclassified_share_stays_out_of_stats(self):
        prof = profile([("A", "/w/a", None)])
        ts = "2026-03-02T10:00:00+00:00"
        sheet, _ = run(prof, [commit(ts, "/w/a/x.py"), commit(ts, "/w/a/logo.png")])
        self.assertAlmostEqual(stat(sheet, "Logic")["points"], 0.5, places=6)
        self.assertAlmostEqual(stat(sheet, "Logic")["share"], 1.0, places=6)
        self.assertAlmostEqual(sheet["season_totals"]["unclassified"], 0.5, places=6)
        self.assertAlmostEqual(sheet["season_totals"]["unclassified_share"], 0.5, places=6)

    def test_skipped_files_never_count(self):
        prof = profile([("A", "/w/a", None)])
        ts = "2026-03-02T10:00:00+00:00"
        sheet, _ = run(prof, [commit(ts, "/w/a/node_modules/x/index.js"), commit(ts, "/w/a/package-lock.json")])
        self.assertEqual(sheet["history"]["points"], 0)

    def test_bulk_import_counts_once(self):
        prof = profile([("A", "/w/a", None), ("B", "/w/b", None)])
        ts = "2026-03-02T10:00:00+00:00"
        evs = [commit(ts, f"/w/a/assets/img{i}.png", h="big", status="A") for i in range(201)]
        evs.append(commit(ts, "/w/b/x.py", h="c2"))
        sheet, _ = run(prof, evs)
        self.assertAlmostEqual(project(sheet, "A")["points"], 0.5, places=6)
        evs = [commit(ts, f"/w/a/assets/img{i}.png", h="big", status="A") for i in range(200)]
        evs.append(commit(ts, "/w/b/x.py", h="c2"))
        sheet, _ = run(prof, evs)
        self.assertGreater(project(sheet, "A")["points"], 0.8)

    def test_level_is_floor_sqrt_of_all_history(self):
        prof = profile([("A", "/w/a", None)])
        for days, level in ((8, 2), (9, 3), (10, 3), (16, 4)):
            evs = [commit(f"2026-03-{d + 1:02d}T10:00:00+00:00", "/w/a/x.py", h=f"h{d}") for d in range(days)]
            sheet, _ = run(prof, evs)
            self.assertEqual(sheet["history"]["level"], level)
            self.assertEqual(sheet["history"]["next_level_at"], (level + 1) ** 2)

    def test_season_limits_class_and_radar_but_not_level(self):
        from datetime import date
        prof = profile([("A", "/w/a", None)])
        evs = [commit("2026-01-05T10:00:00+00:00", "/w/a/x.py", h="h1"),
               commit("2026-02-05T10:00:00+00:00", "/w/a/README.md", h="h2")]
        sheet, _ = run(prof, evs, season=(date(2026, 2, 1), None))
        self.assertEqual(sheet["history"]["points"], 2)
        self.assertEqual(sheet["season_totals"]["points"], 1)
        self.assertAlmostEqual(stat(sheet, "Docs")["share"], 1.0)

    def test_radar_falls_back_to_bars_under_three_stats(self):
        prof = profile([("A", "/w/a", None)])
        ts = "2026-03-02T10:00:00+00:00"
        two = [commit(ts, "/w/a/x.py"), commit(ts, "/w/a/README.md")]
        self.assertEqual(run(prof, two)[0]["chart"], "bars")
        self.assertEqual(run(prof, two + [commit(ts, "/w/a/tests/test_x.py")])[0]["chart"], "radar")


class Tinkerer(unittest.TestCase):
    def test_hand_tags_data_tests_and_docs(self):
        prof = profile([("Game", "/w/game", {"override": [{"glob": "art/**", "stats": {"Art": 1}}]})], set="tinkerer")
        ts = "2026-03-02T10:00:00+00:00"
        evs = [commit(ts, "/w/game/src/a.gd"), commit(ts, "/w/game/src/b.gd"), commit(ts, "/w/game/tests/t.gd"),
               commit(ts, "/w/game/art/moth.png"), commit(ts, "/w/game/README.md")]
        sheet, _ = run(prof, evs)
        self.assertGreater(stat(sheet, "Art")["points"], 0)
        # Tests count with the project's main code stat, Systems. Docs has no tinkerer stat.
        self.assertAlmostEqual(stat(sheet, "Systems")["points"], L(3) / (L(3) + L(1) + L(1)), places=5)
        self.assertAlmostEqual(sheet["season_totals"]["unclassified"], L(1) / (L(3) + L(1) + L(1)), places=5)
        for key in ("Worlds", "Lore", "Community"):
            self.assertEqual(stat(sheet, key)["points"], 0.0)

    def test_whole_project_weights_split_files(self):
        prof = profile([("Bot", "/w/bot", {"stats": {"Community": 1, "Systems": 1}})], set="tinkerer")
        sheet, _ = run(prof, [commit("2026-03-02T10:00:00+00:00", "/w/bot/main.py")])
        self.assertAlmostEqual(stat(sheet, "Community")["share"], 0.5, places=6)


class Milestones(unittest.TestCase):
    def test_milestones_show_as_written(self):
        from datetime import date
        prof = profile([("A", "/w/a", None)])
        sheet, _ = run(prof, [], milestones=[(date(2026, 1, 2), "Shipped the thing")])
        self.assertEqual(sheet["milestones"], [{"date": "2026-01-02", "text": "Shipped the thing"}])


if __name__ == "__main__":
    unittest.main()
