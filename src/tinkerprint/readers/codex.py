"""Codex reader: rollouts under ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl.

Keeps the session_meta id, cwd, originator and time, line times, turn_context models and folders,
and the file paths of confirmed changes. A change counts only from a structured completion
record: a completed FileChange item, or a successful patch_apply_end. Tool call inputs and
outputs are never read, so text inside them can never become a path.
"""
from __future__ import annotations

import glob
import json
import os

from ..events import Event
from ..timeutil import iso, parse_ts
from ._common import closing as _closing, get_dict, get_id, get_str, presence, resolve


def rollout_files(base: str) -> list:
    return sorted(glob.glob(os.path.join(glob.escape(base), "**", "rollout-*.jsonl"), recursive=True))


KNOWN = {"session_meta", "turn_context", "response_item", "event_msg", "compacted"}


def change_paths(changes) -> list:
    """Paths from a structured changes record. A map is {path: change}. A single change object
    ({"path": ..., ...}) or a list of them gives their "path" values. Moves add their target."""
    out = []
    if isinstance(changes, dict) and isinstance(changes.get("path"), str):
        changes = [changes]
    if isinstance(changes, dict):
        for k, v in changes.items():
            if isinstance(k, str) and k:
                out.append(k)
            if get_str(v, "move_path"):
                out.append(v["move_path"])
    elif isinstance(changes, list):
        for c in changes:
            for key in ("path", "move_path"):
                if get_str(c, key):
                    out.append(c[key])
    return out


def read_file(path: str, stream=None) -> list:
    """stream: an iterable of the file's byte lines, when the caller hashes what is parsed."""
    session = ""
    cwd = ""
    origin = ""
    model = ""
    slots: dict = {}
    edits: dict = {}   # (change id, path) -> (ts, model). One change seen in two records counts once.
    if stream is None:
        try:
            f = open(path, "rb")
        except OSError:
            return []
    else:
        f = stream
    with _closing(f):
        for n, raw in enumerate(f):
            try:
                d = json.loads(raw.decode("utf-8", "replace"))
            except ValueError:
                continue
            t = get_str(d, "type")
            if t not in KNOWN or not isinstance(d.get("payload"), dict):
                continue  # only whole, recognized records place presence
            p = d["payload"]
            dt = parse_ts(get_str(d, "timestamp") or None)
            if t == "session_meta":
                session = session or get_id(p, "id")
                origin = origin or get_id(p, "originator")
                if not cwd and get_str(p, "cwd"):
                    cwd = os.path.normpath(p["cwd"])
                if dt is None:
                    dt = parse_ts(get_str(p, "timestamp") or None)
            elif t == "turn_context":
                model = get_str(p, "model") or model
                if get_str(p, "cwd"):
                    cwd = os.path.normpath(p["cwd"])
            if dt is None:
                continue
            presence(slots, dt, model if t == "turn_context" else "", cwd)
            if t != "event_msg":
                continue
            kind = get_str(p, "type")
            found = []
            rid = ""
            if kind == "item_completed":
                item = get_dict(p, "item")
                if get_str(item, "type") == "FileChange" and get_str(item, "status") == "completed":
                    found = change_paths(item.get("changes"))
                    rid = get_id(item, "id") or get_id(item, "call_id") or f"line{n}"
            elif kind == "patch_apply_end" and p.get("success") is True:
                found = change_paths(p.get("changes"))
                rid = get_id(p, "call_id") or f"line{n}"
            for fp in found:
                key = (rid, resolve(fp, cwd))
                if key not in edits:
                    edits[key] = (iso(dt), model)
    if not session:
        session = os.path.splitext(os.path.basename(path))[0]
    out = []
    for (_, m, folder), ts in slots.items():
        out.append(Event(ts=ts, source="codex", kind="session", path=folder, session=session,
                         harness="codex", model=m, actor="agent", origin=origin))
    for (rid, fp), (ts, m) in edits.items():
        out.append(Event(ts=ts, source="codex", kind="edit", path=fp, session=session,
                         harness="codex", model=m, actor="agent", origin=origin, op=rid))
    return sorted(set(out))
