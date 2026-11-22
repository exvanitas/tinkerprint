"""forget: delete what tinkerprint keeps in its data folder, for one profile or for all.

It deletes only what it recognizes as its own: the harness cache, saved sheets, last-build
pointers and, with --all, the default sheets folder. A folder holding anything else is left
alone and named. Repos, agent logs, profiles and --out folders are never touched.
"""
from __future__ import annotations

import os
import re
import shutil

_TMP = re.compile(r"^\..+\.tmp$")
_CACHE = re.compile(r"^(claude|codex)\.json$")
_SEASON = re.compile(r"^(start|\d{4}-\d{2}-\d{2})_(now|\d{4}-\d{2}-\d{2})$")
_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")
_KEY = re.compile(r"^[a-z0-9-]+-[0-9a-f]{8}$")  # a profile's storage key: see profile.profile_id
_POINTER = re.compile(r"^[a-z0-9-]+-[0-9a-f]{8}\.json$")
OUTPUTS = {"sheet.json", "changes.json", "sheet.html", "card.svg", "portrait.png"}


def _names(path: str) -> list | None:
    try:
        return os.listdir(path)
    except OSError:
        return None


def _real_dir(path: str) -> bool:
    return os.path.isdir(path) and not os.path.islink(path)


def _files_like(path: str, ok) -> bool:
    names = _names(path)
    return names is not None and all(
        (ok(n) or _TMP.match(n)) and os.path.isfile(os.path.join(path, n)) and not os.path.islink(os.path.join(path, n))
        for n in names)


def _profile_history(path: str) -> bool:
    names = _names(path)
    return names is not None and all(_SEASON.match(n) and _real_dir(os.path.join(path, n))
                                     and _files_like(os.path.join(path, n), _DAY.match) for n in names)


def _ours(path: str, kind: str) -> bool:
    """Whether path holds only what tinkerprint writes there."""
    if os.path.islink(path):
        return kind == "pointer"
    if kind == "pointer":
        return os.path.isfile(path)
    if not _real_dir(path):
        return False
    if kind == "cache":
        return _files_like(path, _CACHE.match)
    if kind == "pointers":
        return _files_like(path, _POINTER.match)
    if kind == "profile-history":
        return _profile_history(path)
    if kind == "history":
        names = _names(path)
        return names is not None and all(_KEY.match(n) and _real_dir(os.path.join(path, n))
                                         and _profile_history(os.path.join(path, n)) for n in names)
    if kind == "sheets":
        names = _names(path)
        return names is not None and all(_KEY.match(n) and _real_dir(os.path.join(path, n))
                                         and _files_like(os.path.join(path, n), lambda x: x in OUTPUTS)
                                         for n in names)
    raise ValueError(kind)


def _count(path: str) -> int:
    if not os.path.isdir(path) or os.path.islink(path):
        return 1
    return sum(len(files) for _, _, files in os.walk(path))


def plan(home: str, profile_key: str | None):
    """(to delete, left alone): lists of (path, what it is). profile_key None means everything."""
    items = [(os.path.join(home, "cache"), "cache", "the harness cache, shared by all profiles. Rebuilt from "
                                                     "the logs, but sessions kept from deleted logs are lost")]
    if profile_key is None:
        items += [(os.path.join(home, "history"), "history", "saved sheets for every profile"),
                  (os.path.join(home, "last-build"), "pointers", "where each profile's last build went"),
                  (os.path.join(home, "sheets"), "sheets", "sheets built without --out")]
    else:
        items += [(os.path.join(home, "history", profile_key), "profile-history",
                   "this profile's saved sheets, for \"what changed\""),
                  (os.path.join(home, "last-build", profile_key + ".json"), "pointer",
                   "where this profile's last build went")]
    delete, keep = [], []
    for path, kind, what in items:
        if not os.path.lexists(path):
            continue
        (delete if _ours(path, kind) else keep).append((path, what))
    return delete, keep


def remove(items) -> None:
    for path, _ in items:
        if os.path.islink(path) or not os.path.isdir(path):
            os.unlink(path)
        else:
            shutil.rmtree(path)


def forget(home: str, profile_key: str | None, yes: bool) -> list:
    """The lines to print. Deletes only when yes is true."""
    delete, keep = plan(home, profile_key)
    lines = []
    if delete:
        head = "Deleted" if yes else "This deletes"
        lines.append(f"{head}, in {home}:")
        rows = []
        for path, what in delete:
            n = _count(path)
            suffix = os.sep if os.path.isdir(path) and not os.path.islink(path) else ""
            rows.append((os.path.relpath(path, home) + suffix, f"{what} ({n} file{'s' if n != 1 else ''})"))
        width = max(len(r) for r, _ in rows)
        lines += [f"  {r:<{width}}  {w}" for r, w in rows]
    else:
        lines.append(f"Nothing to forget in {home}.")
    for path, _ in keep:
        lines.append(f"Left alone: {path} holds files tinkerprint did not write.")
    if profile_key is not None:
        sheets = os.path.join(home, "sheets", profile_key)
        if os.path.lexists(sheets):
            lines.append(f"Kept: {sheets}, this profile's sheets. Delete them yourself, or use --all.")
    lines.append("Never touched: your repos, agent logs, profiles and --out folders.")
    if delete and not yes:
        lines.append("Run it again with --yes to delete them.")
    if delete and yes:
        remove(delete)
        if profile_key is None:
            try:
                os.rmdir(home)
            except OSError:
                pass
    return lines
