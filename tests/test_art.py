"""Generated art: every class draws, pictures are byte-identical, the card's art reads only its
allowlist, packs are checked, the chronicle follows the class rules, and pages stay small."""
import copy
import json
import os
import re
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from datetime import date

import helpers
from helpers import commit, profile, run
from tinkerprint import art
from tinkerprint.art.compose import Look, look_for
from tinkerprint.art.pack import PackError, check_pack, load_pack
from tinkerprint.art.pixels import Canvas, read_png_size
from tinkerprint.audit import svg_strings
from tinkerprint.build import build
from tinkerprint.chronicle import chronicle
from tinkerprint.classes import pick_class
from tinkerprint.demo import TOBI, WREN, make_person
from tinkerprint.gallery import class_looks, write_gallery
from tinkerprint.profile import load_profile
from tinkerprint.render_card import render_card
from tinkerprint.render_html import render_html
from tinkerprint.sets import PAIR, SETS, SPECIALIST

PACK = art.default_pack()


def png_pixels(data: bytes) -> tuple:
    """(width, height, raw scanlines) after checking every chunk."""
    w, h = read_png_size(data)
    pos, idat = 8, b""
    while pos < len(data):
        n, = struct.unpack(">I", data[pos:pos + 4])
        if data[pos + 4:pos + 8] == b"IDAT":
            idat += data[pos + 8:pos + 8 + n]
        pos += 12 + n
    return w, h, zlib.decompress(idat)


class EveryClass(unittest.TestCase):
    def test_every_class_of_both_sets_draws_a_distinct_portrait(self):
        for set_name in SETS:
            looks = class_looks(set_name)
            self.assertEqual(len(looks), 37)
            seen = {}
            for name, look, _ in looks:
                c = art.portrait(PACK, look)
                fig = art.compose.figure(PACK, look)
                drawn = sum(1 for row in fig.px for p in row if p)
                self.assertGreater(drawn, 250, name)
                self.assertGreaterEqual(len(fig.colors()), 7, name)
                svg = c.svg(3)
                self.assertNotIn(svg, seen, (set_name, name, seen.get(svg)))
                seen[svg] = name

    def test_both_orders_of_every_pair_and_every_runner_up_draw(self):
        for set_name, stats in SETS.items():
            for a, b in PAIR[set_name]:
                for top, item in ((a, b), (b, a)):
                    look = look_for(set_name, "pair", [a, b], [top, item])
                    self.assertEqual((look.top, look.item), (top, item))
                    art.portrait(PACK, look)
            for s in SPECIALIST[set_name]:
                for other in stats:
                    look = look_for(set_name, "specialist", [s], [s, other] if other != s else [s])
                    self.assertEqual(look.item, other)
                    art.portrait(PACK, look)

    def test_figures_stay_inside_the_canvas(self):
        """Only outline reaches the canvas edge, so no outline is ever cut."""
        ok = {None, PACK["outline"]}
        for set_name in SETS:
            for name, look, _ in class_looks(set_name):
                for multi in ((), tuple(SETS[set_name][:2])):
                    fig = art.compose.figure(PACK, Look(look.set_name, look.kind, look.top, look.item, multi))
                    edge = [fig.px[y][0] for y in range(fig.h)] + [fig.px[y][fig.w - 1] for y in range(fig.h)]
                    edge += fig.px[0] + fig.px[fig.h - 1]
                    self.assertLessEqual(set(edge), ok, name)

    def test_familiars_icons_and_trinkets_exist_for_every_key(self):
        from tinkerprint.achievements import RULES
        for h in ("claude", "codex", "agy", "something-new"):
            self.assertGreater(len(art.familiar(PACK, h).colors()), 3)
        svgs = {art.icon(PACK, k).svg() for k in list(RULES) + ["milestone"]}
        self.assertEqual(len(svgs), len(RULES) + 1)
        for stat in {s for v in SETS.values() for s in v}:
            self.assertGreater(len(art.trinket(PACK, stat).colors()), 2)


