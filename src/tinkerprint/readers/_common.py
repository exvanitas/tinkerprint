"""Shared reader helpers: the field formats every reader schema uses, presence slots, hashing."""
from __future__ import annotations

import hashlib
import json
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

_ID = re.compile(r"[A-Za-z0-9._:@/+=-]{1,200}")
_MODEL = re.compile(r"[A-Za-z0-9._:@+-]+(?:/[A-Za-z0-9._:@+-]+)?")
_CONTROL = re.compile(r"[\x00-\x1f\x7f]")


_VERSION = re.compile(r"[0-9][0-9A-Za-z.+-]{0,31}")


def version_text(v) -> str:
    """A log format version like 2.0.14 or 0.46.0-alpha.1, or ''. Anything else is dropped."""
    return v if isinstance(v, str) and _VERSION.fullmatch(v) else ""


def text(v) -> str:
    """A non-empty string field, or ''. Other types never become strings."""
    return v if isinstance(v, str) and v else ""


def ident(v) -> str:
    """An id: letters, digits and . _ : @ / + = -, at most 200 characters. Free text never passes."""
    return v if isinstance(v, str) and _ID.fullmatch(v) else ""


def model_id(v) -> str:
    """A model id: letters, digits and . _ - : @ +, at most one /, none leading, at most 80 characters."""
    return v if isinstance(v, str) and len(v) <= 80 and _MODEL.fullmatch(v) else ""


def path_text(v) -> str:
    """A file path string with no NUL or control characters, at most 4096 characters."""
    return v if isinstance(v, str) and v and len(v) <= 4096 and not _CONTROL.search(v) else ""


# The platform's path rules. Tests set ntpath here to check the Windows rules on any OS.
PATHMOD = os.path

_DRIVE_PATH = re.compile(r"^[A-Za-z]:[\\/]")
# \\server\share\..., with either separator. Device namespaces (\\?\, \\.\) never match.
_UNC_PATH = re.compile(r"^[\\/]{2}(?![?.][\\/])[^\\/]+[\\/][^\\/]+")
_RESERVED = ({"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"} | {f"COM{c}" for c in "123456789\u00b9\u00b2\u00b3"}
             | {f"LPT{c}" for c in "123456789\u00b9\u00b2\u00b3"})


def local_path(p: str, pathmod=None) -> str:
    """p when it is a plain path, else ''. Every path a log gives goes through this before
    anything touches the file system with it. On Windows a plain path is a drive path like C:\\x,
    or a share path like \\\\server\\share\\x, which the resolver follows only inside a root
    the profile names on that share. A device path (\\\\.\\ or \\\\?\\), a path rooted on no drive,
    one naming a device such as NUL or COM1, and one with a colon past the drive, as a stream
    (file.txt:stream) or a device (NUL:) has, are not."""
    pm = pathmod or PATHMOD
    if not p or pm.sep != "\\":
        return p
    if _DRIVE_PATH.match(p):
        rest = p[3:]
    elif _UNC_PATH.match(p):
        rest = p[2:]
    else:
        return ""
    if ":" in rest:
        return ""
    for part in re.split(r"[\\/]", rest):
        if part.split(".", 1)[0].rstrip(" ").upper() in _RESERVED:
            return ""
    return p


def abs_path(v, pathmod=None) -> str:
    """An absolute local path, or ''."""
    pm = pathmod or PATHMOD
    p = path_text(v)
    return local_path(p, pm) if p and pm.isabs(p) else ""


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


def resolve(path: str, cwd: str, pathmod=None) -> str:
    """Absolute paths stay. Relative paths join the folder current at that event, unnormalized,
    so '..' resolves after symlinks. With no known folder they stay relative, which no profile
    root matches: unassigned. '' when the result is not a local path (see local_path)."""
    pm = pathmod or PATHMOD
    if pm.isabs(path):
        return local_path(path, pm)
    if not cwd:
        return path
    return local_path(pm.join(cwd, path), pm)


# ---------------------------------------------------------------- health

def new_health() -> dict:
    """Counts a reader keeps about one log, for the build's reader health line. Never any text
    but version numbers. lines: lines or rows seen. records: those of a shape the reader knows.
    tool_calls: tool calls of any kind. edit_calls: calls or records of an edit kind it knows.
    rejected: records skipped because they would not decode, nested too deep or ran too long.
    The Claude reader counts only lines that name one of its record types: a line that names
    none is no record of its own and is passed over uncounted, decodable or not."""
    return {"lines": 0, "records": 0, "tool_calls": 0, "edit_calls": 0, "rejected": 0, "versions": set()}


# ---------------------------------------------------------------- records

# The longest record a reader parses. Real records are far shorter, even ones holding a whole file.
MAX_RECORD = 32 << 20


class TooLong(bytes):
    """Stands for a line longer than MAX_RECORD: its start only, never parsed."""


def decode(raw):
    """One JSON record, or None when it is too long, will not decode or nests too deep for the
    decoder. A bad record is skipped and counted, never the end of a read."""
    if isinstance(raw, TooLong) or len(raw) > MAX_RECORD:
        return None
    try:
        return json.loads(raw.decode("utf-8", "replace") if isinstance(raw, bytes) else raw)
    except (ValueError, RecursionError):
        return None


def byte_lines(f, seen=None):
    """The lines of a binary file, each read at most MAX_RECORD bytes at a time, so one huge line
    never sits in memory whole. A longer line comes back once as a TooLong. seen(chunk) gets every
    byte read, in order."""
    while True:
        line = f.readline(MAX_RECORD + 1)
        if not line:
            return
        if seen:
            seen(line)
        if len(line) <= MAX_RECORD or line.endswith(b"\n"):
            yield line
            continue
        while True:  # the rest of the long line, read and dropped
            more = f.readline(1 << 20)
            if seen and more:
                seen(more)
            if not more or more.endswith(b"\n"):
                break
        yield TooLong(line[:64])


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
        yield from byte_lines(self.f, self._seen)

    def _seen(self, chunk: bytes) -> None:
        self.h.update(chunk)
        self.size += len(chunk)

    def digest(self) -> str:
        return self.h.hexdigest()
