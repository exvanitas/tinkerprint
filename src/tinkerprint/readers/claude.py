"""Claude Code reader: session transcripts under ~/.claude/projects.

Schema. Records it accepts, field by field. Any other record or field is dropped.
  line:        dict with type in {user, assistant, system, attachment}
               sessionId: id      cwd: absolute path      timestamp: ISO string
               message: dict
  assistant:   message.model: model id
               message.content: list of tool_use {id: id, name: Edit|Write|MultiEdit|NotebookEdit,
                                                  input: {file_path | notebook_path: path}}
  user:        message.content: list of tool_result {tool_use_id: id, is_error: absent or false}

An edit counts when its result comes back with no error, at the result's time, in the session of
the record that asked for it. A model belongs only to the assistant record that names it.
Subagent transcripts (<session>/subagents/*.jsonl) fall back to their parent session.
Message text, tool inputs other than the path, and tool output are never kept.
"""
from __future__ import annotations

import glob
import json
import os
import re

from ..events import Event
from ..timeutil import iso
from ._common import abs_path, closing, get_dict, get_id, get_list, get_str, ident, model_id, path_text, presence
from ._common import resolve, when

EDIT_TOOLS = {"Edit": "file_path", "Write": "file_path", "MultiEdit": "file_path", "NotebookEdit": "notebook_path"}
LINE_TYPES = {"user", "assistant", "system", "attachment"}
# Prefilter for speed only: a line that can be one of LINE_TYPES has this somewhere, whatever its
# key order or spacing. Every line that passes is parsed in full before anything is recorded.
_MAYBE = re.compile(rb'"type"\s*:\s*"(?:user|assistant|system|attachment)"')


def transcript_files(base: str) -> list:
    files = glob.glob(os.path.join(glob.escape(base), "*", "*.jsonl"))
    files += glob.glob(os.path.join(glob.escape(base), "*", "*", "subagents", "*.jsonl"))
    return sorted(files)


def fallback_session(path: str) -> str:
    """The parent session folder for a subagent transcript, else the file name."""
    parts = os.path.normpath(path).split(os.sep)
    if len(parts) >= 3 and parts[-2] == "subagents" and ident(parts[-3]):
        return parts[-3]
    return ident(os.path.splitext(parts[-1])[0]) or "session"


def read_file(path: str, stream=None) -> list:
    """stream: an iterable of the file's byte lines, when the caller hashes what is parsed."""
    fallback = fallback_session(path)
    cwd = ""
    slots: dict = {}     # (slot, model, folder) -> ts, per session
    pending: dict = {}   # tool_use id -> (session, path, model)
    edits: dict = {}     # tool_use id -> (session, ts, path, model)
    if stream is None:
        try:
            f = open(path, "rb")
        except OSError:
            return []
    else:
        f = stream
    with closing(f):
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
            session = get_id(d, "sessionId") or fallback
            folder = abs_path(d.get("cwd"))
            if folder:
                cwd = folder
            dt = when(d.get("timestamp"))
            msg = get_dict(d, "message")
            model = model_id(msg.get("model")) if kind_line == "assistant" else ""
            if dt is not None:
                presence(slots.setdefault(session, {}), dt, model, cwd)
            for item in get_list(msg, "content"):
                if not isinstance(item, dict):
                    continue
                kind = get_str(item, "type")
                if kind_line == "assistant" and kind == "tool_use":
                    name = get_str(item, "name")
                    tid = get_id(item, "id")
                    if name in EDIT_TOOLS and tid:
                        p = path_text(get_dict(item, "input").get(EDIT_TOOLS[name]))
                        if p:
                            pending[tid] = (session, resolve(p, cwd), model)
                elif kind_line == "user" and kind == "tool_result":
                    tid = get_id(item, "tool_use_id")
                    if tid in pending:
                        s, p, m = pending.pop(tid)
                        # Success only when the error flag is absent or literally false.
                        if item.get("is_error", False) is False and dt is not None:
                            edits[tid] = (s, iso(dt), p, m)
    out = []
    for session, sl in slots.items():
        for (_, m, folder), ts in sl.items():
            out.append(Event(ts=ts, source="claude", kind="session", path=folder, session=session,
                             harness="claude", model=m, actor="agent"))
    for tid, (session, ts, p, m) in edits.items():
        out.append(Event(ts=ts, source="claude", kind="edit", path=p, session=session,
                         harness="claude", model=m, actor="agent", op=tid))
    return sorted(set(out))
