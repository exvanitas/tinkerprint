"""Profile mistakes are plain ProfileErrors that name the key, and the CLI never shows a traceback.
Every name, path and email here is invented."""
import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

import helpers  # noqa: F401
from tinkerprint.cli import main
from tinkerprint.profile import ProfileError, load_profile, parse_profile

BASE = {"name": "Pip Quill", "identity": {"emails": ["pip@quill.example.test"]},
        "project": [{"name": "Kite", "root": "/w/kite"}]}


def parse(**over):
    data = {k: (dict(v) if isinstance(v, dict) else list(v) if isinstance(v, list) else v) for k, v in BASE.items()}
    data.update(over)
    return parse_profile(data, "/nonexistent-base")


class UnknownKeys(unittest.TestCase):
    def check(self, data_or_over, key, suggestion=None):
        with self.assertRaises(ProfileError) as cm:
            parse(**data_or_over)
        msg = str(cm.exception)
        self.assertIn(repr(key), msg)
        if suggestion:
            self.assertIn(f"Did you mean {suggestion!r}", msg)
        return msg

    def test_projects_suggests_project(self):
        self.check({"projects": [{"name": "Kite", "root": "/w/kite"}]}, "projects", "project")

    def test_wrok_suggests_work(self):
        self.check({"wrok": True}, "wrok", "work")

    def test_harness_suggests_harnesses(self):
        self.check({"harness": {"claude": True}}, "harness", "harnesses")

    def test_nested_keys(self):
        self.check({"identity": {"email": ["pip@quill.example.test"]}}, "email", "emails")
        self.check({"harnesses": {"cladue": True}}, "cladue", "claude")
        self.check({"card": {"allwo": True}}, "allwo", "allow")
        self.check({"project": [{"name": "Kite", "root": "/w/kite", "overrides": []}]}, "overrides", "override")
        self.check({"project": [{"name": "Kite", "root": "/w/kite", "part": [{"pth": "web"}]}]}, "pth", "path")
        self.check({"project": [{"name": "Kite", "root": "/w/kite",
                                 "override": [{"glob": "a/**", "stats": {"Logic": 1}, "stat": 1}]}]},
                   "stat", "stats")

    def test_key_from_another_table_says_where_it_goes(self):
        msg = self.check({"bots": ["robot*"]}, "bots")
        self.assertIn("[identity]", msg)

    def test_no_suggestion_for_nonsense(self):
        msg = self.check({"zzqx": 1}, "zzqx")
        self.assertNotIn("Did you mean", msg)

    def test_unknown_stat_suggests_one(self):
        with self.assertRaises(ProfileError) as cm:
            parse(project=[{"name": "Kite", "root": "/w/kite", "stats": {"logic": 1}}])
        self.assertIn("Did you mean 'Logic'", str(cm.exception))

    def test_example_profile_still_parses(self):
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prof = load_profile(os.path.join(here, "examples", "profile.example.toml"))
        self.assertTrue(prof.projects)


class WrongTypes(unittest.TestCase):
    CASES = [
        {"identity": "x"},
        {"identity": ["pip@quill.example.test"]},
        {"harnesses": "claude"},
        {"card": True},
        {"project": {"name": "Kite", "root": "/w/kite"}},
        {"project": ["Kite"]},
        {"project": [{"name": "Kite", "root": "/w/kite", "part": "web"}]},
        {"project": [{"name": "Kite", "root": "/w/kite", "part": [{"path": 3}]}]},
        {"project": [{"name": "Kite", "root": "/w/kite", "part": [3]}]},
        {"project": [{"name": "Kite", "root": "/w/kite", "override": {"glob": "a"}}]},
        {"project": [{"name": "Kite", "root": "/w/kite", "override": ["a/**"]}]},
        {"project": [{"name": "Kite", "root": 7}]},
        {"name": 5},
        {"set": ["builder"]},
        {"timezone": 2},
        {"rollover_hour": True},
        {"milestones": 3},
        {"work": "false"},
        {"harnesses": {"claude_dir": 1}},
    ]

    def test_each_is_a_profile_error(self):
        for over in self.CASES:
            with self.subTest(over=over):
                with self.assertRaises(ProfileError):
                    parse(**over)


    def test_tz_without_data_says_tzdata(self):
        with mock.patch("zoneinfo.available_timezones", return_value=set()), \
                mock.patch("tinkerprint.profile.load_tz", side_effect=KeyError("Europe/Lisbon")):
            with self.assertRaises(ProfileError) as cm:
                parse(timezone="Europe/Lisbon")
        self.assertIn("tzdata", str(cm.exception))


