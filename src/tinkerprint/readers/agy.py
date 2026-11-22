"""Antigravity reader (experimental, off by default): presence only.

Schema: conversation_id: id, workspace_uris: JSON list of file:// URIs naming local absolute
folders, last_modified_time: timestamp. Any other value is dropped.

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
from ._common import ident, path_text


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
    return path if path and pathmod.isabs(path) else None


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
        if isinstance(cid, int) and not isinstance(cid, bool):
            cid = str(cid)
        cid = ident(cid)
        if not cid or not isinstance(ts, (str, int, float)) or isinstance(ts, bool):
            continue
        dt = parse_ts(ts)
        if dt is None:
            continue
        folders = []
        if isinstance(uris, (str, bytes)) and uris:
            try:
                folders = json.loads(uris)
            except ValueError:
                folders = []
        if not isinstance(folders, list):
            folders = []
        # No readable folder: presence stays unassigned.
        paths = sorted({p for p in (_uri_path(u) for u in folders if isinstance(u, str)) if p}) or [""]
        for p in paths:
            out.append(Event(ts=iso(dt), source="agy", kind="session", path=p, session=cid,
                             harness="agy", actor="agent"))
    return sorted(set(out))
