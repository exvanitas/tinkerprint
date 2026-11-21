"""Codex reader: rollouts under ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl.

Keeps the session_meta id, cwd, originator and time, line times, turn_context models, and the
file paths of applied patches when the log has them: FileChange items, and '*** Add File:',
'*** Update File:', '*** Delete File:' and '*** Move to:' lines in tool call inputs.
Without those the session is presence only. Nothing else from a call input is kept.
"""
from __future__ import annotations

import glob
import json
import os
import re

from ..events import Event
from ..timeutil import iso, parse_ts
from ._common import bucket as _bucket

_TS = re.compile(rb'^\{"timestamp":\s*"([^"]+)"')
_NEEDED = (b"session_meta", b"turn_context", b"*** ", b"FileChange")
_PATCH = re.compile(r"^\*\*\* (?:Add File|Update File|Delete File|Move to): (.+?)\s*$", re.M)


def rollout_files(base: str) -> list:
    return sorted(glob.glob(os.path.join(glob.escape(base), "**", "rollout-*.jsonl"), recursive=True))


def _strings(v):
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for x in v.values():
            yield from _strings(x)
    elif isinstance(v, list):
        for x in v:
            yield from _strings(x)


def _patch_paths(payload: dict) -> list:
    raw = payload.get("input") if "input" in payload else payload.get("arguments")
    texts = []
    if isinstance(raw, str):
        texts.append(raw)
        if raw[:1] in "{[":
            try:
                texts.extend(_strings(json.loads(raw)))
            except ValueError:
                pass
    else:
        texts.extend(_strings(raw))
    found = []
    for t in texts:
        if "*** " in t:
            found.extend(m.group(1) for m in _PATCH.finditer(t))
    return found


def read_file(path: str) -> list:
    session = ""
    cwd = ""
    origin = ""
    model = ""
    buckets: dict = {}
    edits = []
    try:
        f = open(path, "rb")
    except OSError:
        return []
    with f:
        for line in f:
            if not any(w in line for w in _NEEDED):
                # Presence only: the time sits first on every rollout line.
                m = _TS.match(line)
                dt = parse_ts(m.group(1).decode("ascii", "replace")) if m else None
                if dt is not None:
                    _bucket(buckets, dt, model)
                continue
            try:
                d = json.loads(line.decode("utf-8", "replace"))
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            t = d.get("type")
            p = d.get("payload") if isinstance(d.get("payload"), dict) else {}
            dt = parse_ts(d.get("timestamp"))
            if t == "session_meta":
                session = session or str(p.get("id") or "")
                if isinstance(p.get("cwd"), str) and p["cwd"]:
                    cwd = cwd or os.path.normpath(p["cwd"])
                origin = origin or str(p.get("originator") or "")
                dt = dt or parse_ts(p.get("timestamp"))
            elif t == "turn_context":
                if isinstance(p.get("model"), str) and p["model"]:
                    model = p["model"]
                if not cwd and isinstance(p.get("cwd"), str) and p["cwd"]:
                    cwd = os.path.normpath(p["cwd"])
            if dt is not None:
                _bucket(buckets, dt, model)
            if dt is None:
                continue
            pt = p.get("type")
            if t == "response_item" and pt in ("function_call", "custom_tool_call"):
                for fp in _patch_paths(p):
                    edits.append((iso(dt), fp, model))
            elif t == "event_msg" and pt == "item_completed":
                item = p.get("item") if isinstance(p.get("item"), dict) else {}
                if item.get("type") == "FileChange" and item.get("status") not in ("failed", "declined"):
                    changes = item.get("changes")
                    keys = list(changes) if isinstance(changes, dict) else [
                        c.get("path") for c in changes or [] if isinstance(c, dict)]
                    for fp in keys:
                        if isinstance(fp, str) and fp:
                            edits.append((iso(dt), fp, model))
    if not session:
        session = os.path.splitext(os.path.basename(path))[0]
    base_cwd = cwd or "/"
    out = []
    for _, (ts, m) in sorted(buckets.items()):
        out.append(Event(ts=ts, source="codex", kind="session", path=base_cwd, session=session,
                         harness="codex", model=m or model, actor="agent", origin=origin))
    for ts, fp, m in edits:
        if not os.path.isabs(fp):
            fp = os.path.join(base_cwd, fp)
        out.append(Event(ts=ts, source="codex", kind="edit", path=os.path.normpath(fp), session=session,
                         harness="codex", model=m or model, actor="agent", origin=origin))
    return sorted(set(out))
