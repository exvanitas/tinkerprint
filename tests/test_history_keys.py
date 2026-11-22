""""What changed" names scope and method changes, and history follows a profile file that moves.
Every name, path and email here is invented."""
import io
import json
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
from tinkerprint.cli import main
from tinkerprint.demo import RepoWriter
from tinkerprint.keys import REGISTRY, lookup, read_registry
from tinkerprint.profile import profile_id
from tinkerprint.render_html import _changes
from tinkerprint.score import compare

UTC = ZoneInfo("UTC")
ME = ("Ida Fenwick", "ida@fenwick.example.test")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = os.path.realpath(self.tmp.name)
        self.data = os.path.join(self.t, "data")
        self.r1 = self.repo("r1", 2)
        self.r2 = self.repo("r2", 3)

    def tearDown(self):
        self.tmp.cleanup()

    def repo(self, name, days):
        root = os.path.join(self.t, name)
        r = RepoWriter(root)
        for d in range(days):
            r.touch(datetime(2026, 3, 2 + d, 10, tzinfo=UTC), ME, {f"{name}.py": 2})
        r.write()
        return root

    def write(self, path, roots, name="Ida", projects=("P",)):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f'name = "{name}"\n[identity]\nemails = ["{ME[1]}"]\n[harnesses]\nclaude = false\ncodex = false\n')
            for p in projects:
                f.write(f'[[project]]\nname = "{p}"\nroots = {json.dumps(roots)}\n')
        return path

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        self.assertEqual(code, 0, err.getvalue())
        return out.getvalue()

    def build(self, path, out, as_of):
        text = self.cli("build", "--profile", path, "--data-dir", self.data, "--out", os.path.join(self.t, out),
                        "--as-of", as_of)
        with open(os.path.join(self.t, out, "changes.json"), encoding="utf-8") as f:
            changes = json.load(f)
        with open(os.path.join(self.t, out, "sheet.html"), encoding="utf-8") as f:
            html = f.read()
        return text, changes, html


class ScopeAndMethod(Base):
    def test_adding_a_root_is_named(self):
        p = self.write(os.path.join(self.t, "prof", "p.toml"), [self.r1])
        self.build(p, "o1", "2026-04-01")
        self.write(p, [self.r1, self.r2])
        _, ch, html = self.build(p, "o2", "2026-04-02")
        self.assertEqual((ch["against"], ch["points_since"], ch["scope_changed"]), ("2026-04-01", 1, ["roots"]))
        self.assertIn("The profile's roots changed since then, so these differences include history newly added "
                      "or removed", html)
        _, ch, html = self.build(p, "o3", "2026-04-03")
        self.assertEqual(ch["scope_changed"], [])
        self.assertNotIn("newly added", html)

    def test_scope_stays_out_of_sheet_json(self):
        p = self.write(os.path.join(self.t, "prof", "p.toml"), [self.r1])
        self.build(p, "o1", "2026-04-01")
        with open(os.path.join(self.t, "o1", "sheet.json"), encoding="utf-8") as f:
            self.assertNotIn("_scope", json.load(f))
        key = lookup(self.data, p)
        saved = os.path.join(self.data, "history", key, "start_now", "2026-04-01.json")
        with open(saved, encoding="utf-8") as f:
            self.assertEqual(set(json.load(f)["_scope"]), {"projects", "roots", "identity", "harnesses", "days"})

    def test_an_earlier_sheet_without_digests_claims_nothing(self):
        sheet = {"method": 3, "profile": {"set": "builder"}, "history": {"points": 2, "level": 1}, "stats": [],
                 "party": [], "achievements": [], "class": None}
        ch = compare(sheet, dict(sheet), "2026-04-01", {"roots": "x"})
        self.assertEqual(ch["scope_changed"], [])
        ch = compare(sheet, dict(sheet, _scope={"roots": "y"}), "2026-04-01", {"roots": "x"})
        self.assertIn("roots", ch["scope_changed"])

    def test_a_method_change_is_said_not_hidden(self):
        sheet = {"method": 3, "profile": {"set": "builder"}, "history": {"points": 2, "level": 1}}
        ch = compare(sheet, dict(sheet, method=2), "2026-04-01")
        self.assertEqual(ch, {"against": "2026-04-01", "method_changed": True, "method_from": 2, "method_to": 3})
        html = _changes(ch)
        self.assertIn("What changed", html)
        self.assertIn("method version 2, and this one by version 3", html)
        self.assertIn("not compared", html)


