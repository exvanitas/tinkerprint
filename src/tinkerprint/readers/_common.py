"""Shared reader helpers: the field formats every reader schema uses, presence slots, hashing."""
from __future__ import annotations

import hashlib
import os
import re
from contextlib import contextmanager
from datetime import timezone

from ..timeutil import iso, parse_ts

# Every real UTC offset is a multiple of 15 minutes and rollover hours are whole hours, so a
# 15-minute UTC slot never straddles a profile day boundary. Presence kept per slot, model and
# folder places every observation on the right profile day without keeping every line time.
SLOT_MINUTES = 15

# ---------------------------------------------------------------- field formats
# A schema keeps a field only when it has the declared type and format. Anything else is dropped.

_ID = re.compile(r"^[A-Za-z0-9._:@/+=-]{1,200}$")
_MODEL = re.compile(r"^[A-Za-z0-9._:@+-]+(?:/[A-Za-z0-9._:@+-]+)?$")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


_VERSION = re.compile(r"^[0-9][0-9A-Za-z.+-]{0,31}$")


def version_text(v) -> str:
    """A log format version like 2.0.14 or 0.46.0-alpha.1, or ''. Anything else is dropped."""
    return v if isinstance(v, str) and _VERSION.match(v) else ""


def text(v) -> str:
    """A non-empty string field, or ''. Other types never become strings."""
    return v if isinstance(v, str) and v else ""


def ident(v) -> str:
    """An id: letters, digits and . _ : @ / + = -, at most 200 characters. Free text never passes."""
    return v if isinstance(v, str) and _ID.match(v) else ""


def model_id(v) -> str:
    """A model id: letters, digits and . _ - : @ +, at most one /, none leading, at most 80 characters."""
    return v if isinstance(v, str) and len(v) <= 80 and _MODEL.match(v) else ""


def path_text(v) -> str:
    """A file path string with no NUL or control characters, at most 4096 characters."""
    return v if isinstance(v, str) and v and len(v) <= 4096 and not _CONTROL.search(v) else ""


def abs_path(v) -> str:
    p = path_text(v)
    return p if p and os.path.isabs(p) else ""


def when(v):
    """A timestamp field: a string that parses, or None."""
    return parse_ts(v) if isinstance(v, str) else None


def get_str(d, key) -> str:
    return text(d.get(key)) if isinstance(d, dict) else ""


def get_id(d, key) -> str:
    return ident(d.get(key)) if isinstance(d, dict) else ""


def get_dict(d, key) -> dict:
    v = d.get(key) if isinstance(d, dict) else None
    return v if isinstance(v, dict) else {}


def get_list(d, key) -> list:
    v = d.get(key) if isinstance(d, dict) else None
    return v if isinstance(v, list) else []


def resolve(path: str, cwd: str) -> str:
    """Absolute paths stay. Relative paths join the folder current at that event, unnormalized,
    so '..' resolves after symlinks. With no known folder they stay relative, which no profile
    root matches: unassigned."""
    if os.path.isabs(path) or not cwd:
        return path
    return os.path.join(cwd, path)


# ---------------------------------------------------------------- health

def new_health() -> dict:
    """Counts a reader keeps about one log, for the build's reader health line. Never any text
    but version numbers. lines: lines or rows seen. records: those of a shape the reader knows.
    tool_calls: tool calls of any kind. edit_calls: calls or records of an edit kind it knows."""
    return {"lines": 0, "records": 0, "tool_calls": 0, "edit_calls": 0, "versions": set()}


# ---------------------------------------------------------------- presence

def presence(slots: dict, dt, model: str, folder: str) -> None:
    """Record presence: the earliest time per (UTC 15-minute slot, model, folder)."""
    u = dt.astimezone(timezone.utc)
    key = (u.strftime("%Y%m%d%H") + f"{u.minute // SLOT_MINUTES:d}", model, folder)
    ts = iso(dt)
    old = slots.get(key)
    if old is None or parse_ts(ts) < parse_ts(old):
        slots[key] = ts


# ---------------------------------------------------------------- streams

@contextmanager
def closing(f):
    """Close a file the reader opened. A caller's stream stays the caller's to close."""
    try:
        yield f
    finally:
        if hasattr(f, "close") and not isinstance(f, HashingStream):
            f.close()


class HashingStream:
    """Byte lines of a file, hashed as the reader takes them. The digest and size cover exactly
    the bytes the reader parsed, never bytes that arrived after it stopped."""

    def __init__(self, f):
        self.f = f
        self.h = hashlib.sha256()
        self.size = 0

    def __iter__(self):
        for line in self.f:
            self.h.update(line)
            self.size += len(line)
            yield line

    def digest(self) -> str:
        return self.h.hexdigest()
