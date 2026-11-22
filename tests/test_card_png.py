"""card.png: the pixel font, the PNG and its audit. Every name, path and email here is invented."""
import copy
import io
import os
import struct
import tempfile
import unittest
import zlib
from contextlib import redirect_stdout
from datetime import date

import helpers  # noqa: F401
from test_card_options import tie_card
from tinkerprint import art, pixelfont
from tinkerprint.audit import audit_card, check_png, png_chunks, svg_strings
from tinkerprint.build import build
from tinkerprint.demo import WREN, make_person
from tinkerprint.profile import load_profile
from tinkerprint.render_card import H, PX, PY, W, portrait_box, portrait_plate, render_card, shows, visible
from tinkerprint.render_card_png import draw_card, render_card_png


class PixelFont(unittest.TestCase):
    def test_glyphs_are_rectangles_of_ink(self):
        for ch, rows in pixelfont.GLYPHS.items():
            self.assertEqual(len({len(r) for r in rows}), 1, ch)
            self.assertTrue(set("".join(rows)) <= {"#", "."}, ch)
            self.assertIn(len(rows), (7, 8, 9), ch)

    def test_every_printable_ascii_character_has_a_glyph(self):
        for code in range(32, 127):
            self.assertIn(chr(code), pixelfont.GLYPHS, repr(chr(code)))

    def test_width_matches_what_draw_draws(self):
        from tinkerprint.art.pixels import Canvas
        for text, scale, bold in (("Tobi Marsh", 7, True), ("Interface 15%", 2, True), ("Zoë · Ångström", 3, False)):
            c = Canvas(900, 120)
            end = pixelfont.draw(c, 10, 80, text, "#ffffff", scale, bold=bold)
            self.assertEqual(end - 10, pixelfont.width(text, scale, bold=bold), text)
            inked = [x for row in c.px for x, v in enumerate(row) if v]
            self.assertEqual(max(inked) + 1, end, text)

    def test_accents_keep_their_letter_and_unknown_characters_draw(self):
        self.assertEqual(pixelfont.width("é", 2), pixelfont.width("e", 2))
        self.assertEqual(pixelfont.width("ß"), pixelfont.width("ss"))
        self.assertEqual(pixelfont.width("龍"), pixelfont.width("?"))

    def test_fit_and_clip(self):
        self.assertEqual(pixelfont.fit("Tobi", 1000, 7), 7)
        self.assertLess(pixelfont.fit("W" * 22, 496, 7, bold=True), 7)
        cut = pixelfont.clip("Interface and more", 60, 2)
        self.assertTrue(cut.endswith("…"))
        self.assertLessEqual(pixelfont.width(cut, 2), 60)


