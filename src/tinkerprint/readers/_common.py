"""Shared helpers for harness readers."""
from __future__ import annotations

from datetime import timezone

from ..timeutil import iso


def bucket(buckets: dict, dt, model: str) -> None:
    """Presence in hour buckets: the earliest time in each UTC hour and the last model seen there.

    Hour buckets let any profile time zone and rollover hour place a session on the right days
    without keeping every line time.
    """
    key = dt.astimezone(timezone.utc).strftime("%Y%m%d%H")
    ts = iso(dt)
    b = buckets.get(key)
    if b is None:
        buckets[key] = [ts, model]
        return
    if ts < b[0]:
        b[0] = ts
    if model:
        b[1] = model
