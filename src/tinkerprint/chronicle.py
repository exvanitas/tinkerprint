"""The chronicle: one chapter per calendar quarter over all history, each with the class its own
points would give under the same class rules. Runs of quiet quarters collapse into one rest.

It reads the per-day points that scoring already made, so it adds no rule about points.
"""
from __future__ import annotations

import math
from collections import defaultdict
from datetime import date

from .classes import card_pct, multiclass, pick_class
from .sets import stats_of


def _quarter(d: date) -> tuple:
    return (d.year, (d.month - 1) // 3)


def _next(q: tuple) -> tuple:
    return (q[0] + 1, 0) if q[1] == 3 else (q[0], q[1] + 1)


def _bounds(q: tuple) -> tuple:
    y, i = q
    start = date(y, 3 * i + 1, 1)
    end = date(y + 1, 1, 1) if i == 3 else date(y, 3 * i + 4, 1)
    return start.isoformat(), date.fromordinal(end.toordinal() - 1).isoformat()


def _label(q: tuple) -> str:
    return f"{q[0]} Q{q[1] + 1}"


def _cls(c):
    return {"kind": c["kind"], "stats": list(c["stats"]), "name": c["name"]} if c else None


def chronicle(day_points: dict, set_name: str) -> list:
    """day_points: {day: {project: {stat or "": points}}}, as scoring builds it."""
    stats = stats_of(set_name)
    by_q = defaultdict(list)
    for d in sorted(day_points):
        by_q[_quarter(d)].append(d)
    if not by_q:
        return []
    out: list = []
    rest = None
    q, last = min(by_q), max(by_q)
    while q <= last:
        days = by_q.get(q)
        if not days:
            if rest is None:
                rest = {"rest": True, "label": _label(q), "from": _bounds(q)[0], "quarters": 0}
                out.append(rest)
            rest["quarters"] += 1
            rest["to"] = _bounds(q)[1]
            rest["label_to"] = _label(q)
            q = _next(q)
            continue
        rest = None
        parts = {s: [] for s in stats}
        for d in days:
            for pname in sorted(day_points[d]):
                for s, v in sorted(day_points[d][pname].items(), key=lambda kv: str(kv[0])):
                    if s:
                        parts[s].append(v)
        pts = {s: math.fsum(parts[s]) for s in stats}
        total = math.fsum(pts[s] for s in stats)
        shares = {s: (pts[s] / total if total > 0 else 0.0) for s in stats}
        cls = pick_class(shares, set_name)
        multi = multiclass(shares, set_name, cls)
        start, end = _bounds(q)
        out.append({
            "label": _label(q),
            "from": start,
            "to": end,
            "active_days": len(days),
            "class": _cls(cls),
            "close": (cls.get("close") or {}).get("name") if cls else None,
            "multiclass": list(multi["stats"]) if multi else None,
            "shares": {s: card_pct(shares[s]) for s in stats if card_pct(shares[s]) > 0},
        })
        q = _next(q)
    return out
