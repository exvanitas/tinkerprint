"""Every class of both sets draws in the Keepsake art, in every presentation, inside its tile, and every
pin, trinket and instrument exists. These replace the tests of the retired 48-pixel sprites."""
import unittest

import helpers  # noqa: F401
from tinkerprint import art
from tinkerprint.achievements import RULES
from tinkerprint.art import keepsake
from tinkerprint.art.compose import Look, look_for
from tinkerprint.art.pack import PackError
from tinkerprint.gallery import class_looks
from tinkerprint.sets import PAIR, SETS, SPECIALIST

PACK = art.default_pack()


def cases(set_name):
    return class_looks(set_name) + [("Unclassed", look_for(set_name, None, [], []), "")]


class EveryClass(unittest.TestCase):
    def test_every_class_draws_a_distinct_figure_in_each_presentation(self):
        for set_name in SETS:
            seen = {}
            for name, look, _ in cases(set_name):
                renders = set()
                for mode in ("neutral", "man", "woman"):
                    with self.subTest(set=set_name, name=name, mode=mode):
                        fig = keepsake.figure(PACK, look, presentation=mode)
                        self.assertEqual((fig.w, fig.h), (64, 64))
                        self.assertGreater(sum(1 for row in fig.px for p in row if p), 900, name)
                        self.assertGreaterEqual(len(fig.colors()), 7, name)
                        renders.add(fig.png())
                self.assertEqual(len(renders), 3, (set_name, name))
                neutral = keepsake.figure(PACK, look).png()
                self.assertNotIn(neutral, seen, (set_name, name, seen.get(neutral)))
                seen[neutral] = name

    def test_both_orders_of_every_pair_and_every_runner_up_draw(self):
        for set_name, stats in SETS.items():
            for a, b in PAIR[set_name]:
                drawn = []
                for top, item in ((a, b), (b, a)):
                    look = look_for(set_name, "pair", [a, b], [top, item])
                    self.assertEqual((look.top, look.item), (top, item))
                    drawn.append(keepsake.figure(PACK, look).png())
                self.assertNotEqual(drawn[0], drawn[1], (a, b))
            for s in SPECIALIST[set_name]:
                for other in stats:
                    look = look_for(set_name, "specialist", [s], [s, other] if other != s else [s])
                    self.assertEqual(look.item, other)
                    keepsake.figure(PACK, look)

    def test_figures_and_capes_keep_a_clear_border(self):
        for set_name in SETS:
            looks = [look for _, look, _ in cases(set_name)]
            looks += [Look(set_name, "pair", a, b) for a in SETS[set_name] for b in SETS[set_name] if a != b]
            for look in looks:
                for multi in ((), tuple(SETS[set_name][:2])):
                    fig = keepsake.figure(PACK, Look(look.set_name, look.kind, look.top, look.item, multi))
                    edge = [fig.px[y][x] for y in range(fig.h) for x in (0, fig.w - 1)] + fig.px[0]
                    self.assertEqual(set(edge), {None}, look)

    def test_unknown_presentation_is_refused(self):
        look = look_for("builder", None, [], [])
        for unknown in ("automatic", "", None, []):
            with self.assertRaisesRegex(PackError, "unknown presentation"):
                keepsake.figure(PACK, look, presentation=unknown)
            with self.assertRaisesRegex(PackError, "unknown presentation"):
                keepsake.plate(PACK, look, "Rae Quill", presentation=unknown)

    def test_pins_trinkets_and_instruments_exist_for_every_key(self):
        pins = {keepsake.pin(PACK, k).png() for k in list(RULES) + ["milestone"]}
        self.assertEqual(len(pins), len(RULES) + 1)
        self.assertEqual(keepsake.pin(PACK, "no-such-achievement").png(), keepsake.pin(PACK, "milestone").png())
        for stat in {s for v in SETS.values() for s in v}:
            self.assertGreater(len(keepsake.trinket(PACK, stat).colors()), 2)
        drawn = {keepsake.instrument(h).png() for h in keepsake.MEMBERS}
        self.assertEqual(len(drawn), len(keepsake.MEMBERS))
        self.assertEqual(keepsake.instrument("something-new").png(), keepsake.instrument("default").png())


if __name__ == "__main__":
    unittest.main()
