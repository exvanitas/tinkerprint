"""[look]: validation, the name-seeded picks, the card's look tokens, and the pictures drawn from them."""
import base64
import copy
import dataclasses
import json
import os
import tempfile
import unittest

import helpers  # noqa: F401
from helpers import profile
from tinkerprint import art
from tinkerprint.art import keepsake
from tinkerprint.audit import audit_card
from tinkerprint.build import build
from tinkerprint.cli import STARTER, look_line
from tinkerprint.demo import TOBI, WREN, make_person
from tinkerprint.look import describe, of_card, resolve
from tinkerprint.profile import ProfileError, load_profile, parse_profile
from tinkerprint.render_card import portrait_plate, render_card
from tinkerprint.render_card_png import render_card_png
from tinkerprint.render_html import render_html

PACK = art.default_pack()


def with_look(**look):
    return profile([("Kite", "/nonexistent/kite", None)], look=look)


class ProfileLook(unittest.TestCase):
    def test_every_choice_is_checked_with_a_suggestion(self):
        self.assertEqual(with_look().look, {})
        full = with_look(presentation="woman", skin="deep", hair="chignon", eyes="plum", expression="calm")
        self.assertEqual(full.look, {"presentation": "woman", "skin": "deep", "hair": "chignon", "eyes": "plum",
                                     "expression": "calm"})
        for look, words in (({"presentation": "women"}, "Did you mean 'woman'?"),
                            ({"skin": "medim"}, "Did you mean 'medium'?"),
                            ({"eyes": "mos"}, "Did you mean 'moss'?"),
                            ({"expression": "grinning"}, "Did you mean 'grin'?"),
                            ({"hair": "curl", "presentation": "man"}, "Did you mean 'curls'?"),
                            ({"colour": "moss"}, "look: unknown key 'colour'"),
                            ({"skin": 3}, "look.skin must be text in quotes")):
            with self.subTest(look=look):
                with self.assertRaisesRegex(ProfileError, words.replace("?", r"\?").replace(".", r"\.")):
                    with_look(**look)

    def test_hair_must_come_from_the_chosen_presentations_pool(self):
        self.assertEqual(with_look(presentation="man", hair="side part").look["hair"], "side part")
        with self.assertRaisesRegex(ProfileError, 'not a neutral cut. It is a cut for presentation "woman"'):
            with_look(hair="braid")
        with self.assertRaisesRegex(ProfileError, 'not a woman cut. It is a cut for presentation "man"'):
            with_look(presentation="woman", hair="crop")

    def test_starter_lists_look_commented_out_with_every_option(self):
        text = STARTER.format(name_line='name = "Your Name"', tz_line='timezone = "UTC"', tz_note="",
                              ident_note="", emails='"you@example.test"', names="")
        block = text[text.index("[look]"):text.index("[[project]]")]
        for word in ("neutral", "man", "woman", "light", "medium", "deep", "honey", "moss", "slate", "chestnut",
                     "plum", "lagoon", *keepsake.EXPRESSIONS, *(c for cuts in keepsake.HAIRSTYLES.values() for c in cuts)):
            self.assertIn(word, block)
        self.assertTrue(all(line.startswith("#") for line in block.splitlines()[1:] if line.strip()))
        import tomllib
        data = tomllib.loads(text)
        self.assertEqual(data["look"], {})
        self.assertEqual(parse_profile(data, "/nonexistent-base").look, {})


