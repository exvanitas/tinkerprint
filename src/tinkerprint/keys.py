"""Storage keys: which saved history, last-build pointer and sheets folder belong to a profile file.

A profile file gets a key the first time it is built: its stem and a hash of its real path, as
tinkerprint 0.1 made them, so an existing user's history carries over as it is. profiles.json in
the data folder records each key's file and a signature of what the profile is. When a file moves,
its key follows it, but only when its old path is gone and its signature is unchanged. Two profile
files that both exist never share a key.
"""
from __future__ import annotations

import hashlib
import json
import os

from .datadir import _write, pretty
from .profile import Profile, is_key, profile_id

REGISTRY = "profiles.json"


def signature(profile: Profile) -> str:
    """What a profile is, apart from where its file lives: its name, set, work flag, identity and
    project names. Roots, parts and weights can change without making it another profile, but
    they do not decide a move either."""
    what = [profile.name, profile.set, profile.work, sorted(profile.emails), sorted(profile.names),
            sorted(p.name for p in profile.projects)]
    return hashlib.sha256(json.dumps(what, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def _path(home: str) -> str:
    return os.path.join(home, REGISTRY)


def read_registry(home: str) -> dict:
    """{key: {"path": real path, "sig": signature}}. A missing or unreadable file is empty. A row
    whose key is not one profile_id makes is dropped, so no key from this file reaches a path."""
    try:
        with open(_path(home), encoding="utf-8") as f:
            data = json.load(f)
        rows = data.get("profiles") if isinstance(data, dict) else None
    except (OSError, ValueError):
        return {}
    if not isinstance(rows, dict):
        return {}
    return {k: v for k, v in rows.items() if is_key(k) and isinstance(v, dict) and isinstance(v.get("path"), str)}


def write_registry(home: str, rows: dict) -> None:
    os.makedirs(home, exist_ok=True)
    _write(_path(home), pretty({"v": 1, "profiles": rows}))


def _used(home: str, key: str) -> bool:
    """Whether a key already holds anything in the data folder."""
    return any(os.path.lexists(p) for p in (os.path.join(home, "history", key),
                                            os.path.join(home, "last-build", key + ".json"),
                                            os.path.join(home, "sheets", key)))


def lookup(home: str, path: str) -> str:
    """The key of a profile file by its path alone, without reading or writing anything else.
    For forget, whose profile file may be gone."""
    real = os.path.realpath(os.path.expanduser(path))
    for key, row in sorted(read_registry(home).items()):
        if row["path"] == real:
            return key
    return profile_id(real)


def resolve(home: str, profile: Profile, write: bool = True) -> tuple:
    """(key, the old path when the file moved, else None). Records the key unless write is False."""
    real = profile.source
    rows = read_registry(home)
    sig = signature(profile)
    moved = None
    key = next((k for k, r in sorted(rows.items()) if r["path"] == real), None)
    if key is None:
        own = profile_id(real)
        # The 0.1 key of this path, unless it now belongs to a file that moved away from here.
        if own not in rows and _used(home, own):
            key = own
    if key is None:
        gone = [k for k, r in sorted(rows.items()) if r.get("sig") == sig and not os.path.lexists(r["path"])]
        if len(gone) == 1:
            key, moved = gone[0], rows[gone[0]]["path"]
    if key is None:
        salt = 0
        while True:
            key = profile_id(real, salt)
            if key not in rows and (salt == 0 or not _used(home, key)):
                break
            salt += 1
    if write and rows.get(key) != {"path": real, "sig": sig}:
        rows[key] = {"path": real, "sig": sig}
        write_registry(home, rows)
    return key, moved


def adopt(home: str, profile: Profile, write: bool = True):
    """Set profile.id to its storage key. Returns the old path when the file moved, else None.
    A profile that did not come from a file keeps the id it has."""
    if not profile.source:
        return None
    profile.id, moved = resolve(home, profile, write)
    return moved


def forget_key(home: str, key: str) -> None:
    """Drop one key from the registry, so its file starts afresh."""
    rows = read_registry(home)
    if key in rows:
        del rows[key]
        if rows:
            write_registry(home, rows)
        else:
            os.remove(_path(home))
