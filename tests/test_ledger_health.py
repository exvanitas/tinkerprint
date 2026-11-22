"""Kept history from deleted logs, and reader health. Every name, path and email here is invented."""
import io
import json
import os
import random
import sqlite3
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
from tinkerprint.build import CACHE_VERSION, _cached, build, health_lines, health_warnings, new_report
from tinkerprint.cli import main
from tinkerprint.demo import RepoWriter, write_agy_db, write_claude_session, write_codex_session
from tinkerprint.events import Inputs
from tinkerprint.profile import load_profile
from tinkerprint.readers import agy, claude, codex

UTC = ZoneInfo("UTC")
ME = ("Ida Fenwick", "ida@fenwick.example.test")


def lines(path, records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")
    return path


def claude_lines(sid, n_tools=0, tool="Bash", version="2.1.4", day="2026-03-02"):
    out = [{"type": "user", "sessionId": sid, "timestamp": f"{day}T10:00:00Z", "cwd": "/w/a", "version": version,
            "message": {"role": "user", "content": "invented"}}]
    for i in range(n_tools):
        out.append({"type": "assistant", "sessionId": sid, "timestamp": f"{day}T10:01:00Z", "cwd": "/w/a",
                    "version": version, "message": {"role": "assistant", "model": "m-1", "content": [
                        {"type": "tool_use", "id": f"t{i}", "name": tool, "input": {"file_path": "/w/a/x.py"}}]}})
        out.append({"type": "user", "sessionId": sid, "timestamp": f"{day}T10:01:05Z", "cwd": "/w/a",
                    "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": f"t{i}"}]}})
    return out


class Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = os.path.realpath(self.tmp.name)
        self.base = os.path.join(self.t, "logs")
        self.cache = os.path.join(self.t, "data", "cache", "claude.json")

    def tearDown(self):
        self.tmp.cleanup()

    def file(self, name, records):
        return lines(os.path.join(self.base, "proj", name), records)

    def read(self, files, base=None):
        rep = new_report()
        evs = _cached(files, claude.read_file, self.cache, self.base if base is None else base, rep)
        return evs, rep

    def entries(self):
        with open(self.cache, encoding="utf-8") as f:
            return json.load(f)["files"]