class CardPng(unittest.TestCase):
    def test_png_is_1200_by_630_and_holds_image_chunks_only(self):
        data = render_card_png(tie_card())
        chunks = png_chunks(data)
        self.assertEqual([k for k, _ in chunks if k not in (b"IDAT",)], [b"IHDR", b"PLTE", b"IEND"])
        self.assertEqual(struct.unpack(">II", chunks[0][1][:8]), (W, H))
        self.assertEqual(render_card_png(tie_card()), data)

    def test_png_reads_only_visible_fields(self):
        card = tie_card()
        base = render_card_png(card)
        extra = dict(card, projects_hidden=["Secret Kite"], reason="private")
        self.assertEqual(render_card_png(extra), base)
        for change in ({"name": "Rae Quill"}, {"level": 16}, {"party": []}, {"class": "Warden"}):
            self.assertNotEqual(render_card_png(dict(card, **change)), base, change)

    def test_portrait_is_crisp_at_an_integer_scale(self):
        pack = art.default_pack()
        card = tie_card()
        scale, padding, frame = portrait_box(pack)
        canvas = draw_card(card, pack)
        sprite = portrait_plate(card, pack)
        self.assertEqual(scale * sprite.w, 192)
        sx, sy = PX + frame + 14, PY + frame - 14  # the level seal covers the frame's corner
        checked = 0
        for j in range(0, sprite.h, 3):
            for i in range(0, sprite.w, 3):
                want = sprite.get(i, j)
                x, y = PX + padding + i * scale, PY + padding + j * scale
                if want is None or (x - sx) ** 2 + (y - sy) ** 2 < 50 ** 2:
                    continue
                checked += 1
                block = {canvas.get(x + a, y + b) for a in range(scale) for b in range(scale)}
                self.assertEqual(block, {want}, (i, j))
        self.assertGreater(checked, 200)

    def test_a_long_multiclass_wraps_instead_of_cutting(self):
        from tinkerprint.render_card import INK2, multiclass_room
        pack = art.default_pack()
        card = dict(tie_card(), multiclass="Quartermaster, close to Quartermaster")
        canvas = draw_card(card, pack)
        _, _, frame = portrait_box(pack)
        x0 = PX + frame + 58
        rows = lambda a, b: [x for y in range(a, b) for x, c in enumerate(canvas.px[y]) if c == INK2 and x >= x0]
        first, second = rows(PY + 26, PY + 41), rows(PY + 46, PY + 61)
        self.assertTrue(first and second)
        self.assertLessEqual(max(first + second), x0 + multiclass_room(x0))
        # Both lines together draw more ink than any one-line cut would.
        one = draw_card(dict(card, multiclass="Quartermaster"), pack)
        self.assertGreater(len(second), 0)
        self.assertNotEqual(one.px[PY + 55], canvas.px[PY + 55])

    def test_three_party_members_fit_without_a_cut(self):
        from tinkerprint.render_card import BOTTOM_Y, MUTED, RADAR_LEFT
        pack = art.default_pack()
        card = dict(tie_card(), party=["Claude Code", "Codex", "Antigravity"])
        canvas = draw_card(card, pack)
        ink = [x for y in range(BOTTOM_Y - 14, BOTTOM_Y + 4) for x, c in enumerate(canvas.px[y])
               if c == MUTED and x > RADAR_LEFT]
        self.assertLessEqual(max(ink), W - 64)
        # No ellipsis: the members' line draws exactly the unclipped text's width.
        start = min(ink)
        self.assertEqual(max(ink) + 1 - start, pixelfont.width("Claude Code · Codex · Antigravity", 2))

    def test_portrait_room_fits_a_64_pixel_figure_at_3x(self):
        _, padding, frame = portrait_box({"canvas": [64, 64]})
        self.assertEqual(frame - 2 * padding, 192)


def _with_chunk(data: bytes, kind: bytes, body: bytes) -> bytes:
    chunk = struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)
    end = data.rindex(b"IEND") - 4
    return data[:end] + chunk + data[end:]