class Moves(Base):
    def test_history_follows_a_moved_profile(self):
        p = self.write(os.path.join(self.t, "a", "p.toml"), [self.r1])
        self.build(p, "o1", "2026-04-01")
        key = lookup(self.data, p)
        moved = os.path.join(self.t, "b", "renamed.toml")
        os.makedirs(os.path.dirname(moved))
        os.rename(p, moved)
        text, ch, _ = self.build(moved, "o2", "2026-04-02")
        self.assertIn(f"This profile moved from {p}.", text)
        self.assertEqual(ch["against"], "2026-04-01")
        self.assertEqual(lookup(self.data, moved), key)
        text, ch, _ = self.build(moved, "o3", "2026-04-03")
        self.assertNotIn("moved", text)
        self.assertEqual(ch["against"], "2026-04-02")

    def test_a_copy_starts_its_own_history(self):
        p = self.write(os.path.join(self.t, "a", "p.toml"), [self.r1])
        self.build(p, "o1", "2026-04-01")
        copy = os.path.join(self.t, "b", "p.toml")
        os.makedirs(os.path.dirname(copy))
        shutil.copy(p, copy)
        _, ch, _ = self.build(copy, "o2", "2026-04-02")
        self.assertIsNone(ch["against"])
        self.assertNotEqual(lookup(self.data, copy), lookup(self.data, p))

    def test_a_moved_and_changed_profile_is_another_profile(self):
        p = self.write(os.path.join(self.t, "a", "p.toml"), [self.r1])
        self.build(p, "o1", "2026-04-01")
        os.remove(p)
        other = self.write(os.path.join(self.t, "b", "p.toml"), [self.r1], name="Someone Else")
        _, ch, _ = self.build(other, "o2", "2026-04-02")
        self.assertIsNone(ch["against"])

    def test_a_new_file_at_the_old_path_does_not_take_the_moved_history(self):
        p = self.write(os.path.join(self.t, "a", "p.toml"), [self.r1])
        self.build(p, "o1", "2026-04-01")
        moved = os.path.join(self.t, "b", "p.toml")
        os.makedirs(os.path.dirname(moved))
        os.rename(p, moved)
        self.build(moved, "o2", "2026-04-02")
        self.write(p, [self.r1])
        text, ch, _ = self.build(p, "o3", "2026-04-03")
        self.assertIsNone(ch["against"])
        self.assertNotIn("moved", text)
        self.assertNotEqual(lookup(self.data, p), lookup(self.data, moved))
        self.assertEqual(lookup(self.data, moved), profile_id(p))

    def test_two_gone_matches_are_not_guessed(self):
        a = self.write(os.path.join(self.t, "a", "p.toml"), [self.r1])
        b = self.write(os.path.join(self.t, "b", "p.toml"), [self.r1])
        self.build(a, "o1", "2026-04-01")
        self.build(b, "o2", "2026-04-01")
        os.remove(a)
        os.remove(b)
        c = self.write(os.path.join(self.t, "c", "p.toml"), [self.r1])
        _, ch, _ = self.build(c, "o3", "2026-04-02")
        self.assertIsNone(ch["against"])

    def test_history_from_before_the_profile_list_carries_over(self):
        p = self.write(os.path.join(self.t, "a", "p.toml"), [self.r1])
        self.build(p, "o1", "2026-04-01")
        os.remove(os.path.join(self.data, REGISTRY))  # a data folder from tinkerprint 0.1
        _, ch, _ = self.build(p, "o2", "2026-04-02")
        self.assertEqual(ch["against"], "2026-04-01")
        self.assertEqual(read_registry(self.data)[profile_id(p)]["path"], p)

    def test_forget_follows_the_moved_key(self):
        p = self.write(os.path.join(self.t, "a", "p.toml"), [self.r1])
        keep = self.write(os.path.join(self.t, "k", "keep.toml"), [self.r1], name="Kept")
        self.build(p, "o1", "2026-04-01")
        self.build(keep, "o0", "2026-04-01")
        key = lookup(self.data, p)
        moved = os.path.join(self.t, "b", "p.toml")
        os.makedirs(os.path.dirname(moved))
        os.rename(p, moved)
        self.build(moved, "o2", "2026-04-02")
        text = self.cli("forget", "--profile", moved, "--data-dir", self.data)
        self.assertIn(os.path.join("history", key), text)
        self.assertIn(REGISTRY + "  ", text)
        self.assertIn("this profile's entry in the profile list", text)
        self.cli("forget", "--profile", moved, "--data-dir", self.data, "--yes")
        self.assertFalse(os.path.exists(os.path.join(self.data, "history", key)))
        self.assertEqual(set(read_registry(self.data)), {lookup(self.data, keep)})
        self.assertIn("Nothing to forget", self.cli("forget", "--profile", moved, "--data-dir", self.data))
        self.cli("forget", "--all", "--data-dir", self.data, "--yes")
        self.assertFalse(os.path.exists(self.data))


if __name__ == "__main__":
    unittest.main()