class Cli(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def write(self, text, name="p.toml"):
        path = os.path.join(self.t, name)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def test_missing_profile_is_a_plain_message(self):
        code, _, err = self.run_cli("build", "--profile", os.path.join(self.t, "nope.toml"),
                                    "--data-dir", os.path.join(self.t, "data"))
        self.assertEqual(code, 2)
        self.assertIn("no profile at", err)
        self.assertIn("tinkerprint init", err)
        self.assertNotIn("Errno", err)
        self.assertNotIn("Traceback", err)

    def test_folder_as_profile(self):
        code, _, err = self.run_cli("build", "--profile", self.t, "--data-dir", os.path.join(self.t, "data"))
        self.assertEqual(code, 2)
        self.assertIn("is a folder", err)
        self.assertNotIn("Errno", err)

    @unittest.skipUnless(os.name == "posix" and hasattr(os, "geteuid") and os.geteuid() != 0, "POSIX, not root")
    def test_unreadable_profile(self):
        path = self.write('name = "Pip"\n')
        os.chmod(path, 0)
        code, _, err = self.run_cli("build", "--profile", path, "--data-dir", os.path.join(self.t, "data"))
        self.assertEqual(code, 2)
        self.assertIn("permission denied", err)
        self.assertNotIn("Errno", err)

    def test_not_utf8(self):
        path = os.path.join(self.t, "p.toml")
        with open(path, "wb") as f:
            f.write(b'name = "\xff\xfe"\n')
        code, _, err = self.run_cli("build", "--profile", path, "--data-dir", os.path.join(self.t, "data"))
        self.assertEqual(code, 2)
        self.assertIn("not UTF-8", err)

    def test_bad_toml(self):
        path = self.write("name = \n")
        code, _, err = self.run_cli("build", "--profile", path, "--data-dir", os.path.join(self.t, "data"))
        self.assertEqual(code, 2)
        self.assertIn("p.toml", err)

    def test_wrong_type_through_the_cli(self):
        path = self.write('identity = "x"\n')
        code, _, err = self.run_cli("build", "--profile", path, "--data-dir", os.path.join(self.t, "data"))
        self.assertEqual(code, 2)
        self.assertIn("identity must be a table", err)
        self.assertNotIn("Traceback", err)

    def test_unknown_key_through_the_cli(self):
        path = self.write('name = "Pip"\n[identity]\nemails = ["pip@quill.example.test"]\n'
                          '[[projects]]\nname = "Kite"\nroot = "/w/kite"\n')
        code, _, err = self.run_cli("audit", "--profile", path, "--data-dir", os.path.join(self.t, "data"))
        self.assertEqual(code, 2)
        self.assertIn("Did you mean 'project'", err)

    def test_bad_season_and_date(self):
        path = self.write('name = "Pip"\n[identity]\nemails = ["pip@quill.example.test"]\n')
        for extra in (["--season", "2026"], ["--as-of", "soon"]):
            with self.subTest(extra=extra):
                code, _, err = self.run_cli("build", "--profile", path, "--data-dir", os.path.join(self.t, "data"),
                                            *extra)
                self.assertEqual(code, 2)
                self.assertTrue(err.startswith("tinkerprint: "))

    def test_bad_art_pack(self):
        path = self.write("{}", name="pack.json")
        code, _, err = self.run_cli("gallery", "--out", os.path.join(self.t, "g"), "--art-pack", path)
        self.assertEqual(code, 2)
        self.assertTrue(err.startswith("tinkerprint: "))

    def test_unexpected_error_is_one_line(self):
        import argparse
        from tinkerprint import cli

        def boom(args):
            raise RuntimeError("boom")
        fake = mock.Mock()
        fake.return_value.parse_args.return_value = argparse.Namespace(func=boom)
        with mock.patch.object(cli, "parser", fake), mock.patch.dict(os.environ, {"TINKERPRINT_DEBUG": ""}):
            code, _, err = self.run_cli()
        self.assertEqual(code, 1)
        self.assertIn("This is a bug", err)
        self.assertIn("boom", err)
        self.assertNotIn("Traceback", err)

    def test_missing_tz_data_is_a_message(self):
        import argparse
        from zoneinfo import ZoneInfoNotFoundError
        from tinkerprint import cli

        def boom(args):
            raise ZoneInfoNotFoundError("No time zone found with key Invented/Zone")
        fake = mock.Mock()
        fake.return_value.parse_args.return_value = argparse.Namespace(func=boom)
        with mock.patch.object(cli, "parser", fake):
            code, _, err = self.run_cli()
        self.assertEqual(code, 2)
        self.assertIn("tzdata", err)


if __name__ == "__main__":
    unittest.main()
