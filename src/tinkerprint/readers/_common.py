"""Shared helpers for harness readers."""
from __future__ import annotations

import hashlib
import os
import re
from contextlib import contextmanager
from datetime import timezone

from ..timeutil import iso

# Every real UTC offset is a multiple of 15 minutes and rollover hours are whole hours, so a
# 15-minute UTC slot never straddles a profile day boundary. Presence kept per slot, model and
# folder places every observation on the right profile day without keeping every line time.
SLOT_MINUTES = 15


def presence(slots: dict, dt, model: str, folder: str) -> None:
    """Record presence: the earliest time per (UTC 15-minute slot, model, folder)."""
    u = dt.astimezone(timezone.utc)
    key = (u.strftime("%Y%m%d%H") + f"{u.minute // SLOT_MINUTES:d}", model, folder)
    ts = iso(dt)
    old = slots.get(key)
    if old is None or ts < old:
        slots[key] = ts


def text(v) -> str:
    """A non-empty string field, or ''. Other types never become strings."""
    return v if isinstance(v, str) and v else ""


def resolve(path: str, cwd: str) -> str:
    """Absolute paths stay. Relative paths join the folder current at that event.
    With no known folder they stay relative, which no profile root matches: unassigned."""
    if os.path.isabs(path):
        return os.path.normpath(path)
    if cwd:
        return os.path.normpath(os.path.join(cwd, path))
    return os.path.normpath(path)


def get_str(d, key) -> str:
    """d[key] when d is a dict and the value is a non-empty string, else ''."""
    return text(d.get(key)) if isinstance(d, dict) else ""


def get_dict(d, key) -> dict:
    v = d.get(key) if isinstance(d, dict) else None
    return v if isinstance(v, dict) else {}


def get_list(d, key) -> list:
    v = d.get(key) if isinstance(d, dict) else None
    return v if isinstance(v, list) else []


@contextmanager
def closing(f):
    """Close a file the reader opened. A caller's stream stays the caller's to close."""
    try:
        yield f
    finally:
        if hasattr(f, "close") and not isinstance(f, HashingStream):
            f.close()


class HashingStream:
    """Byte lines of a file, hashed as they are read, so a digest always matches what was parsed."""

    def __init__(self, f):
        self.f = f
        self.h = hashlib.sha256()

    def __iter__(self):
        for line in self.f:
            self.h.update(line)
            yield line

    def digest(self) -> str:
        for block in iter(lambda: self.f.read(1 << 20), b""):
            self.h.update(block)
        return self.h.hexdigest()


_ID = re.compile(r"^[A-Za-z0-9._:@/+=-]{1,200}$")


def ident(v) -> str:
    """An id-shaped string (session, call, item or originator id), or ''. Free text never passes."""
    return v if isinstance(v, str) and _ID.match(v) else ""


def get_id(d, key) -> str:
    return ident(d.get(key)) if isinstance(d, dict) else ""
