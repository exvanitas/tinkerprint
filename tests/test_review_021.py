"""0.2.0 review, round 2: audit's schema and aliases, the public month, Windows log paths, git
manifests, Antigravity rows, shallow boundaries, damaged history and exact key grammar.
Every name, path and email here is invented."""
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

import helpers  # noqa: F401
from helpers import commit, profile, run
from tinkerprint.art import default_pack
from tinkerprint.audit import audit, schema_problems
from tinkerprint.cli import main
from tinkerprint.look import public_name
from tinkerprint.render_card import portrait_gif, portrait_png, render_card
from tinkerprint.render_card_png import render_card_png


def write_card(out, sheet):
    """sheet.json and every card file, drawn from the sheet's card fields as they are."""
    card = sheet["card"]
    files = {"sheet.json": json.dumps(sheet).encode(), "card.svg": render_card(card, PACK).encode(),
             "card.png": render_card_png(card, PACK), "portrait.png": portrait_png(card, PACK),
             "portrait.gif": portrait_gif(card, PACK)}
    for name, data in files.items():
        with open(os.path.join(out, name), "wb") as f:
            f.write(data)


PACK = default_pack()


class AuditPolicy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.out = os.path.join(self.tmp.name, "out")
        os.makedirs(self.out)
        self.evs = [commit("2026-03-02T10:00:00+00:00", "/w/kite/app.py"),
                    commit("2026-03-03T10:00:00+00:00", "/w/kite/app.py", h="c2")]
        sheet = run(self.prof(), self.evs)[0]
        self.assertIn("projects", sheet["card"])
        write_card(self.out, sheet)

    def tearDown(self):
        self.tmp.cleanup()

    def prof(self):
        return profile([("Kite", "/w/kite", None)], name="Ida Fenwick", card={"show": ["projects"]})

    def sheet(self):
        with open(os.path.join(self.out, "sheet.json"), encoding="utf-8") as f:
            return json.load(f)

    def test_an_empty_profile_is_not_a_missing_one(self):
        err = io.StringIO()
        with redirect_stdout(io.StringIO()), redirect_stderr(err):
            code = main(["audit", "--profile", "", "--out", self.out])
        self.assertNotEqual(code, 0)
        self.assertIn("--profile is empty", err.getvalue())

    def test_a_withdrawn_project_alias_fails(self):
        renamed = self.prof()
        renamed.projects[0].name = "Kestrel"
        lines, clean = audit(self.out, renamed)
        self.assertFalse(clean)
        self.assertIn("projects", lines[-1])

    def test_edited_fields_outside_the_schema_fail_before_any_redraw(self):
        for field, value in (("built", "2026-03-02"), ("built", 202603), ("chart", "pie"),
                             ("stats", [{"stat": "Logic", "pct": 37}]), ("stats", [{"stat": "Secrets", "pct": 50}]),
                             ("stats", [{"stat": "Logic", "pct": 50, "note": "x"}]), ("chart", "bars")):
            sheet = self.sheet()
            if field == "chart" and value == "bars":
                sheet["card"]["stats"] = [{"stat": s, "pct": 20} for s in ("Logic", "Tools", "Docs")]
            sheet["card"][field] = value
            try:
                write_card(self.out, sheet)
            except (KeyError, TypeError, ValueError, AttributeError):
                with open(os.path.join(self.out, "sheet.json"), "w", encoding="utf-8") as f:
                    json.dump(sheet, f)
            self.assertIn(field, schema_problems(sheet["card"]), (field, value))
            for prof in (None, self.prof()):
                lines, clean = audit(self.out, prof)
                self.assertFalse(clean, (field, value))
                self.assertIn("hold what a card may not show", "\n".join(lines))

    def test_a_month_is_fine(self):
        sheet = self.sheet()
        sheet["card"]["built"] = "Mar 2026"
        write_card(self.out, sheet)
        self.assertEqual(schema_problems(sheet["card"]), [])
        self.assertTrue(audit(self.out, self.prof())[1])

    def test_a_saved_name_seeds_the_portrait_as_the_card_clips_it(self):
        card = dict(self.sheet()["card"], name="Ida Fenwick Quillworth-Abernathy")
        clipped = dict(card, name="Ida Fenwick Quillworth…")
        self.assertEqual(portrait_png(card, PACK), portrait_png(clipped, PACK))
        self.assertEqual(portrait_gif(card, PACK), portrait_gif(clipped, PACK))


