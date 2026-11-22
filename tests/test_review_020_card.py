"""0.2.0 review: the card audit, the card's dates, its seed, the sheet's title and non-Latin names.
Every name, path and email here is invented."""
import io
import json
import os
import struct
import tempfile
import unittest
import zlib
from contextlib import redirect_stdout
from datetime import date

import helpers  # noqa: F401
from helpers import commit, profile, run
from test_card_options import tie_card
from tinkerprint.art import default_pack
from tinkerprint.look import of_sheet
from tinkerprint.audit import audit, check_png, check_portrait_png, png_chunks
from tinkerprint.cli import main
from tinkerprint.render_card import portrait_gif, portrait_png, render_card, visible
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


class SeasonDates(unittest.TestCase):
    def setUp(self):
        self.evs = [commit("2026-03-02T10:00:00+00:00", "/w/kite/app.py")]
        self.season = (date(2026, 2, 3), date(2026, 7, 12))

    def card(self, **extra):
        return run(profile([("Kite", "/w/kite", None)], **extra), self.evs, season=self.season)[0]["card"]

    def test_months_by_default(self):
        card = self.card()
        self.assertEqual(card["season"], "Feb 2026 to Jul 2026")
        svg = render_card(card, PACK)
        self.assertNotIn("Feb 3", svg)
        self.assertNotIn("Jul 12", svg)

    def test_days_when_dates_are_shown(self):
        self.assertEqual(self.card(card={"show": ["dates"]})["season"], "Feb 3, 2026 to Jul 12, 2026")


class Seed(unittest.TestCase):
    def test_hidden_characters_do_not_change_the_art(self):
        evs = [commit("2026-03-02T10:00:00+00:00", "/w/kite/app.py")]
        long_a = "Ida Fenwick Quillworth-Abernathy"
        long_b = "Ida Fenwick Quillworth-Zabriskie"
        cards = [run(profile([("Kite", "/w/kite", None)], name=n), evs)[0] for n in (long_a, long_b)]
        a, b = cards
        self.assertEqual(visible(a["card"])["name"], visible(b["card"])["name"])
        self.assertEqual(a["card"]["name"], visible(a["card"])["name"])
        self.assertEqual(a["look"]["seed"], a["card"]["name"])
        self.assertEqual(a["card"]["look"], b["card"]["look"])
        self.assertEqual(portrait_png(a["card"], PACK), portrait_png(b["card"], PACK))
        self.assertEqual(render_card_png(a["card"], PACK), render_card_png(b["card"], PACK))
        self.assertEqual(of_sheet(a), of_sheet(b))


class StalePolicy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "out")
        os.makedirs(self.out)
        self.evs = [commit("2026-03-02T10:00:00+00:00", "/w/kite/app.py"),
                    commit("2026-03-03T10:00:00+00:00", "/w/kite/app.py", h="c2")]
        self.base = {"name": "Ida Fenwick", "card": {"show": ["projects"]}}
        sheet = run(self.prof(), self.evs)[0]
        self.assertIn("projects", sheet["card"])
        files = {"sheet.json": json.dumps(sheet).encode(), "card.svg": render_card(sheet["card"], PACK).encode(),
                 "card.png": render_card_png(sheet["card"], PACK), "portrait.png": portrait_png(sheet["card"], PACK),
                 "portrait.gif": portrait_gif(sheet["card"], PACK)}
        for name, data in files.items():
            with open(os.path.join(self.out, name), "wb") as f:
                f.write(data)

    def tearDown(self):
        self.tmp.cleanup()

    def prof(self, **change):
        extra = json.loads(json.dumps(self.base))
        for k, v in change.items():
            if k == "card":
                extra["card"] = dict(extra["card"], **v)
            else:
                extra[k] = v
        return profile([("Kite", "/w/kite", None)], **extra)

    def test_the_same_settings_certify(self):
        lines, clean = audit(self.out, self.prof())
        self.assertTrue(clean, lines)

    def test_changed_settings_do_not(self):
        for change, field in (({"card": {"show": []}}, "projects"), ({"card": {"name": "quillwork"}}, "name"),
                              ({"card": {"hide": ["level"]}}, "level"), ({"look": {"skin": "deep"}}, "look"),
                              ({"card": {"hide": ["party"], "show": ["projects", "dates"]}}, "")):
            lines, clean = audit(self.out, self.prof(**change))
            self.assertFalse(clean, change)
            self.assertIn("built with other [card] or [look] settings", lines[-1])
            self.assertIn(field, lines[-1])

    def test_an_unreadable_profile_given_by_name_fails(self):
        missing = os.path.join(self.tmp.name, "missing.toml")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["audit", "--profile", missing, "--out", self.out])
        self.assertEqual(code, 1)
        self.assertIn("The audit fails", buf.getvalue())
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["audit", "--out", self.out]), 0)


if __name__ == "__main__":
    unittest.main()
