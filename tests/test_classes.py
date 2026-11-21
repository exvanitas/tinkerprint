import unittest

import helpers  # noqa: F401
from helpers import commit, profile, run
from tinkerprint.classes import multiclass, raw_class, with_hysteresis

B = "builder"


def shares(**kw):
    base = {s: 0.0 for s in ("Interface", "Logic", "Infra", "Tools", "Data", "Models", "Tests", "Docs")}
    base.update(kw)
    return base


class ClassRules(unittest.TestCase):
    def test_specialist_at_fifty_percent(self):
        c = raw_class(shares(Logic=0.5, Interface=0.3, Tests=0.2), B)
        self.assertEqual((c["kind"], c["stats"], c["name"]), ("specialist", ["Logic"], "Sage"))
        c = raw_class(shares(Logic=0.49, Interface=0.31, Tests=0.2), B)
        self.assertEqual(c["kind"], "pair")

    def test_generalist_when_no_stat_over_twenty(self):
        c = raw_class(shares(Logic=0.2, Interface=0.2, Tests=0.2, Docs=0.2, Infra=0.2), B)
        self.assertEqual((c["kind"], c["name"]), ("generalist", "Adventurer"))
        c = raw_class(shares(Logic=0.21, Interface=0.2, Tests=0.2, Docs=0.2, Infra=0.19), B)
        self.assertEqual(c["kind"], "pair")

    def test_runner_up_threshold(self):
        c = raw_class(shares(Logic=0.45, Interface=0.10, Tests=0.10, Docs=0.10, Infra=0.10, Data=0.10, Tools=0.05), B)
        self.assertEqual((c["kind"], c["stats"]), ("pair", ["Interface", "Logic"]))
        c = raw_class(shares(Logic=0.46, Interface=0.09, Tests=0.09, Docs=0.09, Infra=0.09, Data=0.09, Tools=0.09), B)
        self.assertEqual((c["kind"], c["stats"]), ("specialist", ["Logic"]))

    def test_multiclass_threshold(self):
        s = shares(Logic=0.4, Interface=0.3, Tests=0.15, Docs=0.15)
        m = multiclass(s, B, raw_class(s, B))
        self.assertEqual((m["stats"], m["name"]), (["Tests", "Docs"], "Arbiter"))
        s = shares(Logic=0.4, Interface=0.3, Tests=0.21, Docs=0.09)
        self.assertIsNone(multiclass(s, B, raw_class(s, B)))

    def test_tie_order_follows_the_set(self):
        c = raw_class(shares(Logic=0.4, Tests=0.2, Interface=0.2, Docs=0.2), B)
        self.assertEqual(c["stats"], ["Interface", "Logic"])
        c = raw_class(shares(Tests=0.4, Logic=0.4, Docs=0.2), B)
        self.assertEqual(c["stats"], ["Logic", "Tests"])

    def test_two_point_hysteresis(self):
        prev = {"kind": "pair", "stats": ["Interface", "Logic"], "name": "Spellblade"}
        held = shares(Logic=0.30, Tests=0.21, Interface=0.20, Docs=0.15, Infra=0.14)
        new = raw_class(held, B)
        self.assertEqual(new["stats"], ["Logic", "Tests"])
        cls, was_held = with_hysteresis(new, prev, held, B)
        self.assertTrue(was_held)
        self.assertEqual(cls["name"], "Spellblade")
        moved = shares(Logic=0.30, Tests=0.23, Interface=0.20, Docs=0.14, Infra=0.13)
        cls, was_held = with_hysteresis(raw_class(moved, B), prev, moved, B)
        self.assertFalse(was_held)
        self.assertEqual(cls["stats"], ["Logic", "Tests"])

    def test_hysteresis_on_specialist_threshold(self):
        prev = {"kind": "specialist", "stats": ["Logic"], "name": "Sage"}
        s = shares(Logic=0.49, Interface=0.3, Tests=0.21)
        self.assertTrue(with_hysteresis(raw_class(s, B), prev, s, B)[1])
        s = shares(Logic=0.47, Interface=0.3, Tests=0.23)
        self.assertFalse(with_hysteresis(raw_class(s, B), prev, s, B)[1])

    def test_finish_applies_hysteresis_and_new_class(self):
        prof = profile([("A", "/w/a", None)])
        ts = "2026-03-02T10:00:00+00:00"
        sheet, _ = run(prof, [commit(ts, "/w/a/x.py")])
        self.assertEqual(sheet["class"]["name"], "Sage")
        prev = dict(sheet, **{"class": {"kind": "specialist", "stats": ["Docs"], "name": "Scribe"}})
        new, _ = run(prof, [commit(ts, "/w/a/x.py")], prev=prev)
        self.assertEqual(new["class"]["name"], "Sage")
        self.assertIn("new-class", [a["id"] for a in new["achievements"]])
        self.assertEqual(new["changes"]["class_from"], "Scribe")


if __name__ == "__main__":
    unittest.main()
