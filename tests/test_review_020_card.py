"""0.2.0 review: the card audit, the card's dates, its seed, the sheet's title and non-Latin names.
Every name, path and email here is invented."""
import struct
import unittest
import zlib

import helpers  # noqa: F401
from test_card_options import tie_card
from tinkerprint.art import default_pack
from tinkerprint.audit import check_png, check_portrait_png, png_chunks
from tinkerprint.render_card import portrait_png, render_card
from tinkerprint.render_card_png import render_card_png

PACK = default_pack()


def _chunk(kind: bytes, body: bytes) -> bytes:
    return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body) & 0xFFFFFFFF)


def _rebuild(data: bytes, edit) -> bytes:
    """data with each (kind, body) chunk replaced by edit(kind, body)."""
    out = b"\x89PNG\r\n\x1a\n"
    for k, b in png_chunks(data):
        out += _chunk(k, edit(k, b))
    return out


def _hidden(data: bytes) -> list:
    """Two copies of data that hide text where the old pixel check never looked."""
    in_iend = _rebuild(data, lambda k, b: b + b"Ida Fenwick, ida@fenwick.example.test" if k == b"IEND" else b)
    idat = [b for k, b in png_chunks(data) if k == b"IDAT"]
    last = len(idat) - 1
    seen = []

    def after_stream(k, b):
        if k != b"IDAT":
            return b
        seen.append(b)
        return b + b"private project names" if len(seen) - 1 == last else b
    return [in_iend, _rebuild(data, after_stream)]


class PngBytes(unittest.TestCase):
    def setUp(self):
        self.card = tie_card()
        self.svg = render_card(self.card, PACK).encode("utf-8")

    def test_card_png_with_hidden_bytes_is_not_certified(self):
        png = render_card_png(self.card, PACK)
        self.assertTrue(check_png(png, self.card, self.svg, PACK)[0])
        for bad in _hidden(png):
            self.assertNotEqual(bad, png)
            ok, msg = check_png(bad, self.card, self.svg, PACK)
            self.assertFalse(ok, msg)

    def test_portrait_png_with_hidden_bytes_is_not_certified(self):
        png = portrait_png(self.card, PACK)
        self.assertTrue(check_portrait_png(png, self.card, PACK)[0])
        for bad in _hidden(png):
            ok, msg = check_portrait_png(bad, self.card, PACK)
            self.assertFalse(ok, msg)


if __name__ == "__main__":
    unittest.main()
