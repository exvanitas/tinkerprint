"""portrait.gif: the plate's idle loop from the card fields alone, and its audit. Everything here is invented."""
import copy
import os
import tempfile
import unittest
from datetime import date

import helpers  # noqa: F401
from gif_reader import Gif
from tinkerprint import art, look
from tinkerprint.art import keepsake
from tinkerprint.audit import audit_card, check_portrait_gif, check_portrait_png, gif_blocks
from tinkerprint.build import build
from tinkerprint.cli import output_lines
from tinkerprint.demo import WREN, make_person
from tinkerprint.profile import load_profile
from tinkerprint.render_card import portrait_gif, portrait_png

PACK = art.default_pack()


def _insert(data: bytes, block: bytes) -> bytes:
    """data with block placed just before the trailer."""
    return data[:-1] + block + b";"


class PortraitGif(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.prof = load_profile(make_person(os.path.join(cls.tmp.name, "w"), WREN))
        cls.out = os.path.join(cls.tmp.name, "out")
        cls.res = build(cls.prof, cls.out, home=os.path.join(cls.tmp.name, "data"), today=date(2026, 11, 1))
        cls.card = cls.res["sheet"]["card"]
        with open(os.path.join(cls.out, "portrait.gif"), "rb") as f:
            cls.gif = f.read()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_it_is_the_plate_idling_at_the_png_scale(self):
        self.assertEqual(self.res["paths"]["portrait_gif"], os.path.join(self.out, "portrait.gif"))
        g = Gif(self.gif)
        self.assertEqual((g.w, g.h), (384, 384))
        self.assertEqual(g.loop, 0)
        self.assertEqual([im.delay for im in g.images], list(keepsake.DELAYS_MS))
        frames = keepsake.plate_frames(PACK, art.card_look(self.card), self.card["name"],
                                       **look.options(look.of_card(self.card)))
        for i, (screen, frame) in enumerate(zip(g.screens(), frames)):
            self.assertEqual(screen, g.indices(frame, 6), i)
        # Frame zero is portrait.png's still, and the loop is no bigger than a small avatar needs.
        with open(os.path.join(self.out, "portrait.png"), "rb") as f:
            self.assertEqual(f.read(), frames[0].png(6, indexed=True))
        self.assertLess(len(self.gif), 24_000)

    def test_it_reads_only_the_card_fields(self):
        self.assertEqual(portrait_gif(self.card, PACK), self.gif)
        sheet = copy.deepcopy(self.res["sheet"])
        sheet["profile"]["name"] = "Someone Else"
        sheet["projects"] = []
        sheet["party"] = []
        self.assertEqual(portrait_gif(sheet["card"], PACK), self.gif)
        self.assertNotEqual(portrait_gif(dict(self.card, name="Rae Quill"), PACK), self.gif)
        self.assertNotEqual(portrait_gif(dict(self.card, look=dict(self.card["look"], skin="deep")), PACK), self.gif)

    def test_build_prints_it_and_card_off_removes_it(self):
        self.assertIn(f"  portrait {self.out}/portrait.gif", output_lines(self.res))
        with tempfile.TemporaryDirectory() as t:
            out = os.path.join(t, "out")
            os.makedirs(out)
            with open(os.path.join(out, "portrait.gif"), "wb") as f:
                f.write(b"old")
            prof = copy.copy(self.prof)
            prof.card_allow = False
            res = build(prof, out, home=os.path.join(t, "data"), today=date(2026, 11, 1))
            self.assertFalse(os.path.exists(os.path.join(out, "portrait.gif")))
            self.assertNotIn("portrait_gif", res["paths"])

    def test_audit_certifies_it(self):
        lines = audit_card(self.out, self.prof)
        self.assertIn("portrait.gif holds image frames only, no comment or text, and is exactly the card's idle loop.",
                      lines)
        self.assertIn("portrait.png holds image data only, and draws exactly the card's portrait.", lines)
        kinds = [b[0] for b in gif_blocks(self.gif)]
        self.assertEqual(kinds.count("image"), len(keepsake.DELAYS_MS))
        self.assertEqual([b for b in gif_blocks(self.gif) if b[0] == "application"], [("application", "NETSCAPE2.0")])

    def test_comments_text_and_other_extensions_are_refused(self):
        comment = b"\x21\xfe\x0cPrivate note\x00"
        text = b"\x21\x01\x0c" + bytes(12) + b"\x05hello\x00"
        app = b"\x21\xff\x0bXMP DataXMP\x04note\x00"
        for block, word in ((comment, "a comment"), (text, "plain text"), (app, "XMP DataXMP")):
            ok, msg = check_portrait_gif(_insert(self.gif, block), self.card, PACK)
            self.assertFalse(ok, word)
            self.assertIn(word, msg)
            self.assertIn("not certified", msg)

    def test_other_bytes_or_no_fields_are_refused(self):
        self.assertTrue(check_portrait_gif(self.gif, self.card, PACK)[0])
        other = portrait_gif(dict(self.card, name="Rae Quill"), PACK)
        ok, msg = check_portrait_gif(other, self.card, PACK)
        self.assertFalse(ok)
        self.assertIn("is not the loop", msg)
        for broken in (self.gif[:-1], self.gif + b"\0", b"GIF87a" + self.gif[6:], b"", self.gif[:200] + b";"):
            self.assertFalse(check_portrait_gif(broken, self.card, PACK)[0])
        self.assertFalse(check_portrait_gif(self.gif, None, PACK)[0])
        self.assertFalse(check_portrait_gif(self.gif, {"enabled": False}, PACK)[0])

    def test_portrait_png_is_checked_like_card_png(self):
        png = portrait_png(self.card, PACK)
        self.assertTrue(check_portrait_png(png, self.card, PACK)[0])
        ok, msg = check_portrait_png(portrait_png(dict(self.card, name="Rae Quill"), PACK), self.card, PACK)
        self.assertFalse(ok)
        self.assertIn("does not draw the card's portrait", msg)
        self.assertFalse(check_portrait_png(png[:-3], self.card, PACK)[0])
        self.assertFalse(check_portrait_png(self.gif, self.card, PACK)[0])


if __name__ == "__main__":
    unittest.main()
