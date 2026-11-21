"""Class rules: specialist, pair, generalist, multiclass, and naming a close runner-up.

No rule looks at an earlier sheet. When the runner-up is within 2 points of share of the
winner, the sheet names both: "Artificer, close to Alchemist". Thresholds compare exactly, and
only exactly equal shares tie.
"""
from __future__ import annotations

from .sets import GENERALIST, PAIR, SPECIALIST, pair_name, stats_of

SPECIALIST_AT = 0.50
GENERALIST_UNDER = 0.20
RUNNER_UP_AT = 0.10
MULTICLASS_AT = 0.10
CLOSE = 0.02


def ranked(shares: dict, set_name: str) -> list:
    """Stats by full-precision share, highest first. Equal shares go to the earlier stat in the set."""
    order = stats_of(set_name)
    return sorted(order, key=lambda s: (-shares.get(s, 0.0), order.index(s)))


def make_class(kind: str, stats: list, set_name: str) -> dict:
    if kind == "generalist":
        name = GENERALIST[set_name]
        stats = []
    elif kind == "specialist":
        name = SPECIALIST[set_name][stats[0]]
    else:
        order = stats_of(set_name)
        stats = sorted(stats, key=order.index)
        name = PAIR[set_name][tuple(stats)]
    return {"kind": kind, "stats": list(stats), "name": name}


def _with_close(cls: dict, close: dict | None) -> dict:
    out = dict(cls, close=close)
    out["display"] = f"{cls['name']}, close to {close['name']}" if close else cls["name"]
    return out


def raw_class(shares: dict, set_name: str) -> dict | None:
    if sum(shares.values()) <= 0:
        return None
    r = ranked(shares, set_name)
    top, second = shares.get(r[0], 0.0), shares.get(r[1], 0.0)
    if top >= SPECIALIST_AT:
        return make_class("specialist", [r[0]], set_name)
    if top <= GENERALIST_UNDER:
        return make_class("generalist", [], set_name)
    if second >= RUNNER_UP_AT:
        return make_class("pair", [r[0], r[1]], set_name)
    return make_class("specialist", [r[0]], set_name)


def pick_class(shares: dict, set_name: str) -> dict | None:
    """The class, plus the runner-up when it sits within 2 points of share.

    A pair's runner-up swaps its second stat for the third. A specialist's runner-up is the
    second stat as a specialist. A generalist has none.
    """
    cls = raw_class(shares, set_name)
    if not cls:
        return None
    r = ranked(shares, set_name)
    v = [shares.get(s, 0.0) for s in r]
    close = None
    if cls["kind"] == "pair" and v[1] - v[2] <= CLOSE:
        close = make_class("pair", [r[0], r[2]], set_name)
    elif cls["kind"] == "specialist" and v[0] - v[1] <= CLOSE:
        close = make_class("specialist", [r[1]], set_name)
    return _with_close(cls, close)


def multiclass(shares: dict, set_name: str, main: dict | None) -> dict | None:
    """The third and fourth stats, when each holds 10% or more, with a close runner-up named
    the same way: the fourth stat swapped for the fifth."""
    if not main or main["kind"] == "generalist":
        return None
    r = ranked(shares, set_name)
    v = [shares.get(s, 0.0) for s in r]
    if v[2] < MULTICLASS_AT or v[3] < MULTICLASS_AT:
        return None
    a, b = sorted([r[2], r[3]], key=stats_of(set_name).index)
    multi = {"stats": [a, b], "name": pair_name(set_name, a, b)}
    close = None
    if v[3] - v[4] <= CLOSE:
        c, d = sorted([r[2], r[4]], key=stats_of(set_name).index)
        close = {"stats": [c, d], "name": pair_name(set_name, c, d)}
    return _with_close(multi, close)


def class_key(cls: dict | None):
    if not cls:
        return None
    return (cls["kind"], tuple(cls["stats"]))