class Resolve(unittest.TestCase):
    def test_skin_and_presentation_are_never_random(self):
        for name in ("Ada Example", "Rae Quill", "Juno Fable", ""):
            look = resolve({}, name)
            self.assertEqual((look["presentation"], look["skin"]), ("neutral", None))
            self.assertEqual(look["picked"], ["hair", "eyes", "expression"])
            self.assertIn(look["hair"], keepsake.HAIRSTYLES["neutral"])
        chosen = resolve({"presentation": "man", "skin": "medium", "eyes": "slate"}, "Ada Example")
        self.assertEqual((chosen["presentation"], chosen["skin"], chosen["eyes"]), ("man", "medium", "slate"))
        self.assertEqual(chosen["picked"], ["hair", "expression"])
        self.assertIn(chosen["hair"], keepsake.HAIRSTYLES["man"])

    def test_the_same_name_picks_the_same_traits_and_different_names_differ(self):
        a, b = resolve({}, "Ada Example"), resolve({}, "Rae Quill")
        self.assertEqual(a, resolve({}, "Ada Example"))
        self.assertNotEqual({k: a[k] for k in ("hair", "eyes", "expression")},
                            {k: b[k] for k in ("hair", "eyes", "expression")})
        # Picks come from the name alone, never from the class or the stats.
        self.assertEqual(keepsake.traits("Ada Example", art.Look("builder", "pair", "Logic", "Tests"), "neutral"),
                         keepsake.traits("Ada Example", None, "neutral"))

    def test_the_build_line_names_the_look_and_what_was_picked(self):
        look = dict(resolve({"skin": "deep", "hair": "shag"}, "Ada Example"))
        line = describe(look, PACK)
        self.assertTrue(line.startswith(f"Look: neutral, skin deep, hair shag, eyes {look['eyes']}, {look['expression']} ("))
        self.assertIn("(eyes and expression picked from your name; set them under [look] to keep them)", line)
        one = describe(dict(look, picked=["eyes"]), PACK, from_card_name=True)
        self.assertTrue(one.endswith("(eyes picked from your card name; set it under [look] to keep it)"))
        none = describe(dict(resolve({"skin": "light"}, "x"), picked=[]), PACK)
        self.assertNotIn("(", none)
        # Unset skin is the pack's, named when it is one of the three.
        self.assertIn("skin light,", describe(resolve({}, "x"), PACK))
        odd = dict(PACK, skin_colors=["#ffffff", "#eeeeee", "#dddddd", "#cccccc"])
        self.assertIn("skin from the art pack,", describe(resolve({}, "x"), odd))


