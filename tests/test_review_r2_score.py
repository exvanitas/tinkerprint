"""Review round 2, scoring items. Each test reproduces a reported case. All data is invented."""
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


class Item04CardChartFromPublicShares(unittest.TestCase):
    def test_rounded_shares_decide_the_card_chart(self):
        prof = profile([("A", "/w/a", {"stats": {"Logic": 98, "Docs": 0.6, "Tests": 0.6}})])
        sheet, _ = run(prof, [commit(TS, "/w/a/x.py")])
        self.assertEqual(sheet["chart"], "radar")
        self.assertEqual(sheet["card"]["chart"], "bars")


class Item05UnassignedListing(unittest.TestCase):
    prof = profile([("A", "/w/mono/a", None)])

    def test_every_outside_folder_is_listed(self):
        evs = [session(TS, "/w/out-a", sid="s1"), session("2026-03-02T11:00:00+00:00", "/w/out-b", sid="s1"),
               session(TS, "/w/mono/a", sid="s2"), session("2026-03-02T12:00:00+00:00", "/w/out-c", sid="s2")]
        sheet, local = run(self.prof, evs)
        folders = [f for f, _ in local["unassigned_folders"]]
        self.assertEqual(sorted(folders), ["/w/out-a", "/w/out-b", "/w/out-c"])
        self.assertEqual(sheet["unassigned"]["sessions"], 2)

    def test_season_filters_each_observation(self):
        evs = [session("2026-03-01T10:00:00+00:00", "/w/mono/a", sid="s1"), session(TS, "/w/out", sid="s1")]
        sheet, _ = run(self.prof, evs, season=(date(2026, 3, 2), None))
        self.assertEqual(sheet["unassigned"]["sessions"], 1)

    def test_commit_files_outside_roots_are_listed(self):
        evs = [commit(TS, "/w/mono/a/x.py"), commit(TS, "/w/mono/b/y.py")]
        sheet, local = run(self.prof, evs)
        self.assertIn("/w/mono/b", local["unassigned_edit_folders"])
        self.assertEqual(sheet["unassigned"]["edits"], 1)


class Item06BulkUsesTheWholeCommit(unittest.TestCase):
    def test_outside_files_count_toward_the_threshold(self):
        prof = profile([("A", "/w/mono/a", None)])
        evs = [commit(TS, f"/w/mono/a/img{i}.png", h="big", status="A") for i in range(200)]
        evs += [commit(TS, "/w/mono/b/img.png", h="big", status="A"), commit(TS, "/w/mono/a/x.py", h="c2")]
        sheet, _ = run(prof, evs)
        bulk, code = 200 / 201, 1
        self.assertAlmostEqual(sheet["season_totals"]["unclassified"], L(bulk) / (L(bulk) + L(code)), places=5)


class Item10TimeZones(unittest.TestCase):
    base = {"identity": {"emails": ["a@example.test"]}}

    def test_offsets_must_be_quarter_hours(self):
        with self.assertRaises(ProfileError):
            parse_profile(dict(self.base, timezone="+00:05"), "/")
        for ok in ("+05:45", "-03:30", "Asia/Kathmandu", "UTC"):
            parse_profile(dict(self.base, timezone=ok), "/")


class Item11ScoreOthers(Tmp):
    def test_founder_date_uses_instants(self):
        from tinkerprint.events import Commit
        commits = [Commit(ts="2026-03-01T23:00:00-08:00", hash="a", repo="r1", top="/w/a", mine=True, bot=False, root=True),
                   Commit(ts="2026-03-02T10:00:00+09:00", hash="b", repo="r2", top="/w/a", mine=True, bot=False, root=True)]
        sheet, _ = run(profile([("A", "/w/a", None)], rollover=4), [], commits=commits)
        founder = [x for x in sheet["achievements"] if x["id"] == "founder"][0]
        self.assertEqual(founder["date"], "2026-03-01")

    def test_party_role_needs_a_majority(self):
        evs = [session(TS, "/w/a", sid=f"s{i}") for i in range(9)] + [edit(TS, "/w/a/x.py", session="e")]
        sheet, _ = run(profile([("A", "/w/a", None)]), evs)
        self.assertNotEqual(sheet["party"][0]["role"], "Mostly edits")

    def test_tiny_lead_is_not_a_tie(self):
        prof = profile([("A", "/w/a", {"stats": {"Interface": 1, "Logic": 1.000000001}})])
        self.assertEqual(run(prof, [commit(TS, "/w/a/x.py")])[0]["class"]["name"], "Sage")

    def test_nonfinite_weights_are_refused(self):
        for bad in (float("inf"), float("nan")):
            with self.assertRaises(ProfileError):
                profile([("A", "/w/a", {"stats": {"Logic": bad}})])



class Item11MulticlassNeverReusesTheClass(unittest.TestCase):
    """Astra 16 came from the 2-point hold, which round 2 removed. This checks the property directly."""

    def test_random_shares(self):
        import random
        from tinkerprint.classes import multiclass, pick_class
        from tinkerprint.sets import BUILDER_STATS
        rng = random.Random(7)
        for _ in range(2000):
            raw = {s: rng.random() ** 2 for s in BUILDER_STATS}
            total = sum(raw.values())
            shares = {s: v / total for s, v in raw.items()}
            cls = pick_class(shares, "builder")
            multi = multiclass(shares, "builder", cls)
            if multi:
                self.assertFalse(set(multi["stats"]) & set(cls["stats"]), shares)


if __name__ == "__main__":
    unittest.main()