class PublicMonth(unittest.TestCase):
    def test_a_future_session_outside_every_root_never_sets_the_month(self):
        from datetime import date
        from helpers import session
        from tinkerprint.build import build
        from tinkerprint.events import Inputs
        with tempfile.TemporaryDirectory() as t:
            prof = profile([("Kite", os.path.join(t, "kite"), None)], name="Ida Fenwick")
            evs = [commit("2026-03-02T10:00:00+00:00", os.path.join(t, "kite", "app.py")),
                   session("2027-07-04T10:00:00+00:00", os.path.join(t, "elsewhere"), sid="s9")]
            res = build(prof, os.path.join(t, "out"), home=os.path.join(t, "data"), inputs=Inputs(events=evs),
                        today=date(2026, 11, 23))
            self.assertEqual(res["sheet"]["card"]["built"], "Nov 2026")
            res = build(prof, os.path.join(t, "out"), home=os.path.join(t, "data"), inputs=Inputs(events=evs),
                        as_of=date(2026, 5, 1), today=date(2026, 11, 23))
            self.assertEqual(res["sheet"]["card"]["built"], "May 2026")


class WindowsLogPaths(unittest.TestCase):
    """On Windows rules (ntpath), on any OS."""

    def setUp(self):
        import ntpath
        from unittest import mock
        from tinkerprint.readers import _common
        self.nt = ntpath
        patch = mock.patch.object(_common, "PATHMOD", ntpath)
        patch.start()
        self.addCleanup(patch.stop)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def resolver(self, roots):
        from unittest import mock
        from tinkerprint.projects import Resolver
        prof = profile([("P", "/w", None)])
        prof.projects[0].roots[:] = roots
        res = Resolver(prof.projects, self.nt)
        res._real = mock.Mock(side_effect=self.nt.normpath)
        return res

    def test_a_path_outside_every_root_never_reaches_the_file_system(self):
        res = self.resolver([r"C:\w\kite"])
        for p in (r"Z:\mapped\x.py", r"\\server\share\x.py", r"C:\w\kite2\x.py", r"C:\w\kite\..\other\x.py"):
            self.assertIsNone(res.resolve_root(p), p)
        res._real.assert_not_called()
        self.assertEqual(res.resolve_root(r"c:\W\Kite\a.py")[2], "a.py")
        res._real.assert_called_once()

    def test_device_and_stream_syntax_is_refused(self):
        from tinkerprint.readers._common import local_path
        res = self.resolver([r"C:\work"])
        for p in (r"C:\work\NUL:", r"C:\work\file.txt:stream", r"C:\work\a\CON.txt", r"\\.\C:\work\x",
                  r"\\?\C:\work\x", "//?/C:/work/x", r"\work\x"):
            self.assertEqual(local_path(p, self.nt), "", p)
            self.assertIsNone(res.resolve_root(p), p)
        res._real.assert_not_called()

    def jsonl(self, records):
        path = os.path.join(self.tmp.name, "log.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r) + "\n")
        return path

    def test_a_refused_codex_folder_clears_the_last_one(self):
        from tinkerprint.readers import codex
        local, device = r"C:\w\kite", r"\\.\pipe\x"
        recs = [{"type": "session_meta", "timestamp": "2026-03-02T10:00:00Z", "payload": {"id": "c1", "cwd": local}},
                {"type": "turn_context", "timestamp": "2026-03-02T10:00:01Z", "payload": {"model": "m-1",
                                                                                        "cwd": device}},
                {"type": "event_msg", "timestamp": "2026-03-02T10:00:02Z", "payload": {
                    "type": "patch_apply_end", "success": True, "call_id": "k1", "changes": {"a.py": {}}}},
                {"type": "turn_context", "timestamp": "2026-03-02T10:00:03Z", "payload": {"model": "m-1"}},
                {"type": "event_msg", "timestamp": "2026-03-02T10:00:04Z", "payload": {
                    "type": "patch_apply_end", "success": True, "call_id": "k2", "changes": {"b.py": {}}}}]
        evs = codex.read_file(self.jsonl(recs))
        self.assertEqual(sorted(e.path for e in evs if e.kind == "edit"), ["a.py", "b.py"])  # unassigned

    def test_a_refused_claude_folder_clears_the_last_one(self):
        from tinkerprint.readers import claude
        local, device = r"C:\w\kite", r"C:\w\kite\NUL:"

        def rec(cwd, i, **extra):
            out = [{"type": "assistant", "sessionId": "s1", "timestamp": "2026-03-02T10:01:00Z",
                    "message": {"role": "assistant", "model": "m-1", "content": [
                        {"type": "tool_use", "id": f"t{i}", "name": "Edit", "input": {"file_path": f"f{i}.py"}}]}},
                   {"type": "user", "sessionId": "s1", "timestamp": "2026-03-02T10:01:05Z",
                    "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": f"t{i}"}]}}]
            if cwd is not None:
                out[0]["cwd"] = cwd
            return out
        evs = claude.read_file(self.jsonl(rec(local, 0) + rec(None, 1) + rec(device, 2) + rec(None, 3)))
        self.assertEqual(sorted(e.path for e in evs if e.kind == "edit"),
                         sorted([local + r"\f0.py", local + r"\f1.py", "f2.py", "f3.py"]))


if __name__ == "__main__":
    unittest.main()