class BuiltLook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        world = os.path.join(cls.tmp.name, "world")
        cls.wren = load_profile(make_person(world, WREN))
        cls.tobi = load_profile(make_person(world, TOBI))
        cls.res = cls.build(cls.wren, "a")

    @classmethod
    def build(cls, prof, tag):
        return build(prof, os.path.join(cls.tmp.name, "out", tag), home=os.path.join(cls.tmp.name, "data", tag),
                     built_at="t")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def files(self, res):
        out = {}
        for key in ("html", "card", "card_png", "portrait", "json"):
            with open(res["paths"][key], "rb") as f:
                out[key] = f.read()
        return out

    def test_same_inputs_give_byte_identical_pictures(self):
        again = self.build(self.wren, "b")
        self.assertEqual(self.files(again), self.files(self.res))

    def test_two_names_get_different_random_traits(self):
        other = self.build(dataclasses.replace(self.wren, name="Mara Quill"), "renamed")
        a, b = self.res["sheet"]["look"], other["sheet"]["look"]
        self.assertEqual((a["seed"], b["seed"]), ("Wren Aldous", "Mara Quill"))
        self.assertNotEqual({k: a[k] for k in ("hair", "eyes", "expression")},
                            {k: b[k] for k in ("hair", "eyes", "expression")})
        self.assertNotEqual(self.files(other)["portrait"], self.files(self.res)["portrait"])

    def test_the_seed_is_the_card_name_and_choices_stick(self):
        chosen = {"presentation": "woman", "skin": "medium", "hair": "waves", "eyes": "lagoon", "expression": "calm"}
        prof = dataclasses.replace(self.wren, card_name="wrenfold", look=chosen)
        res = self.build(prof, "handle")
        look = res["sheet"]["look"]
        self.assertEqual(look["seed"], "wrenfold")
        self.assertEqual(look["picked"], [])
        self.assertEqual(res["sheet"]["card"]["look"], chosen)
        self.assertEqual(look_line(res["sheet"], prof, PACK),
                         "Look: woman, skin medium, hair waves, eyes lagoon, calm")
        self.assertIn("picked from your card name",
                      look_line(self.build(dataclasses.replace(prof, look={}), "handle2")["sheet"], prof, PACK))

    def test_portrait_png_is_the_plate_at_6x(self):
        card = self.res["sheet"]["card"]
        plate = keepsake.plate(PACK, art.card_look(card), card["name"], **of_card(card))
        self.assertEqual(portrait_plate(card, PACK).px, plate.px)
        self.assertEqual(self.files(self.res)["portrait"], plate.png(6, indexed=True))

    def test_card_portrait_follows_only_the_card_name_and_look_tokens(self):
        card = copy.deepcopy(self.res["sheet"]["card"])
        svg, png = render_card(card), render_card_png(card)
        for key, value in (("hair", "curtains" if card["look"]["hair"] != "curtains" else "bob"),
                           ("skin", "deep"), ("eyes", "plum" if card["look"]["eyes"] != "plum" else "moss")):
            changed = dict(card, look=dict(card["look"], **{key: value}))
            self.assertNotEqual(render_card(changed), svg, key)
            self.assertNotEqual(render_card_png(changed), png, key)
        # The sheet's own look, its seed and its record of picks never reach the card.
        sheet = copy.deepcopy(self.res["sheet"])
        sheet["look"] = dict(sheet["look"], seed="Someone Else", picked=[])
        self.assertEqual(render_card(sheet["card"]), svg)

    def test_audit_lists_the_look_tokens(self):
        lines = audit_card(os.path.dirname(self.res["paths"]["card"]), self.wren)
        look = self.res["sheet"]["card"]["look"]
        line = next(x for x in lines if x.startswith("The portrait is drawn from"))
        self.assertEqual(line, "The portrait is drawn from the card's name and these look tokens: presentation "
                               f"neutral, skin from the art pack, hair {look['hair']}, eyes {look['eyes']}, "
                               f"expression {look['expression']}.")

    def test_chronicle_party_pins_and_trinkets_use_keepsake_art(self):
        sheet = self.res["sheet"]
        page = self.files(self.res)["html"].decode("utf-8")
        seed, look = sheet["look"]["seed"], of_card(sheet["card"])
        last = art.chapter_look(sheet["chronicle"][-1], sheet["profile"]["set"])
        tile = keepsake.plate(PACK, last, seed, **look)
        self.assertIn(base64.b64encode(tile.png(2, indexed=True)).decode("ascii"), page)
        for m in sheet["party"]:
            self.assertIn(base64.b64encode(keepsake.instrument(m["harness"]).png(4, indexed=True)).decode(), page)
        for a in sheet["achievements"]:
            self.assertIn(base64.b64encode(keepsake.pin(PACK, a["id"]).png(4, indexed=True)).decode(), page)
        for r in sheet["stats"]:
            if r["points"] > 0:
                self.assertIn(base64.b64encode(keepsake.trinket(PACK, r["key"]).png(5, indexed=True)).decode(), page)
        # A quiet stretch rests at the person's own camp; a milestone wears the milestone pin.
        quiet = json.loads(json.dumps(sheet))
        quiet["chronicle"].insert(1, {"rest": True, "quarters": 1, "label": "2026 Q1"})
        quiet["milestones"] = [{"date": "2026-03-01", "text": "Shipped the kite"}]
        rest = render_html(quiet)
        camp = keepsake.camp(PACK, sheet["profile"]["set"], seed)
        self.assertIn(base64.b64encode(camp.png(2, indexed=True)).decode(), rest)
        self.assertIn(base64.b64encode(keepsake.pin(PACK, "milestone").png(2, indexed=True)).decode(), rest)

    def test_party_drawings_depend_on_the_harness_name_alone(self):
        sheet = json.loads(json.dumps(self.res["sheet"]))
        member = sheet["party"][0]
        before = render_html(sheet)
        drawing = base64.b64encode(keepsake.instrument(member["harness"]).png(4, indexed=True)).decode()
        member.update(name="Renamed Helper", sessions=1)
        self.assertIn(drawing, before)
        self.assertIn(drawing, render_html(sheet))


if __name__ == "__main__":
    unittest.main()
