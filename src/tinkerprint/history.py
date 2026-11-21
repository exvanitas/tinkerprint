"""Saved sheets for "what changed". Never an input to sheet.json.

Each successful build saves its sheet under the profile file's key and the season, named by the
build's as-of date. A build compares against the newest saved sheet whose as-of date is earlier
than its own, so an earlier --as-of never compares against a later sheet.
"""
from __future__ import annotations

import json
import os
import re
from datetime import date

from .datadir import _write, pretty, season_key

_NAME = re.compile(r"^(\d{4}-\d{2}-\d{2})\.json$")


class History:
    def __init__(self, home: str, profile_key: str, season):
        self.dir = os.path.join(home, "history", profile_key, season_key(season))

    def previous(self, as_of: date):
        """(as-of date string, sheet) of the newest saved sheet before as_of, or (None, None)."""
        try:
            names = os.listdir(self.dir)
        except OSError:
            return None, None
        days = sorted((m.group(1) for m in map(_NAME.match, names) if m), reverse=True)
        for d in days:
            if d >= as_of.isoformat():
                continue
            try:
                with open(os.path.join(self.dir, d + ".json"), encoding="utf-8") as f:
                    sheet = json.load(f)
            except (OSError, ValueError):
                continue
            if isinstance(sheet, dict):
                return d, sheet
        return None, None

    def save(self, as_of: date, sheet: dict) -> str:
        os.makedirs(self.dir, exist_ok=True)
        path = os.path.join(self.dir, as_of.isoformat() + ".json")
        _write(path, pretty(sheet))
        return path
