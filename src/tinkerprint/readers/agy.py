"""Antigravity reader (experimental, off by default): presence only.

Reads conversation_id, workspace_uris and last_modified_time from conversation_summaries.
Titles, previews, summaries and the search index are never read.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3

from ..events import Event
from ..timeutil import iso, parse_ts


def _uri_path(uri: str) -> str | None:
    if not isinstance(uri, str) or not uri.startswith("file://"):
        return None
    p = uri[len("file://"):]
    if not p.startswith("/"):
        p = p[p.find("/"):] if "/" in p else ""
    raw = re.sub(r"%([0-9A-Fa-f]{2})", lambda m: chr(int(m.group(1), 16)), p)
    try:
        raw = raw.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return os.path.normpath(raw) if raw else None


def _ro_uri(path: str) -> str:
    q = path.replace("%", "%25").replace("?", "%3f").replace("#", "%23")
    return f"file:{q}?mode=ro"


def read_db(path: str) -> list:
    if not os.path.isfile(path):
        return []
    try:
        con = sqlite3.connect(_ro_uri(path), uri=True)
    except sqlite3.Error:
        return []
    out = []
    try:
        rows = con.execute(
            "select conversation_id, workspace_uris, last_modified_time from conversation_summaries").fetchall()
    except sqlite3.Error:
        rows = []
    finally:
        con.close()
    for cid, uris, ts in rows:
        dt = parse_ts(ts)
        if dt is None:
            continue
        try:
            folders = json.loads(uris) if uris else []
        except ValueError:
            folders = []
        paths = sorted({p for p in (_uri_path(u) for u in folders if isinstance(u, str)) if p}) or ["/"]
        for p in paths:
            out.append(Event(ts=iso(dt), source="agy", kind="session", path=p, session=str(cid),
                             harness="agy", actor="agent"))
    return sorted(set(out))
