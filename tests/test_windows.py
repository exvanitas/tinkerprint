"""Windows-safe paths, time zones and URIs, checked with Windows path rules (ntpath) on any OS.
Every name, path and email here is invented."""
import ntpath
import os
import posixpath
import re
import sqlite3
import tempfile
import tomllib
import unittest
from datetime import date, datetime, timedelta, timezone

import helpers  # noqa: F401
from helpers import profile
from tinkerprint.cli import local_tz, starter
from tinkerprint.datadir import inside_repo_or_root, path_within
from tinkerprint.profile import load_profile, parse_profile, toml_string
from tinkerprint.demo import write_agy_db
from tinkerprint.readers import agy
from tinkerprint.readers.agy import _ro_uri, _uri_path

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TomlPaths(unittest.TestCase):
    def test_windows_path_round_trips(self):
        for p in (r"C:\Users\Ana\code\kite", "C:\\Users\\u0041\\x", r"\\server\share\kite"):
            with self.subTest(p=p):
                self.assertEqual(tomllib.loads(f"x = {toml_string(p)}")["x"], p)

    def test_demo_profile_parses_under_a_backslash_folder(self):
        if os.sep == "\\":
            self.skipTest("a backslash is a separator here")
        from tinkerprint.build import build
        from tinkerprint.demo import PEOPLE, make_person
        with tempfile.TemporaryDirectory() as t:
            work = os.path.join(t, "C:\\Users\\Ana")  # \U would start a unicode escape in a TOML basic string
            os.makedirs(work)
            prof = load_profile(make_person(work, PEOPLE[0]))
            self.assertTrue(prof.projects[0].roots[0].startswith(work))
            res = build(prof, os.path.join(t, "out"), home=os.path.join(t, "data"), today=date(2026, 11, 1))
            self.assertGreater(res["sheet"]["history"]["points"], 0)
            self.assertGreater(res["sheet"]["inputs"]["sessions"], 0)


class LocalTz(unittest.TestCase):
    def now(self, minutes):
        return datetime(2026, 3, 2, 10, tzinfo=timezone(timedelta(minutes=minutes)))

    def test_offset_fallback_without_etc(self):
        with tempfile.TemporaryDirectory() as etc:
            self.assertEqual(local_tz(etc, self.now(330)), ("+05:30", True))
            self.assertEqual(local_tz(etc, self.now(-180)), ("-03:00", True))
            self.assertEqual(local_tz(etc, self.now(345)), ("+05:45", True))
            self.assertEqual(local_tz(etc, self.now(0)), ("UTC", True))

    def test_fallback_parses_and_says_to_replace_it(self):
        with tempfile.TemporaryDirectory() as etc:
            tz, guessed = local_tz(etc, self.now(-570))
        text = starter(tz=tz, tz_guessed=guessed)
        self.assertIn("IANA name", text.split("[identity]")[0].split("timezone =")[1])
        data = tomllib.loads(text)
        self.assertEqual(data["timezone"], "-09:30")
        parse_profile(data, "/nonexistent-base")

    def test_names_from_etc(self):
        with tempfile.TemporaryDirectory() as etc:
            with open(os.path.join(etc, "timezone"), "w") as f:
                f.write("Europe/Lisbon\n")
            self.assertEqual(local_tz(etc), ("Europe/Lisbon", False))
        with tempfile.TemporaryDirectory() as etc:
            os.symlink("/usr/share/zoneinfo/America/Chicago", os.path.join(etc, "localtime"))
            self.assertEqual(local_tz(etc), ("America/Chicago", False))

    def test_tzdata_only_on_windows(self):
        with open(os.path.join(HERE, "pyproject.toml"), "rb") as f:
            proj = tomllib.load(f)["project"]
        self.assertEqual(proj["dependencies"], ['tzdata; sys_platform == "win32"'])
        self.assertEqual(proj["urls"]["Homepage"], "https://github.com/exvanitas/tinkerprint")


