"""forget shows what tinkerprint keeps and where, and deletes only with --all --yes: the whole data
folder, when it is tinkerprint's and holds nothing else. Every name, path and email here is invented."""
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from unittest import mock
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
from tinkerprint import forget as fg
from tinkerprint.cli import main
from tinkerprint.datadir import MARKER, REGISTRY, claim_home, data_lock, Gone
from tinkerprint.demo import RepoWriter
from tinkerprint.keys import lookup, read_registry
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
            # An empty claude folder: the build writes a cache without reading anyone's real logs.
            f.write(f'name = "{name}"\n[identity]\nemails = ["{ME[1]}"]\n[harnesses]\nclaude = true\ncodex = false\n'
                    f'claude_dir = "{self.logs}"\n[[project]]\nname = "P"\nroot = "{self.root}"\n')
        return path

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def cli(self, *argv):
        code, out, err = self.run_cli(*argv)
        self.assertEqual(code, 0, err)
        return out

    def build(self, prof, *extra, data=None):
        return self.cli("build", "--profile", prof, "--data-dir", data or self.data, "--as-of", "2026-04-01", *extra)

    def put(self, path, text="mine\n"):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def exists(self, *parts):
        return os.path.lexists(os.path.join(self.data, *parts))


class Show(Base):
    def setUp(self):
        super().setUp()
        self.a = self.write(os.path.join(self.t, "a.toml"))
        self.b = self.write(os.path.join(self.t, "b.toml"))
        self.out = os.path.join(self.t, "exported")
        self.build(self.a)
        self.build(self.a, "--out", self.out)
        self.build(self.b)

    def test_without_flags_it_shows_the_data_folder_and_deletes_nothing(self):
        old = os.getcwd()
        os.chdir(self.t)  # no tinkerprint.toml here
        try:
            text = self.cli("forget", "--data-dir", self.data)
        finally:
            os.chdir(old)
        self.assertIn(f"tinkerprint keeps its data in {self.data} (", text)
        self.assertIn(f"tinkerprint forget --all --yes --data-dir {self.data}", text)
        self.assertIn("delete the folders 'tinkerprint forget --profile PATH' shows", text)
        self.assertNotIn("Profile ", text)
        for part in ("cache", "history", "last-build", "sheets", REGISTRY, MARKER):
            self.assertTrue(self.exists(part), part)

    def test_a_profile_shows_its_own_folders(self):
        ka = profile_id(self.a)
        text = self.cli("forget", "--profile", self.a, "--data-dir", self.data)
        self.assertIn(f"Profile {self.a}:", text)
        self.assertIn(os.path.join(self.data, "history", ka) + " (", text)
        self.assertIn(os.path.join(self.data, "last-build", ka + ".json") + " (", text)
        self.assertIn(os.path.join(self.data, "sheets", ka) + " (", text)
        self.assertNotIn(profile_id(self.b), text)
        self.assertTrue(self.exists("history", ka))
        self.assertTrue(self.exists("cache"))
        self.assertTrue(os.path.isfile(os.path.join(self.out, "sheet.html")))

    def test_a_profile_file_that_is_gone(self):
        os.unlink(self.a)
        text = self.cli("forget", "--profile", self.a, "--data-dir", self.data)
        self.assertIn(os.path.join(self.data, "history", profile_id(self.a)), text)

    def test_yes_without_all_deletes_nothing(self):
        code, _, err = self.run_cli("forget", "--profile", self.a, "--data-dir", self.data, "--yes")
        self.assertEqual(code, 2)
        self.assertIn("forget deletes only with --all", err)
        self.assertTrue(self.exists("history", profile_id(self.a)))

    def test_a_data_folder_that_does_not_exist(self):
        text = self.cli("forget", "--data-dir", os.path.join(self.t, "none"))
        self.assertIn("does not exist", text)
        self.assertFalse(os.path.exists(os.path.join(self.t, "none")))

    def test_all_without_yes_lists_it(self):
        text = self.cli("forget", "--all", "--data-dir", self.data)
        self.assertIn(f"This deletes {self.data} (", text)
        self.assertIn("cache" + os.sep, text)
        self.assertIn("Run it again with --yes", text)
        self.assertTrue(self.exists("cache"))

    def test_all(self):
        text = self.cli("forget", "--all", "--data-dir", self.data, "--yes")
        self.assertIn(f"Deleted {self.data} (", text)
        self.assertFalse(os.path.exists(self.data))
        self.assertTrue(os.path.isfile(os.path.join(self.out, "sheet.html")))
        self.assertTrue(os.path.isdir(self.logs))
        self.assertTrue(os.path.isdir(os.path.join(self.root, ".git")))
        self.assertTrue(os.path.isfile(self.a))


