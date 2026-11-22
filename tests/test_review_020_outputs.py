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


if __name__ == "__main__":
    unittest.main()
