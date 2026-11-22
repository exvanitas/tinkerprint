"""Card options, ties, the footer and alt text. Every name, path and email here is invented."""
import copy
import os
import re
import tempfile
import unittest
from datetime import date

import helpers  # noqa: F401
from helpers import commit, profile, run
from tinkerprint.build import build
from tinkerprint.demo import TOBI, make_person
from tinkerprint.profile import ProfileError, load_profile, parse_profile
from tinkerprint.render_card import alt_text, card_strings, render_card, shows, visible

BASE = {"name": "Pip Quill", "identity": {"emails": ["pip@quill.example.test"]},
        "project": [{"name": "Kite", "root": "/w/kite"}]}


def parse(**over):
    data = copy.deepcopy(BASE)
    data.update(over)
    return parse_profile(data, "/nonexistent-base")


def card_of(**over) -> dict:
    """A small card from a scored sheet: Logic and Tests, Kite's commits."""
    prof = profile([("Kite", "/w/kite", None)], **over)
    evs = [commit(f"2026-03-{1 + i:02d}T10:00:00+00:00", "/w/kite/app.py" if i % 3 else "/w/kite/tests/test_a.py",
                  h=f"c{i}") for i in range(9)]
    return run(prof, evs)[0]["card"]


def tie_card() -> dict:
    """Tobi's tie: Tests and Infra both round to 10%, and the multiclass is named for Tests."""
    pcts = {"Interface": 15, "Logic": 35, "Data": 20, "Infra": 10, "Tools": 5, "Models": 0, "Tests": 10, "Docs": 5}
    return {"enabled": True, "name": "Tobi Marsh", "set": "Builder", "class": "Alchemist", "multiclass": "Duelist",
            "named": ["Logic", "Data", "Interface", "Tests"], "level": 15, "days": {"active": 237, "classified": 237},
            "stats": [{"stat": s, "pct": p} for s, p in pcts.items()], "achievements": [], "party": ["Codex"],
            "chart": "radar", "method": 3, "built": "Nov 2026", "season": ""}


class CardOptions(unittest.TestCase):
    def test_enabled_defaults_by_profile_kind(self):
        self.assertTrue(parse().card_enabled)
        self.assertFalse(parse(work=True).card_enabled)

    def test_enabled_works_on_every_profile(self):
        self.assertFalse(parse(card={"enabled": False}).card_enabled)
        self.assertTrue(parse(work=True, card={"enabled": True}).card_enabled)

    def test_allow_still_works_on_work_profiles(self):
        self.assertTrue(parse(work=True, card={"allow": True}).card_enabled)
        self.assertFalse(parse(work=True, card={"allow": False}).card_enabled)

    def test_enabled_and_allow_must_agree(self):
        with self.assertRaises(ProfileError) as cm:
            parse(card={"enabled": True, "allow": False})
        self.assertIn("disagree", str(cm.exception))
        self.assertTrue(parse(work=True, card={"enabled": True, "allow": True}).card_enabled)

    def test_enabled_needs_a_boolean(self):
        with self.assertRaises(ProfileError):
            parse(card={"enabled": "yes"})

    def test_unknown_hide_and_show_values_suggest_the_right_one(self):
        for over, bad, good in (({"hide": ["partty"]}, "partty", "party"), ({"hide": ["levle"]}, "levle", "level"),
                                ({"show": ["date"]}, "date", "dates")):
            with self.assertRaises(ProfileError) as cm:
                parse(card=over)
            self.assertIn(repr(bad), str(cm.exception))
            self.assertIn(f"Did you mean {good!r}", str(cm.exception))

    def test_unknown_card_key_suggests_the_right_one(self):
        with self.assertRaises(ProfileError) as cm:
            parse(card={"hdie": ["party"]})
        self.assertIn("Did you mean 'hide'", str(cm.exception))

    def test_name_must_be_a_handle(self):
        for bad in ("", "   ", "a\nb", 3):
            with self.assertRaises(ProfileError, msg=repr(bad)):
                parse(card={"name": bad})
        self.assertEqual(parse(card={"name": " quillwork "}).card_name, "quillwork")

    def test_handle_goes_on_the_card_and_the_sheet_keeps_the_profile_name(self):
        prof = profile([("Kite", "/w/kite", None)], card={"name": "quillwork"})
        sheet = run(prof, [commit("2026-03-01T10:00:00+00:00", "/w/kite/app.py")])[0]
        self.assertEqual(sheet["card"]["name"], "quillwork")
        self.assertEqual(sheet["profile"]["name"], "Test Person")
        svg = render_card(sheet["card"])
        self.assertIn("quillwork", svg)
        self.assertNotIn("Test Person", svg)

    def test_hide_leaves_each_field_out_of_the_card_fields(self):
        full = card_of()
        self.assertTrue({"level", "days", "achievements", "party"} <= set(full))
        for hidden, keys in (("party", {"party"}), ("level", {"level", "days"}), ("achievements", {"achievements"})):
            card = card_of(card={"hide": [hidden]})
            self.assertFalse(keys & set(card), hidden)
        none = card_of(card={"hide": ["party", "level", "achievements"]})
        v = visible(none)
        self.assertEqual((v["level"], v["party"], v["achievements"], v["members"]), ("", "", [], []))

    def test_hidden_level_drops_the_seal_and_the_day_count(self):
        sheet_card = tie_card()
        del sheet_card["level"]
        svg = render_card(sheet_card)
        self.assertNotIn("LEVEL", svg)
        self.assertNotIn("url(#seal)", svg)
        self.assertNotIn("237", svg)
        self.assertNotIn("Level grows", svg)
        self.assertIn("Shares are of classified activity.", svg)

    def test_hidden_party_draws_no_familiars(self):
        card = tie_card()
        with_party = render_card(card)
        card.pop("party")
        without = render_card(card)
        self.assertNotIn("PARTY", without)
        art_of = lambda svg: re.search(r'<g shape-rendering="crispEdges">(.*?)</g>', svg).group(1)
        self.assertNotEqual(art_of(with_party), art_of(without))
        self.assertNotIn("Party", visible(card)["alt"])

    def test_off_reasons(self):
        prof = profile([("Kite", "/w/kite", None)], card={"enabled": False})
        card = run(prof, [commit("2026-03-01T10:00:00+00:00", "/w/kite/app.py")])[0]["card"]
        self.assertEqual(card, {"enabled": False, "reason": "The profile sets [card] enabled = false."})
        work = profile([("Kite", "/w/kite", None)], work=True)
        card = run(work, [commit("2026-03-01T10:00:00+00:00", "/w/kite/app.py")])[0]["card"]
        self.assertIn("[card] enabled = true", card["reason"])
        self.assertEqual(shows(card), "nothing: the card is off")


