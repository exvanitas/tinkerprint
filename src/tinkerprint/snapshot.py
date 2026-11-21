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
    def __init__(self, home: str, profile_id: str, season):
        self.dir = os.path.join(home, "profiles", profile_id, "snapshots", season_key(season))

    def _index(self) -> list:
        try:
            with open(os.path.join(self.dir, "index.json"), encoding="utf-8") as f:
                data = json.load(f)
            return [k for k in data if isinstance(k, str)] if isinstance(data, list) else []
        except (OSError, ValueError):
            return []

    def previous(self, key: str) -> dict | None:
        for k in reversed(self._index()):
            if k == key:
                continue
            try:
                with open(os.path.join(self.dir, k + ".json"), encoding="utf-8") as f:
                    return json.load(f)
            except (OSError, ValueError):
                continue
        return None

    def save(self, key: str, sheet: dict) -> str:
        os.makedirs(self.dir, exist_ok=True)
        path = os.path.join(self.dir, key + ".json")
        _write(path, pretty(sheet))
        index = [k for k in self._index() if k != key] + [key]
        _write(os.path.join(self.dir, "index.json"), pretty(index))
        return path


def _write(path: str, text: str) -> None:
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)
