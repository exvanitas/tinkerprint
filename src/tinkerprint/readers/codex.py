"""Codex reader: rollouts under ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl.

Schema. Records it accepts, field by field. Any other record or field is dropped.
  line:            dict with type in KNOWN, payload: dict, timestamp: ISO string
  session_meta:    id: id, cwd: absolute path, originator: id, timestamp: ISO string,
                   cli_version: version, for reader health only
  turn_context:    model: model id, cwd: absolute path
  item_completed:  item {type: FileChange, status: completed, call_id: id, id: id, changes}
  patch_apply_end: success: true, call_id: id, changes
  changes:         a path map {path: change object}, a single change object {path: path, ...},
                   or a list of single change objects. A change object may name move_path: path.
                   The shape decides which, and a malformed entry is dropped.

A change counts once per call id (item id when no call id), at its first completion. A model
belongs only to the turn that names it. Tool call inputs and outputs are never read.
"""
from __future__ import annotations

import glob
import json
import os

from ..events import Event
from ..timeutil import iso
from ._common import abs_path, closing, get_dict, get_id, get_str, model_id, new_health, path_text, presence
from ._common import resolve, version_text, when

KNOWN = {"session_meta", "turn_context", "response_item", "event_msg", "compacted"}


def rollout_files(base: str) -> list:
    return sorted(glob.glob(os.path.join(glob.escape(base), "**", "rollout-*.jsonl"), recursive=True))


def _single(change) -> list:
    if not isinstance(change, dict):
        return []
    p = path_text(change.get("path"))
    if not p:
        return []
    out = [p]
    mp = path_text(change.get("move_path"))
    if mp:
        out.append(mp)
    return out


def change_paths(changes) -> list:
    """Paths from a changes record, told apart by shape."""
    if isinstance(changes, list):
        return [p for c in changes for p in _single(c)]
    if not isinstance(changes, dict):
        return []
    if changes and all(isinstance(v, dict) for v in changes.values()):
        out = []
        for k, v in changes.items():
            p = path_text(k)
            if p:
                out.append(p)
                mp = path_text(v.get("move_path"))
                if mp:
                    out.append(mp)
        return out
    if "path" in changes:
        return _single(changes)
    return []


def read_file(path: str, stream=None, health: dict | None = None) -> list:
    """stream: an iterable of the file's byte lines, when the caller hashes what is parsed.
    health: a dict from new_health() to count into."""
    hc = health if health is not None else new_health()
    session = ""
    cwd = ""
    origin = ""
    model = ""
    slots: dict = {}
    edits: dict = {}   # (change id, path) -> (ts, model)
    if stream is None:
        try:
            f = open(path, "rb")
        except OSError:
            return []
    else:
        f = stream
    with closing(f):
        for n, raw in enumerate(f):
            if raw.strip():
                hc["lines"] += 1
            try:
                d = json.loads(raw.decode("utf-8", "replace"))
            except ValueError:
                continue
            t = get_str(d, "type")
            if t not in KNOWN or not isinstance(d.get("payload"), dict):
                continue  # only whole, recognized records place presence
            p = d["payload"]
            hc["records"] += 1
            if t == "response_item" and get_str(p, "type").endswith("_call"):
                hc["tool_calls"] += 1
            elif t == "event_msg" and (get_str(p, "type") == "patch_apply_end" or (
                    get_str(p, "type") == "item_completed" and get_str(get_dict(p, "item"), "type") == "FileChange")):
                hc["edit_calls"] += 1
            dt = when(d.get("timestamp"))
            record_model = ""
            if t == "session_meta":
                v = version_text(p.get("cli_version"))
                if v:
                    hc["versions"].add(v)
                session = session or get_id(p, "id")
                origin = origin or get_id(p, "originator")
                cwd = cwd or abs_path(p.get("cwd"))
                if dt is None:
                    dt = when(p.get("timestamp"))
            elif t == "turn_context":
                model = model_id(p.get("model"))  # this turn's model, or none
                record_model = model
                cwd = abs_path(p.get("cwd")) or cwd
            if dt is None:
                continue
            presence(slots, dt, record_model, cwd)
            if t != "event_msg":
                continue
            kind = get_str(p, "type")
            found = []
            op = ""
            if kind == "item_completed":
                item = get_dict(p, "item")
                if get_str(item, "type") == "FileChange" and get_str(item, "status") == "completed":
                    found = change_paths(item.get("changes"))
                    op = get_id(item, "call_id") or get_id(item, "id")
            elif kind == "patch_apply_end" and p.get("success") is True:
                found = change_paths(p.get("changes"))
                op = get_id(p, "call_id")
            op = op or f"line{n}"
            for fp in found:
                fp = resolve(fp, cwd)
                if not fp:
                    continue  # not a local path
                key = (op, fp)
                if key not in edits:
                    edits[key] = (iso(dt), model)
    if not session:
        session = get_id({"s": os.path.splitext(os.path.basename(path))[0]}, "s") or "session"
    out = []
    for (_, m, folder), ts in slots.items():
        out.append(Event(ts=ts, source="codex", kind="session", path=folder, session=session,
                         harness="codex", model=m, actor="agent", origin=origin))
    for (op, fp), (ts, m) in edits.items():
        out.append(Event(ts=ts, source="codex", kind="edit", path=fp, session=session,
                         harness="codex", model=m, actor="agent", origin=origin, op=op))
    return sorted(set(out))