class KeptHistory(Tmp):
    def test_events_of_a_deleted_log_still_count(self):
        a = self.file("a.jsonl", claude_lines("sa", 1, "Edit"))
        b = self.file("b.jsonl", claude_lines("sb", 1, "Edit", day="2026-03-03"))
        first, _ = self.read([a, b])
        os.remove(b)
        again, rep = self.read([a])
        self.assertEqual(sorted(first), sorted(again))
        self.assertEqual((rep["seen"], rep["read"], rep["kept_files"], rep["kept_sessions"]), (1, 1, 1, 1))
        self.assertEqual((rep["sessions"], rep["edits"]), (1, 1))
        self.assertTrue(self.entries()[b]["gone"])
        self.assertNotIn("gone", self.entries()[a])
        # Kept across builds, not only the first one after the deletion.
        third, rep = self.read([a])
        self.assertEqual(sorted(first), sorted(third))
        self.assertEqual(rep["kept_sessions"], 1)

    def test_a_log_that_comes_back_is_read_as_now(self):
        b = self.file("b.jsonl", claude_lines("sb", 1, "Edit"))
        self.read([b])
        os.remove(b)
        self.read([])
        self.file("b.jsonl", claude_lines("sb2", 0))
        evs, rep = self.read([b])
        self.assertEqual({e.session for e in evs}, {"sb2"})
        self.assertEqual((rep["kept_files"], rep["kept_sessions"]), (0, 0))
        self.assertNotIn("gone", self.entries()[b])

    def test_same_bytes_back_reuse_the_entry(self):
        b = self.file("b.jsonl", claude_lines("sb", 1, "Edit"))
        first, _ = self.read([b])
        with open(b, "rb") as f:
            raw = f.read()
        os.remove(b)
        self.read([])
        with open(b, "wb") as f:
            f.write(raw)
        again, rep = self.read([b])
        self.assertEqual(sorted(first), sorted(again))
        self.assertEqual((rep["read"], rep["kept_files"]), (1, 0))

    def test_an_unreadable_listed_log_keeps_its_events(self):
        a = self.file("a.jsonl", claude_lines("sa", 1, "Edit"))
        first, _ = self.read([a])
        os.remove(a)
        evs, rep = self.read([a])  # still listed, but stat fails
        self.assertEqual(sorted(first), sorted(evs))
        self.assertEqual((rep["seen"], rep["read"], rep["kept_files"]), (1, 0, 1))

    def test_another_folders_entries_stay_but_do_not_count(self):
        a = self.file("a.jsonl", claude_lines("sa", 1, "Edit"))
        self.read([a])
        other = os.path.join(self.t, "other-logs")
        evs, rep = self.read([], base=other)
        self.assertEqual((evs, rep["kept_files"]), ([], 0))
        self.assertIn(a, self.entries())
        evs, _ = self.read([a])
        self.assertTrue(evs)

    def test_a_version_change_keeps_only_gone_entries(self):
        a = self.file("a.jsonl", claude_lines("sa", 1, "Edit"))
        gone = os.path.join(self.base, "proj", "gone.jsonl")
        os.makedirs(os.path.dirname(self.cache))
        kept_event = {"ts": "2025-01-05T10:00:00+00:00", "source": "claude", "kind": "session", "path": "/w/a",
                      "session": "old", "harness": "claude", "actor": "agent"}
        stale = {"stat": None, "sha256": "0" * 64, "size": 1, "events": [dict(kept_event, session="stale")],
                 "health": {}}
        with open(self.cache, "w", encoding="utf-8") as f:
            json.dump({"v": 3, "files": {
                a: stale, gone: {"gone": True, "stat": None, "sha256": "1" * 64, "size": 1,
                                 "events": [kept_event], "health": {}}}}, f)
        evs, rep = self.read([a])
        self.assertEqual({e.session for e in evs}, {"sa", "old"})
        self.assertEqual(rep["kept_files"], 1)


class KeptHistoryBuild(Tmp):
    def setUp(self):
        super().setUp()
        self.root = os.path.join(self.t, "repo")
        r = RepoWriter(self.root)
        r.touch(datetime(2026, 3, 2, 10, tzinfo=UTC), ME, {"a.py": 2})
        r.write()
        rng = random.Random(4)
        self.logs = []
        for d in range(3):
            when = datetime(2026, 4, 1 + d, 10, tzinfo=UTC)
            sid = write_claude_session(self.base, self.root, when, "model-x",
                                       [(when + timedelta(minutes=5), os.path.join(self.root, "a.py"), "Edit")], rng)
            self.logs.append(sid)
        self.prof_path = os.path.join(self.t, "p.toml")
        with open(self.prof_path, "w", encoding="utf-8") as f:
            f.write(f'name = "Ida"\n[identity]\nemails = ["{ME[1]}"]\n[harnesses]\nclaude = true\ncodex = false\n'
                    f'claude_dir = "{self.base}"\n[[project]]\nname = "P"\nroot = "{self.root}"\n')

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        self.assertEqual(code, 0, err.getvalue())
        return out.getvalue()

    def build(self, out):
        return self.cli("build", "--profile", self.prof_path, "--data-dir", os.path.join(self.t, "data"),
                        "--out", os.path.join(self.t, out))

    def sheet(self, out):
        with open(os.path.join(self.t, out, "sheet.json"), encoding="utf-8") as f:
            return json.load(f)

    def delete_logs(self):
        for dirpath, _, names in os.walk(self.base):
            for n in names:
                os.remove(os.path.join(dirpath, n))

    def test_sheet_keeps_its_days_after_the_logs_are_deleted(self):
        self.build("o1")
        before = self.sheet("o1")
        self.assertEqual(before["history"]["active_days"], 4)
        self.delete_logs()
        text = self.build("o2")
        after = self.sheet("o2")
        self.assertEqual(after["history"], before["history"])
        self.assertEqual(after["party"], before["party"])
        self.assertIn("Plus 3 sessions kept from logs that are gone.", text)
        # Same logs plus the same kept history give the same sheet.
        self.build("o3")
        with open(os.path.join(self.t, "o2", "sheet.json"), "rb") as a, \
                open(os.path.join(self.t, "o3", "sheet.json"), "rb") as b:
            self.assertEqual(a.read(), b.read())

    def test_missing_folder_says_kept_sessions_still_count(self):
        self.build("o1")
        self.delete_logs()
        os.rename(self.base, self.base + "-moved")
        text = self.build("o2")
        self.assertIn("does not exist", text)
        self.assertIn("The 3 sessions kept from earlier builds still count.", text)
        self.assertEqual(self.sheet("o2")["history"]["active_days"], 4)

    def test_forget_clears_the_kept_history(self):
        self.build("o1")
        self.delete_logs()
        text = self.cli("forget", "--profile", self.prof_path, "--data-dir", os.path.join(self.t, "data"))
        self.assertIn("sessions kept from deleted logs are lost", text)
        self.cli("forget", "--profile", self.prof_path, "--data-dir", os.path.join(self.t, "data"), "--yes")
        self.build("o2")
        self.assertEqual(self.sheet("o2")["history"]["active_days"], 1)
        self.assertEqual(self.sheet("o2")["party"], [])


