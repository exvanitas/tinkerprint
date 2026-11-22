"""The sheet's banner: the Keepsake room idling at a whole-number scale, a still for reduced motion, the
close-call costume swap and the phone crop. Every person here is invented."""
import base64
import json
import os
import re
import tempfile
import unittest

import helpers  # noqa: F401
from gif_reader import Gif
from tinkerprint import art, look as looks
from tinkerprint.art import _keepsake_idle as idle, keepsake
from tinkerprint.art._keepsake_room import room
from tinkerprint.build import build
from tinkerprint.demo import TOBI, WREN, make_person
from tinkerprint.profile import load_profile
from tinkerprint.render_html import CSP, CSS, JS, render_html

PACK = art.default_pack()


def pictures(page: str) -> list:
    """(class, still PNG, loop GIF, alt) for every banner layer, in document order."""
    return [(m.group(1), base64.b64decode(m.group(2)), base64.b64decode(m.group(3)), m.group(4)) for m in re.finditer(
        r'<picture class="([^"]+)"><source media="\(prefers-reduced-motion: reduce\)" '
        r'srcset="data:image/png;base64,([A-Za-z0-9+/=]+)"><img src="data:image/gif;base64,([A-Za-z0-9+/=]+)" '
        r'alt="([^"]*)"></picture>', page)]


def screens(gif: bytes) -> list:
    """Every frame of a GIF as rows of colors, None where clear."""
    g = Gif(gif)
    return [[[g.palette[i] if i else None for i in screen[y * g.w:(y + 1) * g.w]] for y in range(g.h)]
            for screen in g.screens()]


def ranked_of(sheet: dict) -> list:
    pcts = art.sheet_pcts(sheet)
    return [(s, pcts[s]) for s in art.art_rank(pcts, sheet["profile"]["set"])]


def with_close(sheet: dict) -> dict:
    sheet = json.loads(json.dumps(sheet))
    sheet["class"]["close"] = {"kind": "pair", "stats": ["Logic", "Tests"], "name": "Paladin"}
    return sheet


