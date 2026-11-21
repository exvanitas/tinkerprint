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
from ._common import closing as _closing, get_dict, get_id, get_list, get_str, presence, resolve

EDIT_TOOLS = {"Edit": "file_path", "Write": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}
LINE_TYPES = {"user", "assistant", "system", "attachment"}
# Prefilter for speed only: a line that can be one of LINE_TYPES has this somewhere, whatever its
# key order or spacing. Every line that passes is parsed in full before anything is recorded.
_MAYBE = re.compile(rb'"type"\s*:\s*"(?:user|assistant|system|attachment)"')


def transcript_files(base: str) -> list:
    files = glob.glob(os.path.join(glob.escape(base), "*", "*.jsonl"))
    files += glob.glob(os.path.join(glob.escape(base), "*", "*", "subagents", "*.jsonl"))
    return sorted(files)


def read_file(path: str, stream=None) -> list:
    """stream: an iterable of the file's byte lines, when the caller hashes what is parsed."""
    stem = os.path.splitext(os.path.basename(path))[0]
    session = ""
    cwd = ""
    slots: dict = {}
    pending: dict = {}   # tool_use id -> (path, model)
    edits: dict = {}     # tool_use id -> (ts, path, model)
    if stream is None:
        try:
            f = open(path, "rb")
        except OSError:
            return []
    else:
        f = stream
    with _closing(f):
        for raw in f:
            if not _MAYBE.search(raw):
                continue
            try:
                d = json.loads(raw.decode("utf-8", "replace"))
            except ValueError:
                continue
            kind_line = get_str(d, "type")
            if kind_line not in LINE_TYPES:
                continue
            session = session or get_id(d, "sessionId")
            if get_str(d, "cwd"):
                cwd = os.path.normpath(d["cwd"])
            dt = parse_ts(get_str(d, "timestamp") or None)
            msg = get_dict(d, "message")
            # A model belongs only to the assistant record that names it.
            model = ""
            if kind_line == "assistant":
                m = get_str(msg, "model")
                if m and not m.startswith("<"):
                    model = m
            if dt is not None:
                presence(slots, dt, model, cwd)
            for item in get_list(msg, "content"):
                if not isinstance(item, dict):
                    continue
                kind = get_str(item, "type")
                if kind_line == "assistant" and kind == "tool_use":
                    name = get_str(item, "name")
                    tid = get_id(item, "id")
                    if name in EDIT_TOOLS and tid:
                        p = get_str(get_dict(item, "input"), EDIT_TOOLS[name])
                        if p:
                            pending[tid] = (resolve(p, cwd), model)
                elif kind_line == "user" and kind == "tool_result":
                    tid = get_id(item, "tool_use_id")
                    if tid in pending:
                        p, m = pending.pop(tid)
                        # Success only when the error flag is absent or literally false.
                        if item.get("is_error", False) is False and dt is not None:
                            edits[tid] = (iso(dt), p, m)
    session = session or stem
    out = []
    for (_, m, folder), ts in slots.items():
        out.append(Event(ts=ts, source="claude", kind="session", path=folder, session=session,
                         harness="claude", model=m, actor="agent"))
    for tid, (ts, p, m) in edits.items():
        out.append(Event(ts=ts, source="claude", kind="edit", path=p, session=session,
                         harness="claude", model=m, actor="agent", op=tid))
    return sorted(set(out))
