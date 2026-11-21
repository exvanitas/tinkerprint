"""Review round 3, readers: schemas (S1), Codex correlation and models (2), cache (3), sessions and URIs (9)."""
import copy
import json
import os
import re
import sqlite3
import tempfile
import unittest
from datetime import date

import helpers  # noqa: F401
from helpers import profile, run
from test_review_r2_readers import CLAUDE_FIXTURE, CODEX_FIXTURE, key_paths, mutated, write_lines
from tinkerprint.readers import agy, claude, codex

MODEL = re.compile(r"^(?!/)[A-Za-z0-9._:@+-]+(?:/[A-Za-z0-9._:@+-]+)?$")
SECRET = "FUZZSECRET"
STRUCTURAL = (None, {"x": None}, {"a.py": "text"}, {"path": None}, [None, {}], [[SECRET]], {"path": {"path": SECRET}},
              "/private/models/local.gguf", "a sentence with spaces", "/w/a/\u0000bad", "relative/path",
              {"message": SECRET}, [SECRET], 7, True)


# Planted values that are themselves valid paths may legitimately become a path when they land in
# a path field. Nothing else may: no key names, no text, no invented files.
PLANTED_PATHS = {"/private/models/local.gguf", "/w/a/path", "/w/a/relative/path", "relative/path", "path",
                 "/w/a/a sentence with spaces"}


def check(test, evs, allowed_edits):
    allowed_edits = set(allowed_edits) | PLANTED_PATHS
    for e in evs:
        test.assertTrue(e.model == "" or MODEL.match(e.model) and len(e.model) <= 80, e.model)
        for v in e.to_dict().values():
            if isinstance(v, str):
                test.assertNotIn(SECRET, v)
                test.assertFalse(any(ord(c) < 32 or ord(c) == 127 for c in v), v)
        if e.kind == "edit":
            test.assertIn(e.path, allowed_edits, e.path)
        if e.kind == "session" and e.path:
            test.assertTrue(e.path.startswith("/"), e.path)


class Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = self.tmp.name

    def tearDown(self):
        self.tmp.cleanup()


class S1Schemas(Tmp):
    def structural_fuzz(self, fixture, read, allowed):
        n = 0
        for i, rec in enumerate(fixture):
            for path in key_paths(rec):
                for value in STRUCTURAL:
                    evs = read(mutated(fixture, i, path, value))
                    check(self, evs, allowed)
                    n += 1
        return n

    def test_claude_structural_fuzz(self):
        p = os.path.join(self.t, "p", "s.jsonl")
        n = self.structural_fuzz(CLAUDE_FIXTURE, lambda r: claude.read_file(write_lines(p, r)), {"/w/a/x.py"})
        self.assertGreater(n, 300)

    def test_codex_structural_fuzz(self):
        p = os.path.join(self.t, "rollout-x.jsonl")
        n = self.structural_fuzz(CODEX_FIXTURE, lambda r: codex.read_file(write_lines(p, r)),
                                 {"/w/a/x.py", "/w/a/y.py"})
        self.assertGreater(n, 300)

    def test_model_must_be_an_id(self):
        for bad in ("/private-client/models/local.gguf", "a sentence here", "x" * 81, "a/b/c"):
            recs = copy.deepcopy(CODEX_FIXTURE)
            recs[1]["payload"]["model"] = bad
            evs = codex.read_file(write_lines(os.path.join(self.t, "rollout-m.jsonl"), recs))
            self.assertNotIn(bad, {e.model for e in evs})
            recs = copy.deepcopy(CLAUDE_FIXTURE)
            recs[1]["message"]["model"] = bad
            evs = claude.read_file(write_lines(os.path.join(self.t, "p", "m.jsonl"), recs))
            self.assertNotIn(bad, {e.model for e in evs})
        recs = copy.deepcopy(CODEX_FIXTURE)
        recs[1]["payload"]["model"] = "vendor/model-2.5@x"
        evs = codex.read_file(write_lines(os.path.join(self.t, "rollout-m.jsonl"), recs))
        self.assertIn("vendor/model-2.5@x", {e.model for e in evs})

    def test_malformed_single_change_invents_nothing(self):
        recs = CODEX_FIXTURE[:2] + [{"timestamp": "2026-03-02T10:05:00Z", "type": "event_msg", "payload": {
            "type": "item_completed", "item": {"type": "FileChange", "id": "f", "status": "completed",
                                               "changes": {"path": None, "kind": "update", "unified_diff": "x"}}}}]
        evs = codex.read_file(write_lines(os.path.join(self.t, "rollout-s.jsonl"), recs))
        self.assertEqual([e for e in evs if e.kind == "edit"], [])

    def test_null_byte_folder_does_not_abort(self):
        recs = copy.deepcopy(CLAUDE_FIXTURE)
        recs[0]["cwd"] = "/w/a\u0000x"
        evs = claude.read_file(write_lines(os.path.join(self.t, "p", "n.jsonl"), recs))
        run(profile([("A", "/w/a", None)]), evs)


