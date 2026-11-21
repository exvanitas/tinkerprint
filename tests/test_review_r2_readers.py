"""Review round 2, reader items. Each test reproduces a reported case. All data is invented."""
import copy
import io
import json
import math
import os
import sqlite3
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, datetime
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
from helpers import commit, edit, profile, project, run, session
from tinkerprint.demo import RepoWriter, git_env, write_agy_db
from tinkerprint.profile import ProfileError, load_profile, parse_profile
from tinkerprint.readers import agy, claude, codex

UTC = ZoneInfo("UTC")
ME = ("Ida Fenwick", "ida@fenwick.example.test")
MATE = ("Oren Pell", "oren@fenwick.example.test")
TS = "2026-03-02T10:00:00+00:00"
L = math.log1p
SECRET = "FUZZSECRET"
WRONG = ({"message": SECRET}, [SECRET], 7, None, True)


def write_lines(path, records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write((r if isinstance(r, str) else json.dumps(r)) + "\n")
    return path


def key_paths(obj, prefix=()):
    """Every key path in a JSON value, sorted, so the fuzz is deterministic."""
    out = []
    if isinstance(obj, dict):
        for k in sorted(obj):
            out.append(prefix + (k,))
            out += key_paths(obj[k], prefix + (k,))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.append(prefix + (i,))
            out += key_paths(v, prefix + (i,))
    return out


def mutated(records, index, path, value):
    recs = copy.deepcopy(records)
    target = recs[index]
    for k in path[:-1]:
        target = target[k]
    target[path[-1]] = copy.deepcopy(value)
    return recs


def stringified(evs):
    """Event string fields that look like a printed dict or list, or carry the planted text."""
    bad = []
    for e in evs:
        for k, v in e.to_dict().items():
            if isinstance(v, str) and (SECRET in v or v.startswith(("{", "[")) or "{'" in v or "['" in v):
                bad.append((k, v))
    return bad


CLAUDE_FIXTURE = [
    {"type": "user", "sessionId": "cs1", "timestamp": "2026-03-02T10:00:00Z", "cwd": "/w/a",
     "message": {"role": "user", "content": "invented"}},
    {"type": "assistant", "sessionId": "cs1", "timestamp": "2026-03-02T10:01:00Z", "cwd": "/w/a",
     "message": {"role": "assistant", "model": "m-1", "content": [
         {"type": "tool_use", "id": "t1", "name": "Edit", "input": {"file_path": "/w/a/x.py"}}]}},
    {"type": "user", "sessionId": "cs1", "timestamp": "2026-03-02T10:01:05Z", "cwd": "/w/a",
     "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}]}},
]
CODEX_FIXTURE = [
    {"timestamp": "2026-03-02T10:00:00Z", "type": "session_meta",
     "payload": {"id": "s1", "timestamp": "2026-03-02T10:00:00Z", "cwd": "/w/a", "originator": "codex_exec"}},
    {"timestamp": "2026-03-02T10:00:01Z", "type": "turn_context", "payload": {"model": "m-2", "cwd": "/w/a"}},
    {"timestamp": "2026-03-02T10:02:00Z", "type": "event_msg", "payload": {"type": "item_completed", "item": {
        "type": "FileChange", "id": "fc1", "status": "completed", "changes": {"/w/a/x.py": {"type": "update"}}}}},
    {"timestamp": "2026-03-02T10:03:00Z", "type": "event_msg", "payload": {
        "type": "patch_apply_end", "call_id": "c9", "success": True, "changes": {"/w/a/y.py": {"type": "add"}}}},
]




class Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()


class Item01ReaderFuzz(Tmp):
    def fuzz(self, fixture, read):
        n = 0
        for i, rec in enumerate(fixture):
            for path in key_paths(rec):
                for value in WRONG:
                    recs = mutated(fixture, i, path, value)
                    evs = read(recs)
                    self.assertEqual(stringified(evs), [], (i, path, value))
                    n += 1
        return n

    def test_claude_fuzz(self):
        path = os.path.join(self.t, "p", "s.jsonl")
        self.assertGreater(self.fuzz(CLAUDE_FIXTURE, lambda r: claude.read_file(write_lines(path, r))), 100)

    def test_codex_fuzz(self):
        path = os.path.join(self.t, "rollout-x.jsonl")
        self.assertGreater(self.fuzz(CODEX_FIXTURE, lambda r: codex.read_file(write_lines(path, r))), 100)

    def test_agy_fuzz(self):
        db = os.path.join(self.t, "agy.db")
        values = {"conversation_id": "c1", "workspace_uris": json.dumps(["file:///w/a"]),
                  "last_modified_time": "2026-03-02 10:00:00+00:00"}
        for col in values:
            for value in WRONG + ("not json", json.dumps([{"message": SECRET}]), json.dumps({"a": SECRET})):
                if os.path.exists(db):
                    os.remove(db)
                con = sqlite3.connect(db)
                con.execute("create table conversation_summaries (conversation_id, workspace_uris, last_modified_time)")
                row = dict(values)
                row[col] = json.dumps(value) if isinstance(value, (dict, list)) else value
                con.execute("insert into conversation_summaries values (?,?,?)",
                            (row["conversation_id"], row["workspace_uris"], row["last_modified_time"]))
                con.commit()
                con.close()
                self.assertEqual(stringified(agy.read_db(db)), [], (col, value))

    def test_claude_odd_top_level_type(self):
        path = os.path.join(self.t, "p", "s.jsonl")
        for t in ({}, [], 3):
            evs = claude.read_file(write_lines(path, [{"type": t, "message": {"type": "assistant"}}] + CLAUDE_FIXTURE))
            self.assertEqual(len([e for e in evs if e.kind == "edit"]), 1)


class Item02ClaudeErrorsAndModels(Tmp):
    def test_only_absent_or_false_error_flag_succeeds(self):
        path = os.path.join(self.t, "p", "s.jsonl")
        for flag, count in ((1, 0), ("true", 0), ("false", 0), (None, 0), (False, 1)):
            recs = copy.deepcopy(CLAUDE_FIXTURE)
            recs[2]["message"]["content"][0]["is_error"] = flag
            evs = claude.read_file(write_lines(path, recs))
            self.assertEqual(len([e for e in evs if e.kind == "edit"]), count, flag)

    def test_model_only_on_records_that_carry_it(self):
        recs = [
            {"type": "assistant", "sessionId": "cs1", "timestamp": "2026-03-02T10:00:00Z", "cwd": "/w/out",
             "message": {"role": "assistant", "model": "work-model", "content": "invented"}},
            {"type": "user", "sessionId": "cs1", "timestamp": "2026-03-03T10:00:00Z", "cwd": "/w/a",
             "message": {"role": "user", "content": "invented"}},
            {"type": "assistant", "sessionId": "cs1", "timestamp": "2026-03-03T10:01:00Z", "cwd": "/w/a",
             "message": {"role": "assistant", "model": "home-model", "content": "invented"}},
        ]
        evs = claude.read_file(write_lines(os.path.join(self.t, "p", "s.jsonl"), recs))
        sheet, _ = run(profile([("A", "/w/a", None)]), evs, season=(date(2026, 3, 3), None))
        self.assertEqual(sheet["party"][0]["models"], ["home-model"])


class Item03CodexOneChangeOnce(Tmp):
    def test_two_records_of_one_patch_count_once(self):
        recs = CODEX_FIXTURE[:2] + [
            {"timestamp": "2026-03-02T03:59:59Z", "type": "event_msg", "payload": {
                "type": "patch_apply_end", "call_id": "c1", "success": True, "changes": {"/w/a/x.py": {}}}},
            {"timestamp": "2026-03-02T04:00:00Z", "type": "event_msg", "payload": {"type": "item_completed", "item": {
                "type": "FileChange", "id": "c1", "status": "completed", "changes": {"/w/a/x.py": {}}}}}]
        evs = codex.read_file(write_lines(os.path.join(self.t, "rollout-a.jsonl"), recs))
        self.assertEqual(len([e for e in evs if e.kind == "edit"]), 1)
        sheet, _ = run(profile([("A", "/w/a", None)]), evs)
        self.assertEqual(sheet["history"]["points"], 1)

    def test_distinct_patches_stay_distinct(self):
        recs = CODEX_FIXTURE[:2] + [
            {"timestamp": f"2026-03-02T10:05:00.{ms}Z", "type": "event_msg", "payload": {
                "type": "item_completed", "item": {"type": "FileChange", "id": f"fc{ms}", "status": "completed",
                                                   "changes": {"/w/a/x.py": {}}}}} for ms in ("110", "720")]
        evs = codex.read_file(write_lines(os.path.join(self.t, "rollout-b.jsonl"), recs))
        self.assertEqual(len([e for e in evs if e.kind == "edit"]), 2)


class Item11ReaderOthers(Tmp):
    def test_codex_bare_timestamp_line_makes_no_presence(self):
        recs = CODEX_FIXTURE[:2] + [{"timestamp": "2026-03-09T10:00:00Z"}]
        evs = codex.read_file(write_lines(os.path.join(self.t, "rollout-c.jsonl"), recs))
        self.assertNotIn("2026-03-09", {e.ts[:10] for e in evs})

    def test_codex_single_change_object(self):
        recs = CODEX_FIXTURE[:2] + [{"timestamp": "2026-03-02T10:05:00Z", "type": "event_msg", "payload": {
            "type": "item_completed", "item": {"type": "FileChange", "id": "f", "status": "completed",
                                               "changes": {"path": "a.py", "kind": "update", "unified_diff": "x"}}}}]
        evs = codex.read_file(write_lines(os.path.join(self.t, "rollout-d.jsonl"), recs))
        self.assertEqual([e.path for e in evs if e.kind == "edit"], ["/w/a/a.py"])

    def test_cache_digest_matches_the_bytes_parsed(self):
        from tinkerprint.build import _cached
        path = write_lines(os.path.join(self.t, "rollout-e.jsonl"), CODEX_FIXTURE[:3])
        with open(path, "rb") as f:
            original = f.read()
        extra = json.dumps(CODEX_FIXTURE[3]) + "\n"

        def racy(p, *args, **kw):
            with open(p, "a") as f:
                f.write(extra)
            return codex.read_file(p, *args, **kw)

        cache = os.path.join(self.t, "cache.json")
        _cached([path], racy, cache)
        with open(path, "wb") as f:
            f.write(original)
        evs = _cached([path], codex.read_file, cache)
        self.assertEqual(sorted(e.path for e in evs if e.kind == "edit"), ["/w/a/x.py"])

    def test_agy_remote_authority_is_unassigned(self):
        db = os.path.join(self.t, "agy.db")
        con = sqlite3.connect(db)
        con.execute("create table conversation_summaries (conversation_id, workspace_uris, last_modified_time)")
        con.execute("insert into conversation_summaries values ('c', ?, '2026-03-02 10:00:00+00:00')",
                    (json.dumps(["file://build-server/w/a"]),))
        con.commit()
        con.close()
        sheet, _ = run(profile([("A", "/w/a", None)]), agy.read_db(db))
        self.assertEqual(sheet["party"], [])



if __name__ == "__main__":
    unittest.main()
