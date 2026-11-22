"""Saved sheets for "what changed". Never an input to sheet.json.

Each successful build saves its sheet under the profile file's key and the season, named by the
build's as-of date. A build compares against the newest saved sheet whose as-of date is earlier
than its own, so an earlier --as-of never compares against a later sheet.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import date

from .datadir import _write, pretty, season_key
from .projects import canonical

_NAME = re.compile(r"(\d{4}-\d{2}-\d{2})\.json")


def _h(x) -> str:
    return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:16]


def scope_digests(profile) -> dict:
    """Short digests of what decides which history a profile reads and how it scores, apart from
    the set (see score.SCOPE_PARTS). Kept only in the private saved copy of a sheet, never in
    sheet.json, so "what changed" can say when they differ."""
    projects = [[p.name, [[x.path, x.stats] for x in p.parts], p.stats, [[o.glob, o.stats] for o in p.overrides]]
                for p in profile.projects]
    return {
        "projects": _h(projects),
        "roots": _h(sorted([p.name, sorted(canonical(r) for r in p.roots)] for p in profile.projects)),
        "identity": _h([sorted(profile.emails), sorted(profile.names), sorted(profile.bots)]),
        "harnesses": _h([[profile.claude, profile.claude_dir if profile.claude else ""],
                         [profile.codex, profile.codex_dir if profile.codex else ""],
                         [profile.agy, profile.agy_db if profile.agy else ""]]),
        "days": _h([profile.timezone, profile.rollover_hour]),
    }


class History:
    def __init__(self, home: str, profile_key: str, season):
        self.dir = os.path.join(home, "history", profile_key, season_key(season))

    def previous(self, as_of: date):
        """(as-of date string, sheet) of the newest usable saved sheet before as_of, or (None,
        None). A file named for no real date, or one that will not load, is passed over."""
        try:
            names = os.listdir(self.dir)
        except OSError:
            return None, None
        days = sorted((m.group(1) for m in map(_NAME.fullmatch, names) if m), reverse=True)
        for d in days:
            try:
                if date.fromisoformat(d) >= as_of:
                    continue
            except ValueError:
                continue  # like 2026-02-31
            try:
                with open(os.path.join(self.dir, d + ".json"), encoding="utf-8") as f:
                    sheet = json.load(f)
            except (OSError, ValueError, RecursionError):
                continue
            if isinstance(sheet, dict):
                return d, sheet
        return None, None

    def save(self, as_of: date, sheet: dict) -> str:
        os.makedirs(self.dir, exist_ok=True)
        path = os.path.join(self.dir, as_of.isoformat() + ".json")
        _write(path, pretty(sheet))
        return path