class Item02CodexCorrelationAndModels(Tmp):
    def test_call_id_links_both_records(self):
        recs = CODEX_FIXTURE[:2] + [
            {"timestamp": "2026-03-02T03:59:59Z", "type": "event_msg", "payload": {
                "type": "patch_apply_end", "call_id": "c", "success": True, "changes": {"/w/a/x.py": {}}}},
            {"timestamp": "2026-03-02T04:00:00Z", "type": "event_msg", "payload": {"type": "item_completed", "item": {
                "type": "FileChange", "id": "fc", "call_id": "c", "status": "completed",
                "changes": {"/w/a/x.py": {}}}}}]
        evs = codex.read_file(write_lines(os.path.join(self.t, "rollout-c.jsonl"), recs))
        self.assertEqual(len([e for e in evs if e.kind == "edit"]), 1)
        self.assertEqual(run(profile([("A", "/w/a", None)]), evs)[0]["history"]["points"], 1)

    def test_model_belongs_to_the_turn_that_names_it(self):
        recs = [CODEX_FIXTURE[0],
                {"timestamp": "2026-03-01T10:00:00Z", "type": "turn_context", "payload": {"model": "work-model",
                                                                                          "cwd": "/w/out"}},
                {"timestamp": "2026-03-02T10:00:00Z", "type": "turn_context", "payload": {"cwd": "/w/a"}},
                {"timestamp": "2026-03-02T10:02:00Z", "type": "event_msg", "payload": {"type": "item_completed", "item": {
                    "type": "FileChange", "id": "fc", "status": "completed", "changes": {"/w/a/x.py": {}}}}}]
        evs = codex.read_file(write_lines(os.path.join(self.t, "rollout-t.jsonl"), recs))
        sheet, _ = run(profile([("A", "/w/a", None)]), evs, season=(date(2026, 3, 2), None))
        self.assertEqual(sheet["party"][0]["models"], [])


class Item03CacheHashesParsedBytes(Tmp):
    def test_bytes_after_the_reader_stops_force_a_reparse(self):
        from tinkerprint.build import _cached
        path = write_lines(os.path.join(self.t, "rollout-e.jsonl"), CODEX_FIXTURE[:2])
        extra = json.dumps(CODEX_FIXTURE[2]) + "\n"

        def late_append(p, *args, **kw):
            evs = codex.read_file(p, *args, **kw)
            with open(p, "a") as f:
                f.write(extra)
            return evs

        cache = os.path.join(self.t, "cache.json")
        _cached([path], late_append, cache)
        warm = _cached([path], codex.read_file, cache)
        cold = codex.read_file(path)
        self.assertEqual(sorted(warm), sorted(cold))


class Item09SessionsAndUris(Tmp):
    def test_each_record_keeps_its_session(self):
        recs = copy.deepcopy(CLAUDE_FIXTURE)
        recs[0]["sessionId"] = "s1"
        recs[1]["sessionId"] = "s2"
        recs[2]["sessionId"] = "s2"
        evs = claude.read_file(write_lines(os.path.join(self.t, "p", "s1.jsonl"), recs))
        self.assertEqual({e.session for e in evs}, {"s1", "s2"})

    def test_subagent_without_ids_joins_its_parent(self):
        recs = copy.deepcopy(CLAUDE_FIXTURE)
        for r in recs:
            r.pop("sessionId")
        path = os.path.join(self.t, "p", "parent-1", "subagents", "agent-t.jsonl")
        evs = claude.read_file(write_lines(path, recs))
        self.assertEqual({e.session for e in evs}, {"parent-1"})

    def test_agy_unicode_uri(self):
        db = os.path.join(self.t, "agy.db")
        con = sqlite3.connect(db)
        con.execute("create table conversation_summaries (conversation_id, workspace_uris, last_modified_time)")
        con.execute("insert into conversation_summaries values ('c', ?, '2026-03-02 10:00:00+00:00')",
                    (json.dumps(["file:///m/音楽/caf%C3%A9"]),))
        con.commit()
        con.close()
        self.assertEqual([e.path for e in agy.read_db(db)], ["/m/音楽/café"])

    def test_dotdot_resolves_after_symlinks(self):
        os.makedirs(os.path.join(self.t, "b", "sub"))
        os.makedirs(os.path.join(self.t, "a"))
        os.symlink(os.path.join(self.t, "b", "sub"), os.path.join(self.t, "a", "link"))
        recs = copy.deepcopy(CLAUDE_FIXTURE)
        for r in recs:
            r["cwd"] = os.path.join(self.t, "a", "link")
        recs[1]["message"]["content"][0]["input"]["file_path"] = "../x.py"
        evs = claude.read_file(write_lines(os.path.join(self.t, "p", "d.jsonl"), recs))
        prof = profile([("B", os.path.join(self.t, "b"), None), ("A", os.path.join(self.t, "a"), None)])
        sheet, _ = run(prof, evs)
        self.assertEqual([p["name"] for p in sheet["projects"]], ["B"])


if __name__ == "__main__":
    unittest.main()