class Banner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        world = os.path.join(cls.tmp.name, "world")
        cls.sheet = {}
        for p in (WREN, TOBI):
            prof = load_profile(make_person(world, p))
            res = build(prof, os.path.join(cls.tmp.name, "out", p.slug),
                        home=os.path.join(cls.tmp.name, "data", p.slug), built_at="t")
            cls.sheet[p.slug] = res["sheet"]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_layers_recompose_the_whole_room_on_every_beat(self):
        """The room GIF, then the costume GIF over it, is the Keepsake banner frame for frame."""
        for slug, sheet in self.sheet.items():
            page = render_html(sheet)
            layers = pictures(page)
            self.assertEqual([c for c, *_ in layers], ["room", "wear main"], slug)
            (_, room_still, room_gif, room_alt), (_, wear_still, wear_gif, wear_alt) = layers
            self.assertEqual(Gif(room_gif).w, 252)
            self.assertEqual([im.delay for im in Gif(room_gif).images], list(keepsake.DELAYS_MS))
            self.assertEqual([im.delay for im in Gif(wear_gif).images], list(keepsake.DELAYS_MS))
            seed, tokens = looks.of_sheet(sheet)
            self.assertEqual(seed, sheet["card"]["name"])
            options = looks.options(tokens)
            skin = keepsake.SKINS.get(options.pop("skin"))
            main, _ = art.sheet_looks(sheet)
            harnesses = [m["harness"] for m in sheet["party"]]
            for i, (back, front) in enumerate(zip(screens(room_gif), screens(wear_gif))):
                scene = [[f if f else b for b, f in zip(rb, rf)] for rb, rf in zip(back, front)]
                expected = room.banner(PACK, main, ranked_of(sheet), harnesses, seed, motion=idle.BEATS[i],
                                       skin=skin, **options)
                self.assertEqual(scene, expected.px, (slug, i))
            # Reduced motion gets exactly frame zero of each layer.
            drawn = keepsake.banner_layers(PACK, main, ranked_of(sheet), harnesses, seed, **looks.options(tokens))
            self.assertEqual(room_still, drawn.background.still.png(1, indexed=True))
            self.assertIn("A workshop. Its shelves hold", room_alt)
            self.assertIn("at the counter", wear_alt)

    def test_scale_is_whole_and_pixelated_and_the_policy_allows_data_images(self):
        css = re.sub(r"\s+", " ", CSS)
        scales = re.findall(r"@media \(min-width: (\d+)px\) \{ \.banner \{ --k: (\d); \} \}", css)
        self.assertEqual([int(k) for _, k in scales], [2, 3, 4, 5])
        # Each step starts where the room at the scale below no longer fills the hero: the page's padding and
        # the hero's border take 36 px up to 560 px wide, and 38 px above.
        for width, k in scales:
            gutter = 36 if int(width) <= 560 else 38
            self.assertEqual(int(width), 252 * (int(k) - 1) + gutter + 1)
        self.assertIn(".set img { position: absolute; inset: 0; width: 100%; height: 100%; display: block; "
                      "image-rendering: pixelated;", css)
        self.assertIn("img-src data:", CSP)
        self.assertEqual(CSP.count("img-src"), 1)

    def test_phone_crop_keeps_the_figure_and_the_case(self):
        for slug, sheet in self.sheet.items():
            page = render_html(sheet)
            m = re.search(r'<div class="banner" style="--lx:(\d+);--fx:(\d+)">', page)
            lx, fx = int(m.group(1)), int(m.group(2))
            x, _, w, _ = keepsake.banner_layers(PACK, art.sheet_looks(sheet)[0], (), ()).figure_box
            self.assertEqual(lx, x + 8)
            # With a party, the focus sits halfway between the figure and the case's last berth.
            self.assertEqual(fx, (lx + 246) // 2, slug)
        alone = json.loads(json.dumps(self.sheet["tobi"]))
        alone["party"] = []
        alone["card"]["party"] = []
        m = re.search(r'--lx:(\d+);--fx:(\d+)"', render_html(alone))
        self.assertEqual(int(m.group(2)), (int(m.group(1)) + 84 + 56) // 2)

    def test_close_call_swaps_figure_and_counter_together(self):
        page = render_html(with_close(self.sheet["tobi"]))
        layers = pictures(page)
        self.assertEqual([c for c, *_ in layers], ["room", "wear main", "wear alt"])
        self.assertIn('<div class="set flip">', page)
        self.assertIn("Paladin at the counter", layers[2][3])
        self.assertNotEqual(layers[1][2], layers[2][2])
        css = re.sub(r"\s+", " ", CSS)
        self.assertIn("@keyframes costume-a { 0% { opacity: 1; } 50% { opacity: 0; } }", css)
        self.assertIn("@keyframes costume-b { 0% { opacity: 0; } 50% { opacity: 1; } }", css)
        self.assertIn(".flip .wear.main { animation: costume-a 6s steps(1) infinite; }", css)
        self.assertIn(".flip .wear.alt { animation: costume-b 6s steps(1) infinite; }", css)
        self.assertIn(".flip .hit:hover ~ .wear.alt, .flip.worn .wear.alt { animation: none; opacity: 1; }", css)
        self.assertRegex(css, r"@media \(prefers-reduced-motion: reduce\) \{ \.flip \.wear\.main \{ animation: none; "
                              r"opacity: 1; \} \.flip \.wear\.alt \{ animation: none; opacity: 0; \} \}")
        # The button wears the other costume from the keyboard or a tap, since it is a real button.
        self.assertIn('id="costumeBtn" type="button"', page)
        self.assertIn('data-b="Paladin"', page)
        self.assertIn("document.querySelector('.set.flip')", JS)
        # The hover target covers the figure only, not the whole room.
        self.assertRegex(page, r'<div class="hit" style="left:[\d.]+%;top:[\d.]+%;width:25\.397%;height:88\.889%">')

    def test_no_close_call_no_swap(self):
        page = render_html(self.sheet["wren"])
        self.assertNotIn("flip", page.split("</style>")[1].split("<script>")[0])
        self.assertNotIn('class="hit"', page)

    def test_banner_is_byte_identical(self):
        sheet = with_close(self.sheet["tobi"])
        self.assertEqual(render_html(sheet), render_html(sheet))


if __name__ == "__main__":
    unittest.main()
