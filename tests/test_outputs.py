"""End to end: privacy of the card and audit, determinism, the no-network rule and the demo."""
import ast
import io
import os
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date

import helpers  # noqa: F401
from tinkerprint.audit import audit_card, svg_strings
from tinkerprint.build import build, compute
from tinkerprint.demo import TOBI, WREN, make_person
from tinkerprint.profile import load_profile
from tinkerprint.render_card import card_strings

SRC = helpers.SRC


class Built(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.world = os.path.join(cls.tmp.name, "world")
        cls.profiles = {p.slug: load_profile(make_person(cls.world, p)) for p in (WREN, TOBI)}
        cls.out = {}
        for slug, prof in cls.profiles.items():
            home = os.path.join(cls.tmp.name, "data", slug)
            dest = os.path.join(cls.tmp.name, "out", slug)
            build(prof, dest, as_of=date(2026, 9, 15), home=home, built_at="t")
            cls.out[slug] = build(prof, dest, home=home, built_at="t")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def distinctive(self, slug):
        """Folder names, roots, emails and project names of the fixture."""
        person = WREN if slug == "wren" else TOBI
        words = [person.email, self.world, "example.test"]
        for p in person.projects:
            words += [p.folder, p.name]
        return words

    def test_card_and_audit_hold_no_project_names_paths_or_emails(self):
        for slug, res in self.out.items():
            with open(res["paths"]["card"], encoding="utf-8") as f:
                svg = f.read()
            lines = "\n".join(audit_card(os.path.dirname(res["paths"]["card"]), self.profiles[slug]))
            for word in self.distinctive(slug):
                self.assertNotIn(word, svg, (slug, word))
                self.assertNotIn(word, lines, (slug, word))
            self.assertIn(self.profiles[slug].name, lines)

    def test_card_draws_only_allowlisted_strings(self):
        from html import unescape
        split = re.compile(r"[\s·/%…]+")
        for slug, res in self.out.items():
            with open(res["paths"]["card"], encoding="utf-8") as f:
                svg = f.read()
            allowed = {"SET", "LEVEL", "ACHIEVEMENTS", "PARTY"}
            for _, v in card_strings(res["sheet"]["card"]):
                allowed |= {w for w in split.split(v) if w} | {w.upper() for w in split.split(v) if w}
            for t in re.findall(r">([^<>]+)</text>", svg):
                for word in split.split(unescape(t)):
                    if word:
                        self.assertIn(word, allowed, (slug, t))

    def test_sheet_json_and_html_hold_no_paths_or_emails(self):
        for slug, res in self.out.items():
            for kind in ("json", "html"):
                with open(res["paths"][kind], encoding="utf-8") as f:
                    text = f.read()
                for word in (self.world, "example.test", "/code/"):
                    self.assertNotIn(word, text, (slug, kind, word))
                self.assertNotIn("Invented", text)

    def test_cache_keeps_no_message_text(self):
        for slug in self.out:
            cache = os.path.join(self.tmp.name, "data", slug, "cache")
            for name in os.listdir(cache):
                with open(os.path.join(cache, name), encoding="utf-8") as f:
                    self.assertNotIn("Invented", f.read())

    def test_two_builds_give_identical_sheet_json(self):
        for slug, prof in self.profiles.items():
            home = os.path.join(self.tmp.name, "data", slug)
            dest = os.path.join(self.tmp.name, "again", slug)
            again = build(prof, dest, home=home, built_at="other time")
            with open(self.out[slug]["paths"]["json"], "rb") as a, open(again["paths"]["json"], "rb") as b:
                self.assertEqual(a.read(), b.read())
            fresh = os.path.join(self.tmp.name, "fresh", slug)
            first = build(prof, os.path.join(fresh, "o1"), home=fresh)
            second = build(prof, os.path.join(fresh, "o2"), home=fresh)
            with open(first["paths"]["json"], "rb") as a, open(second["paths"]["json"], "rb") as b:
                self.assertEqual(a.read(), b.read())

    def test_what_changed_comes_from_the_earlier_sheet(self):
        ch = self.out["tobi"]["changes"]
        self.assertEqual(ch["against"], "2026-09-15")
        self.assertGreater(ch["points_since"], 0)

    def test_builder_demo_lights_five_stats(self):
        sheet = self.out["tobi"]["sheet"]
        lit = [r["key"] for r in sheet["stats"] if r["points"] > 0]
        self.assertGreaterEqual(len(lit), 5, lit)
        self.assertEqual(sheet["profile"]["set"], "builder")

    def test_work_profile_without_allow_makes_no_card(self):
        prof = self.profiles["tobi"]
        prof.card_allow = False
        try:
            sheet = compute(prof, home=os.path.join(self.tmp.name, "data", "tobi"))[0]
        finally:
            prof.card_allow = True
        self.assertEqual(set(sheet["card"]), {"enabled", "reason"})
        self.assertEqual(card_strings(sheet["card"]), [])

    def test_html_page_contract(self):
        with open(self.out["wren"]["paths"]["html"], encoding="utf-8") as f:
            page = f.read()
        self.assertIn("default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:", page)
        self.assertNotRegex(page, r"(?i)(src|href)=\"https?:")
        self.assertIn("Method version 2", page)
        self.assertIn("What changed", page)
        self.assertIn('class="radar"', page)

    def test_cli_audit_prints_card_strings(self):
        from tinkerprint.cli import main
        prof_path = os.path.join(self.world, "wren", "profile.toml")
        buf = io.StringIO()
        with redirect_stdout(buf):
            code = main(["audit", "--profile", prof_path, "--out", os.path.join(self.tmp.name, "out", "wren")])
        self.assertEqual(code, 0)
        self.assertIn("Wren Aldous", buf.getvalue())
        for word in self.distinctive("wren"):
            self.assertNotIn(word, buf.getvalue())


class NoNetwork(unittest.TestCase):
    BANNED = {"urllib", "http", "socket", "requests", "ssl", "ftplib", "smtplib", "xmlrpc", "asyncio", "xml"}

    def test_no_network_imports_in_source(self):
        for dirpath, _, files in os.walk(os.path.join(SRC, "tinkerprint")):
            for name in files:
                if not name.endswith(".py"):
                    continue
                path = os.path.join(dirpath, name)
                with open(path, encoding="utf-8") as f:
                    tree = ast.parse(f.read(), path)
                for node in ast.walk(tree):
                    mods = []
                    if isinstance(node, ast.Import):
                        mods = [a.name for a in node.names]
                    elif isinstance(node, ast.ImportFrom) and node.level == 0:
                        mods = [node.module or ""]
                    for m in mods:
                        self.assertNotIn(m.split(".")[0], self.BANNED, f"{path} imports {m}")

    def test_no_network_modules_loaded_at_runtime(self):
        code = ("import sys, pkgutil, importlib, tinkerprint\n"
                "for m in pkgutil.walk_packages(tinkerprint.__path__, 'tinkerprint.'):\n"
                "    if m.name != 'tinkerprint.__main__': importlib.import_module(m.name)\n"
                "bad = sorted(n for n in sys.modules if n.split('.')[0] in ('socket','ssl','http','urllib','requests'))\n"
                "print(','.join(bad))\n")
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                             env=dict(os.environ, PYTHONPATH=SRC), check=True)
        self.assertEqual(out.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
