"""The app-facing Keepsake surface, using only invented seeds and class data."""
import unittest

from gif_reader import Gif
from tinkerprint import art
from tinkerprint.art import keepsake as k
from tinkerprint.art._drawing import Drawing
from tinkerprint.art._keepsake_idle import BEATS
from tinkerprint.art._keepsake_room import room
from tinkerprint.art.pixels import Canvas


class ShippingArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = art.default_pack()
        cls.main = art.Look("builder", "pair", "Docs", "Models", ("Infra", "Data"))
        cls.alt = art.Look("builder", "pair", "Docs", "Tools", ("Infra", "Data"))

    def test_profile_options_render_through_the_facade(self):
        self.assertEqual(tuple(k.SKINS), ("light", "medium", "deep"))
        for mode, cuts in k.HAIRSTYLES.items():
            chosen = k.traits("quiet guest", self.main, mode)
            self.assertIn(chosen["hair"], cuts)
            self.assertIn(chosen["eyes"], k.EYES)
            self.assertIn(chosen["expression"], k.EXPRESSIONS)
            for name, ramp in k.SKINS.items():
                with self.subTest(mode=mode, skin=name):
                    expected = k.figure(self.pack, self.main, presentation=mode, skin=ramp, **chosen)
                    kw = dict(presentation=mode, skin=name, **chosen)
                    self.assertEqual(k.figure(self.pack, self.main, **kw).px, expected.px)
                    frames = k.figure_frames(self.pack, self.main, **kw)
                    self.assertEqual(frames[0].px, expected.px)
                    self.assertEqual(len(frames), len(k.DELAYS_MS))
        self.assertEqual(k.figure(self.pack, self.main).px, k.figure(self.pack, self.main, skin="light").px)
        changed = dict(self.pack, skin_colors=k.SKINS["deep"])
        self.assertEqual(k.figure(changed, self.main).px, k.figure(self.pack, self.main, skin="deep").px)
        with self.assertRaisesRegex(art.PackError, "skin"):
            k.figure(self.pack, self.main, skin="unknown")

    def test_plate_is_figure_over_its_own_native_window_crop_on_every_beat(self):
        for seed, left, skin in (("salt-glass", 145, "medium"), ("copper-reed", 29, "deep")):
            plan = room.plan_room(self.pack, self.main, (), seed)
            touches = dict(plan.touches)
            # Let the seed pick the cut and iris; an explicit expression wins.
            kw = dict(presentation="woman", skin=skin, expression="curious")
            generated = k.traits(seed, self.main, "woman")
            generated.update(kw)
            figures = k.figure_frames(self.pack, self.main, **generated)
            frames = k.plate_frames(self.pack, self.main, seed, **kw)
            self.assertEqual(len(frames), len(k.DELAYS_MS))
            self.assertEqual(frames[0].px, k.plate(self.pack, self.main, seed, **kw).px)
            self.assertGreater(len({f.png() for f in frames}), 1)
            for i, (beat, fig, tile) in enumerate(zip(BEATS, figures, frames)):
                with self.subTest(seed=seed, frame=i):
                    self.assertEqual((tile.w, tile.h), (64, 64))
                    wall = Drawing(252, 72)
                    room.architecture(wall, self.pack, self.main, touches, beat.wisp)
                    room.plant(wall, touches, beat.bend)
                    expected = [row[left:left+64] for row in wall.px[:64]]
                    for y, row in enumerate(fig.px):
                        for x, ink in enumerate(row):
                            if ink is not None:
                                expected[y][x] = ink
                    self.assertEqual(tile.px, expected)
                    self.assertFalse(any(None in row for row in tile.px))

    def test_close_call_layers_recompose_both_banner_costumes_on_every_beat(self):
        seed, crew = "salt-glass", ("codex", "agy")
        stats = [("Docs", 40), ("Models", 30), ("Tools", 30)]
        kw = dict(presentation="woman", expression="grin", eyes="moss", hair="waves")
        layers = k.banner_layers(self.pack, self.main, iter(stats), iter(crew), seed,
                                 alternate=self.alt, skin="deep", **kw)
        x, y, w, h = layers.figure_box
        self.assertEqual((x, y), art.banner_figure_box(self.pack, layers.figure.still))
        self.assertEqual((w, h), (64, 64))
        looks = ((self.main, layers.figure, layers.foreground),
                 (self.alt, layers.alternate_figure, layers.alternate_foreground))
        for look, figs, fronts in looks:
            for layer in (layers.background, figs, fronts):
                self.assertIs(layer.still, layer.frames[0])
                self.assertEqual(len(layer.frames), len(k.DELAYS_MS))
            for i, beat in enumerate(BEATS):
                with self.subTest(look=look.item, frame=i):
                    scene = Canvas(252, 72)
                    scene.paste(layers.background.frames[i])
                    scene.paste(figs.frames[i], x, y)
                    scene.paste(fronts.frames[i])
                    expected = room.banner(self.pack, self.main, stats, crew, seed,
                                           figure_look=look, motion=beat, skin=k.SKINS["deep"], **kw)
                    self.assertEqual(scene.px, expected.px)
        self.assertNotEqual(layers.foreground.still.px, layers.alternate_foreground.still.px)
        plain = k.banner_layers(self.pack, self.alt, ())
        self.assertIsNone(plain.alternate_figure)
        self.assertIsNone(plain.alternate_foreground)
        self.assertEqual(plain.figure.still.px, k.figure(self.pack, self.alt).px)

    def test_camps_depend_on_set_and_seed_and_only_fire_moves(self):
        seen = set()
        for guild in ("builder", "tinkerer"):
            for seed in ("flint-gate", "sedge-mill"):
                with self.subTest(guild=guild, seed=seed):
                    tile = k.camp(self.pack, guild, seed)
                    seen.add(tile.png())
                    self.assertEqual((tile.w, tile.h), (64, 64))
                    self.assertFalse(any(None in row for row in tile.px))
                    frames = k.camp_frames(self.pack, guild, seed)
                    self.assertEqual(len(frames), len(k.DELAYS_MS))
                    self.assertEqual(frames[0].px, tile.px)
                    self.assertEqual(len({f.png() for f in frames}), 3)
                    for frame in frames:
                        changed = [(x,y) for y,row in enumerate(frame.px) for x,ink in enumerate(row)
                                   if ink != tile.get(x,y)]
                        self.assertTrue(all(34 <= x <= 55 and 39 <= y <= 50 for x,y in changed))
        self.assertEqual(len(seen), 4)

    def test_camp_gif_decodes_to_both_laps(self):
        frames = k.camp_frames(self.pack, "builder", "flint-gate")
        data = k.encode(frames, k.DELAYS_MS, scale=3)
        self.assertEqual(data, k.encode(frames, k.DELAYS_MS, scale=3))
        gif = Gif(data)
        self.assertEqual(gif.loop, 0)
        self.assertEqual((gif.w, gif.h), (192,192))
        self.assertEqual([im.delay for im in gif.images], list(k.DELAYS_MS))
        self.assertEqual(list(gif.screens(laps=2)), [gif.indices(f,3) for f in frames]*2)

    def test_party_pins_and_shelf_stat_use_the_pack_keys(self):
        pins = {k.pin(self.pack, key).png() for key in self.pack["icons"]}
        self.assertEqual(len(pins), 11)
        self.assertEqual(k.pin(self.pack, "invented award").px, k.pin(self.pack, "milestone").px)
        self.assertEqual(len({k.trinket(self.pack, stat).png() for stat in self.pack["looks"]}), 13)
        self.assertEqual(k.instrument("invented harness").px, k.instrument("default").px)
        self.assertEqual(len({k.instrument(key).png() for key in ("agy","codex","claude","default")}), 4)
