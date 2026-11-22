"""audit's exit code: 0 only when every card file is there and certified. Everything here is invented."""
import copy
import io
import os
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date

import helpers  # noqa: F401
from tinkerprint.audit import audit
from tinkerprint.build import build
from tinkerprint.cli import main
from tinkerprint.demo import WREN, make_person
from tinkerprint.profile import load_profile

CARD_FILES = ("card.svg", "card.png", "portrait.png", "portrait.gif")


class AuditExit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.path = make_person(os.path.join(cls.tmp.name, "w"), WREN)
        cls.prof = load_profile(cls.path)
        cls.built = os.path.join(cls.tmp.name, "built")
        build(cls.prof, cls.built, home=os.path.join(cls.tmp.name, "data"), today=date(2026, 11, 1))
        # The same person under another card name: well-formed files that draw other card fields.
        cls.other = os.path.join(cls.tmp.name, "other")
        prof = copy.copy(cls.prof)
        prof.card_name = "Rae Quill"
        build(prof, cls.other, home=os.path.join(cls.tmp.name, "data2"), today=date(2026, 11, 1))

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.t.name, "out")
        shutil.copytree(self.built, self.out)

    def tearDown(self):
        self.t.cleanup()

    def cli(self, *extra):
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["audit", "--out", self.out, *extra])
        return code, buf.getvalue()

    def test_a_clean_audit_exits_0(self):
        code, text = self.cli()
        self.assertEqual(code, 0, text)
        self.assertTrue(audit(self.out, self.prof)[1])
        self.assertNotIn("not certified", text)

    def test_each_missing_card_file_exits_1(self):
        for name in CARD_FILES:
            with self.subTest(name=name):
                self.setUp()
                os.remove(os.path.join(self.out, name))
                code, text = self.cli()
                self.assertEqual(code, 1, name)
                self.assertIn(f"No {name} in", text)
                self.tearDown()

    def test_each_malformed_card_file_exits_1(self):
        for name in CARD_FILES:
            with self.subTest(name=name):
                self.setUp()
                with open(os.path.join(self.out, name), "r+b") as f:
                    data = f.read()
                    f.seek(0)
                    f.write(data[: len(data) // 2])
                    f.truncate()
                code, text = self.cli()
                self.assertEqual(code, 1, name)
                self.assertIn("not", text)
                self.tearDown()

    def test_each_uncertified_card_file_exits_1(self):
        """Well-formed files that draw something other than the card fields in sheet.json."""
        for name in CARD_FILES:
            with self.subTest(name=name):
                self.setUp()
                shutil.copy(os.path.join(self.other, name), os.path.join(self.out, name))
                code, text = self.cli()
                self.assertEqual(code, 1, name)
                self.assertIn("not certified", text)
                self.tearDown()

    def test_no_card_fields_or_a_card_the_profile_forbids_exits_1(self):
        os.remove(os.path.join(self.out, "sheet.json"))
        self.assertEqual(self.cli()[0], 1)
        self.setUp()
        prof = copy.copy(self.prof)
        prof.card_allow = False
        lines, clean = audit(self.out, prof)
        self.assertFalse(clean)
        self.assertIn("no longer allows a card", lines[-1])


if __name__ == "__main__":
    unittest.main()
