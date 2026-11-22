"""0.2.0 review, part 2: the sheet's HTML, parts, small fixes and shallow clones.
Every name, path and email here is invented."""
import json
import os
import tempfile
import unittest
from datetime import date

import helpers  # noqa: F401
from tinkerprint.render_html import _changes
from tinkerprint.score import compare


def sheet_like():
    return {"method": 3, "profile": {"set": "builder"}, "history": {"points": 9, "level": 3},
            "stats": [{"key": "Logic", "share": 1.0}], "party": [{"harness": "claude", "name": "Claude Code",
                                                                  "sessions": 4}],
            "achievements": [], "class": None}


class SavedHistory(unittest.TestCase):
    """A saved sheet that was damaged or edited never breaks a build or puts markup on the page."""

    BAD = "<script>alert(1)</script>"

    def test_text_where_numbers_go(self):
        prev = {"method": 3, "profile": {"set": "builder"},
                "history": {"points": "12; DROP", "level": self.BAD},
                "stats": [{"key": "Logic", "share": "most"}, "junk", {"share": 1}],
                "party": [{"harness": "claude", "sessions": "many"}, {"no": "harness"}],
                "achievements": [{"id": 5}, "x"], "class": {"kind": self.BAD}}
        ch = compare(sheet_like(), prev, "2026-03-01")
        self.assertIsNone(ch["level_from"])
        self.assertEqual(ch["points_since"], 9)
        self.assertEqual(ch["class_from"], "Unclassed")
        html = _changes(ch)
        self.assertNotIn("<script", html)
        self.assertIn("+9 points.", html)

    def test_wrong_shapes_never_raise(self):
        for prev in ({"method": 3, "history": [], "profile": "x", "stats": {}, "party": "x", "achievements": 3},
                     {"method": 3, "history": {"level": True, "points": 1.5}},
                     {"method": [self.BAD]}):
            with self.subTest(prev=prev):
                ch = compare(sheet_like(), prev, "2026-03-01")
                self.assertNotIn("<script", _changes(ch))

    def test_the_panel_escapes_what_it_is_handed(self):
        ch = {"against": "2026-03-01", "points_since": 2, "level_from": self.BAD, "level_to": 3,
              "set_changed": False, "new_class": False, "class_to": "Sage", "drift": [],
              "party_sessions": [{"name": "Claude Code", "sessions_since": self.BAD}]}
        html = _changes(ch)
        self.assertNotIn("<script", html)
        self.assertIn("Claude Code: +0 sessions.", html)


class PartsStayInside(unittest.TestCase):
    """A part is a folder inside its project's root. Nothing outside the root is ever read."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = os.path.realpath(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def parse(self, part):
        from helpers import profile
        return profile([("P", os.path.join(self.t, "root"), {"part": [{"path": part}]})])

    def test_a_part_that_leaves_its_root_is_refused(self):
        from tinkerprint.profile import ProfileError
        for part in ("../other", "..", "web/../../other", ".", "web/..", "C:/other", "c:other"):
            with self.subTest(part=part):
                with self.assertRaises(ProfileError) as cm:
                    self.parse(part)
                self.assertIn("inside the project's root", str(cm.exception))
        self.assertEqual(self.parse("web/./api/").projects[0].parts[0].path, "web/api")
        self.assertEqual(self.parse("web/../api").projects[0].parts[0].path, "api")

    def test_a_linked_part_is_not_read(self):
        from tinkerprint.projects import scan_priors
        root, other = os.path.join(self.t, "root"), os.path.join(self.t, "other")
        os.makedirs(root)
        os.makedirs(other)
        with open(os.path.join(other, "package.json"), "w") as f:
            json.dump({"name": "x", "bin": {"x": "x.js"}}, f)
        with open(os.path.join(other, "requirements.txt"), "w") as f:
            f.write("torch\n")
        os.symlink(other, os.path.join(root, "web"))
        os.makedirs(os.path.join(root, "api"))
        os.symlink(os.path.join(other, "package.json"), os.path.join(root, "api", "package.json"))
        from helpers import profile
        prof = profile([("P", root, {"part": [{"path": "web"}, {"path": "api"}]})])
        self.assertEqual(scan_priors(prof.projects)["P"], {})


if __name__ == "__main__":
    unittest.main()