class AuditPng(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        world = os.path.join(cls.tmp.name, "w")
        cls.prof = load_profile(make_person(world, WREN))
        cls.out = os.path.join(cls.tmp.name, "out")
        cls.res = build(cls.prof, cls.out, home=os.path.join(cls.tmp.name, "data"), today=date(2026, 11, 1))
        with open(os.path.join(cls.out, "card.png"), "rb") as f:
            cls.png = f.read()
        with open(os.path.join(cls.out, "card.svg"), "rb") as f:
            cls.svg = f.read()
        cls.card = cls.res["sheet"]["card"]

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_build_writes_card_png_and_audit_certifies_it(self):
        self.assertEqual(self.res["paths"]["card_png"], os.path.join(self.out, "card.png"))
        lines = audit_card(self.out, self.prof)
        self.assertIn("card.png holds image data only, and draws exactly the fields card.svg draws.", lines)
        self.assertEqual(self.card["built"], "Nov 2026")

    def test_text_chunks_are_refused(self):
        for kind in (b"tEXt", b"iTXt", b"zTXt"):
            ok, msg = check_png(_with_chunk(self.png, kind, b"Comment\x00private"), self.card, self.svg)
            self.assertFalse(ok)
            self.assertIn(kind.decode(), msg)
            self.assertIn("not certified", msg)

    def test_other_chunks_are_refused(self):
        ok, msg = check_png(_with_chunk(self.png, b"tIME", b"\x07\xea\x0b\x16\x00\x00\x00"), self.card, self.svg)
        self.assertFalse(ok)
        self.assertIn("tIME", msg)

    def test_pixels_from_other_fields_are_refused(self):
        other = render_card_png(dict(self.card, name="Rae Quill"))
        ok, msg = check_png(other, self.card, self.svg)
        self.assertFalse(ok)
        self.assertIn("does not draw the card fields", msg)

    def test_a_card_svg_from_other_fields_is_refused(self):
        other_svg = render_card(dict(self.card, name="Rae Quill")).encode()
        ok, _ = check_png(self.png, self.card, other_svg)
        self.assertFalse(ok)

    def test_recompressed_png_still_matches(self):
        """The check compares pixels, so another zlib build or level gives the same verdict."""
        out = b"\x89PNG\r\n\x1a\n"
        for k, b in png_chunks(self.png):
            if k == b"IDAT":
                b = zlib.compress(zlib.decompress(b), 1)
            out += struct.pack(">I", len(b)) + k + b + struct.pack(">I", zlib.crc32(k + b) & 0xFFFFFFFF)
        self.assertNotEqual(out, self.png)
        ok, msg = check_png(out, self.card, self.svg)
        self.assertTrue(ok, msg)

    def test_broken_or_unmatched_pngs_are_not_certified(self):
        self.assertFalse(check_png(self.png[:-5], self.card, self.svg)[0])
        self.assertFalse(check_png(b"GIF89a", self.card, self.svg)[0])
        self.assertFalse(check_png(self.png, None, self.svg)[0])
        self.assertFalse(check_png(self.png, {"enabled": False}, self.svg)[0])

    def test_audit_without_sheet_json_does_not_certify_the_png(self):
        with tempfile.TemporaryDirectory() as t:
            for name, data in (("card.svg", self.svg), ("card.png", self.png)):
                with open(os.path.join(t, name), "wb") as f:
                    f.write(data)
            lines = audit_card(t)
            self.assertIn("card.png holds image data only, but there are no card fields", "\n".join(lines))
            self.assertIn("not certified", next(l for l in lines if l.startswith("card.png")))
            self.assertTrue(lines[0].endswith("strings and nothing else:"))
            os.remove(os.path.join(t, "card.svg"))
            lines = audit_card(t)
            self.assertIn("without card.svg", lines[-1])

    def test_audit_lists_the_footer_and_alt_text(self):
        strings = svg_strings(self.svg.decode())
        v = visible(self.card)
        for line in v["footer"]:
            self.assertIn(line, strings)
        self.assertIn(v["alt"], strings)

    def test_build_prints_the_png_what_the_card_shows_and_alt_text(self):
        from tinkerprint.cli import output_lines
        lines = output_lines(self.res)
        self.assertTrue(any(l.startswith("  card ") and l.endswith("card.png  (share this one)") for l in lines))
        self.assertIn("  shows    " + shows(self.card), lines)
        self.assertIn("  alt      " + visible(self.card)["alt"], lines)

    def test_card_off_removes_every_card_file(self):
        with tempfile.TemporaryDirectory() as t:
            out = os.path.join(t, "out")
            for name in ("card.svg", "card.png", "portrait.png", "portrait.gif"):
                os.makedirs(out, exist_ok=True)
                with open(os.path.join(out, name), "wb") as f:
                    f.write(b"old")
            prof = copy.copy(self.prof)
            prof.card_allow = False
            res = build(prof, out, home=os.path.join(self.tmp.name, "data"), today=date(2026, 11, 1))
            for name in ("card.svg", "card.png", "portrait.png", "portrait.gif"):
                self.assertFalse(os.path.exists(os.path.join(out, name)), name)
            from tinkerprint.cli import output_lines
            self.assertIn("  card     off: The profile sets [card] enabled = false.", output_lines(res))


class DemoPrints(unittest.TestCase):
    def test_demo_prints_card_png(self):
        from tinkerprint.cli import main
        with tempfile.TemporaryDirectory() as t:
            buf = io.StringIO()
            with redirect_stdout(buf):
                self.assertEqual(main(["demo", "--out", os.path.join(t, "demo")]), 0)
            text = buf.getvalue()
            self.assertEqual(text.count("card.png  (share this one)"), 2)
            self.assertEqual(text.count("portrait.gif"), 2)
            self.assertEqual(text.count("  alt      tinkerprint card for "), 2)
            for slug in ("wren", "tobi"):
                for name in ("card.png", "portrait.gif"):
                    self.assertTrue(os.path.isfile(os.path.join(t, "demo", slug, name)))


if __name__ == "__main__":
    unittest.main()
