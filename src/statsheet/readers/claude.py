"""Claude Code reader: session transcripts under ~/.claude/projects.

Keeps session id, line times, cwd, model ids and the file paths of Edit, Write, MultiEdit and
NotebookEdit calls. Message text, tool inputs other than the path, and tool output are never kept.
Subagent transcripts (<session>/subagents/*.jsonl) belong to their parent session.
"""
from __future__ import annotations

import glob
import json
import os

from ..events import Event
from ..timeutil import iso, parse_ts
from ._common import bucket as _bucket

EDIT_TOOLS = {"Edit": "file_path", "Write": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}
LINE_TYPES = {"user", "assistant", "system", "attachment"}


def transcript_files(base: str) -> list:
    files = glob.glob(os.path.join(glob.escape(base), "*", "*.jsonl"))
    files += glob.glob(os.path.join(glob.escape(base), "*", "*", "subagents", "*.jsonl"))
    return sorted(files)


def read_file(path: str) -> list:
    stem = os.path.splitext(os.path.basename(path))[0]
    session = ""
    cwd = ""
    buckets: dict = {}   # hour key -> (ts, model)
    edits = []           # (ts, tool_use id, path, model)
    errors = set()
    model = ""
    try:
        f = open(path, encoding="utf-8", errors="replace")
    except OSError:
        return []
    with f:
        for line in f:
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if not isinstance(d, dict) or d.get("type") not in LINE_TYPES:
                continue
            if not session and isinstance(d.get("sessionId"), str):
                session = d["sessionId"]
            if not cwd and isinstance(d.get("cwd"), str) and d["cwd"]:
                cwd = os.path.normpath(d["cwd"])
            dt = parse_ts(d.get("timestamp"))
            msg = d.get("message") if isinstance(d.get("message"), dict) else {}
            if d["type"] == "assistant":
                m = msg.get("model")
                if isinstance(m, str) and m and not m.startswith("<"):
                    model = m
            if dt is not None:
                _bucket(buckets, dt, model)
            content = msg.get("content")
            if not isinstance(content, list):
                continue
            for item in content:
                if not isinstance(item, dict):
                    continue
                if d["type"] == "assistant" and item.get("type") == "tool_use" and item.get("name") in EDIT_TOOLS:
                    inp = item.get("input") if isinstance(item.get("input"), dict) else {}
                    p = inp.get(EDIT_TOOLS[item["name"]])
                    if isinstance(p, str) and p and dt is not None:
                        edits.append((iso(dt), item.get("id", ""), p, model))
                elif d["type"] == "user" and item.get("type") == "tool_result" and item.get("is_error") is True:
                    errors.add(item.get("tool_use_id"))
    session = session or stem
    base_cwd = cwd or "/"
    out = []
    for _, (ts, m) in sorted(buckets.items()):
        out.append(Event(ts=ts, source="claude", kind="session", path=base_cwd, session=session,
                         harness="claude", model=m, actor="agent"))
    for ts, tid, p, m in edits:
        if tid and tid in errors:
            continue
        if not os.path.isabs(p):
            p = os.path.join(base_cwd, p)
        out.append(Event(ts=ts, source="claude", kind="edit", path=os.path.normpath(p), session=session,
                         harness="claude", model=m, actor="agent"))
    return out
