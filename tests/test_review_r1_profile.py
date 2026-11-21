"""Review round 1: profile consent, profile identity, snapshot pinning, data folder location."""
import os
import tempfile
import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
from tinkerprint.build import build
from tinkerprint.demo import RepoWriter
from tinkerprint.profile import ProfileError, load_profile, parse_profile

UTC = ZoneInfo("UTC")
ME = ("Ida Fenwick", "ida@fenwick.example.test")


def write_profile(path, roots, extra=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f'name = "Ida"\n[identity]\nemails = ["{ME[1]}"]\n[harnesses]\nclaude = false\ncodex = false\n{extra}\n')
        for i, (root, stats) in enumerate(roots):
            f.write(f'[[project]]\nname = "P{i}"\nroot = "{root}"\n')
            if stats:
                f.write(f"stats = {stats}\n")
    return path


class Item03CardConsentNeedsBooleans(unittest.TestCase):
    base = {"identity": {"emails": ["a@example.test"]}, "project": [], "work": True}

    def test_string_false_is_refused(self):
        with self.assertRaises(ProfileError):
            parse_profile(dict(self.base, card={"allow": "false"}), "/")
        with self.assertRaises(ProfileError):
            parse_profile(dict(self.base, work="true"), "/")
        with self.assertRaises(ProfileError):
            parse_profile(dict(self.base, harnesses={"agy": 1}), "/")

    def test_booleans_work(self):
        self.assertFalse(parse_profile(dict(self.base, card={"allow": False}), "/").card_enabled)
        self.assertTrue(parse_profile(dict(self.base, card={"allow": True}), "/").card_enabled)


class Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def repo(self, name, days):
        root = os.path.join(self.t, name)
        r = RepoWriter(root)
        for d in days:
            r.touch(datetime(2026, 3, d, 10, tzinfo=UTC), ME, {f"f{d}.py": 2})
        r.write()
        return root


class Item04ProfilesKeepTheirOwnSnapshots(Tmp):
    def test_default_ids_differ_and_class_does_not_leak(self):
        root = self.repo("repo", [2])
        work = load_profile(write_profile(os.path.join(self.t, "work", "profile.toml"),
                                          [(root, "{ Logic = 51, Interface = 49 }")]))
        personal = load_profile(write_profile(os.path.join(self.t, "personal", "profile.toml"),
                                              [(root, "{ Interface = 51, Logic = 49 }")]))
        self.assertNotEqual(work.id, personal.id)
        home = os.path.join(self.t, "data")
        self.assertEqual(build(work, os.path.join(self.t, "o1"), home=home)["sheet"]["class"]["name"], "Sage")
        res = build(personal, os.path.join(self.t, "o2"), home=home)
        self.assertEqual(res["sheet"]["class"]["name"], "Illusionist")
        self.assertIsNone(res["changes"]["against"])


class Item05RebuildIsByteIdentical(Tmp):
    def test_rebuilding_an_earlier_cutoff(self):
        root = self.repo("repo", [2, 3])
        prof = load_profile(write_profile(os.path.join(self.t, "p.toml"), [(root, None)]))
        home = os.path.join(self.t, "data")

        def sheet_bytes(as_of, out):
            res = build(prof, os.path.join(self.t, out), as_of=as_of, home=home)
            with open(res["paths"]["json"], "rb") as f:
                return f.read()

        first = sheet_bytes(date(2026, 3, 2), "a1")
        sheet_bytes(date(2026, 3, 3), "b")
        self.assertEqual(sheet_bytes(date(2026, 3, 2), "a2"), first)


class Item06DataFolderStaysOutOfRepos(Tmp):
    def test_refuses_inside_a_worktree_or_root(self):
        root = self.repo("repo", [2])
        plain = os.path.join(self.t, "plain")
        os.makedirs(plain)
        prof = load_profile(write_profile(os.path.join(self.t, "p.toml"), [(root, None), (plain, None)]))
        for home in (os.path.join(root, ".tinkerprint"), os.path.join(plain, "data")):
            with self.assertRaises(ValueError):
                build(prof, os.path.join(self.t, "out"), home=home)
            self.assertFalse(os.path.exists(os.path.join(home, "cache")))


if __name__ == "__main__":
    unittest.main()
