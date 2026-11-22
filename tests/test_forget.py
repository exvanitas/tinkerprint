"""forget lists what it would delete, deletes only with --yes, and only what tinkerprint wrote.
Every name, path and email here is invented."""
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
from tinkerprint.cli import main
from tinkerprint.demo import RepoWriter
from tinkerprint.profile import profile_id

UTC = ZoneInfo("UTC")
ME = ("Ida Fenwick", "ida@fenwick.example.test")


class Forget(unittest.TestCase):
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
        self.a = self.write("a.toml")
        self.b = self.write("b.toml")
        self.out = os.path.join(self.t, "exported")
        self.cli("build", "--profile", self.a, "--data-dir", self.data)
        self.cli("build", "--profile", self.a, "--data-dir", self.data, "--out", self.out)
        self.cli("build", "--profile", self.b, "--data-dir", self.data)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, name):
        path = os.path.join(self.t, name)
        with open(path, "w", encoding="utf-8") as f:
            # An empty claude folder: the build writes a cache without reading anyone's real logs.
            f.write(f'name = "Ida"\n[identity]\nemails = ["{ME[1]}"]\n[harnesses]\nclaude = true\ncodex = false\n'
                    f'claude_dir = "{self.logs}"\n[[project]]\nname = "P"\nroot = "{self.root}"\n')
        return path

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        self.assertEqual(code, 0, err.getvalue())
        return out.getvalue()

    def exists(self, *parts):
        return os.path.lexists(os.path.join(self.data, *parts))

    def test_lists_without_yes(self):
        text = self.cli("forget", "--profile", self.a, "--data-dir", self.data)
        ka = profile_id(self.a)
        self.assertIn("This deletes", text)
        self.assertIn("cache" + os.sep, text)
        self.assertIn(os.path.join("history", ka), text)
        self.assertIn(os.path.join("last-build", ka + ".json"), text)
        self.assertIn("--yes", text)
        self.assertIn("Kept: ", text)
        self.assertTrue(self.exists("history", ka))
        self.assertTrue(self.exists("cache"))

    def test_one_profile(self):
        ka, kb = profile_id(self.a), profile_id(self.b)
        text = self.cli("forget", "--profile", self.a, "--data-dir", self.data, "--yes")
        self.assertIn("Deleted", text)
        self.assertFalse(self.exists("history", ka))
        self.assertFalse(self.exists("last-build", ka + ".json"))
        self.assertFalse(self.exists("cache"))
        self.assertTrue(self.exists("history", kb))
        self.assertTrue(self.exists("last-build", kb + ".json"))
        self.assertTrue(self.exists("sheets", ka, "sheet.html"))
        self.assertTrue(os.path.isfile(os.path.join(self.out, "sheet.html")))
        self.assertTrue(os.path.isdir(os.path.join(self.root, ".git")))
        self.assertTrue(os.path.isfile(self.a))
        self.assertIn("Nothing to forget", self.cli("forget", "--profile", self.a, "--data-dir", self.data))

    def test_a_profile_file_that_is_gone(self):
        os.unlink(self.a)
        self.cli("forget", "--profile", self.a, "--data-dir", self.data, "--yes")
        self.assertFalse(self.exists("history", profile_id(self.a)))

    def test_all(self):
        self.cli("forget", "--all", "--data-dir", self.data, "--yes")
        self.assertFalse(os.path.exists(self.data))
        self.assertTrue(os.path.isfile(os.path.join(self.out, "sheet.html")))
        self.assertTrue(os.path.isdir(self.logs))
        self.assertTrue(os.path.isdir(os.path.join(self.root, ".git")))

    def test_foreign_files_are_left_alone(self):
        with open(os.path.join(self.data, "cache", "notes.txt"), "w") as f:
            f.write("mine\n")
        os.makedirs(os.path.join(self.data, "keep-me"))
        text = self.cli("forget", "--all", "--data-dir", self.data, "--yes")
        self.assertIn("Left alone: " + os.path.join(self.data, "cache"), text)
        self.assertTrue(self.exists("cache", "notes.txt"))
        self.assertTrue(self.exists("keep-me"))
        self.assertFalse(self.exists("history"))

    def test_data_dir_that_is_not_ours(self):
        home = os.path.join(self.t, "someone")
        for d in ("cache", "history", "sheets", "last-build"):
            os.makedirs(os.path.join(home, d, "stuff"))
        text = self.cli("forget", "--all", "--data-dir", home, "--yes")
        self.assertIn("Nothing to forget", text)
        for d in ("cache", "history", "sheets", "last-build"):
            self.assertTrue(os.path.isdir(os.path.join(home, d, "stuff")))

    def test_needs_a_profile_or_all(self):
        old = os.getcwd()
        os.chdir(self.t)
        try:
            err = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(err):
                code = main(["forget", "--data-dir", self.data])
        finally:
            os.chdir(old)
        self.assertEqual(code, 2)
        self.assertIn("--all", err.getvalue())


if __name__ == "__main__":
    unittest.main()
