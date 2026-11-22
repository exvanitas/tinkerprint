"""Full party from any three harnesses, Shipwright's tags, and achievements judged inside the
profile's roots. Every name, path and email here is invented."""
import os
import subprocess
import tempfile
import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
from helpers import profile, run, session
from tinkerprint.achievements import RULES, evaluate, version_of
from tinkerprint.build import build
from tinkerprint.demo import RepoWriter, git_env
from tinkerprint.events import Commit, Tag
from test_review_r2_git import ME, MATE, git, write_profile

UTC = ZoneInfo("UTC")


def ids(sheet):
    return {a["id"]: a for a in sheet["achievements"]}


class FullParty(unittest.TestCase):
    def test_any_three_on_one_day(self):
        d1, d2 = date(2026, 2, 2), date(2026, 2, 9)
        harness_days = {"claude": {d1}, "codex": {d1}, "agy": {d1}, "fourth": {d2}}
        got = {a["id"]: a for a in evaluate([], [], [], harness_days, None, None, [])}
        self.assertEqual((got["full-party"]["date"], got["full-party"]["count"]), ("2026-02-02", 1))

    def test_two_a_day_is_not_enough(self):
        days = [date(2026, 2, d) for d in (2, 3, 4)]
        harness_days = {"claude": {days[0], days[1]}, "codex": {days[1], days[2]}, "agy": {days[2], days[0]}}
        got = {a["id"] for a in evaluate([], [], [], harness_days, None, None, [])}
        self.assertNotIn("full-party", got)

    def test_counts_every_day_with_three(self):
        prof = profile([("A", "/w/a", None)])
        evs = []
        for day in ("2026-02-02", "2026-02-05"):
            ts = f"{day}T10:00:00+00:00"
            evs += [session(ts, "/w/a", f"c{day}", "claude"), session(ts, "/w/a", f"x{day}", "codex"),
                    session(ts, "/w/a", f"g{day}", "agy")]
        evs.append(session("2026-02-03T10:00:00+00:00", "/w/a", "c-late", "claude"))
        got = ids(run(prof, evs)[0])["full-party"]
        self.assertEqual((got["date"], got["count"]), ("2026-02-02", 2))

    def test_rule_text(self):
        self.assertEqual(RULES["full-party"][1], "Any three harnesses on the same day.")


class Shipwright(unittest.TestCase):
    prof = profile([("A", "/w/a", None)])

    def tag(self, name, ts="2025-06-01T10:00:00+00:00", scoped=True):
        return Tag(ts=ts, name=name, repo="r", top="/w/a", mine=True, scoped=scoped)

    def test_prefixed_tags_count_by_their_last_part(self):
        for name in ("cli/v1.2.0", "packages/core/2.0", "v1.0"):
            self.assertTrue(version_of(name), name)
        for name in ("cli/v0.9.0", "release-1.0", "v1.0/notes", "cli/"):
            m = version_of(name)
            self.assertFalse(m and int(m.group(1)) >= 1, name)
        got = ids(run(self.prof, [], tags=[self.tag("cli/v1.2.0")])[0])
        self.assertEqual(got["shipwright"]["detail"], "cli/v1.2.0 in A")

    def test_rule_text_says_what_counts(self):
        rule = RULES["shipwright"][1]
        for words in ("1.0 or higher", "cli/v1.2.0", "annotated by you", "lightweight on your commit"):
            self.assertIn(words, rule)

    def test_out_of_scope_tag_does_not_count(self):
        self.assertNotIn("shipwright", ids(run(self.prof, [], tags=[self.tag("v1.0.0", scoped=False)])[0]))


class ScopedCommits(unittest.TestCase):
    prof = profile([("A", "/w/a", None)])

    def c(self, ts, h, root=False, scoped=True):
        return Commit(ts=ts, hash=h, repo="r1", top="/w/a", mine=True, bot=False, root=root, files=1, scoped=scoped)

    def test_out_of_scope_commits_earn_nothing(self):
        commits = [self.c("2025-01-01T10:00:00+00:00", "root", root=True, scoped=False)]
        commits += [self.c(f"2025-02-01T10:{i // 60:02d}:{i % 60:02d}+00:00", f"s{i}", scoped=False)
                    for i in range(100)]
        commits += [self.c("2025-12-01T10:00:00+00:00", "back", scoped=False)]
        got = ids(run(self.prof, [], commits=commits)[0])
        for key in ("founder", "swarm-day", "necromancer"):
            self.assertNotIn(key, got)
        commits = [self.c(x.ts, x.hash, root=x.root) for x in commits]
        got = ids(run(self.prof, [], commits=commits)[0])
        for key in ("founder", "swarm-day", "necromancer"):
            self.assertIn(key, got)


class Monorepo(unittest.TestCase):
    """One repo with app/ and site/. A profile of app/ alone judges only commits that touch app/."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = os.path.realpath(self.tmp.name)
        self.repo = os.path.join(self.t, "mono")
        r = RepoWriter(self.repo)
        r.touch(datetime(2026, 3, 2, 10, tzinfo=UTC), ME, {"site/index.md": 2}, tag="site/v1.0.0")
        r.touch(datetime(2026, 3, 3, 10, tzinfo=UTC), MATE, {"app/main.py": 2})
        r.touch(datetime(2026, 3, 4, 10, tzinfo=UTC), ME, {"app/main.py": 2}, tag="app/v1.1.0")
        r.write()

    def tearDown(self):
        self.tmp.cleanup()

    def sheet(self, roots, out):
        prof = write_profile(os.path.join(self.t, "p.toml"), [("App", roots)])
        return build(prof, os.path.join(self.t, out), home=os.path.join(self.t, "data"),
                     today=date(2026, 11, 1))["sheet"]

    def test_subfolder_profile_has_no_founder_from_a_sibling(self):
        got = ids(self.sheet([os.path.join(self.repo, "app")], "o1"))
        self.assertNotIn("founder", got)
        self.assertEqual(got["shipwright"]["detail"], "app/v1.1.0 in App")
        self.assertEqual(got["shipwright"]["count"], 1)

    def test_whole_repo_profile_keeps_founder(self):
        got = ids(self.sheet([self.repo], "o2"))
        self.assertEqual(got["founder"]["date"], "2026-03-02")
        self.assertEqual(got["shipwright"]["count"], 2)

    def test_empty_root_commit(self):
        empty = os.path.join(self.t, "empty")
        os.makedirs(empty)
        git(empty, "init", "-q", "-b", "main")
        git(empty, "commit", "-q", "--allow-empty", "-m", "start")
        os.makedirs(os.path.join(empty, "app"))
        with open(os.path.join(empty, "app", "x.py"), "w") as f:
            f.write("x\n")
        git(empty, "add", ".")
        git(empty, "commit", "-qm", "x")
        self.assertIn("founder", ids(self.sheet([empty], "o3")))
        self.assertNotIn("founder", ids(self.sheet([os.path.join(empty, "app")], "o4")))


if __name__ == "__main__":
    unittest.main()
