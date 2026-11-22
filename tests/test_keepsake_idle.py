"""Native motion on the shared clock, room compositing, and the GIF89a writer."""
from itertools import product
from random import Random
import unittest

from gif_reader import Gif
from keepsake_helpers import MODES, SKINS, cast, equipped_looks, kit_parts, native_pen, pixels, stats_for
from tinkerprint import art
from tinkerprint.art import _keepsake_idle as idle, keepsake
from tinkerprint.art._anime import half_head, keepsake_half as half
from tinkerprint.art._anime.traits import EXPRESSIONS, EYE_RAMPS, HAIRSTYLES
from tinkerprint.art._keepsake_gif import encode
from tinkerprint.art._keepsake_room import companions, room
from tinkerprint.art.pixels import Canvas

# Four rooms with different seeds, presentations and crews.
ROOMS = (
    ("Warden", "honey-vale", "neutral", ("claude", "agy")),
    ("Painter", "opal-glass", "woman", ("gemini", "cline", "aider")),
    ("Lorekeeper", "juniper-harbor", "man", ("opencode", "cursor")),
    ("Innkeeper", "willow-glass", "woman", ("codex", "copilot", "roo")),
)


def room_frames(pack, look, stats, harnesses, seed, **kw):
    """The whole banner on every beat, room, figure and counter together."""
    stats, harnesses = tuple(stats), tuple(harnesses)
    return tuple(room.banner(pack, look, stats, harnesses, seed, motion=beat, **kw) for beat in idle.BEATS)


class GifTest(unittest.TestCase):
    def assert_movie(self, frames, delays, scale=1):
        data = encode(frames, delays, scale)
        self.assertEqual(data, encode(frames, delays, scale))
        g = Gif(data)
        self.assertEqual((g.w, g.h), (frames[0].w*scale, frames[0].h*scale))
        self.assertEqual(g.loop, 0)
        self.assertEqual([im.delay for im in g.images], delays)
        expected = [g.indices(frame, scale) for frame in frames]
        self.assertEqual(list(g.screens(laps=2)), expected*2)
        return g

    def test_erasures_transparent_holds_and_loop_seam(self):
        frames = []
        for positions in ((), (0,8), (0,), (0,), (), (5,10)):
            f = Canvas(12,4)
            for x in positions:
                f.rect(x,1,2,2,"#000000")
            frames.append(f)
        g = self.assert_movie(frames, [200,90,80,300,150,120], 3)
        self.assertTrue(any(im.rect[2] < g.w for im in g.images))
        self.assertTrue(any(im.data.count(0) for im in g.images))
        # A retiring opaque pixel that came from an earlier frame must
        # disappear even when no new opaque pixel replaces it.
        self.assert_movie(frames[1:], [70]*5)

    def test_lzw_width_boundaries_dictionary_resets_and_subblocks(self):
        rng = Random(417)
        for n in (1, 2, 3, 7, 15, 31, 63, 127, 255):
            f = Canvas(311, 73)
            colors = [f"#{i:06x}" for i in range(n)]
            f.px = [[rng.choice(colors) for _ in range(f.w)] for _ in range(f.h)]
            self.assert_movie([f], [60])

    def test_exact_palette_timing_and_geometry_limits(self):
        f = Canvas(256,1)
        f.px[0] = [f"#{i:06x}" for i in range(256)]
        for frames, delays, scale in (([f],[10],1), ([],[],1), ([Canvas(1,1)],[],1),
                                      ([Canvas(1,1)],[95],1), ([Canvas(1,1)],[10],0),
                                      ([Canvas(1,1)],[10],65536), ([Canvas(2,1),Canvas(1,1)],[10,10],1)):
            with self.assertRaises(ValueError):
                encode(frames, delays, scale)


class IdleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = art.default_pack()
        cls.looks = cast()

    def test_every_ordered_kit_animates_with_a_fixed_head_and_clear_tile_edges(self):
        sockets = {(30+x,17+y) for x in (*range(-8,0), *range(3,11)) for y in range(-2,4)}
        # The cast, and every third pair: each kit, cut, expression, eye and skin still turns up.
        looks = list(equipped_looks())
        looks = looks[:len(cast())] + looks[len(cast())::3]
        for i, look in enumerate(looks):
            mode, expr = MODES[i%3], EXPRESSIONS[(i//3)%6]
            hair = HAIRSTYLES[mode][(i//6)%3]
            traits = dict(presentation=mode, expression=expr, hair=hair,
                          skin=SKINS[(i//2)%3], eyes=tuple(EYE_RAMPS)[i%6])
            frames = idle.figure_frames(self.pack, look, **traits)
            still = keepsake.figure(self.pack, look, **traits)
            self.assertEqual(still.px, frames[0].px)
            hat, travel, item = kit_parts(self.pack, look)
            head = native_pen(self.pack, look)
            half_head.head(head, mode, hat, travel, expr, hair)
            mask = pixels(head.image)
            with self.subTest(look=look, traits=traits):
                for beat, f in zip(idle.BEATS, frames):
                    self.assertEqual((f.w, f.h), (64,64))
                    self.assertFalse(any(f.px[0]) or any(f.px[-1]) or
                                     any(row[0] or row[-1] for row in f.px))
                    face_diff = {(x,y) for x,y in mask if f.get(x,y) != still.get(x,y)}
                    self.assertLessEqual(face_diff, sockets)
                    self.assertEqual(bool(face_diff), bool(beat.blink and expr != "joy"))
                    self.assertEqual(f.px != still.px, bool(face_diff or beat.breath or
                                                            (item == "lantern" and beat.ember)))

    def test_every_hair_clears_the_whole_tool_in_each_pose(self):
        # Breathing only deforms fabric. Bound the item on a padded drawing
        # to catch clipping, then intersect its two-pixel ring with each cut.
        heads = {}
        for look in equipped_looks():
            hat, travel, item = kit_parts(self.pack, look)
            p = native_pen(self.pack, look, padding=8)
            left, right = half.joints(item)
            half.equipment(p,item,left,right,travel)
            obj = {(x-8, y-8) for x,y in pixels(p.image)}
            self.assertTrue(all(1 <= x <= 62 and 1 <= y <= 62 for x,y in obj))
            ring = {(x+dx,y+dy) for x,y in obj for dx,dy in product(range(-2,3),repeat=2)}
            for mode, pool in HAIRSTYLES.items():
                for hair in pool:
                    key = (hat, travel, mode, hair)
                    if key not in heads:
                        head = native_pen(self.pack, look)
                        half_head.head(head, mode, hat, travel, hair=hair)
                        heads[key] = pixels(head.image).keys()
                    self.assertTrue(ring.isdisjoint(heads[key]), (look,mode,hair))
        # The flame stays inside the held lantern throughout its cycle.
        look = self.looks["Summoner"]
        frames = idle.figure_frames(self.pack, look, beats=[
            idle.BEATS[0]._replace(ember=level) for level in (0,1,2)])
        self.assertEqual(len({f.png() for f in frames}),3)
        self.assertTrue(all(pixels(f).keys() == pixels(frames[0]).keys() for f in frames))

    def test_rooms_have_four_local_motions_and_match_the_static_banner(self):
        for i,(name, seed, mode, crew) in enumerate(ROOMS):
            look = self.looks[name]
            stats = stats_for(look)
            kw = dict(skin=SKINS[i%3], presentation=mode)
            frames = room_frames(self.pack, look, iter(stats), iter(crew), seed, **kw)
            still = room.banner(self.pack, look, stats, crew, seed, **kw)
            self.assertEqual(frames[0].px, still.px)
            changes = {(x,y) for f in frames for y,row in enumerate(f.px) for x,c in enumerate(row)
                       if c != still.px[y][x]}
            t = dict(room.plan_room(self.pack,look,stats,seed).touches)
            sx = 84 if t["view"] in ("windmill","harbor") else 151
            hook = (56 if t["arrangement"] == "left" else 18)-1
            pot = 152 if t["sill"] == "near" else 163
            berths = companions.berths(crew)
            active = next(h for h in companions.CLOCKWORK if h in berths)
            cx = 193+21*berths.index(active)
            bx, by = art.banner_figure_box(self.pack, Canvas(64,64))
            rects = ((bx,by,bx+63,by+63), (sx-12,11,sx+15,12), (hook-1,12,hook,14),
                     (pot-5,30,pot+16,40), (cx-9,49,cx+9,66))
            self.assertTrue(all(None not in row for f in frames for row in f.px))
            for x0,y0,x1,y1 in rects:
                region = {(x,y) for x,y in changes if x0 <= x <= x1 and y0 <= y <= y1}
                self.assertTrue(region, (name,(x0,y0,x1,y1)))
                changes -= region
            self.assertFalse(changes, (name,changes))
            self.assertEqual(frames[0].px, room_frames(self.pack,look,stats,crew,seed,**kw)[0].px)

    def test_clock_and_each_party_mechanism(self):
        self.assertEqual(len(idle.BEATS),len(idle.DELAYS_MS))
        self.assertTrue(8 <= len(idle.BEATS) <= 16)
        self.assertTrue(2000 <= sum(idle.DELAYS_MS) <= 4000)
        self.assertEqual([b.blink for b in idle.BEATS if b.blink], [1,2])
        self.assertEqual(idle.BEATS[0], idle.Beat(0,0,0,0,0,0))
        for i, beat in enumerate(idle.BEATS):
            following = idle.BEATS[(i+1)%len(idle.BEATS)]
            self.assertLessEqual(abs(beat.breath-following.breath),1)
            self.assertLessEqual(abs(beat.bend-following.bend),1)
            self.assertLessEqual((following.gear-beat.gear)%8,1)
            self.assertEqual((following.wisp-beat.wisp)%16,1)
        for harness in (*companions.MEMBERS, "invented instrument"):
            members = [companions.member(harness,b.gear) for b in idle.BEATS]
            self.assertEqual(len({(f.w,f.h) for f in members}),1)
            self.assertGreater(len({f.png() for f in members}),1)


if __name__ == "__main__":
    unittest.main()
