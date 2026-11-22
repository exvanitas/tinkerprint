"""The sheet says how many active days its class rests on. Every name and path here is invented."""
import unittest

import helpers  # noqa: F401
from helpers import commit, profile, run
from tinkerprint.render_html import render_html


class Evidence(unittest.TestCase):
    prof = profile([("A", "/w/a", None)])

    def sheet(self, logic_days, image_days):
        evs = [commit(f"2026-03-{1 + i:02d}T10:00:00+00:00", "/w/a/app.py", h=f"p{i}") for i in range(logic_days)]
        evs += [commit(f"2026-04-{1 + i:02d}T10:00:00+00:00", f"/w/a/art/{i}.png", h=f"i{i}")
                for i in range(image_days)]
        return run(self.prof, evs)[0]

    def test_one_classified_day_of_ten(self):
        sheet = self.sheet(1, 9)
        self.assertEqual(sheet["class"]["stats"], ["Logic"])
        self.assertEqual((sheet["season_totals"]["classified_days"], sheet["season_totals"]["active_days"]), (1, 10))
        html = render_html(sheet)
        self.assertIn("Based on 1 of 10 active days. The rest changed only unclassified files.", html)

    def test_every_day_classified(self):
        html = render_html(self.sheet(3, 0))
        self.assertIn("Based on 3 of 3 active days.", html)
        self.assertNotIn("The rest changed only", html)

    def test_unclassed_says_nothing_more(self):
        sheet = self.sheet(0, 4)
        self.assertIsNone(sheet["class"])
        self.assertEqual(sheet["season_totals"]["classified_days"], 0)
        self.assertNotIn("Based on", render_html(sheet))

    def test_card_is_unchanged(self):
        self.assertNotIn("classified_days", repr(self.sheet(1, 9)["card"]))


if __name__ == "__main__":
    unittest.main()
