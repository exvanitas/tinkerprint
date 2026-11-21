"""Class rules: specialist, pair, generalist, multiclass, and the 2-point hysteresis."""
from __future__ import annotations

from .sets import GENERALIST, PAIR, SPECIALIST, pair_name, stats_of

SPECIALIST_AT = 0.50
GENERALIST_UNDER = 0.20
RUNNER_UP_AT = 0.10
MULTICLASS_AT = 0.10
HYSTERESIS = 0.02
_TINY = 1e-9


def ranked(shares: dict, set_name: str) -> list:
    """Stats by share, highest first. Exact ties go to the earlier stat in the set's order."""
    order = stats_of(set_name)
    return sorted(order, key=lambda s: (-round(shares.get(s, 0.0), 9), order.index(s)))


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


def raw_class(shares: dict, set_name: str) -> dict | None:
    if sum(shares.values()) <= 0:
        return None
    r = ranked(shares, set_name)
    top, second = shares.get(r[0], 0.0), shares.get(r[1], 0.0)
    if top >= SPECIALIST_AT - _TINY:
        return make_class("specialist", [r[0]], set_name)
    if top <= GENERALIST_UNDER + _TINY:
        return make_class("generalist", [], set_name)
    if second >= RUNNER_UP_AT - _TINY:
        return make_class("pair", [r[0], r[1]], set_name)
    return make_class("specialist", [r[0]], set_name)


def multiclass(shares: dict, set_name: str, main: dict | None) -> dict | None:
    if not main or main["kind"] == "generalist":
        return None
    r = ranked(shares, set_name)
    a, b = r[2], r[3]
    if shares.get(a, 0.0) >= MULTICLASS_AT - _TINY and shares.get(b, 0.0) >= MULTICLASS_AT - _TINY:
        return {"stats": sorted([a, b], key=stats_of(set_name).index), "name": pair_name(set_name, a, b)}
    return None


def qualifies(cls: dict, shares: dict, set_name: str, slack: float) -> bool:
    """Whether shares still support a class when every threshold may miss by up to `slack`."""
    order = stats_of(set_name)
    vals = {s: shares.get(s, 0.0) for s in order}
    top = max(vals.values()) if vals else 0.0
    eps = slack + _TINY
    kind = cls.get("kind")
    if kind == "generalist":
        return top <= GENERALIST_UNDER + eps
    stats = [s for s in cls.get("stats", []) if s in vals]
    if kind == "specialist" and len(stats) == 1:
        s = stats[0]
        rest = max((v for k, v in vals.items() if k != s), default=0.0)
        if vals[s] < top - eps or vals[s] <= GENERALIST_UNDER - eps:
            return False
        return vals[s] >= SPECIALIST_AT - eps or rest < RUNNER_UP_AT + eps
    if kind == "pair" and len(stats) == 2:
        a, b = stats
        lo, hi = min(vals[a], vals[b]), max(vals[a], vals[b])
        third = max((v for k, v in vals.items() if k not in (a, b)), default=0.0)
        return (hi >= top - eps and lo >= third - eps and lo >= RUNNER_UP_AT - eps
                and top < SPECIALIST_AT + eps and top > GENERALIST_UNDER - eps)
    return False


def class_key(cls: dict | None):
    if not cls:
        return None
    return (cls["kind"], tuple(cls["stats"]))


def with_hysteresis(new: dict | None, prev: dict | None, shares: dict, set_name: str) -> tuple:
    """Keep the previous class unless the new one leads by more than 2 points of share.

    Returns (class, held) where held is True when the previous class was kept.
    """
    if not new or not prev or class_key(new) == class_key(prev):
        return new, False
    if prev.get("kind") not in ("specialist", "pair", "generalist"):
        return new, False
    try:
        kept = make_class(prev["kind"], list(prev.get("stats", [])), set_name)
    except (KeyError, IndexError):
        return new, False
    if qualifies(kept, shares, set_name, HYSTERESIS):
        return kept, True
    return new, False