class Refusals(Base):
    def setUp(self):
        super().setUp()
        self.a = self.write(os.path.join(self.t, "a.toml"))
        self.build(self.a)

    def test_a_folder_no_build_marked_is_left_alone(self):
        other = os.path.join(self.t, "some-app")
        cache = self.put(os.path.join(other, "cache", "codex.json"), "{}")
        reg = self.put(os.path.join(other, REGISTRY), '{"profiles": {}}')
        text = self.cli("forget", "--all", "--data-dir", other, "--yes")
        self.assertIn(f"Nothing was deleted. {other} has no {MARKER}", text)
        self.assertTrue(os.path.isfile(cache))
        self.assertTrue(os.path.isfile(reg))
        self.assertEqual(sorted(os.listdir(other)), ["cache", REGISTRY])

    def test_anything_else_at_the_top_stops_it(self):
        keep = self.put(os.path.join(self.data, "notes.txt"))
        os.makedirs(os.path.join(self.data, "keep-me"))
        text = self.cli("forget", "--all", "--data-dir", self.data, "--yes")
        self.assertIn("Nothing was deleted.", text)
        self.assertIn("keep-me, notes.txt", text)
        self.assertTrue(os.path.isfile(keep))
        self.assertTrue(self.exists("cache", "claude.json"))
        self.assertTrue(self.exists("history"))

    def test_a_stray_tmp_file_at_the_top_is_not_ours(self):
        stray = self.put(os.path.join(self.data, ".notes.tmp"))
        text = self.cli("forget", "--all", "--data-dir", self.data, "--yes")
        self.assertIn("Nothing was deleted.", text)
        self.assertTrue(os.path.isfile(stray))

    def test_its_own_tmp_files_go(self):
        self.put(os.path.join(self.data, "." + REGISTRY + ".k2x_9q0z.tmp"))
        self.put(os.path.join(self.data, "." + MARKER + ".abcdefgh.tmp"))
        self.cli("forget", "--all", "--data-dir", self.data, "--yes")
        self.assertFalse(os.path.exists(self.data))

    @unittest.skipIf(os.name == "nt", "symlinks need privileges on Windows")
    def test_a_linked_data_folder_is_left_alone(self):
        link = os.path.join(self.t, "link")
        os.symlink(self.data, link)
        text = self.cli("forget", "--all", "--data-dir", link, "--yes")
        self.assertIn(f"Nothing was deleted. {link} is a link.", text)
        self.assertTrue(self.exists("cache", "claude.json"))

    @unittest.skipIf(os.name == "nt", "symlinks need privileges on Windows")
    def test_a_link_inside_goes_and_its_target_stays(self):
        outside = os.path.join(self.t, "outside")
        victim = self.put(os.path.join(outside, "2026-04-01.json"), "{}")
        key = lookup(self.data, self.a)
        os.symlink(outside, os.path.join(self.data, "history", key, "2026-01-01_now"))
        os.rename(os.path.join(self.data, "last-build"), os.path.join(self.t, "old-lb"))
        os.symlink(outside, os.path.join(self.data, "last-build"))
        self.cli("forget", "--all", "--data-dir", self.data, "--yes")
        self.assertFalse(os.path.lexists(self.data))
        self.assertTrue(os.path.isfile(victim))

    def test_a_folder_that_appears_after_the_check_stays(self):
        real = fg._refusal
        calls = []

        def late(home):
            out = real(home)
            calls.append(home)
            if len(calls) == 2:  # the check under the lock
                os.makedirs(os.path.join(home, "late"))
            return out
        with mock.patch.object(fg, "_refusal", side_effect=late):
            lines = fg.forget_all(self.data, True)
        self.assertIn("Left: late", lines[-1])
        self.assertEqual(os.listdir(self.data), ["late"])


