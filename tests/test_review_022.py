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


if __name__ == "__main__":
    unittest.main()
