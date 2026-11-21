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
from ._common import presence, resolve, text


def rollout_files(base: str) -> list:
    return sorted(glob.glob(os.path.join(glob.escape(base), "**", "rollout-*.jsonl"), recursive=True))


def change_paths(changes) -> list:
    """Paths from a structured changes record: {path: {...}} or [{"path": ...}]. Moves add their target."""
    out = []
    if isinstance(changes, dict):
        for k, v in changes.items():
            if isinstance(k, str) and k:
                out.append(k)
            if isinstance(v, dict) and text(v.get("move_path")):
                out.append(v["move_path"])
    elif isinstance(changes, list):
        for c in changes:
            if isinstance(c, dict):
                for key in ("path", "move_path"):
                    if text(c.get(key)):
                        out.append(c[key])
    return out


def read_file(path: str) -> list:
    session = ""
    cwd = ""
    origin = ""
    model = ""
    slots: dict = {}
    edits: dict = {}   # (record id, path) -> (ts, model)
    try:
        f = open(path, "rb")
    except OSError:
        return []
    with f:
        for n, raw in enumerate(f):
            try:
                d = json.loads(raw.decode("utf-8", "replace"))
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            t = d.get("type")
            p = d.get("payload") if isinstance(d.get("payload"), dict) else {}
            dt = parse_ts(d.get("timestamp")) if isinstance(d.get("timestamp"), str) else None
            if t == "session_meta":
                session = session or text(p.get("id"))
                origin = origin or text(p.get("originator"))
                if not cwd and text(p.get("cwd")):
                    cwd = os.path.normpath(p["cwd"])
                if dt is None and isinstance(p.get("timestamp"), str):
                    dt = parse_ts(p["timestamp"])
            elif t == "turn_context":
                model = text(p.get("model")) or model
                if text(p.get("cwd")):
                    cwd = os.path.normpath(p["cwd"])
            if dt is None:
                continue
            presence(slots, dt, model, cwd)
            if t != "event_msg":
                continue
            kind = p.get("type")
            found = []
            rid = ""
            if kind == "item_completed":
                item = p.get("item") if isinstance(p.get("item"), dict) else {}
                if item.get("type") == "FileChange" and item.get("status") == "completed":
                    found = change_paths(item.get("changes"))
                    rid = text(item.get("id")) or f"line{n}"
            elif kind == "patch_apply_end" and p.get("success") is True:
                found = change_paths(p.get("changes"))
                rid = text(p.get("call_id")) or f"line{n}"
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
    for (_, fp), (ts, m) in edits.items():
        out.append(Event(ts=ts, source="codex", kind="edit", path=fp, session=session,
                         harness="codex", model=m, actor="agent", origin=origin))
    return sorted(set(out))
