"""0.2.0 review, round 2: audit's schema and aliases, the public month, Windows log paths, git
manifests, Antigravity rows, shallow boundaries, damaged history and exact key grammar.
Every name, path and email here is invented."""
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

import helpers  # noqa: F401
from helpers import commit, profile, run
from tinkerprint.art import default_pack
from tinkerprint.audit import audit, schema_problems
from tinkerprint.cli import main
from tinkerprint.look import public_name
from tinkerprint.render_card import portrait_gif, portrait_png, render_card
from tinkerprint.render_card_png import render_card_png


def write_card(out, sheet):
    """sheet.json and every card file, drawn from the sheet's card fields as they are."""
    card = sheet["card"]
    files = {"sheet.json": json.dumps(sheet).encode(), "card.svg": render_card(card, PACK).encode(),
             "card.png": render_card_png(card, PACK), "portrait.png": portrait_png(card, PACK),
             "portrait.gif": portrait_gif(card, PACK)}
    for name, data in files.items():
        with open(os.path.join(out, name), "wb") as f:
            f.write(data)


PACK = default_pack()


class AuditPolicy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "out")
        os.makedirs(self.out)
        self.evs = [commit("2026-03-02T10:00:00+00:00", "/w/kite/app.py"),
                    commit("2026-03-03T10:00:00+00:00", "/w/kite/app.py", h="c2")]
        sheet = run(self.prof(), self.evs)[0]
        self.assertIn("projects", sheet["card"])
        write_card(self.out, sheet)

    def tearDown(self):
        self.tmp.cleanup()

    def prof(self):
        return profile([("Kite", "/w/kite", None)], name="Ida Fenwick", card={"show": ["projects"]})

    def sheet(self):
        with open(os.path.join(self.out, "sheet.json"), encoding="utf-8") as f:
            return json.load(f)

    def test_an_empty_profile_is_not_a_missing_one(self):
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            code = main(["audit", "--profile", "", "--out", self.out])
        self.assertNotEqual(code, 0)
        self.assertIn("--profile is empty", err.getvalue())

    def test_a_withdrawn_project_alias_fails(self):
        renamed = self.prof()
        renamed.projects[0].name = "Kestrel"
        lines, clean = audit(self.out, renamed)
        self.assertFalse(clean)
        self.assertIn("projects", lines[-1])

    def test_edited_fields_outside_the_schema_fail_before_any_redraw(self):
        for field, value in (("built", "2026-03-02"), ("built", 202603), ("chart", "pie"),
                             ("stats", [{"stat": "Logic", "pct": 37}]), ("stats", [{"stat": "Secrets", "pct": 50}]),
                             ("stats", [{"stat": "Logic", "pct": 50, "note": "x"}]), ("chart", "bars")):
            sheet = self.sheet()
            if field == "chart" and value == "bars":
                sheet["card"]["stats"] = [{"stat": s, "pct": 20} for s in ("Logic", "Tools", "Docs")]
            sheet["card"][field] = value
            try:
                write_card(self.out, sheet)
            except (KeyError, TypeError, ValueError, AttributeError):
                with open(os.path.join(self.out, "sheet.json"), "w", encoding="utf-8") as f:
                    json.dump(sheet, f)
            self.assertIn(field, schema_problems(sheet["card"]), (field, value))
            for prof in (None, self.prof()):
                lines, clean = audit(self.out, prof)
                self.assertFalse(clean, (field, value))
                self.assertIn("hold what a card may not show", "\n".join(lines))

    def test_a_month_is_fine(self):
        sheet = self.sheet()
        sheet["card"]["built"] = "Mar 2026"
        write_card(self.out, sheet)
        self.assertEqual(schema_problems(sheet["card"]), [])
        self.assertTrue(audit(self.out, self.prof())[1])

    def test_a_saved_name_seeds_the_portrait_as_the_card_clips_it(self):
        card = dict(self.sheet()["card"], name="Ida Fenwick Quillworth-Abernathy")
        clipped = dict(card, name="Ida Fenwick Quillworth…")
        self.assertEqual(portrait_png(card, PACK), portrait_png(clipped, PACK))
        self.assertEqual(portrait_gif(card, PACK), portrait_gif(clipped, PACK))


class PublicMonth(unittest.TestCase):
    def test_a_future_session_outside_every_root_never_sets_the_month(self):
        from datetime import date
        from helpers import session
        from tinkerprint.build import build
        from tinkerprint.events import Inputs
        with tempfile.TemporaryDirectory() as t:
            prof = profile([("Kite", os.path.join(t, "kite"), None)], name="Ida Fenwick")
            evs = [commit("2026-03-02T10:00:00+00:00", os.path.join(t, "kite", "app.py")),
                   session("2027-07-04T10:00:00+00:00", os.path.join(t, "elsewhere"), sid="s9")]
            res = build(prof, os.path.join(t, "out"), home=os.path.join(t, "data"), inputs=Inputs(events=evs),
                        today=date(2026, 11, 23))
            self.assertEqual(res["sheet"]["card"]["built"], "Nov 2026")
            res = build(prof, os.path.join(t, "out"), home=os.path.join(t, "data"), inputs=Inputs(events=evs),
                        as_of=date(2026, 5, 1), today=date(2026, 11, 23))
            self.assertEqual(res["sheet"]["card"]["built"], "May 2026")


if __name__ == "__main__":
    unittest.main()
