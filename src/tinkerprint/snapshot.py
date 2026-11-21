"""Snapshots: one saved sheet per distinct result, per profile and season, outside every repo.

A snapshot's key is a hash of the part of the sheet that does not depend on earlier snapshots.
The previous sheet is the most recent snapshot with a different key, so building twice from the
same inputs gives the same sheet.
"""
from __future__ import annotations

import hashlib
import json
import os


def data_home(override: str | None = None) -> str:
    if override:
        return os.path.abspath(os.path.expanduser(override))
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "tinkerprint")


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def pretty(obj) -> str:
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def core_key(core: dict) -> str:
    return hashlib.sha256(canonical(core).encode("utf-8")).hexdigest()[:20]


def season_key(season) -> str:
    frm, to = season
    return f"{frm.isoformat() if frm else 'start'}_{to.isoformat() if to else 'now'}"


class SnapshotStore:
    """Snapshots for one profile, set and season.

    Each result key pins the predecessor it was first compared with, so rebuilding the same
    inputs later compares with the same sheet and gives the same bytes.
    """

    def __init__(self, home: str, profile_id: str, season, set_name: str = ""):
        self.dir = os.path.join(home, "profiles", profile_id, "snapshots", season_key(season))
        self.meta = {"profile": profile_id, "set": set_name, "season": season_key(season)}

    def _index(self) -> dict:
        try:
            with open(os.path.join(self.dir, "index.json"), encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            data = None
        if not isinstance(data, dict):
            return {"order": [], "prev": {}}
        order = [k for k in data.get("order", []) if isinstance(k, str)]
        prev = {k: v for k, v in (data.get("prev") or {}).items()
                if isinstance(k, str) and (v is None or isinstance(v, str))}
        return {"order": order, "prev": prev}

    def load(self, key: str) -> dict | None:
        """A saved sheet, only when it belongs to this profile, set and season."""
        try:
            with open(os.path.join(self.dir, key + ".json"), encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return None
        if not isinstance(data, dict) or data.get("meta") != self.meta or not isinstance(data.get("sheet"), dict):
            return None
        return data["sheet"]

    def predecessor(self, key: str):
        """(key, sheet) of the sheet to compare with, or (None, None)."""
        idx = self._index()
        if key in idx["prev"]:
            pk = idx["prev"][key]
            return (pk, self.load(pk)) if pk else (None, None)
        for k in reversed(idx["order"]):
            if k != key:
                sheet = self.load(k)
                if sheet is not None:
                    return k, sheet
        return None, None

    def previous(self, key: str) -> dict | None:
        return self.predecessor(key)[1]

    def save(self, key: str, sheet: dict, prev_key: str | None) -> str:
        os.makedirs(self.dir, exist_ok=True)
        path = os.path.join(self.dir, key + ".json")
        _write(path, pretty({"meta": self.meta, "sheet": sheet}))
        idx = self._index()
        idx["prev"].setdefault(key, prev_key)
        idx["order"] = [k for k in idx["order"] if k != key] + [key]
        _write(os.path.join(self.dir, "index.json"), pretty(idx))
        return path


def inside_repo_or_root(path: str, roots=()) -> str | None:
    """Why a data folder may not live at path, or None when it may.

    The cache holds raw paths and session metadata, so it stays outside every git worktree
    and every profile root.
    """
    real = os.path.realpath(path)
    for root in roots:
        r = os.path.realpath(root)
        if real == r or real.startswith(r.rstrip("/") + "/"):
            return "it is inside a profile root"
    probe = real
    while True:
        if os.path.exists(os.path.join(probe, ".git")):
            return "it is inside a git worktree"
        parent = os.path.dirname(probe)
        if parent == probe:
            return None
        probe = parent


def _write(path: str, text: str) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)
