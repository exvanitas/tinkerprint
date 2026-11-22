"""What a picture shows: the look a class gives, the stat ranking the art uses, and the pack's colors.

Everything here is a pure function of its arguments. The drawings themselves are in keepsake.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..sets import GENERALIST, PAIR, SPECIALIST, stats_of


@dataclass(frozen=True)
class Look:
    """What a portrait shows. Looks follow class shape only, never level or points."""
    set_name: str
    kind: str | None          # specialist, pair, generalist, or None when unclassed
    top: str | None           # outfit
    item: str | None          # held item
    trim: tuple = ()          # multiclass stats, cape then hem


def art_rank(pcts: dict, set_name: str) -> list:
    """Stats with a nonzero rounded share, highest first, ties in the set's order. The sheet and the
    card both rank this way, so the card's portrait always matches the sheet's."""
    order = stats_of(set_name)
    return [s for s in sorted(order, key=lambda s: (-pcts.get(s, 0), order.index(s))) if pcts.get(s, 0) > 0]


def look_for(set_name: str, kind: str | None, stats: list, ranked: list, multi: list | None = None) -> Look:
    """kind and stats as in a class record. ranked from art_rank."""
    def by_rank(xs):
        return sorted(xs, key=lambda s: ranked.index(s) if s in ranked else 99 + stats_of(set_name).index(s))

    trim = tuple(by_rank(multi)) if multi else ()
    if kind == "specialist":
        top = stats[0]
        rest = [s for s in ranked if s != top]
        return Look(set_name, kind, top, rest[0] if rest else top, trim)
    if kind == "pair":
        a, b = by_rank(stats)
        return Look(set_name, kind, a, b, trim)
    if kind == "generalist":
        return Look(set_name, kind, ranked[0] if ranked else None, None, ())
    return Look(set_name, None, None, None, ())


_BY_NAME: dict = {}


def class_by_name(set_name: str, name: str):
    """(kind, stats) for a class name of a set, or None. Class names are unique within a set."""
    if not _BY_NAME:
        for sname in SPECIALIST:
            table = {}
            for stat, n in SPECIALIST[sname].items():
                table[n] = ("specialist", [stat])
            for pair, n in PAIR[sname].items():
                table[n] = ("pair", list(pair))
            table[GENERALIST[sname]] = ("generalist", [])
            _BY_NAME[sname] = table
    return _BY_NAME.get(set_name, {}).get(name)


def _ramp(pack, stat):
    return pack["stat_colors"].get(stat) or pack["wanderer_colors"]


def palette(pack: dict, look: Look | None = None) -> dict:
    """The figure's dyes: A B C F the outfit, X Y Z H the equipment, T U the cape, V W its hem."""
    if look and look.kind in ("specialist", "pair"):
        a = _ramp(pack, look.top)
        x = _ramp(pack, look.item)
    else:
        a = pack["wanderer_colors"]
        x = _ramp(pack, look.top) if look and look.top else a
    pal = dict(zip("ABCF", a))
    pal.update(zip("XYZH", x))
    trim = look.trim if look else ()
    t = _ramp(pack, trim[0]) if trim else a
    v = _ramp(pack, trim[1]) if len(trim) > 1 else t
    pal.update({"T": t[0], "U": t[1], "V": v[0], "W": v[1]})
    return pal


# The room's case has 18 cubbies.
CUBBIES = 18


def shelf_counts(ranked_pcts: list, slots: int = 16) -> list:
    """How many trinkets each stat puts on the shelves: share of the slots, at least one each."""
    out = []
    for stat, p in ranked_pcts:
        if p <= 0:
            continue
        out.append((stat, max(1, round(p / 100 * slots))))
    total = 0
    trimmed = []
    for stat, n in out:
        n = min(n, CUBBIES - total)
        if n <= 0:
            break
        trimmed.append((stat, n))
        total += n
    return trimmed


def banner_figure_box(pack: dict, fig) -> tuple:
    """Where the room places the figure: (x, y) on the 252 x 72 banner."""
    return 116 - fig.w // 2, 65 - fig.h + fig.h // 10


def stat_ramp(pack: dict, stat: str) -> list:
    """A stat's four colors, highlight to deep shadow. The sheet and card tint each stat with them."""
    return list(_ramp(pack, stat))