class Deterministic(unittest.TestCase):
    def test_same_input_same_bytes(self):
        look = look_for("tinkerer", "pair", ["Art", "Worlds"], ["Art", "Worlds", "Lore", "Community"],
                        ["Lore", "Community"])
        ranked = [("Art", 30), ("Worlds", 25), ("Lore", 15), ("Community", 10)]
        a = art.banner(PACK, look, ranked, ["claude", "codex"], "seed")
        b = art.banner(art.default_pack(), look, ranked, ["claude", "codex"], "seed")
        self.assertEqual(a.svg(), b.svg())
        self.assertEqual(a.png(4), b.png(4))
        self.assertNotEqual(a.svg(), art.banner(PACK, look, ranked, ["claude", "codex"], "other").svg())

    def test_gallery_is_byte_identical_across_processes_and_hash_seeds(self):
        code = ("import hashlib, os, sys\n"
                "from tinkerprint.gallery import write_gallery\n"
                "out = sys.argv[1]\n"
                "write_gallery(out, png=True)\n"
                "h = hashlib.sha256()\n"
                "for root, _, files in sorted(os.walk(out)):\n"
                "    for f in sorted(files):\n"
                "        h.update(f.encode()); h.update(open(os.path.join(root, f), 'rb').read())\n"
                "print(h.hexdigest())\n")
        digests = []
        with tempfile.TemporaryDirectory() as tmp:
            for seed in ("1", "2"):
                env = dict(os.environ, PYTHONPATH=helpers.SRC, PYTHONHASHSEED=seed)
                out = subprocess.run([sys.executable, "-c", code, os.path.join(tmp, seed)], env=env,
                                     capture_output=True, text=True, check=True)
                digests.append(out.stdout.strip())
        self.assertEqual(digests[0], digests[1])

    def test_png_writer_makes_valid_files(self):
        c = Canvas(3, 2)
        c.set(0, 0, "#ff0000")
        c.set(2, 1, "#00ff00")
        w, h, raw = png_pixels(c.png(2))
        self.assertEqual((w, h), (6, 4))
        self.assertEqual(len(raw), h * (1 + w * 4))
        self.assertEqual(raw[1:5], b"\xff\x00\x00\xff")
        self.assertEqual(raw[5:9], b"\xff\x00\x00\xff")
        self.assertEqual(raw[9:13], b"\x00\x00\x00\x00")

    def test_svg_paths_cover_exactly_the_drawn_pixels(self):
        c = art.portrait(PACK, look_for("builder", "pair", ["Logic", "Tests"], ["Logic", "Tests"]))
        cover = {}
        for path in c.svg_paths():
            color = re.search(r'fill="([^"]+)"', path).group(1)
            for x, y, w, h in re.findall(r"M(\d+) (\d+)h(\d+)v(\d+)h-\d+z", path):
                for yy in range(int(y), int(y) + int(h)):
                    for xx in range(int(x), int(x) + int(w)):
                        self.assertNotIn((xx, yy), cover)
                        cover[(xx, yy)] = color
        want = {(x, y): p for y, row in enumerate(c.px) for x, p in enumerate(row) if p}
        self.assertEqual(cover, want)


class Packs(unittest.TestCase):
    def test_export_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "pack.json")
            art.export_pack(path)
            self.assertEqual(load_pack(path), art.default_pack())

    def test_bad_packs_are_refused(self):
        def broken(fn):
            p = copy.deepcopy(PACK)
            fn(p)
            return p
        cases = [
            lambda p: p["ink"].__setitem__("k", '"/><text>hi</text>'),
            lambda p: p["stat_colors"].__setitem__("Logic", ["#000000"]),
            lambda p: p["parts"]["base"]["rows"].__setitem__(0, "?" * 14),
            lambda p: p["parts"]["base"]["rows"].__setitem__(0, "..."),
            lambda p: p["looks"]["Tools"].__setitem__("item", "missing"),
            lambda p: p["icons"].pop("founder"),
            lambda p: p["parts"].__setitem__("Bad Name", {"at": [0, 0], "rows": ["."]}),
            lambda p: p["ink"].__setitem__("A", "#000000"),
        ]
        for fn in cases:
            with self.assertRaises(PackError):
                check_pack(broken(fn))

    def test_a_pack_changes_pixels_only(self):
        p = copy.deepcopy(PACK)
        p["stat_colors"]["Logic"] = ["#ffffff", "#cccccc", "#999999"]
        check_pack(p)
        look = look_for("builder", "specialist", ["Logic"], ["Logic"])
        self.assertNotEqual(art.portrait(p, look).svg(), art.portrait(PACK, look).svg())