class Ties(unittest.TestCase):
    def test_a_tie_never_hides_a_named_stat(self):
        v = visible(tie_card())
        self.assertEqual([s for s, _ in v["stats"]], ["Logic", "Data", "Interface", "Tests"])

    def test_without_named_stats_the_set_order_breaks_ties(self):
        card = tie_card()
        card["named"] = []
        self.assertEqual([s for s, _ in visible(card)["stats"]], ["Logic", "Data", "Interface", "Infra"])

    def test_the_demo_card_shows_both_multiclass_stats(self):
        with tempfile.TemporaryDirectory() as t:
            prof = load_profile(make_person(os.path.join(t, "w"), TOBI))
            sheet = build(prof, os.path.join(t, "out"), home=os.path.join(t, "data"), today=date(2026, 11, 1))["sheet"]
        shown = [s for s, _ in visible(sheet["card"])["stats"]]
        for stat in sheet["class"]["stats"] + (sheet["multiclass"] or {}).get("stats", []):
            self.assertIn(stat, shown)


class FooterAndAlt(unittest.TestCase):
    def test_footer_says_what_the_card_is(self):
        top, meaning = visible(tie_card())["footer"]
        self.assertEqual(top, "tinkerprint · method 3 · Nov 2026")
        self.assertEqual(meaning, "Shares are of classified activity on 237 active days. Level grows with active days.")
        svg = render_card(tie_card())
        self.assertIn(">tinkerprint · method 3 · Nov 2026</text>", svg)

    def test_footer_counts_unclassified_days(self):
        card = dict(tie_card(), days={"active": 10, "classified": 1})
        self.assertIn("on 1 of 10 active days.", visible(card)["footer"][1])
        card = dict(tie_card(), days={"active": 1, "classified": 1})
        self.assertIn("on 1 active day.", visible(card)["footer"][1])

    def test_a_season_build_says_its_season(self):
        prof = profile([("Kite", "/w/kite", None)])
        evs = [commit("2026-03-02T10:00:00+00:00", "/w/kite/app.py")]
        card = run(prof, evs, season=(date(2026, 1, 1), date(2026, 6, 30)))[0]["card"]
        self.assertEqual(card["season"], "Jan 1, 2026 to Jun 30, 2026")
        self.assertIn("season Jan 1, 2026 to Jun 30, 2026", visible(card)["footer"][0])
        self.assertEqual(run(prof, evs)[0]["card"]["season"], "")
        self.assertIn("season from Jan 1, 2026",
                      visible(run(prof, evs, season=(date(2026, 1, 1), None))[0]["card"])["footer"][0])

    def test_multiclass_has_a_label(self):
        svg = render_card(tie_card())
        self.assertIn(">MULTICLASS</text>", svg)
        self.assertNotIn("/ Duelist", svg)
        self.assertEqual(visible(tie_card())["multiclass"], "Duelist")

    def test_alt_text_is_the_accessible_name_and_title(self):
        card = tie_card()
        v = visible(card)
        self.assertEqual(v["alt"], "tinkerprint card for Tobi Marsh, Builder set: Alchemist, multiclass Duelist, "
                                   "level 15. Top stats Logic 35%, Data 20%, Interface 15%, Tests 10%. Party Codex.")
        svg = render_card(card)
        self.assertIn(f'aria-label="{v["alt"]}"', svg)
        self.assertIn(f"<title>{v['alt']}</title>", svg)
        self.assertIn(("alt", v["alt"]), card_strings(card))

    def test_alt_text_reads_only_visible_fields(self):
        card = tie_card()
        card["projects"] = ["Secret Kite"]
        self.assertEqual(visible(card)["alt"], visible(tie_card())["alt"])
        self.assertEqual(alt_text(visible(card), "Builder"), visible(card)["alt"])

    def test_shows_line_lists_each_drawn_field(self):
        line = shows(tie_card())
        self.assertEqual(line, 'name "Tobi Marsh", set, class, multiclass, level and active days, 4 top stats, '
                               "radar of rounded shares, party (Codex), portrait, footer")
        card = dict(tie_card(), achievements=[{"title": "Founder", "when": "Sep 2025"}])
        self.assertIn("1 achievement with months", shows(card))
        card = dict(tie_card(), achievements=[{"title": "Founder", "when": "Sep 3, 2025"}])
        self.assertIn("1 achievement with dates", shows(card))


if __name__ == "__main__":
    unittest.main()
