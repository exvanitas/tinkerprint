"""0.2.0 review, round 3: which data folders a build adopts and forget deletes, card files left in a
folder the user chose, a build and forget --all in turn, saved card fields of the wrong type, and
what forget says when something is left. Every name, path and email here is invented."""
import io
import json
import os
import threading
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

import helpers  # noqa: F401
from test_forget import Base
from tinkerprint import build as bd
from tinkerprint import forget as fg
from tinkerprint.datadir import LOCK, MARKER, MARKER_HEAD, data_lock
from tinkerprint.profile import load_profile

CARD_FILES = ("card.svg", "card.png", "portrait.png", "portrait.gif")


class LegacyAdoption(Base):
    def test_a_custom_folder_holding_only_tinkerprint_names_is_refused(self):
        other = os.path.join(self.t, "app-data")
        self.put(os.path.join(other, "cache", "app.db"), "another app's database\n")
        a = self.write(os.path.join(self.t, "a.toml"))
        code, _, err = self.run_cli("build", "--profile", a, "--data-dir", other)
        self.assertEqual(code, 2)
        self.assertIn("is not empty and is not a tinkerprint data folder", err)
        self.assertIn(f"create {MARKER} in it", err)
        self.assertEqual(os.listdir(other), ["cache"])
        code, out, _ = self.run_cli("forget", "--all", "--yes", "--data-dir", other)
        self.assertIn("Nothing was deleted", out)
        self.assertTrue(os.path.isfile(os.path.join(other, "cache", "app.db")))

    def test_a_custom_01_folder_is_adopted_once_marked(self):
        a = self.write(os.path.join(self.t, "a.toml"))
        self.build(a)
        os.remove(os.path.join(self.data, MARKER))
        code, _, err = self.run_cli("build", "--profile", a, "--data-dir", self.data)
        self.assertEqual(code, 2)
        self.put(os.path.join(self.data, MARKER), MARKER_HEAD + "\n")
        self.build(a)
        self.cli("forget", "--all", "--data-dir", self.data, "--yes")
        self.assertFalse(os.path.exists(self.data))

    def test_forget_deletes_an_unmarked_01_folder_at_the_default_location(self):
        xdg = os.path.join(self.t, "xdg")
        home = os.path.join(xdg, "tinkerprint")
        self.put(os.path.join(home, "cache", "claude.json"), "{}")
        self.put(os.path.join(home, "history", "a-0badc0de", "x.json"), "{}")
        with mock.patch.dict(os.environ, {"XDG_DATA_HOME": xdg}):
            text = self.cli("forget", "--all", "--yes")
        self.assertIn("Deleted", text)
        self.assertFalse(os.path.exists(home))


class ForgetReport(Base):
    def setUp(self):
        super().setUp()
        self.build(self.write(os.path.join(self.t, "a.toml")))

    def test_a_lock_file_held_open_is_named(self):
        import functools
        real_unlink, real_left = os.unlink, fg._left

        def held(path, *a, **k):
            if os.path.basename(path) == LOCK:  # as on Windows, while another process has it open
                raise PermissionError(13, "in use", path)
            return real_unlink(path, *a, **k)
        with mock.patch.object(os, "unlink", side_effect=held), \
                mock.patch.object(fg, "_left", functools.partial(real_left, wait=0.1)):
            lines = fg.forget_all(self.data, True)
        self.assertNotIn(f"Deleted {self.data} (", lines[-1])
        self.assertIn(f"Still there: {LOCK}", lines[-1])
        self.assertEqual(os.listdir(self.data), [LOCK])

    def test_a_file_that_cannot_be_removed_is_named(self):
        real = os.unlink

        def stuck(path, *a, **k):
            if os.path.basename(path) == "profiles.json":
                raise PermissionError(13, "in use", path)
            return real(path, *a, **k)
        with mock.patch.object(os, "unlink", side_effect=stuck):
            lines = fg.forget_all(self.data, True)
        self.assertIn("Still there: profiles.json", lines[-1])
        self.assertNotIn(f"Deleted {self.data} (", lines[-1])

    def test_a_second_forget_that_waited_says_so_and_leaves_nothing(self):
        result = []
        with data_lock(self.data):
            th = threading.Thread(target=lambda: result.append(fg.forget_all(self.data, True)), daemon=True)
            th.start()
            th.join(0.3)
            self.assertTrue(th.is_alive())
            self.assertIn("Deleted", fg.forget_all(self.data, True)[-1])
        th.join(10)
        self.assertIn("another tinkerprint run deleted", result[0][-1])
        self.assertFalse(os.path.exists(self.data))


if __name__ == "__main__":
    unittest.main()
