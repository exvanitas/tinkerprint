"""Antigravity reader (experimental, off by default): presence only.

Schema: conversation_id: id, workspace_uris: JSON list of file:// URIs naming local absolute
folders, last_modified_time: timestamp. Any other value is dropped.

Reads conversation_id, workspace_uris and last_modified_time from conversation_summaries.
Titles, previews, summaries and the search index are never read.
"""
from __future__ import annotations

import os
import re
import sqlite3

from ..events import Event
from ..timeutil import iso, parse_ts
from . import _common
from ._common import decode, ident, local_path, new_health, path_text


_DRIVE = re.compile(r"^/[A-Za-z]:(/|$)")


def _uri_path(uri: str, pathmod=os.path) -> str | None:
    """A local folder from a file:// URI. Percent escapes decode as UTF-8 bytes, literal characters
    stay as they are. A URI naming another host gives None. On Windows, file:///C:/x (or
    file:///c%3A/x) becomes C:\\x."""
    if not isinstance(uri, str) or not uri.startswith("file://"):
        return None
    p = uri[len("file://"):]
    if not p.startswith("/"):
        host, _, rest = p.partition("/")
        if host.lower() != "localhost" or not rest:
            return None
        p = "/" + rest
    raw = bytearray()
    i = 0
    while i < len(p):
        if p[i] == "%" and re.match(r"[0-9A-Fa-f]{2}", p[i + 1:i + 3]):
            raw.append(int(p[i + 1:i + 3], 16))
            i += 3
        else:
            raw += p[i].encode("utf-8", "surrogatepass")
            i += 1
    path = raw.decode("utf-8", "replace")
    if pathmod.sep == "\\":
        if _DRIVE.match(path):
            path = path[1:]
        path = path.replace("/", "\\")
    path = path_text(path)
    # A share, device or other path off this machine's disks never reaches the file system.
    return path if path and pathmod.isabs(path) and local_path(path, pathmod) else None


def _ro_uri(path: str, pathmod=os.path) -> str:
    """A read-only SQLite URI for a local file. On Windows, C:\\x\\db becomes file:///C:/x/db and
    \\\\server\\share\\db becomes file:////server/share/db, as SQLite's URI rules want."""
    q = path.replace("%", "%25").replace("?", "%3f").replace("#", "%23")
    if pathmod.sep == "\\":
        q = q.replace("\\", "/")
    if re.match(r"^[A-Za-z]:", q) and pathmod.sep == "\\":
        q = "///" + q
    elif q.startswith("//"):
        q = "//" + q  # an empty authority, so the path's own leading slashes stay in the path
    return f"file:{q}?mode=ro"


# The longest id or time value read. Real ones are far shorter.
_SHORT = 400


def _text(v):
    """A TEXT value fetched as bytes, as str. Raises ValueError when it is not UTF-8."""
    return v.decode("utf-8") if isinstance(v, bytes) else v


def _row(cid, uris, size, ts, hc: dict) -> list:
    """The events of one row. Raises ValueError for a row that will not decode."""
    cid, ts = _text(cid), _text(ts)
    if isinstance(cid, int) and not isinstance(cid, bool):
        cid = str(cid)
    cid = ident(cid)
    if not cid or not isinstance(ts, (str, int, float)) or isinstance(ts, bool):
        return []
    dt = parse_ts(ts)
    if dt is None:
        return []
    hc["records"] += 1
    folders = []
    if isinstance(uris, bytes) and uris:
        folders = decode(uris)
        if folders is None:
            hc["rejected"] += 1  # presence stays, unassigned
    elif uris is None and isinstance(size, int) and size > _common.MAX_RECORD:
        hc["rejected"] += 1
    if not isinstance(folders, list):
        folders = []
    # No readable folder: presence stays unassigned.
    paths = sorted({p for p in (_uri_path(u) for u in folders if isinstance(u, str)) if p}) or [""]
    return [Event(ts=iso(dt), source="agy", kind="session", path=p, session=cid, harness="agy", actor="agent")
            for p in paths]


def read_db(path: str, health: dict | None = None) -> list:
    """health: a dict from new_health() to count into. A database that opens but has no table of
    the expected shape counts its rows as none recognised and sets health["unreadable"]."""
    hc = health if health is not None else new_health()
    if not os.path.isfile(path):
        return []
    try:
        con = sqlite3.connect(_ro_uri(path), uri=True)
    except sqlite3.Error:
        hc["unreadable"] = True
        return []
    # Every text value comes back as bytes and is decoded here, one row at a time, so a row that
    # is not UTF-8 is counted and skipped and never ends the read.
    con.text_factory = bytes
    out = []
    try:
        # Lengths are measured in bytes, by SQLite, before any value is fetched. A folder list
        # longer than _common.MAX_RECORD, or an id or time longer than any real one, is never loaded.
        cur = con.execute(
            "select case when length(cast(conversation_id as blob)) <= ? then conversation_id end, "
            "case when length(cast(workspace_uris as blob)) <= ? then cast(workspace_uris as blob) end, "
            "length(cast(workspace_uris as blob)), "
            "case when length(cast(last_modified_time as blob)) <= ? then last_modified_time end "
            "from conversation_summaries", (_SHORT, _common.MAX_RECORD, _SHORT))
        while True:
            row = cur.fetchone()  # one row at a time: a large table never sits in memory whole
            if row is None:
                break
            hc["lines"] += 1
            try:
                out += _row(*row, hc)
            except (ValueError, TypeError, OverflowError):
                hc["rejected"] += 1
    except sqlite3.Error:
        hc["unreadable"] = True
    finally:
        con.close()
    return sorted(set(out))
