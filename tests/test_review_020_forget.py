"""0.2.0 review: forget deletes only in its own data folder, only files it wrote, never through a
link and never another profile's history. Every name, path and email here is invented."""
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
from tinkerprint import forget as fg
from tinkerprint.cli import main
from tinkerprint.datadir import MARKER, SHEETS_MARK
from tinkerprint.demo import RepoWriter
from tinkerprint.keys import REGISTRY, lookup, read_registry
from tinkerprint.profile import is_key, profile_id

UTC = ZoneInfo("UTC")
ME = ("Ida Fenwick", "ida@fenwick.example.test")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = os.path.realpath(self.tmp.name)
        self.root = os.path.join(self.t, "repo")
        r = RepoWriter(self.root)
        r.touch(datetime(2026, 3, 2, 10, tzinfo=UTC), ME, {"a.py": 2})
        r.write()
        self.logs = os.path.join(self.t, "logs")
        os.makedirs(self.logs)
        self.data = os.path.join(self.t, "data")

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, path, name="Ida"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(f'name = "{name}"\n[identity]\nemails = ["{ME[1]}"]\n[harnesses]\nclaude = true\ncodex = false\n'
                    f'claude_dir = "{self.logs}"\n[[project]]\nname = "P"\nroot = "{self.root}"\n')
        return path

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        self.assertEqual(code, 0, err.getvalue())
        return out.getvalue()

    def build(self, prof, *extra):
        return self.cli("build", "--profile", prof, "--data-dir", self.data, "--as-of", "2026-04-01", *extra)

    def put(self, path, text="mine\n"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path


class Ownership(Base):
    def test_a_folder_no_build_marked_is_left_alone(self):
        other = os.path.join(self.t, "some-app")
        cache = self.put(os.path.join(other, "cache", "codex.json"), "{}")
        reg = self.put(os.path.join(other, REGISTRY), '{"profiles": {}}')
        text = self.cli("forget", "--all", "--data-dir", other, "--yes")
        self.assertIn(f"Left alone: {other} has no {MARKER}", text)
        self.assertTrue(os.path.isfile(cache))
        self.assertTrue(os.path.isfile(reg))

    def test_every_build_marks_its_data_folder(self):
        a = self.write(os.path.join(self.t, "a.toml"))
        self.build(a)
        self.assertTrue(os.path.isfile(os.path.join(self.data, MARKER)))
        os.remove(os.path.join(self.data, MARKER))  # a data folder from 0.1
        self.build(a)
        self.assertTrue(os.path.isfile(os.path.join(self.data, MARKER)))

    def test_a_stray_tmp_file_is_not_ours(self):
        a = self.write(os.path.join(self.t, "a.toml"))
        self.build(a)
        stray = self.put(os.path.join(self.data, "cache", ".notes.tmp"))
        text = self.cli("forget", "--all", "--data-dir", self.data, "--yes")
        self.assertIn("Left alone: " + os.path.join(self.data, "cache"), text)
        self.assertTrue(os.path.isfile(stray))
        self.assertTrue(os.path.isfile(os.path.join(self.data, "cache", "claude.json")))
        self.assertTrue(os.path.isfile(os.path.join(self.data, MARKER)))

    def test_its_own_tmp_file_goes(self):
        a = self.write(os.path.join(self.t, "a.toml"))
        self.build(a)
        self.put(os.path.join(self.data, "cache", ".claude.json.k2x_9q0z.tmp"))
        self.cli("forget", "--all", "--data-dir", self.data, "--yes")
        self.assertFalse(os.path.exists(self.data))

    def test_an_out_folder_inside_sheets_is_never_touched(self):
        a = self.write(os.path.join(self.t, "a.toml"))
        b = self.write(os.path.join(self.t, "b.toml"))
        self.build(a)
        named = os.path.join(self.data, "sheets", "mine-0badc0de")
        self.build(b, "--out", named)
        self.assertTrue(is_key("mine-0badc0de"))
        self.assertTrue(os.path.isfile(os.path.join(self.data, "sheets", profile_id(a), SHEETS_MARK)))
        self.assertFalse(os.path.exists(os.path.join(named, SHEETS_MARK)))
        text = self.cli("forget", "--all", "--data-dir", self.data, "--yes")
        self.assertIn(f"Left alone: {named}, not a folder of builds made without --out.", text)
        self.assertTrue(os.path.isfile(os.path.join(named, "sheet.html")))
        self.assertFalse(os.path.exists(os.path.join(self.data, "sheets", profile_id(a))))
        self.assertFalse(os.path.exists(os.path.join(self.data, "history")))


class Links(Base):
    def setUp(self):
        super().setUp()
        self.a = self.write(os.path.join(self.t, "a.toml"))
        self.build(self.a)
        self.key = lookup(self.data, self.a)
        self.outside = os.path.join(self.t, "outside")

    def test_a_linked_history_folder(self):
        # history/ points elsewhere, holding what looks like this profile's saved sheets.
        victim = self.put(os.path.join(self.outside, self.key, "start_now", "2026-04-01.json"), "{}")
        hist = os.path.join(self.data, "history")
        os.rename(hist, os.path.join(self.t, "old-history"))
        os.symlink(self.outside, hist)
        text = self.cli("forget", "--profile", self.a, "--data-dir", self.data, "--yes")
        self.assertIn(f"Left alone: {os.path.join(hist, self.key)} is a link, or inside one.", text)
        self.assertTrue(os.path.isfile(victim))
        text = self.cli("forget", "--all", "--data-dir", self.data, "--yes")
        self.assertIn(f"Left alone: {hist} is a link", text)
        self.assertTrue(os.path.isfile(victim))

    def test_a_linked_last_build_folder(self):
        victim = self.put(os.path.join(self.outside, self.key + ".json"), "{}")
        lb = os.path.join(self.data, "last-build")
        os.rename(lb, os.path.join(self.t, "old-lb"))
        os.symlink(self.outside, lb)
        self.cli("forget", "--profile", self.a, "--data-dir", self.data, "--yes")
        self.assertTrue(os.path.isfile(victim))

    def test_a_linked_season_folder(self):
        victim = self.put(os.path.join(self.outside, "2026-04-01.json"), "{}")
        season = os.path.join(self.data, "history", self.key, "2026-01-01_now")
        os.symlink(self.outside, season)
        text = self.cli("forget", "--profile", self.a, "--data-dir", self.data, "--yes")
        self.assertIn("Left alone: " + os.path.join(self.data, "history", self.key), text)
        self.assertTrue(os.path.isfile(victim))

    def test_a_folder_that_gains_a_file_while_forget_runs(self):
        delete, keep = fg.plan(self.data, self.key)
        self.assertEqual(keep, [])
        late = self.put(os.path.join(self.data, "history", self.key, "start_now", "notes.txt"))
        left = fg.remove(self.data, delete)
        self.assertEqual(left, [os.path.join(self.data, "history", self.key, "start_now")])
        self.assertTrue(os.path.isfile(late))
        self.assertFalse(os.path.exists(os.path.join(self.data, "history", self.key, "start_now", "2026-04-01.json")))

    def test_a_folder_swapped_for_a_link_while_forget_runs(self):
        delete, _ = fg.plan(self.data, self.key)
        victim = self.put(os.path.join(self.outside, "2026-04-01.json"), "{}")
        season = os.path.join(self.data, "history", self.key, "start_now")
        os.rename(season, os.path.join(self.t, "moved-season"))
        os.symlink(self.outside, season)
        fg.remove(self.data, delete)
        self.assertTrue(os.path.isfile(victim))


class Keys(Base):
    def test_a_registry_key_that_is_a_path_is_dropped(self):
        a = self.write(os.path.join(self.t, "a.toml"))
        self.build(a)
        victim = self.put(os.path.join(self.t, "elsewhere", "start_now", "2026-04-01.json"), "{}")
        with open(os.path.join(self.data, REGISTRY), encoding="utf-8") as f:
            reg = json.load(f)
        reg["profiles"] = {"../../elsewhere": {"path": a, "sig": "x"}}
        with open(os.path.join(self.data, REGISTRY), "w", encoding="utf-8") as f:
            json.dump(reg, f)
        self.assertEqual(read_registry(self.data), {})
        self.assertTrue(is_key(lookup(self.data, a)))
        self.cli("forget", "--profile", a, "--data-dir", self.data, "--yes")
        self.assertTrue(os.path.isfile(victim))
        with self.assertRaises(ValueError):
            fg.forget(self.data, "../../elsewhere", True)

    def test_a_profile_named_without_latin_letters(self):
        star = self.write(os.path.join(self.t, "星.toml"))
        self.build(star)
        key = lookup(self.data, star)
        self.assertRegex(key, r"^[0-9a-f]{8}$")
        self.assertTrue(is_key(key))
        self.cli("forget", "--all", "--data-dir", self.data, "--yes")
        self.assertFalse(os.path.exists(self.data))

    def test_every_key_profile_id_makes_parses(self):
        for name in ("a.toml", "My Profile.toml", "星.toml", "--.toml", "x_y.z.toml", "İ.toml"):
            for salt in (0, 3):
                self.assertTrue(is_key(profile_id(os.path.join(self.t, name), salt)), name)
        for bad in ("", "..", "a/b-0badc0de", "A-0badc0de", "x-0badc0d", "-0badc0de", "a--0badc0de"):
            self.assertFalse(is_key(bad), bad)


if __name__ == "__main__":
    unittest.main()
