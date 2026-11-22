import unittest
from datetime import date, timedelta

import helpers  # noqa: F401
from helpers import commit, edit, profile, run, session
from tinkerprint.events import Commit, Tag


def ids(sheet):
    return {a["id"]: a for a in sheet["achievements"]}


def days(start, n, path="/w/a/x.py"):
    return [commit(f"{start + timedelta(days=i)}T10:00:00+00:00", path, h=f"h{start}{i}") for i in range(n)]


class Achievements(unittest.TestCase):
    prof = profile([("A", "/w/a", None)])

    def test_first_light_and_long_road(self):
        sheet, _ = run(self.prof, days(date(2026, 1, 1), 30))
        got = ids(sheet)
        self.assertEqual(got["first-light"]["date"], "2026-01-01")
        self.assertEqual(got["long-road"]["date"], "2026-01-30")
        sheet, _ = run(self.prof, days(date(2026, 1, 1), 29))
        self.assertNotIn("long-road", ids(sheet))

    def test_founder_thousandfold_swarm_and_necromancer(self):
        def c(ts, h, root=False, mine=True):
            return Commit(ts=ts, hash=h, repo="r1", top="/w/a", mine=mine, bot=False, root=root, files=1)
        commits = [c("2025-01-01T10:00:00+00:00", "root", root=True)]
        commits += [c(f"2025-02-01T10:{i // 60:02d}:{i % 60:02d}+00:00", f"s{i}") for i in range(100)]
        commits += [c(f"2025-03-{1 + i // 500:02d}T10:00:00+00:00", f"t{i}") for i in range(900)]
        commits += [c("2025-12-01T10:00:00+00:00", "back")]
        sheet, _ = run(self.prof, [], commits=commits)
        got = ids(sheet)
        self.assertEqual(got["founder"]["detail"], "A")
        self.assertEqual(got["swarm-day"]["date"], "2025-02-01")
        self.assertEqual(got["thousandfold"]["date"], "2025-03-02")
        self.assertEqual(got["necromancer"]["date"], "2025-12-01")

    def test_founder_needs_your_root_commit(self):
        commits = [Commit(ts="2025-01-01T10:00:00+00:00", hash="r", repo="r", top="/w/a", mine=False, bot=False,
                          root=True)]
        self.assertNotIn("founder", ids(run(self.prof, [], commits=commits)[0]))

    def test_shipwright_needs_one_point_oh(self):
        tags = [Tag(ts="2025-05-01T10:00:00+00:00", name="v0.9.0", repo="r", top="/w/a", mine=True),
                Tag(ts="2025-06-01T10:00:00+00:00", name="v1.0.0", repo="r", top="/w/a", mine=True),
                Tag(ts="2025-04-01T10:00:00+00:00", name="v2.0.0", repo="r", top="/w/a", mine=False)]
        got = ids(run(self.prof, [], tags=tags)[0])
        self.assertEqual(got["shipwright"]["date"], "2025-06-01")

    def test_polyglot(self):
        evs = []
        for i, ext in enumerate(("py", "ts", "go", "rs", "sql")):
            evs.append(commit(f"2026-01-0{i + 1}T10:00:00+00:00", f"/w/a/f.{ext}", h=f"p{i}", status="A", added=1001))
        got = ids(run(self.prof, evs)[0])
        self.assertEqual(got["polyglot"]["date"], "2026-01-05")
        self.assertNotIn("polyglot", ids(run(self.prof, evs[:4])[0]))

    def test_full_party(self):
        ts = "2026-02-02T10:00:00+00:00"
        evs = [session(ts, "/w/a", "s1", "claude"), session(ts, "/w/a", "s2", "codex"), session(ts, "/w/a", "s3", "agy")]
        self.assertEqual(ids(run(self.prof, evs)[0])["full-party"]["date"], "2026-02-02")
        self.assertNotIn("full-party", ids(run(self.prof, evs[:2])[0]))

    def test_seasons_turn(self):
        evs = []
        for q, month in enumerate((1, 4, 7, 10)):
            evs += days(date(2025, month, 1), 10)
        got = ids(run(self.prof, evs)[0])
        self.assertEqual(got["seasons-turn"]["date"], "2025-10-10")
        self.assertNotIn("seasons-turn", ids(run(self.prof, evs[:-1])[0]))

    def test_party_roles(self):
        ts = "2026-02-02T10:00:00+00:00"
        evs = [session(ts, "/w/a", "r1", "codex", origin="codex_exec"),
               session(ts, "/w/a", "r2", "codex", origin="codex_exec"),
               session(ts, "/w/a", "e1", "codex", origin="codex_exec"),
               edit(ts, "/w/a/x.py", "e1", "codex")]
        m = run(self.prof, evs)[0]["party"][0]
        # 0.2.0: an exec session with no recorded edit is no longer called a review.
        self.assertEqual((m["edit_sessions"], m["role"]), (1, "Some edits recorded"))
        self.assertNotIn("review_sessions", m)
        m = run(self.prof, evs[:2])[0]["party"][0]
        self.assertEqual((m["edit_sessions"], m["role"]), (0, "No edits recorded"))
        m = run(self.prof, evs[2:])[0]["party"][0]
        self.assertEqual(m["role"], "Mostly edits")

    def test_presence_only_reader(self):
        ts = "2026-02-02T10:00:00+00:00"
        m = run(self.prof, [session(ts, "/w/a", "g1", "agy", model="")])[0]["party"][0]
        self.assertEqual((m["name"], m["role"], m["sessions"]), ("Antigravity", "Presence only", 1))


if __name__ == "__main__":
    unittest.main()