class Chronicle(unittest.TestCase):
    def test_one_chapter_per_quarter_with_rests_collapsed(self):
        dp = {
            date(2025, 1, 5): {"P": {"Logic": 1.0}},
            date(2025, 2, 5): {"P": {"Tests": 0.5, "Logic": 0.5}},
            date(2025, 11, 2): {"P": {"Docs": 1.0}},
            date(2026, 1, 3): {"P": {"": 1.0}},
        }
        ch = chronicle(dp, "builder")
        self.assertEqual([c["label"] for c in ch], ["2025 Q1", "2025 Q2", "2025 Q4", "2026 Q1"])
        self.assertTrue(ch[1]["rest"])
        self.assertEqual((ch[1]["quarters"], ch[1]["label_to"]), (2, "2025 Q3"))
        self.assertEqual(ch[0]["active_days"], 2)
        self.assertEqual(ch[0]["class"]["name"], pick_class({"Logic": 0.75, "Tests": 0.25}, "builder")["name"])
        self.assertEqual(ch[2]["class"]["name"], "Scribe")
        self.assertIsNone(ch[3]["class"])  # only unclassified points
        self.assertEqual(ch[0]["from"], "2025-01-01")
        self.assertEqual(ch[0]["to"], "2025-03-31")

    def test_sheet_chronicle_respects_as_of(self):
        prof = profile([("P", "/r/p", None)])
        events = [commit("2025-01-10T12:00:00+00:00", "/r/p/a.py", "c1"),
                  commit("2025-07-10T12:00:00+00:00", "/r/p/b.py", "c2")]
        sheet, _ = run(prof, events, as_of=date(2025, 3, 1))
        self.assertEqual([c["label"] for c in sheet["chronicle"]], ["2025 Q1"])
        sheet, _ = run(prof, events)
        self.assertEqual([c.get("rest", False) for c in sheet["chronicle"]], [False, True, False])


class Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        world = os.path.join(cls.tmp.name, "world")
        cls.out = {}
        for p in (WREN, TOBI):
            prof = load_profile(make_person(world, p))
            cls.out[p.slug] = build(prof, os.path.join(cls.tmp.name, "out", p.slug),
                                    home=os.path.join(cls.tmp.name, "data", p.slug), built_at="t")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_card_portrait_matches_the_sheet_and_reads_only_the_allowlist(self):
        allowed = {"enabled", "name", "set", "class", "multiclass", "level", "stats", "achievements", "party", "chart"}
        for slug, res in self.out.items():
            sheet = res["sheet"]
            card = sheet["card"]
            self.assertLessEqual(set(card), allowed | {"projects"})
            self.assertEqual(art.card_look(card), art.sheet_looks(sheet)[0], slug)
            # The art never changes when anything outside the allowlist changes.
            other = json.loads(json.dumps(sheet))
            other["projects"] = []
            other["profile"]["name"] = "Someone Else"
            other["party"] = []
            self.assertEqual(art.card_look(other["card"]), art.card_look(card))
            # Paths carry only fill and d. audit lists no path data.
            with open(res["paths"]["card"], encoding="utf-8") as f:
                svg = f.read()
            for s in svg_strings(svg):
                self.assertFalse(re.match(r"^M\d", s), s)
            self.assertIn('shape-rendering="crispEdges"', svg)

    def test_card_art_changes_with_allowlisted_fields(self):
        card = copy.deepcopy(self.out["tobi"]["sheet"]["card"])
        before = render_card(card)
        card["class"] = "Warden"
        self.assertNotEqual(render_card(card), before)

    def test_portrait_png_is_written_and_valid(self):
        for res in self.out.values():
            with open(res["paths"]["portrait"], "rb") as f:
                data = f.read()
            w, h, raw = png_pixels(data)
            self.assertEqual((w, h), (256, 256))
            self.assertLess(len(data), 4000)

    def test_sheet_draws_every_picture(self):
        for slug, res in self.out.items():
            with open(res["paths"]["html"], encoding="utf-8") as f:
                page = f.read()
            self.assertIn('class="banner"', page)
            self.assertIn('class="portrait', page)
            self.assertIn("<h2>Chronicle</h2>", page)
            self.assertEqual(page.count('class="fam"'), len(res["sheet"]["party"]))
            self.assertEqual(page.count('class="ic"'), len(res["sheet"]["achievements"]) + len(res["sheet"]["milestones"]))
            self.assertNotRegex(page, r"(?i)(src|href)=\"https?:")

    def test_close_call_shows_both_costumes(self):
        sheet = json.loads(json.dumps(self.out["tobi"]["sheet"]))
        cls = sheet["class"]
        other = [s for s in SETS["builder"] if s not in cls["stats"]][0]
        cls["close"] = {"kind": "pair", "stats": sorted([cls["stats"][0], other], key=SETS["builder"].index),
                        "name": PAIR["builder"][tuple(sorted([cls["stats"][0], other], key=SETS["builder"].index))]}
        page = render_html(sheet)
        self.assertIn('class="portrait flip"', page)
        self.assertIn('class="px alt"', page)
        self.assertIn(f"the {cls['close']['name']} costume", page)

    def test_page_sizes_stay_small(self):
        """Budgets: sheet.html under 160 KB, card.svg under 24 KB, the gallery under 640 KB."""
        for res in self.out.values():
            self.assertLess(os.path.getsize(res["paths"]["html"]), 160_000)
            self.assertLess(os.path.getsize(res["paths"]["card"]), 24_000)
        with tempfile.TemporaryDirectory() as tmp:
            path = write_gallery(tmp)[0]
            self.assertLess(os.path.getsize(path), 640_000)


if __name__ == "__main__":
    unittest.main()
