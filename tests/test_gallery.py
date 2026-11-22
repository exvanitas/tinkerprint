"""The gallery: the Keepsake art a pack draws, on one page. Everything on it is invented."""
import base64
from html import unescape
import os
import re
import tempfile
import unittest

import helpers  # noqa: F401
from gif_reader import Gif
from tinkerprint.achievements import RULES
from tinkerprint.art import keepsake
from tinkerprint.gallery import write_gallery
from tinkerprint.render_html import CSP
from tinkerprint.sets import GENERALIST, PAIR, SETS, SPECIALIST


class Gallery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        paths = write_gallery(cls.tmp.name, png=True)
        with open(paths[0], encoding="utf-8") as f:
            cls.page = f.read()
        cls.pngs = sorted(os.listdir(paths[1]))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def names(self):
        return [unescape(n) for n in re.findall(r'<div class="nm">([^<]+)</div>', self.page)]

    def test_every_class_and_both_orders_of_every_pair(self):
        names = self.names()
        for set_name in SETS:
            for name in list(SPECIALIST[set_name].values()) + [GENERALIST[set_name]]:
                self.assertIn(name, names)
            for (a, b), name in PAIR[set_name].items():
                self.assertGreaterEqual(names.count(name), 2, name)
                self.assertIn(f'<div class="why">wears {a}, holds {b}</div>', self.page)
                self.assertIn(f'<div class="why">wears {b}, holds {a}</div>', self.page)
        self.assertIn("Unclassed", names)

    def test_presentations_faces_rooms_and_small_pieces(self):
        names = self.names()
        for word in ("Neutral", "Man", "Woman"):
            self.assertIn(word, names)
        for options in (keepsake.EXPRESSIONS, keepsake.EYES, keepsake.SKINS,
                        [c for cuts in keepsake.HAIRSTYLES.values() for c in cuts]):
            for x in options:
                self.assertIn(x.capitalize(), names)
        for title, _ in RULES.values():
            self.assertIn(title, names)
        for _, (harness, instrument) in keepsake.MEMBERS.items():
            self.assertIn(f'<div class="why">{instrument}</div>', self.page)
        for h in ("<h2>Rooms</h2>", "<h2>Pins</h2>", "<h2>Trinkets</h2>", "<h2>Party instruments</h2>",
                  "<h2>Camp and chronicle</h2>"):
            self.assertIn(h, self.page)
        self.assertNotRegex(self.page, r"(?i)familiar")

    def test_rooms_and_camps_idle_with_a_still_for_reduced_motion(self):
        loops = re.findall(r'<source media="\(prefers-reduced-motion: reduce\)" srcset="data:image/png;base64,'
                           r'[A-Za-z0-9+/=]+"><img src="data:image/gif;base64,([A-Za-z0-9+/=]+)"', self.page)
        # Two rooms of two layers each, and a camp per set.
        self.assertEqual(len(loops), 2 * 2 + len(SETS))
        for data in loops:
            g = Gif(base64.b64decode(data))
            self.assertEqual([im.delay for im in g.images], list(keepsake.DELAYS_MS))
        self.assertIn("img-src data:", CSP)

    def test_png_folder_holds_each_picture(self):
        self.assertIn("room-builder.png", self.pngs)
        self.assertIn("camp-tinkerer.png", self.pngs)
        self.assertIn("instrument-default.png", self.pngs)
        self.assertIn("pin-milestone.png", self.pngs)
        self.assertEqual(sum(n.startswith("trinket-") for n in self.pngs), len({s for v in SETS.values() for s in v}))


if __name__ == "__main__":
    unittest.main()
