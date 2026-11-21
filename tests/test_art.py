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
                self.assertLessEqual(set(c.colors()), set(PACK["ink"].values()), name)
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
        """All the paint, including the selective outline, fits inside the border."""
        ok = {None}
        for set_name in SETS:
            cases = [(name, look) for name, look, _ in class_looks(set_name)]
            cases += [(f"{a} holding {b}", Look(set_name, "pair", a, b))
                      for a in SETS[set_name] for b in SETS[set_name] if a != b]
            for name, look in cases:
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

    def test_indexed_inline_art_preserves_transparency_and_custom_pack_colors(self):
        c = Canvas(3, 1)
        c.set(0, 0, "#bb6622")
        c.set(2, 0, "#000000")
        data = c.png(2, indexed=True)
        self.assertEqual(data[25], 3)  # IHDR color type
        self.assertIn(b"PLTE" + bytes.fromhex("000000 000000 bb6622"), data)
        self.assertIn(b"tRNS\x00", data)
        self.assertEqual(png_pixels(data)[2], bytes([0, 2, 2, 0, 0, 1, 1]) * 2)
        # A custom composition can exhaust the palette. RGBA still carries every pixel.
        wide = Canvas(256, 1)
        wide.px[0] = [f"#{i:06x}" for i in range(256)]
        self.assertEqual(wide.png(indexed=True), wide.png())

    def test_svg_paths_cover_exactly_the_drawn_pixels(self):
        look = look_for("builder", "pair", ["Logic", "Tests"], ["Logic", "Tests"])
        for scene in (True, False):
            c = art.portrait(PACK, look, scene=scene)
            cover = {}
            for path in c.svg_paths():
                match = re.fullmatch(r'<path fill="(#[0-9a-f]{6})" d="([^"]+)"/>', path)
                self.assertIsNotNone(match)
                color, data = match.groups()
                # Rasterize each orthogonal polygon independently from its vertical crossings.
                for polygon in data.removesuffix("z").split("z"):
                    shape = re.fullmatch(r"M(\d+) (\d+)((?:[hv]-?\d+)+)", polygon)
                    self.assertIsNotNone(shape)
                    x, y = int(shape[1]), int(shape[2])
                    x0, y0 = x, y
                    edges = {}
                    for axis, amount in re.findall(r"([hv])(-?\d+)", shape[3]) + [("z", "0")]:
                        if axis == "h":
                            x += int(amount)
                            continue
                        end = y0 if axis == "z" else y + int(amount)
                        for yy in range(min(y, end), max(y, end)):
                            edges.setdefault(yy, []).append(x)
                        y = end
                    self.assertEqual((x, y), (x0, y0))
                    for yy, xs in edges.items():
                        xs.sort()
                        self.assertEqual(len(xs) % 2, 0)
                        for left, right in zip(xs[::2], xs[1::2]):
                            for xx in range(left, right):
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

    def test_one_replaceable_face_ramp_reaches_every_costume(self):
        from tinkerprint.art._colors import SKIN_KEYS
        pack = copy.deepcopy(PACK)
        custom = ["#ebbc8a", "#ae7555", "#78514d", "#473747"]
        pack["skin_colors"] = custom
        check_pack(pack)
        for set_name in SETS:
            looks = [look for _, look, _ in class_looks(set_name)]
            looks.append(look_for(set_name, None, [], []))
            for look in looks:
                ink = art.compose.palette(pack, look)
                self.assertEqual([ink[k] for k in SKIN_KEYS], custom)
                self.assertIn(custom[0], art.portrait(pack, look).colors(), look)

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
            lambda p: p.update(skin_colors=["#cccccc"]),
            lambda p: p.update(skin_colors=["#ffffff", "blue", "#888888", "#555555"]),
            lambda p: p["parts"]["base"].update(palette={"@": "#000000"}),
            lambda p: p["looks"]["Lore"].__setitem__("gear", "missing"),
            lambda p: p["edges"].__setitem__("#112233", ["red", "#ffffff"]),
            lambda p: p["parts"]["scope"].__setitem__("offset", "left"),
            lambda p: p["parts"]["crook"].__setitem__("sleeve", "missing"),
            lambda p: p["sets"]["builder"].__setitem__("studio", "missing"),
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


    def test_custom_part_names_and_pack_metadata_stay_out_of_the_gallery(self):
        p = copy.deepcopy(PACK)
        marker = "private-part-label"
        p["name"] = marker
        p["parts"][marker] = p["parts"].pop(p["familiars"]["claude"])
        p["familiars"]["claude"] = marker
        p["looks"][marker] = p["looks"]["Tools"]
        check_pack(p)
        with tempfile.TemporaryDirectory() as folder:
            path = write_gallery(folder, p)[0]
            with open(path, encoding="utf-8") as f:
                self.assertNotIn(marker, f.read())


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

    def test_long_names_stay_clear_of_the_radar(self):
        """The name's box ends at least 16 px before the radar's top-left label starts, at any length."""
        from tinkerprint import radar
        from tinkerprint.render_card import text_em
        base = self.out["wren"]["sheet"]["card"]
        n = len(base["stats"])
        lx, _ = radar.point(850, 300, 190, n - 1, n, radar.LABEL_AT)
        label_start = lx - 0.62 * 19 * max(len(s["stat"]) for s in base["stats"])
        for name in ("Wren Aldous", "Wilhelmina Montgomery-Wolfe", "W" * 28, "Mm" * 11):
            card = dict(base, name=name)
            svg = render_card(card)
            m = re.search(r'<text x="([\d.]+)" y="156.0" font-size="(\d+)" font-weight="700"[^>]*>([^<]+)</text>', svg)
            self.assertIsNotNone(m, name)
            x, size, text = float(m.group(1)), int(m.group(2)), m.group(3)
            self.assertEqual(text, name[:22] if len(name) <= 22 else name[:21].rstrip() + "…")
            end = x + size * text_em(text)
            self.assertLessEqual(end + 16, label_start, (name, size, end, label_start))

    def test_portrait_png_is_written_and_valid(self):
        for res in self.out.values():
            with open(res["paths"]["portrait"], "rb") as f:
                data = f.read()
            w, h, raw = png_pixels(data)
            self.assertEqual((w, h), (384, 384))
            self.assertLess(len(data), 4_800)

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

    def test_hero_layers_the_figure_exactly_where_the_banner_draws_it(self):
        """The hero draws the studio without its figure and layers the figure on top. Same pixels."""
        for res in self.out.values():
            sheet = res["sheet"]
            look, _ = art.sheet_looks(sheet)
            ranked = [("Logic", 40), ("Data", 30)]
            whole = art.banner(PACK, look, ranked, ["claude", "codex"], "s")
            stage = art.banner(PACK, look, ranked, ["claude", "codex"], "s", with_figure=False)
            self.assertNotEqual(stage.px, whole.px)
            fig = art.figure(PACK, look)
            stage.paste(fig, *art.banner_figure_box(PACK, fig))
            self.assertEqual(stage.px, whole.px)

    def test_sheet_reads_in_order_hero_first(self):
        for slug, res in self.out.items():
            with open(res["paths"]["html"], encoding="utf-8") as f:
                page = f.read()
            hero = page.index('<section class="hero">')
            # The scene, the figure layer and the nameplate sit together in the hero.
            for part in ('class="banner"', 'class="portrait', 'class="seal"', "<h1>"):
                self.assertLess(hero, page.index(part), (slug, part))
                self.assertLess(page.index(part), page.index("<h2>The build</h2>"), (slug, part))
            heads = ["The build", "Party", "Achievements", "Chronicle", "What changed", "Projects", "Method"]
            at = [page.find(f"<h2>{h}</h2>") for h in heads if f"<h2>{h}</h2>" in page]
            self.assertGreaterEqual(len(at), 6, slug)
            self.assertEqual(at, sorted(at), slug)
            # The phone crop stays inside the scene.
            m = re.search(r'--zoom:([\d.]+)%;--crop:(-?[\d.]+)%', page)
            zoom, crop = float(m.group(1)), float(m.group(2))
            self.assertGreaterEqual(zoom, 100)
            self.assertLessEqual(crop, 0)
            self.assertGreaterEqual(crop + zoom, 100 - 1e-6, slug)

    def test_each_lit_stat_gets_a_card_and_empty_stats_share_one_line(self):
        for slug, res in self.out.items():
            with open(res["paths"]["html"], encoding="utf-8") as f:
                page = f.read()
            stats = res["sheet"]["stats"]
            lit = [s for s in stats if s["points"] > 0]
            self.assertEqual(page.count('class="card stat"'), len(lit), slug)
            dark = [s["key"] for s in stats if s["points"] <= 0]
            if dark:
                line = page[page.index('class="unlit"'):]
                line = line[:line.index("</div>")]
                for key in dark:
                    self.assertIn(f"<b>{key}</b>", line, slug)
            # Strongest first, each tinted with its stat's colors.
            order = [m for m in re.findall(r'class="card stat".*?<h3>([^<]+)</h3>', page)]
            self.assertEqual(order, [s["key"] for s in sorted(lit, key=lambda s: -s["share"])], slug)
            for s in lit:
                self.assertIn(f"--hue-1:{art.stat_ramp(PACK, s['key'])[1]}", page)

    def test_card_familiars_follow_the_allowlisted_party(self):
        card = copy.deepcopy(self.out["wren"]["sheet"]["card"])
        three = render_card(card)
        card["party"] = card["party"][:1]
        one = render_card(card)
        self.assertNotEqual(one, three)
        card["party"] = []
        none = render_card(card)
        self.assertNotIn("PARTY", none)
        # An unknown member gets the fallback familiar, and the party line stays the only party text.
        card["party"] = ["Someone"]
        odd = render_card(card)
        texts = re.findall(r">([^<>]+)</text>", odd)
        self.assertEqual([t for t in texts if "PARTY" in t], ["PARTY  Someone"])
        self.assertEqual(len(texts), len(re.findall(r">([^<>]+)</text>", none)) + 1)
        art_of = lambda svg: re.search(r'<g shape-rendering="crispEdges">(.*?)</g>', svg).group(1)
        self.assertNotEqual(art_of(odd), art_of(none))
        self.assertNotEqual(art_of(one), art_of(three))

    def test_page_sizes_stay_small(self):
        """Budgets: sheet.html under 104 KB, card.svg under 30 KB, the gallery under 240 KB."""
        for res in self.out.values():
            self.assertLess(os.path.getsize(res["paths"]["html"]), 104_000)
            self.assertLess(os.path.getsize(res["paths"]["card"]), 30_000)
        with tempfile.TemporaryDirectory() as tmp:
            path = write_gallery(tmp)[0]
            self.assertLess(os.path.getsize(path), 240_000)


if __name__ == "__main__":
    unittest.main()