class Claim(Base):
    def test_a_build_refuses_a_folder_that_is_not_empty_and_not_ours(self):
        other = os.path.join(self.t, "some-app")
        self.put(os.path.join(other, "cache", "codex.json"), "{}")
        self.put(os.path.join(other, "settings.ini"))
        a = self.write(os.path.join(self.t, "a.toml"))
        code, _, err = self.run_cli("build", "--profile", a, "--data-dir", other)
        self.assertEqual(code, 2)
        self.assertIn(f"{other} is not empty and is not a tinkerprint data folder", err)
        self.assertEqual(sorted(os.listdir(other)), ["cache", "settings.ini"])

    def test_an_empty_folder_is_adopted(self):
        os.makedirs(self.data)
        self.build(self.write(os.path.join(self.t, "a.toml")))
        self.assertTrue(self.exists(MARKER))

    def test_a_data_folder_from_01_is_adopted(self):
        a = self.write(os.path.join(self.t, "a.toml"))
        self.build(a)
        os.remove(os.path.join(self.data, MARKER))
        os.remove(os.path.join(self.data, REGISTRY))
        code, _, err = self.run_cli("build", "--profile", a, "--data-dir", self.data)
        self.assertEqual(code, 2)  # a --data-dir is adopted once its owner marks it
        self.assertIn(f"create {MARKER} in it", err)
        self.put(os.path.join(self.data, MARKER), "tinkerprint data folder\n")
        self.build(a)
        self.assertTrue(self.exists(MARKER))
        self.cli("forget", "--all", "--data-dir", self.data, "--yes")
        self.assertFalse(os.path.exists(self.data))

    def test_the_default_location_is_adopted_whatever_it_holds(self):
        xdg = os.path.join(self.t, "xdg")
        home = os.path.join(xdg, "tinkerprint")
        self.put(os.path.join(home, "notes.txt"))
        with mock.patch.dict(os.environ, {"XDG_DATA_HOME": xdg}):
            claim_home(home)
            self.assertTrue(os.path.isfile(os.path.join(home, MARKER)))
            text = self.cli("forget", "--all", "--yes")
        self.assertIn("notes.txt", text)
        self.assertTrue(os.path.isfile(os.path.join(home, "notes.txt")))

    def test_an_out_folder_inside_the_data_folder_is_refused(self):
        a = self.write(os.path.join(self.t, "a.toml"))
        self.build(a)
        for out in (os.path.join(self.data, "sheets", "mine-0badc0de"),
                    os.path.join(self.data, "sheets", lookup(self.data, a)), self.data):
            code, _, err = self.run_cli("build", "--profile", a, "--data-dir", self.data, "--out", out)
            self.assertEqual(code, 2, out)
            self.assertIn("Choose an output folder outside tinkerprint's data folder, or leave out --out", err)
        self.assertFalse(self.exists("sheets", "mine-0badc0de"))

    @unittest.skipIf(os.name == "nt", "symlinks need privileges on Windows")
    def test_an_out_folder_reached_through_a_link_is_refused(self):
        a = self.write(os.path.join(self.t, "a.toml"))
        self.build(a)
        link = os.path.join(self.t, "link")
        os.symlink(os.path.join(self.data, "sheets"), link)
        code, _, err = self.run_cli("build", "--profile", a, "--data-dir", self.data, "--out",
                                    os.path.join(link, "x"))
        self.assertEqual(code, 2)
        self.assertIn("inside tinkerprint's data folder", err)

    def test_a_build_that_waited_while_forget_ran_writes_nothing(self):
        a = self.write(os.path.join(self.t, "a.toml"))
        self.build(a)
        os.remove(os.path.join(self.data, MARKER))
        with self.assertRaises(Gone):
            with data_lock(self.data, claimed=True):
                pass
        self.cli("forget", "--all", "--data-dir", self.data, "--yes")  # nothing to delete: no marker
        import shutil
        shutil.rmtree(self.data)
        with self.assertRaises(Gone):
            with data_lock(self.data, claimed=True):
                pass
        self.assertFalse(os.path.exists(self.data))


class Keys(Base):
    def test_a_registry_key_that_is_a_path_is_dropped(self):
        import json
        a = self.write(os.path.join(self.t, "a.toml"))
        self.build(a)
        with open(os.path.join(self.data, REGISTRY), encoding="utf-8") as f:
            reg = json.load(f)
        reg["profiles"] = {"../../elsewhere": {"path": a, "sig": "x"}}
        with open(os.path.join(self.data, REGISTRY), "w", encoding="utf-8") as f:
            json.dump(reg, f)
        self.assertEqual(read_registry(self.data), {})
        self.assertTrue(is_key(lookup(self.data, a)))
        with self.assertRaises(ValueError):
            fg.show(self.data, None, "../../elsewhere")

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


class Moves(Base):
    def test_the_old_path_of_a_moved_profile_points_to_the_new_one(self):
        a = self.write(os.path.join(self.t, "a", "p.toml"))
        self.build(a)
        key = lookup(self.data, a)
        b = os.path.join(self.t, "b", "p.toml")
        os.makedirs(os.path.dirname(b))
        os.rename(a, b)
        self.build(b)
        self.assertEqual(lookup(self.data, b), key)
        self.assertIsNone(lookup(self.data, a))
        text = self.cli("forget", "--profile", a, "--data-dir", self.data)
        self.assertIn(f"went with the profile file now at {b}", text)
        self.assertIn(os.path.join(self.data, "history", key), self.cli("forget", "--profile", b, "--data-dir",
                                                                         self.data))

    def test_a_changed_identity_at_the_same_path_is_said(self):
        a = self.write(os.path.join(self.t, "p.toml"))
        self.build(a)
        self.assertNotIn("changed", self.build(a))
        self.write(a, name="Someone Else")
        text = self.build(a)
        hist = os.path.join(self.data, "history", lookup(self.data, a))
        self.assertIn("This profile's name or identity changed since its last build, and its saved sheets carry on. "
                      f"To start afresh, delete {hist} and build again.", text)
        self.assertNotIn("identity changed", self.build(a))


if __name__ == "__main__":
    unittest.main()
