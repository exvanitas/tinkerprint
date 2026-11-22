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


def card_profile(path, base, enabled):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f'name = "Ida"\n[identity]\nemails = ["ida@fenwick.example.test"]\n[harnesses]\nclaude = true\n'
                f'codex = false\nclaude_dir = "{base.logs}"\n[card]\nenabled = {"true" if enabled else "false"}\n'
                f'[[project]]\nname = "P"\nroot = "{base.root}"\n')
    return path


class CardFilesWhenOff(Base):
    def test_an_out_folder_keeps_its_files_and_the_build_names_them(self):
        out = os.path.join(self.t, "exports")
        self.put(os.path.join(out, "portrait.png"), "another tool's picture\n")
        self.put(os.path.join(out, "card.svg"), "<svg/>\n")
        p = card_profile(os.path.join(self.t, "w.toml"), self, False)
        text = self.build(p, "--out", out)
        self.assertTrue(os.path.isfile(os.path.join(out, "portrait.png")))
        self.assertTrue(os.path.isfile(os.path.join(out, "card.svg")))
        self.assertIn(f"Note: {out} still holds card.svg, portrait.png from an earlier build. Delete them if they "
                      "should not be shared.", text)

    def test_the_default_sheets_folder_loses_its_old_card_files(self):
        p = card_profile(os.path.join(self.t, "w.toml"), self, True)
        self.build(p)
        key = os.listdir(os.path.join(self.data, "sheets"))[0]
        out = os.path.join(self.data, "sheets", key)
        self.assertTrue(all(os.path.isfile(os.path.join(out, n)) for n in CARD_FILES))
        card_profile(p, self, False)
        text = self.build(p)
        self.assertFalse(any(os.path.lexists(os.path.join(out, n)) for n in CARD_FILES))
        self.assertNotIn("still holds", text)


class BuildAndForget(Base):
    def test_forget_waits_for_a_build_that_registered_its_profile(self):
        prof = load_profile(self.write(os.path.join(self.t, "a.toml")))
        started, go = threading.Event(), threading.Event()
        real = bd.gather

        def slow(profile, home):
            started.set()
            go.wait(10)
            return real(profile, home)
        done = {}
        with mock.patch.object(bd, "gather", side_effect=slow):
            th = threading.Thread(target=lambda: done.update(res=bd.build(prof, bd.default_out(self.data, prof),
                                                                          home=self.data)), daemon=True)
            th.start()
            self.assertTrue(started.wait(10))
            ft = threading.Thread(target=lambda: done.update(lines=fg.forget_all(self.data, True)), daemon=True)
            ft.start()
            ft.join(0.4)
            self.assertTrue(ft.is_alive(), "forget ran while the build was between registering and publishing")
            go.set()
            th.join(20)
            ft.join(20)
        self.assertIn("res", done)
        self.assertIn("Deleted", done["lines"][-1])
        self.assertFalse(os.path.exists(self.data))

    def test_a_build_after_forget_stops_before_writing(self):
        a = self.write(os.path.join(self.t, "a.toml"))
        self.build(a)
        real = bd.claim_home

        def claim_then_forget(home):
            real(home)
            fg.forget_all(home, True)
        with mock.patch.object(bd, "claim_home", side_effect=claim_then_forget):
            with self.assertRaises(ValueError) as cm:
                bd.build(load_profile(a), os.path.join(self.t, "out"), home=self.data)
        self.assertIn("was deleted while this run waited", str(cm.exception))
        self.assertFalse(os.path.exists(self.data))
        self.assertFalse(os.path.exists(os.path.join(self.t, "out")))

    def test_the_cli_build_nests_in_one_hold(self):
        a = self.write(os.path.join(self.t, "a.toml"))
        done = []
        th = threading.Thread(target=lambda: done.append(self.run_cli("build", "--profile", a, "--data-dir",
                                                                      self.data)), daemon=True)
        th.start()
        th.join(60)
        self.assertFalse(th.is_alive(), "the build waited on itself")
        self.assertEqual(done[0][0], 0, done[0][2])
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            from tinkerprint.cli import main
            self.assertEqual(main(["audit", "--profile", a, "--data-dir", self.data]), 0)


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