class Containment(unittest.TestCase):
    def test_windows_rules(self):
        self.assertTrue(path_within(r"C:\Users\Ana\data", "C:/Users/Ana", ntpath))
        self.assertTrue(path_within(r"c:\users\ana", r"C:\Users\Ana", ntpath))
        self.assertTrue(path_within(r"C:\Users\Ana\data", "C:\\", ntpath))
        self.assertFalse(path_within(r"C:\Users\Anabel", r"C:\Users\Ana", ntpath))
        self.assertFalse(path_within(r"D:\Users\Ana", r"C:\Users\Ana", ntpath))

    def test_posix_rules(self):
        self.assertTrue(path_within("/w/a/b", "/w/a/", posixpath))
        self.assertTrue(path_within("/w/a", "/w/a", posixpath))
        self.assertTrue(path_within("/w/a", "/", posixpath))
        self.assertFalse(path_within("/w/ab", "/w/a", posixpath))
        self.assertFalse(path_within("/w/A", "/w/a", posixpath))

    def test_data_guard_and_aliases(self):
        from tinkerprint.build import alias_of
        with tempfile.TemporaryDirectory() as t:
            root = os.path.join(t, "kite")
            os.makedirs(os.path.join(root, "sub"))
            os.makedirs(os.path.join(t, "kite2"))
            self.assertEqual(inside_repo_or_root(os.path.join(root, "sub"), [root]), "it is inside a profile root")
            self.assertIsNone(inside_repo_or_root(os.path.join(t, "kite2"), [root]))
            prof = profile([("Kite", root, None)])
            self.assertEqual(alias_of(os.path.join(root, "sub"), prof), "Kite")
            self.assertEqual(alias_of(t, prof), "Kite")
            self.assertEqual(alias_of(os.path.join(t, "kite2"), prof), "A repo outside the profile")

    def test_no_slash_prefix_checks_left(self):
        pattern = re.compile(r'rstrip\("/"\)\s*\+\s*"/"|\+ "/"\)')
        src = os.path.join(HERE, "src", "tinkerprint")
        for name in ("datadir.py", "build.py", "score.py", "profile.py"):
            with open(os.path.join(src, name), encoding="utf-8") as f:
                self.assertIsNone(pattern.search(f.read()), name)

    def test_part_paths_use_forward_slashes(self):
        prof = profile([("Kite", "/w/kite", {"part": [{"path": "web//api/"}, "cli/./tools"]})])
        self.assertEqual([p.path for p in prof.projects[0].parts], ["web/api", "cli/tools"])


class AgyUris(unittest.TestCase):
    def test_windows_drive_uris(self):
        self.assertEqual(_uri_path("file:///C:/Users/Ana%20B/kite", ntpath), r"C:\Users\Ana B\kite")
        self.assertEqual(_uri_path("file:///c%3A/Users/Ana/kite", ntpath), r"c:\Users\Ana\kite")
        self.assertEqual(_uri_path("file://localhost/C:/kite", ntpath), r"C:\kite")
        self.assertIsNone(_uri_path("file://otherhost/C:/kite", ntpath))

    def test_posix_unchanged(self):
        self.assertEqual(_uri_path("file:///home/ana/kite%20two", posixpath), "/home/ana/kite two")
        self.assertIsNone(_uri_path("file://otherhost/home/ana", posixpath))
        self.assertEqual(_uri_path("file:///C:/kite", posixpath), "/C:/kite")

    def test_demo_uri_round_trips(self):
        from tinkerprint.demo import file_uri
        p = os.path.join(os.sep, "w", "Ünï code", "kite#1")
        self.assertEqual(_uri_path(file_uri(p)), p)


class RoUri(unittest.TestCase):
    def test_windows_paths(self):
        self.assertEqual(_ro_uri(r"C:\Users\Ana\agy\db.sqlite", ntpath), "file:///C:/Users/Ana/agy/db.sqlite?mode=ro")
        self.assertEqual(_ro_uri(r"\\server\share\db.sqlite", ntpath), "file:////server/share/db.sqlite?mode=ro")
        self.assertEqual(_ro_uri(r"C:\a%b\c?d#e.db", ntpath), "file:///C:/a%25b/c%3fd%23e.db?mode=ro")

    def test_posix_paths(self):
        self.assertEqual(_ro_uri("/home/ana/db.sqlite", posixpath), "file:/home/ana/db.sqlite?mode=ro")
        self.assertEqual(_ro_uri("//odd/db.sqlite", posixpath), "file:////odd/db.sqlite?mode=ro")

    def test_opens_read_only_with_odd_characters(self):
        if os.sep == "\\":
            self.skipTest("? is not allowed in Windows file names")
        with tempfile.TemporaryDirectory() as t:
            db = os.path.join(t, "a%b?c#d", "db.sqlite")
            write_agy_db(db, [("c1", ["/w/a"], datetime(2026, 3, 2, 10, tzinfo=timezone.utc))])
            self.assertEqual(len(agy.read_db(db)), 1)
            con = sqlite3.connect(_ro_uri(db), uri=True)
            with self.assertRaises(sqlite3.OperationalError):
                con.execute("insert into conversation_summaries (conversation_id) values ('x')")
            con.close()


if __name__ == "__main__":
    unittest.main()
