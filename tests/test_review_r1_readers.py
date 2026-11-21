"""Review round 1, reader findings. Each test reproduces one reported case. All data is invented."""
import json
import os
import sqlite3
import tempfile
import unittest

import helpers  # noqa: F401
from helpers import profile, run
from tinkerprint.readers import agy, claude, codex


def write_lines(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for ln in lines:
            f.write(ln if isinstance(ln, str) else json.dumps(ln, separators=(",", ":")))
            f.write("\n")
    return path


def meta(ts="2026-03-02T10:00:00Z", cwd="/w/a", sid="sess-1", origin="codex_exec"):
    return {"timestamp": ts, "type": "session_meta", "payload": {"id": sid, "timestamp": ts, "cwd": cwd,
                                                                 "originator": origin}}


def turn(ts="2026-03-02T10:00:01Z", model="model-r", cwd="/w/a"):
    return {"timestamp": ts, "type": "turn_context", "payload": {"model": model, "cwd": cwd}}


def filechange(ts, changes, status="completed", iid="fc1"):
    return {"timestamp": ts, "type": "event_msg", "payload": {"type": "item_completed", "item": {
        "type": "FileChange", "id": iid, "status": status, "changes": changes}}}


def edits_of(evs):
    return sorted((e.path, e.ts) for e in evs if e.kind == "edit")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.tmp.cleanup()

    def codex(self, lines):
        return codex.read_file(write_lines(os.path.join(self.tmp.name, "rollout-x.jsonl"), lines))

    def claude(self, lines):
        return claude.read_file(write_lines(os.path.join(self.tmp.name, "p", "s.jsonl"), lines))


def cl(kind, ts, content, cwd="/w/a", model=None):
    msg = {"role": kind, "content": content}
    if model:
        msg["model"] = model
    return {"type": kind, "sessionId": "cs1", "timestamp": ts, "cwd": cwd, "message": msg}


def use(tid, name, path, key="file_path"):
    return {"type": "tool_use", "id": tid, "name": name, "input": {key: path}}


def result(tid, error=False):
    r = {"type": "tool_result", "tool_use_id": tid, "content": "invented"}
    if error:
        r["is_error"] = True
    return r


class Item01PatchTextIsNeverAPath(Base):
    def test_message_text_with_patch_header_is_not_an_edit(self):
        args = json.dumps({"message": "see notes\n*** Update File: private review discussion\nthanks"})
        evs = self.codex([meta(), turn(), {"timestamp": "2026-03-02T10:01:00Z", "type": "response_item", "payload": {
            "type": "function_call", "name": "spawn_agent", "call_id": "c1", "arguments": args}}])
        self.assertEqual(edits_of(evs), [])
        self.assertNotIn("private review", repr(evs))

    def test_patch_call_without_completion_is_not_an_edit(self):
        evs = self.codex([meta(), turn(), {"timestamp": "2026-03-02T10:01:00Z", "type": "response_item", "payload": {
            "type": "custom_tool_call", "name": "apply_patch", "call_id": "c1",
            "input": "*** Begin Patch\n*** Update File: x.py\n@@\n-a\n+b\n*** End Patch"}}])
        self.assertEqual(edits_of(evs), [])


class Item02OnlyConfirmedChanges(Base):
    def test_failed_filechange_earns_nothing(self):
        evs = self.codex([meta(), turn(), filechange("2026-03-02T10:02:00Z", {"/w/a/x.py": {}}, status="failed")])
        self.assertEqual(edits_of(evs), [])

    def test_patch_apply_end_counts_once_at_completion(self):
        evs = self.codex([meta(), turn(), {"timestamp": "2026-03-02T04:00:01Z", "type": "event_msg", "payload": {
            "type": "patch_apply_end", "call_id": "c1", "success": True, "changes": {"/w/a/x.py": {"type": "update"}}}},
            {"timestamp": "2026-03-02T04:00:02Z", "type": "event_msg", "payload": {
                "type": "patch_apply_end", "call_id": "c2", "success": False, "changes": {"/w/a/y.py": {}}}}])
        self.assertEqual(edits_of(evs), [("/w/a/x.py", "2026-03-02T04:00:01+00:00")])

    def test_call_and_completion_across_rollover_make_one_day(self):
        evs = self.codex([meta(ts="2026-03-02T03:59:00Z"), turn(ts="2026-03-02T03:59:00Z"),
                          {"timestamp": "2026-03-02T03:59:59Z", "type": "response_item", "payload": {
                              "type": "custom_tool_call", "name": "exec", "call_id": "c1",
                              "input": "apply_patch(`*** Begin Patch\n*** Update File: x.py\n*** End Patch`)"}},
                          filechange("2026-03-02T04:00:01Z", {"/w/a/x.py": {"type": "update"}})])
        sheet, _ = run(profile([("A", "/w/a", None)]), evs)
        self.assertEqual(sheet["history"]["points"], 1)
        self.assertEqual(sheet["history"]["first_day"], "2026-03-02")

    def test_claude_write_without_result_earns_nothing(self):
        evs = self.claude([cl("assistant", "2026-03-02T10:00:00Z", [use("t1", "Write", "/w/a/x.py")], model="m"),
                           cl("assistant", "2026-03-02T10:01:00Z", [use("t2", "Edit", "/w/a/y.py")], model="m"),
                           cl("user", "2026-03-02T10:01:05Z", [result("t2", error=True)]),
                           cl("assistant", "2026-03-02T10:02:00Z", [use("t3", "Edit", "/w/a/z.py")], model="m"),
                           cl("user", "2026-03-02T10:02:05Z", [result("t3")])])
        self.assertEqual(edits_of(evs), [("/w/a/z.py", "2026-03-02T10:02:05+00:00")])


class Item09PresenceKeepsDaysAndModels(Base):
    def test_half_hour_zone_keeps_both_profile_days(self):
        # +05:30 with rollover 04:00: 22:15Z is 03:45 local, 22:45Z is 04:15 local.
        evs = self.codex([meta(ts="2026-03-02T22:15:00Z"), turn(ts="2026-03-02T22:15:00Z"),
                          {"timestamp": "2026-03-02T22:45:00Z", "type": "event_msg",
                           "payload": {"type": "task_started"}}])
        sheet, _ = run(profile([("A", "/w/a", None)], tz="Asia/Kolkata"), evs)
        self.assertEqual(sheet["party"][0]["days_together"], 2)

    def test_two_models_in_one_hour_are_both_kept(self):
        evs = self.codex([meta(), turn(ts="2026-03-02T10:00:01Z", model="m-one"),
                          turn(ts="2026-03-02T10:20:00Z", model="m-two"),
                          {"timestamp": "2026-03-02T10:21:00Z", "type": "event_msg", "payload": {"type": "x"}}])
        sheet, _ = run(profile([("A", "/w/a", None)]), evs)
        self.assertEqual(sorted(sheet["party"][0]["models"]), ["m-one", "m-two"])


class Item10Robustness(Base):
    def test_odd_types_do_not_crash_or_leak(self):
        evs = self.claude([cl("assistant", "2026-03-02T10:00:00Z",
                              [{"type": "tool_use", "id": "t1", "name": [], "input": {"file_path": "/w/a/x.py"}}])])
        self.assertEqual(edits_of(evs), [])
        evs = self.codex([meta(sid={"message": "secret words"}, origin={"message": "secret words"}), turn(),
                          filechange("2026-03-02T10:02:00Z", 1), filechange("2026-03-02T10:02:00Z", True, iid="b")])
        self.assertEqual(edits_of(evs), [])
        self.assertNotIn("secret", repr(evs))
        db = os.path.join(self.tmp.name, "agy.db")
        con = sqlite3.connect(db)
        con.execute("create table conversation_summaries (conversation_id text, workspace_uris text, "
                    "last_modified_time text)")
        con.execute("insert into conversation_summaries values ('a', '[null]', '2026-03-02 10:00:00+00:00')")
        con.execute("insert into conversation_summaries values ('b', '{\"x\": 1}', '2026-03-02 10:00:00+00:00')")
        con.commit()
        con.close()
        self.assertEqual(len(agy.read_db(db)), 2)

    def test_spacing_and_key_order_do_not_drop_events(self):
        line = ('{"message": {"role": "assistant", "model": "m", "content": [{"type": "tool_use", "id": "t1", '
                '"name": "Edit", "input": {"file_path": "/w/a/x.py"}}]}, "type" : "assistant", '
                '"timestamp": "2026-03-02T10:00:00Z", "sessionId": "cs1", "cwd": "/w/a"}')
        evs = self.claude([line, cl("user", "2026-03-02T10:00:03Z", [result("t1")])])
        self.assertEqual([p for p, _ in edits_of(evs)], ["/w/a/x.py"])
        evs = self.codex([meta(), '{"type":"event_msg","payload":{"type":"x"},"timestamp":"2026-03-05T10:00:00Z"}'])
        days = {e.ts[:10] for e in evs if e.kind == "session"}
        self.assertIn("2026-03-05", days)

    def test_truncated_line_makes_no_presence(self):
        evs = self.codex([meta(), '{"timestamp":"2026-01-05T22:20:00Z","type":"event_msg","payload":{"ty'])
        self.assertNotIn("2026-01-05", {e.ts[:10] for e in evs})


class Item11CurrentFolder(Base):
    def test_codex_relative_paths_follow_turn_folder(self):
        evs = self.codex([meta(cwd="/w/a"), turn(cwd="/w/b"),
                          filechange("2026-03-02T10:02:00Z", {"x.py": {"type": "update"}})])
        self.assertEqual([p for p, _ in edits_of(evs)], ["/w/b/x.py"])

    def test_claude_relative_paths_follow_line_folder(self):
        evs = self.claude([cl("assistant", "2026-03-02T10:00:00Z", [use("t1", "Edit", "x.py")], cwd="/w/a"),
                           cl("user", "2026-03-02T10:00:02Z", [result("t1")], cwd="/w/a"),
                           cl("assistant", "2026-03-02T10:01:00Z", [use("t2", "Edit", "y.py")], cwd="/w/b"),
                           cl("user", "2026-03-02T10:01:02Z", [result("t2")], cwd="/w/b")])
        self.assertEqual([p for p, _ in edits_of(evs)], ["/w/a/x.py", "/w/b/y.py"])

    def test_relative_path_without_folder_is_unassigned(self):
        evs = self.codex([{"timestamp": "2026-03-02T10:00:00Z", "type": "session_meta", "payload": {"id": "s"}},
                          filechange("2026-03-02T10:02:00Z", {"x.py": {}})])
        sheet, _ = run(profile([("Root", "/", None)]), evs)
        self.assertEqual(sheet["history"]["points"], 0)
        self.assertEqual(sheet["unassigned"]["edits"], 1)


if __name__ == "__main__":
    unittest.main()
