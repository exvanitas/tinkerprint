"""[look]: validation, the name-seeded picks, the card's look tokens, and the pictures drawn from them."""
import unittest

import helpers  # noqa: F401
from helpers import profile
from tinkerprint import art
from tinkerprint.art import keepsake
from tinkerprint.cli import STARTER
from tinkerprint.look import describe, resolve
from tinkerprint.profile import ProfileError, parse_profile

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


if __name__ == "__main__":
    unittest.main()
