"""Trait assignment, and native face, hat and hand geometry for every cut and expression."""
from itertools import product
import unittest

from keepsake_helpers import MODES, SKIN, SKINS, cast, connected, equipped_looks, kit_parts, native_pen, pixels
from tinkerprint import art
from tinkerprint.art import keepsake
from tinkerprint.art._anime import half_head, keepsake_half as half
from tinkerprint.art._anime.traits import EXPRESSIONS, HAIRSTYLES, _pick
from tinkerprint.art._colors import INK


class AssignmentTest(unittest.TestCase):
    def test_seed_and_presentation_are_the_only_uniform_inputs(self):
        looks = cast()
        for seed, expr, eyes in (("user-01", "determined", "honey"), ("wool|🧶", "grin", "chestnut"),
                                 ("", "grin", "lagoon")):
            for look in looks.values():
                self.assertEqual(keepsake.traits(seed, look, "woman"), {"expression": expr, "hair": "waves", "eyes": eyes})
                for mode in MODES:
                    picked = keepsake.traits(seed, look, mode)
                    self.assertEqual(picked["expression"], expr)
                    self.assertEqual(picked["eyes"], eyes)
                    self.assertIn(picked["hair"], HAIRSTYLES[mode])
                    self.assertEqual(picked, keepsake.traits(seed, look, mode))
        with self.assertRaises(TypeError):
            keepsake.traits(123, looks["Sage"])

    def test_growing_either_pool_only_moves_winners_to_the_added_option(self):
        axes = [("expression", EXPRESSIONS), *(("hair", pool) for pool in HAIRSTYLES.values())]
        for axis, pool in axes:
            moved = 0
            for i in range(2048):
                seed = str(i)
                old = _pick(seed, axis, pool)
                self.assertEqual(_pick(seed, axis, tuple(reversed(pool))), old)
                new = _pick(seed, axis, ("new", *pool))
                if new != old:
                    self.assertEqual(new, "new")
                    moved += 1
            self.assertAlmostEqual(moved/2048, 1/(len(pool)+1), delta=.035)


class TraitDrawingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = art.default_pack()
        cls.cast = cast()

    def test_overrides_are_independent(self):
        look = self.cast["Traveler"]
        for mode, pool in HAIRSTYLES.items():
            def draw(**kw):
                return keepsake.figure(self.pack, look, presentation=mode, **kw).px
            self.assertEqual(draw(), draw(expression="smile", hair=pool[0]))
            self.assertEqual(draw(hair=pool[-1]), draw(expression="smile", hair=pool[-1]))
            self.assertEqual(draw(expression="joy"), draw(expression="joy", hair=pool[0]))
            for kw in ({"expression": ""}, {"hair": "missing"}, {"hair": ""}):
                with self.assertRaises(art.PackError):
                    draw(**kw)
        with self.assertRaises(art.PackError):
            keepsake.figure(self.pack, look, presentation="man", hair="braid")

    def test_all_hats_expressions_and_cuts_keep_a_clear_jaw_and_tucked_crown(self):
        widths = {"man": (9,9,8,7,5,3), "neutral": (8,8,7,6,4,2), "woman": (8,7,6,5,3,1)}
        for name, look in self.cast.items():
            hat, travel, _ = kit_parts(self.pack, look)
            kind = travel or half_head.CROWNS[hat]
            crown = native_pen(self.pack, look)
            half_head.fitted_hat(crown, kind, hat)
            for mode, pool in HAIRSTYLES.items():
                for i, (hair, expr) in enumerate(product(pool, EXPRESSIONS)):
                    p = native_pen(self.pack, look)
                    # Check the skin all the way through the last pixel at each cheek. The skins take
                    # turns, so each ramp meets every cut and expression across the cast.
                    skins = (self.pack["skin_colors"], *SKINS[1:])
                    for skin in (skins[(i + len(name)) % len(skins)],):
                        p.colors["skin"] = skin
                        fig = keepsake.figure(self.pack, look, presentation=mode,
                                              skin=skin, hair=hair, expression=expr)
                        for y, radius in enumerate(widths[mode], 22):
                            jaw = fig.px[y][31-radius:32+radius]
                            permitted = set(skin)
                            if expr == "grin" and y in (23,24):
                                permitted.update(p.colors["white"][:2])
                            self.assertLessEqual(set(jaw), permitted, (name,mode,hair,expr,y))
                            if y >= 24:
                                margin = fig.px[y][29-radius:34+radius]
                                self.assertTrue(set(p.colors["hair"]).isdisjoint(margin), (name,hair,y))
                    inks = set(p.colors["hair"])
                    xx, yy = p.origin
                    if kind not in ("bare", "goggles"):
                        for x in range(xx-19, xx+16):
                            y0 = next((y for y in range(yy+1) if crown.image.get(x, y)), yy-2)
                            self.assertTrue(all(fig.get(x,y) not in inks for y in range(y0)), (hat,hair,x))
                    for x in (xx-7, xx+3):
                        eye = {v for row in fig.px[yy-1:yy+4] for v in row[x:x+7]}
                        self.assertEqual(p.colors["eye"][1] in eye, expr != "joy", (hat,mode,hair,expr))
                    self.assertTrue(connected(fig), (name,mode,hair,expr))

    def test_each_cut_and_expression_has_a_distinct_native_face_under_every_hat(self):
        for name, look in self.cast.items():
            hat, travel, _ = kit_parts(self.pack, look)
            for mode, pool in HAIRSTYLES.items():
                drawings = set()
                for expr, hair in product(EXPRESSIONS, pool):
                    p = native_pen(self.pack, look)
                    p.colors["skin"] = self.pack["skin_colors"]
                    half_head.head(p, mode, hat, travel, expr, hair)
                    drawings.add(p.image.png(indexed=True))
                self.assertEqual(len(drawings), len(EXPRESSIONS)*len(pool), (name,mode))

    def test_new_silhouettes_keep_clear_of_every_equipped_tool(self):
        # The silhouette is independent of the expression. Union every cut once
        # per hat, then check every layer from every pair in either stat order.
        silhouettes = {}
        for look in equipped_looks():
            hat, travel, item = kit_parts(self.pack, look)
            if (hat, travel) not in silhouettes:
                outline = set()
                for mode, pool in HAIRSTYLES.items():
                    for hair in pool:
                        p = native_pen(self.pack, look)
                        half_head.head(p, mode, hat, travel, hair=hair)
                        outline.update(pixels(p.image))
                silhouettes[hat, travel] = outline
            p = native_pen(self.pack, look, padding=8)
            left, right = half.joints(item)
            half.equipment(p, item, left, right, travel)
            if item == "washbrush":
                half.paint_palette(p, left)
            for x, y in pixels(p.image):
                self.assertTrue(9 <= x <= 70 and 9 <= y <= 70)
                self.assertFalse(any((x-8+dx, y-8+dy) in silhouettes[hat, travel]
                                     for dx,dy in product(range(-2,3), repeat=2)), (look,x,y))

    def test_painter_pins_the_palette_and_uses_the_same_blue_on_the_brush(self):
        look = self.cast["Painter"]
        fig = keepsake.figure(self.pack, look, skin=SKIN)
        panel = native_pen(self.pack, look)
        left, right = half.joints("washbrush")
        half.paint_palette(panel, left)
        palette = pixels(panel.image)
        hidden = {pt for pt,c in palette.items() if fig.get(*pt) != c}
        self.assertGreaterEqual(len(hidden), 6)
        self.assertEqual({fig.get(*pt) for pt in hidden}, {SKIN[0]})
        thumb = panel.xy(left[0]-3, left[1]-2)
        self.assertIsNone(panel.image.get(*thumb))
        self.assertEqual(fig.get(*thumb), SKIN[0])
        brush = native_pen(self.pack, look)
        half.equipment(brush, "washbrush", left, right, None)
        for painted in (palette, pixels(brush.image)):
            self.assertGreaterEqual(sum(c == INK["2"] for c in painted.values()), 3)
        pack = dict(self.pack, looks=dict(self.pack["looks"]))
        pack["looks"]["Art"] = dict(pack["looks"]["Art"], trinket="other")
        no_palette = keepsake.figure(pack, look)
        self.assertNotIn(INK["2"], [no_palette.get(*pt) for pt in palette])

    def test_goggle_strap_ends_follow_both_temples_in_every_cut(self):
        look = self.cast["Artificer"]
        g = native_pen(self.pack, look)
        half_head.goggles(g)
        ends = {(x,y) for x,y in pixels(g.image) if (x < 23 or x > 38) and y >= 11}
        self.assertTrue(any(x < 23 for x,y in ends) and any(x > 38 for x,y in ends))
        for mode, pool in HAIRSTYLES.items():
            for hair in pool:
                bare = native_pen(self.pack, look)
                half_head.head(bare, mode, "base", None, hair=hair)
                self.assertTrue(ends <= pixels(bare.image).keys(), (mode,hair))
        hood = native_pen(self.pack, self.cast["Sage"])
        half_head.hood(hood)
        top = min(y for x,y in pixels(hood.image))
        crown = [x for x,y in pixels(hood.image) if y == top]
        self.assertAlmostEqual(sum(crown)/len(crown), hood.origin[0], delta=1)

    def test_nib_hammer_and_relaxed_fingertips_survive_the_native_grid(self):
        look = self.cast["Scribe"]
        p = native_pen(self.pack, look)
        left, right = half.joints("nib")
        fig = keepsake.figure(self.pack, look, skin=SKIN)
        q = p.local(*right)
        self.assertEqual(fig.get(*q.xy(-5,11)), p.colors["dark"][3])
        nib = {fig.get(*q.xy(x,y)) for x in range(-6,1) for y in range(5,10)}
        self.assertTrue(set(p.colors["steel"]) <= nib)
        for tool in half.LONG_TOOLS - {"washbrush"}:
            left, _ = half.joints(tool)
            p = native_pen(self.pack, look)
            half.hand(p, left, -1, "hip")
            x,y = p.xy(*left)
            # Two fingertips below the palm, with a pixel of cloth visible between.
            self.assertEqual([p.image.get(dx,y+6) for dx in range(x+2,x+5)],
                             [SKIN[0], None, SKIN[0]])
        hammer = keepsake.figure(self.pack, self.cast["Artificer"])
        # The lighter striking face, narrower waist and claw stand above the leather loop.
        self.assertEqual(hammer.get(*p.xy(1,28)), p.colors["steel"][0])
        self.assertEqual(hammer.get(*p.xy(8,30)), p.colors["steel"][3])
        self.assertEqual(hammer.get(*p.xy(5,34)), p.colors["gold"][1])
