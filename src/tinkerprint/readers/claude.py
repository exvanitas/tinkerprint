"""Claude Code reader: session transcripts under ~/.claude/projects.

Keeps session id, line times, the folder current at each line, model ids and the file paths of
Edit, Write, MultiEdit and NotebookEdit calls whose result came back without an error. The edit
counts at the result's time. Message text, tool inputs other than the path, and tool output are
never kept.
Subagent transcripts (<session>/subagents/*.jsonl) belong to their parent session.
"""
from __future__ import annotations

import glob
import json
import os
import re

from ..events import Event
from ..timeutil import iso, parse_ts
from ._common import presence, resolve, text

EDIT_TOOLS = {"Edit": "file_path", "Write": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}
LINE_TYPES = {"user", "assistant", "system", "attachment"}
# Prefilter for speed only: a line that can be one of LINE_TYPES has this somewhere, whatever its
# key order or spacing. Every line that passes is parsed in full before anything is recorded.
_MAYBE = re.compile(rb'"type"\s*:\s*"(?:user|assistant|system|attachment)"')


def transcript_files(base: str) -> list:
    files = glob.glob(os.path.join(glob.escape(base), "*", "*.jsonl"))
    files += glob.glob(os.path.join(glob.escape(base), "*", "*", "subagents", "*.jsonl"))
    return sorted(files)


def read_file(path: str) -> list:
    stem = os.path.splitext(os.path.basename(path))[0]
    session = ""
    cwd = ""
    model = ""
    slots: dict = {}
    pending: dict = {}   # tool_use id -> (path, model)
    edits: dict = {}     # tool_use id -> (ts, path, model)
    try:
        f = open(path, "rb")
    except OSError:
        return []
    with f:
        for raw in f:
            if not _MAYBE.search(raw):
                continue
            try:
                d = json.loads(raw.decode("utf-8", "replace"))
            except ValueError:
                continue
            if not isinstance(d, dict) or d.get("type") not in LINE_TYPES:
                continue
            session = session or text(d.get("sessionId"))
            if text(d.get("cwd")):
                cwd = os.path.normpath(d["cwd"])
            ts = d.get("timestamp")
            dt = parse_ts(ts) if isinstance(ts, str) else None
            msg = d.get("message") if isinstance(d.get("message"), dict) else {}
            if d["type"] == "assistant":
                m = text(msg.get("model"))
                if m and not m.startswith("<"):
                    model = m
            if dt is not None:
                presence(slots, dt, model, cwd)
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            for item in content:
                if not isinstance(item, dict):
                    continue
                kind = item.get("type")
                if d["type"] == "assistant" and kind == "tool_use":
                    name = item.get("name")
                    tid = text(item.get("id"))
                    inp = item.get("input") if isinstance(item.get("input"), dict) else {}
                    if isinstance(name, str) and name in EDIT_TOOLS and tid:
                        p = text(inp.get(EDIT_TOOLS[name]))
                        if p:
                            pending[tid] = (resolve(p, cwd), model)
                elif d["type"] == "user" and kind == "tool_result":
                    tid = text(item.get("tool_use_id"))
                    if tid in pending:
                        p, m = pending.pop(tid)
                        if item.get("is_error") is not True and dt is not None:
                            edits[tid] = (iso(dt), p, m)
    session = session or stem
    out = []
    for (_, m, folder), ts in slots.items():
        out.append(Event(ts=ts, source="claude", kind="session", path=folder, session=session,
                         harness="claude", model=m, actor="agent"))
    for ts, p, m in edits.values():
        out.append(Event(ts=ts, source="claude", kind="edit", path=p, session=session,
                         harness="claude", model=m, actor="agent"))
    return sorted(set(out))