class Health(Tmp):
    def test_counts_and_versions(self):
        a = self.file("a.jsonl", claude_lines("sa", 2, "Edit", version="2.1.10"))
        b = self.file("b.jsonl", claude_lines("sb", 1, "Bash", version="2.1.9") +
                      [{"type": "user", "sessionId": "sb", "version": "not a version!", "cwd": "/w/a",
                        "timestamp": "2026-03-04T10:00:00Z", "message": {}}])
        _, rep = self.read([a, b])
        self.assertEqual((rep["seen"], rep["read"], rep["sessions"], rep["edits"]), (2, 2, 2, 2))
        self.assertEqual((rep["records"], rep["tool_calls"], rep["edit_calls"]), (9, 3, 2))
        self.assertEqual(rep["versions"], {"2.1.10", "2.1.9"})
        from helpers import profile
        line = health_lines(profile([("A", "/w/a", None)]), Inputs(setup={"health": {"claude": rep}}))[0]
        self.assertEqual(line, "Claude Code: 2 of 2 files read, 9 records recognised, 2 sessions, 2 edits confirmed, "
                               "newest 2026-03-04, versions 2.1.9 to 2.1.10.")

    def test_cached_reuse_gives_the_same_counts(self):
        a = self.file("a.jsonl", claude_lines("sa", 2, "Edit"))
        _, cold = self.read([a])
        _, warm = self.read([a])
        self.assertEqual(cold, warm)

    def test_no_records_recognised_warns(self):
        a = self.file("a.jsonl", [{"kind": "turn", "at": "2026-03-02T10:00:00Z"}] * 3)
        _, rep = self.read([a])
        text = "\n".join(health_warnings(Inputs(setup={"health": {"claude": rep}})))
        self.assertIn("Claude Code: its 1 log files held no records tinkerprint recognised", text)
        self.assertIn("Update tinkerprint", text)

    def test_tool_calls_without_a_known_edit_tool_warn(self):
        a = self.file("a.jsonl", claude_lines("sa", 25, "Bash"))
        _, rep = self.read([a])
        text = "\n".join(health_warnings(Inputs(setup={"health": {"claude": rep}})))
        self.assertIn("25 tool calls, but none of an edit kind tinkerprint knows", text)
        a = self.file("a.jsonl", claude_lines("sa", 19, "Bash"))
        _, rep = self.read([a])
        self.assertEqual(health_warnings(Inputs(setup={"health": {"claude": rep}})), [])
        a = self.file("a.jsonl", claude_lines("sa", 30, "Bash") + claude_lines("sa", 1, "Write"))
        _, rep = self.read([a])
        self.assertEqual(health_warnings(Inputs(setup={"health": {"claude": rep}})), [])

    def test_codex_counts(self):
        path = os.path.join(self.t, "codex")
        write_codex_session(path, "/w/a", datetime(2026, 3, 2, 10, tzinfo=UTC), "m-2",
                            [(datetime(2026, 3, 2, 10, 5, tzinfo=UTC), "/w/a/x.py")], random.Random(2))
        rep = new_report()
        _cached(codex.rollout_files(path), codex.read_file, os.path.join(self.t, "data", "cache", "codex.json"),
                path, rep)
        self.assertEqual((rep["read"], rep["sessions"], rep["edits"], rep["tool_calls"], rep["edit_calls"]),
                         (1, 1, 1, 1, 1))
        self.assertEqual(rep["versions"], {"0.0.0"})

    def test_agy_database(self):
        from helpers import profile
        db = os.path.join(self.t, "agy", "db.sqlite")
        write_agy_db(db, [("c1", ["/w/a"], datetime(2026, 3, 2, 10, tzinfo=UTC))])
        hc = {"lines": 0, "records": 0, "tool_calls": 0, "edit_calls": 0, "versions": set()}
        self.assertEqual(len(agy.read_db(db, hc)), 1)
        self.assertEqual((hc["lines"], hc["records"], hc.get("unreadable")), (1, 1, None))
        bad = os.path.join(self.t, "agy", "other.sqlite")
        con = sqlite3.connect(bad)
        con.execute("create table something_else (x)")
        con.close()
        hc = {"lines": 0, "records": 0, "tool_calls": 0, "edit_calls": 0, "versions": set()}
        self.assertEqual(agy.read_db(bad, hc), [])
        self.assertTrue(hc["unreadable"])
        rep = dict(new_report(), seen=1, read=0)
        self.assertIn("Antigravity: its database held no records tinkerprint recognised",
                      "\n".join(health_warnings(Inputs(setup={"health": {"agy": rep}}))))
        line = health_lines(profile([("A", "/w/a", None)]), Inputs(setup={"health": {"agy": rep}}))[0]
        self.assertTrue(line.startswith("Antigravity: database not readable"), line)

    def test_health_stays_off_the_sheet_and_card(self):
        root = os.path.join(self.t, "repo")
        r = RepoWriter(root)
        r.touch(datetime(2026, 3, 2, 10, tzinfo=UTC), ME, {"a.py": 2})
        r.write()
        write_claude_session(self.base, root, datetime(2026, 3, 2, 10, tzinfo=UTC), "model-x",
                             [(datetime(2026, 3, 2, 10, 5, tzinfo=UTC), os.path.join(root, "a.py"), "Edit")],
                             random.Random(1))
        path = os.path.join(self.t, "p.toml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f'name = "Ida"\n[identity]\nemails = ["{ME[1]}"]\n[harnesses]\nclaude = true\ncodex = false\n'
                    f'claude_dir = "{self.base}"\n[card]\nallow = true\n[[project]]\nname = "P"\nroot = "{root}"\n')
        res = build(load_profile(path), os.path.join(self.t, "out"), home=os.path.join(self.t, "data"),
                    today=date(2026, 11, 1))
        self.assertTrue(res["local"]["health"][0].startswith("Claude Code: 1 of 1 files read"))
        for name in ("sheet.json", "sheet.html", "card.svg", "changes.json"):
            with open(os.path.join(self.t, "out", name), encoding="utf-8") as f:
                text = f.read()
            for word in ("records recognised", "files read", "0.0.0"):
                self.assertNotIn(word, text, (name, word))


if __name__ == "__main__":
    unittest.main()
