"""Native-grid checks for the half-body tile: grips, sleeves, capes, waists and the counter."""
from itertools import product
import unittest
from unittest.mock import patch

from keepsake_helpers import (DYE, MODES, SKIN, adjacent, cast, connected, equipped_looks, kit_parts, mark,
                              native_pen, pixels)
from tinkerprint import art
from tinkerprint.art import keepsake
from tinkerprint.art._anime import half_head, keepsake_half as half
from tinkerprint.art._drawing import Drawing
from tinkerprint.art._keepsake_room import room


class HalfBodyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = art.default_pack()
        cls.looks = list(equipped_looks())
        cls.cast = cast()

    def test_whole_object_two_clear_pixels_and_visible_grips(self):
        for look in self.looks:
            hat, travel, item = kit_parts(self.pack, look)
            p = native_pen(self.pack, look, padding=16)
            left, right = half.joints(item)
            half.equipment(p, item, left, right, travel)
            obj = {(x-16, y-16): ink for (x, y), ink in pixels(p.image).items()}
            self.assertEqual(bool(obj), bool(item))
            self.assertTrue(all(1 <= x <= 62 and 1 <= y <= 62 for x, y in obj), look)
            two_rings = {(x+dx, y+dy) for x, y in obj for dx, dy in product(range(-2, 3), repeat=2)}
            for mode in MODES:
                with self.subTest(look=look, mode=mode):
                    head = native_pen(self.pack, look)
                    half_head.head(head, mode, hat, travel)
                    self.assertTrue(two_rings.isdisjoint(pixels(head.image)))
                    fig = keepsake.figure(self.pack, look, skin=SKIN, presentation=mode)
                    self.assertTrue(connected(fig))
                    hidden = {pt for pt, c in obj.items() if fig.get(*pt) != c}
                    self.assertTrue(all(fig.get(*pt) == SKIN[0] for pt in hidden))
                    if item == "pavise":
                        self.assertFalse(hidden, "shield face and all four edges must cover the hand")
                    elif item:
                        both = item in ("codex", "map", "cog", "fan", "scope")
                        for joint in (left, right) if both else (right,):
                            cx, cy = head.xy(*joint)
                            self.assertGreaterEqual(sum(abs(x-cx) <= 4 and abs(y-cy) <= 3
                                                        for x, y in hidden), 3)
                        if item in half.LONG_TOOLS:
                            cx, cy = head.xy(*right)
                            self.assertTrue(any(y <= cy-15 for x, y in obj))
                            self.assertTrue(any(y >= cy+5 and (x, y) not in hidden for x, y in obj))
                            self.assertLessEqual(max(x for x, y in obj)-min(x for x, y in obj),
                                                 max(y for x, y in obj)-min(y for x, y in obj))

    def test_each_visible_arm_reaches_from_its_shoulder_around_its_elbow_to_its_wrist(self):
        left_ink, right_ink = "#12ab01", "#12ab02"
        draw_arm = half.arm

        def marked_arm(p, side, *args):
            mark(draw_arm, left_ink if side == -1 else right_ink)(p, side, *args)

        with (patch.object(half, "arm", marked_arm),
              patch.object(half.implements, "trade_shoulder", mark(half.implements.trade_shoulder, left_ink))):
            for look, mode in product(self.looks, MODES):
                _, _, item = kit_parts(self.pack, look)
                pic = keepsake.figure(self.pack, look, presentation=mode, skin=SKIN)
                points = pixels(pic)
                for side, joint, ink in zip((-1, 1), half.joints(item), (left_ink, right_ink)):
                    with self.subTest(look=look, mode=mode, side=side):
                        sleeve = {pt for pt, v in points.items() if v == ink}
                        reached = {pt for pt in sleeve if pt[1] <= 36}
                        self.assertTrue(reached, "exposed shoulder")
                        todo = list(reached)
                        while todo:
                            found = (set(adjacent(*todo.pop())) & sleeve)-reached
                            reached.update(found)
                            todo.extend(found)
                        self.assertTrue(any(y >= 50 and side*(x-30) >= 15 for x, y in reached), "elbow")
                        hx, hy = joint
                        wrist = {pt for pt, v in points.items() if v == SKIN[0]
                                 and abs(pt[0]-30-hx) <= 5 and abs(pt[1]-17-hy) <= 4}
                        self.assertTrue(any(set(adjacent(*pt)) & reached for pt in wrist), "hand to cuff")

    def test_runner_up_on_working_sleeve_and_opposite_shoulder(self):
        for look in self.looks:
            if look.kind == "pair":
                pack = dict(self.pack, stat_colors=dict(self.pack["stat_colors"], **{look.item: [DYE]*4}))
                pic = keepsake.figure(pack, look)
                with self.subTest(look=look):
                    for x0, x1, y0, y1 in ((10, 27, 31, 44), (40, 52, 35, 55)):
                        self.assertGreater(sum(row[x0:x1].count(DYE) for row in pic.px[y0:y1]), 9)

    def test_multiclass_trim_stays_on_the_cape(self):
        look = art.Look("builder", "pair", "Infra", "Tools", ("Logic", "Data"))
        plain = art.Look("builder", "pair", "Infra", "Tools")
        pic = keepsake.figure(self.pack, look)
        base = keepsake.figure(self.pack, plain)
        changed = {(x, y) for y, row in enumerate(pic.px) for x, c in enumerate(row)
                   if c != base.get(x, y)}
        self.assertGreater(len(changed), 10)
        self.assertTrue(all(x <= 21 and y >= 31 for x, y in changed))
        self.assertTrue(connected(pic))

    def test_kit_substitutions_and_distinct_waists(self):
        for name, part in (("Mechanist", "key"), ("Innkeeper", "teapot"), ("Cartographer", "scope")):
            look = self.cast[name]
            pack = dict(self.pack, looks=dict(self.pack["looks"]))
            pack["looks"][look.top] = dict(pack["looks"][look.top], trinket="other")
            _, _, item = kit_parts(pack, look)
            self.assertEqual(item, part)
            p = native_pen(pack, look)
            left, right = half.joints(item)
            half.equipment(p, item, left, right, None)
            bare = pixels(p.image)
            fig = keepsake.figure(pack, look, skin=SKIN)
            self.assertTrue(connected(fig))
            for hx, hy in (left, right) if item == "scope" else (right,):
                around = [(x, y) for x, y in bare if abs(x-30-hx) <= 4 and abs(y-17-hy) <= 3]
                self.assertGreaterEqual(sum(fig.get(x, y) == SKIN[0] for x, y in around), 3)
            self.assertNotEqual(fig.px, keepsake.figure(self.pack, look, skin=SKIN).px)
        finishes = set()
        for body in ("infra-coat", "tools-coat", "community-coat", "logic-coat", "traveler-coat"):
            p = native_pen(self.pack, self.cast["Traveler"])
            half.waist(p, body)
            finishes.add(tuple(tuple(row) for row in p.image.px[54:]))
        self.assertEqual(len(finishes), 5)

    def test_banner_registration_and_foreground_at_waist(self):
        for look, stats in ((self.cast["Warden"], [("Infra", 100)]),
                            (art.Look("tinkerer", "pair", "Art", "Lore"), [("Art", 60), ("Lore", 40)])):
            fig = keepsake.figure(self.pack, look)
            bx, by = art.banner_figure_box(self.pack, fig)
            display = room.banner(self.pack, look, stats)
            self.assertEqual((display.w, display.h), (252, 72))
            _, travel, item = kit_parts(self.pack, look)
            p = native_pen(self.pack, look)
            left, right = half.joints(item)
            half.equipment(p, item, left, right, travel)
            half.hands(p, item, left, right)
            desk = Drawing(252, 72)
            room.counter(desk, (bx+16, by+10))
            hidden, overlap = set(), set()
            for (x, y), color in pixels(fig).items():
                wood = desk.get(bx+x, by+y)
                if wood and p.image.get(x, y):
                    overlap.add((x, y))
                elif wood:
                    hidden.add((x, y))
                    color = wood
                self.assertEqual(display.get(bx+x, by+y), color)
            self.assertGreater(len(hidden), 50)
            if item == "pavise":
                self.assertGreater(len(overlap), 10)


if __name__ == "__main__":
    unittest.main()
