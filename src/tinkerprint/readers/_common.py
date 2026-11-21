"""Shared helpers for harness readers."""
from __future__ import annotations

import os
from datetime import timezone

from ..timeutil import iso

# Every real UTC offset is a multiple of 15 minutes and rollover hours are whole hours, so a
# 15-minute UTC slot never straddles a profile day boundary. Presence kept per slot, model and
# folder places every observation on the right profile day without keeping every line time.
SLOT_MINUTES = 15


def presence(slots: dict, dt, model: str, folder: str) -> None:
    """Record presence: the earliest time per (UTC 15-minute slot, model, folder)."""
    u = dt.astimezone(timezone.utc)
    key = (u.strftime("%Y%m%d%H") + f"{u.minute // SLOT_MINUTES:d}", model, folder)
    ts = iso(dt)
    old = slots.get(key)
    if old is None or ts < old:
        slots[key] = ts


def text(v) -> str:
    """A non-empty string field, or ''. Other types never become strings."""
    return v if isinstance(v, str) and v else ""


def resolve(path: str, cwd: str) -> str:
    """Absolute paths stay. Relative paths join the folder current at that event.
    With no known folder they stay relative, which no profile root matches: unassigned."""
    if os.path.isabs(path):
        return os.path.normpath(path)
    if cwd:
        return os.path.normpath(os.path.join(cwd, path))
    return os.path.normpath(path)
