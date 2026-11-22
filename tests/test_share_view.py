"""The sheet's share view: CSS only, and it leaves only what the card shows.
Every name, path and email here is invented."""
import copy
import re
import unittest

import helpers  # noqa: F401
from helpers import commit, edit, profile, run, session
from tinkerprint.render_card import card_strings, visible
from tinkerprint.render_html import CSS, JS, render_html


def sheet_of(**over):
    prof = profile([("Kite", "/w/kite", None)], **over)
    evs = [commit(f"2026-03-{1 + i:02d}T10:00:00+00:00", "/w/kite/app.py" if i % 3 else "/w/kite/tests/test_a.py",
                  h=f"c{i}") for i in range(9)]
    evs += [session("2026-03-02T09:00:00+00:00", "/w/kite"), edit("2026-03-02T09:10:00+00:00", "/w/kite/app.py")]
    return run(prof, evs)[0]


def share_only(page: str) -> str:
    """The text inside every share-only element."""
    out = []
    for m in re.finditer(r'<(div|span) class="[^"]*\bshare-only\b[^"]*">', page):
        depth, i = 1, m.end()
        tag = m.group(1)
        while depth:
            nxt = re.search(rf"<{tag}\b|</{tag}>", page[i:])
            depth += 1 if nxt.group(0) != f"</{tag}>" else -1
            i += nxt.end()
        out.append(page[m.end():i])
    return "\n".join(out)


class ShareView(unittest.TestCase):
    def test_it_is_css_only(self):
        page = render_html(sheet_of())
        self.assertNotIn("share", JS)
        self.assertRegex(page, r'<body>\n<input class="share-toggle" type="checkbox" id="share-view">\n<div class="wrap">')
        self.assertIn('<label class="ghost-btn share-btn" for="share-view">', page)
        self.assertIn(".share-toggle:checked ~ .wrap .private { display: none !important; }", CSS)
        self.assertIn(".share-toggle:focus-visible ~ .wrap .share-btn", CSS)
        # The box stays in the tab order: it is never display:none or visibility:hidden.
        rule = re.search(r"\.share-toggle \{([^}]*)\}", CSS).group(1)
        self.assertNotIn("display", rule)
        self.assertNotIn("visibility", rule)

    def test_everything_below_the_hero_is_private(self):
        page = render_html(sheet_of())
        after = page.split("</section>\n", 1)[1]
        self.assertTrue(after.startswith('<div class="private">\n'))
        for h in ("The build", "Party", "Achievements", "Projects", "Method"):
            self.assertIn(f">{h}</h2>", after)
        head = page.split("</section>\n", 1)[0]
        self.assertIn('<div class="private"><div class="cls-why">', head)
        self.assertRegex(head, r'<div class="private">\s*<div class="next">')
        self.assertRegex(head, r'<dl class="vitals n\d private">')
        self.assertRegex(head, r'<span class="private"> · All history')

    def test_share_view_shows_only_card_strings(self):
        sheet = sheet_of()
        text = re.sub(r"<[^>]+>", " ", share_only(render_html(sheet)))
        allowed = set()
        for _, value in card_strings(sheet["card"]):
            allowed |= set(re.split(r"[\s·,.:%]+", value))
        for word in re.split(r"[\s·,.:%]+", text):
            if word:
                self.assertIn(word, allowed, word)
        for _, p in visible(sheet["card"])["stats"]:
            self.assertIn(p, text)

    def test_handle_replaces_the_name_in_share_view_only(self):
        page = render_html(sheet_of(card={"name": "quillwork"}))
        self.assertIn('<h1><span class="private">Test Person</span><span class="share-only">quillwork</span></h1>',
                      page)
        self.assertIn("<h1>Test Person</h1>", render_html(sheet_of()))

    def test_hidden_party_gets_a_banner_without_familiars(self):
        plain = render_html(sheet_of())
        hidden = render_html(sheet_of(card={"hide": ["party"]}))
        self.assertEqual(plain.count('class="banner'), 1)
        self.assertIn('<div class="banner private">', hidden)
        self.assertIn('<div class="banner share-only">', hidden)
        banners = re.findall(r'<div class="banner[^"]*">(.*?)</div></div>', hidden, re.S)
        self.assertEqual(len(banners), 2)
        self.assertNotEqual(banners[0], banners[1])

    def test_hidden_level_hides_the_seal(self):
        self.assertIn('<div class="seal private">', render_html(sheet_of(card={"hide": ["level"]})))
        self.assertIn('<div class="seal">', render_html(sheet_of()))

    def test_no_card_no_share_view(self):
        page = render_html(sheet_of(card={"enabled": False}))
        self.assertNotIn("share-toggle", page.split("<style>")[0] + page.split("</style>")[1])
        self.assertNotIn('href="card.png"', page)

    def test_sheet_links_to_the_card_files(self):
        page = render_html(sheet_of())
        self.assertIn('<a href="card.png">card.png</a>', page)
        self.assertIn('<a href="card.svg">card.svg</a>', page)
        self.assertIn('<a class="ghost-btn private" href="card.png">card.png</a>', page)


if __name__ == "__main__":
    unittest.main()
