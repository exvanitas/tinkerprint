"""Compose pictures from a pack: portraits, familiars, icons, shelf trinkets and the banner scene.

Everything here is a pure function of its arguments. The only variation is a counter-mode
SHA-256 stream seeded from sheet fields, so the same sheet always gives the same pixels.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass

from ..sets import GENERALIST, PAIR, SPECIALIST, stats_of
from .pixels import Canvas, mix


@dataclass(frozen=True)
class Look:
    """What a portrait shows. Looks follow class shape only, never level or points."""
    set_name: str
    kind: str | None          # specialist, pair, generalist, or None when unclassed
    top: str | None           # outfit
    item: str | None          # held item
    trim: tuple = ()          # multiclass stats, cape then hem


def pct5(share: float) -> int:
    """The card's rounding: under 5% is 0, the rest round to the nearest 5%."""
    return 0 if share < 0.05 else int(round(share * 20)) * 5


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


# ------------------------------------------------------------------ palettes

def _ramp(pack, stat):
    return pack["stat_colors"].get(stat) or pack["wanderer_colors"]


def palette(pack: dict, look: Look) -> dict:
    pal = dict(pack["ink"])
    if look.kind in ("specialist", "pair"):
        a = _ramp(pack, look.top)
        x = _ramp(pack, look.item)
    else:
        a = pack["wanderer_colors"]
        x = _ramp(pack, look.top) if look.top else pack["wanderer_colors"]
    pal.update(zip("ABC", a))
    pal.update(zip("XYZ", x))
    t = _ramp(pack, look.trim[0]) if look.trim else a
    v = _ramp(pack, look.trim[1]) if len(look.trim) > 1 else t
    pal.update({"T": t[0], "U": t[1], "V": v[0], "W": v[1]})
    return pal


def _stamp(c: Canvas, pack: dict, name: str, pal: dict, dx: int = 0, dy: int = 0) -> None:
    part = pack["parts"][name]
    p = dict(pal, **part.get("palette", {}))
    c.stamp(part["rows"], p, part["at"][0] + dx, part["at"][1] + dy)


# ------------------------------------------------------------------ portrait

def figure(pack: dict, look: Look) -> Canvas:
    """The outlined figure on a clear 32 x 32 canvas."""
    w, h = pack["canvas"]
    c = Canvas(w, h)
    pal = palette(pack, look)
    if look.kind in ("specialist", "pair"):
        parts = pack["looks"]
        hat, body = parts[look.top]["hat"], parts[look.top]["body"]
        item = parts[look.item]["item"]
        back = None
    else:
        g = pack["generalist"]
        hat, body, item = g["hat"], g["body"], (g["item"] if look.kind else None)
        back = g["back"] if look.kind else None
    if look.trim:
        _stamp(c, pack, "cape", pal)
    if back:
        _stamp(c, pack, back, pal)
    _stamp(c, pack, "base", pal)
    _stamp(c, pack, body, pal)
    _stamp(c, pack, hat, pal)
    if item:
        _stamp(c, pack, item, pal)
        if not pack["parts"][item].get("cover"):
            _stamp(c, pack, "hand", pal)
    return c.outline(pack["outline"])


def plate(pack: dict, set_name: str, w: int = 32, h: int = 32) -> Canvas:
    sp = pack["sets"][set_name]
    c = Canvas(w, h, sp["plate"])
    c.rect(0, h - 5, w, 5, sp["floor"])
    shade = mix(sp["floor"], "#000000", 0.35)
    c.rect(10, h - 4, 12, 1, shade)
    c.rect(8, h - 3, 16, 1, shade)
    return c


def portrait(pack: dict, look: Look, scene: bool = True) -> Canvas:
    fig = figure(pack, look)
    if not scene:
        return fig
    c = plate(pack, look.set_name)
    c.paste(fig, 0, 1)
    return c


# ------------------------------------------------------------------ small sprites

def sprite(pack: dict, name: str, pal: dict | None = None) -> Canvas:
    """A part on its own canvas with a one-pixel margin, outlined."""
    part = pack["parts"][name]
    rows = part["rows"]
    c = Canvas(len(rows[0]) + 2, len(rows) + 2)
    p = dict(pack["ink"], **(pal or {}))
    p.update(part.get("palette", {}))
    c.stamp(rows, p, 1, 1)
    return c.outline(pack["outline"])


def familiar(pack: dict, harness: str) -> Canvas:
    fam = pack["familiars"]
    return sprite(pack, fam.get(harness) or fam["default"])


def icon(pack: dict, achievement: str) -> Canvas:
    ic = pack["icons"]
    return sprite(pack, ic.get(achievement) or ic["milestone"])


def trinket(pack: dict, stat: str) -> Canvas:
    x = _ramp(pack, stat)
    return sprite(pack, pack["looks"][stat]["trinket"], dict(zip("XYZ", x)))


def campfire(pack: dict) -> Canvas:
    return sprite(pack, "campfire")


# ------------------------------------------------------------------ banner

class Stream:
    """Deterministic choices from a seed string: SHA-256 in counter mode."""

    def __init__(self, seed: str):
        self.seed = seed.encode("utf-8")
        self.n = 0
        self.buf = b""

    def byte(self) -> int:
        if not self.buf:
            self.buf = hashlib.sha256(self.seed + self.n.to_bytes(8, "big")).digest()
            self.n += 1
        b, self.buf = self.buf[0], self.buf[1:]
        return b

    def below(self, n: int) -> int:
        return (self.byte() * 256 + self.byte()) % n

    def shuffle(self, xs: list) -> list:
        xs = list(xs)
        for i in range(len(xs) - 1, 0, -1):
            j = self.below(i + 1)
            xs[i], xs[j] = xs[j], xs[i]
        return xs


BANNER_W, BANNER_H = 224, 48
SHELF_SLOTS = [(44 + 9 * i, 17) for i in range(4)] + [(158 + 9 * i, 11) for i in range(7)] + \
              [(158 + 9 * i, 25) for i in range(7)]


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
        n = min(n, len(SHELF_SLOTS) - total)
        if n <= 0:
            break
        trimmed.append((stat, n))
        total += n
    return trimmed


def banner(pack: dict, look: Look, ranked_pcts: list, harnesses: list, seed: str) -> Canvas:
    """A workshop: shelves hold trinkets for the strongest stats, the figure stands on a rug in its
    top stat's colors, and each party harness sends its familiar."""
    sp = pack["sets"][look.set_name]
    rng = Stream("banner|" + seed)
    W, H = BANNER_W, BANNER_H
    c = Canvas(W, H, sp["wall"])
    # Wall: stone courses for the builder set, planks for the tinkerer set.
    if look.set_name == "builder":
        for y in range(3, 40, 6):
            c.rect(0, y, W, 1, sp["mortar"])
            off = 0 if (y // 6) % 2 else 8
            for x in range(off, W, 16):
                c.rect(x, y + 1, 1, 5, sp["mortar"])
            for x in range(off + 3, W, 16):
                if rng.below(5) == 0:
                    c.rect(x, y + 2, 6, 3, sp["wall2"])
    else:
        for x in range(0, W, 9):
            c.rect(x, 0, 1, 40, sp["mortar"])
            for y in (6, 30):
                c.set(x + 2, y + rng.below(3), sp["wall2"])
            if rng.below(3) == 0:
                c.rect(x + 3, 8 + rng.below(20), 3, 1, sp["wall2"])
    c.rect(0, 0, W, 3, sp["board2"])
    c.rect(0, 2, W, 1, mix(sp["board2"], "#000000", 0.3))
    # Floor.
    c.rect(0, 40, W, 8, sp["board"])
    c.rect(0, 40, W, 1, mix(sp["board"], "#ffffff", 0.15))
    for y in (43, 46):
        c.rect(0, y, W, 1, sp["board2"])
    for x in range(5, W, 23):
        c.rect(x + rng.below(6), 41 + 3 * rng.below(2), 1, 2, sp["board2"])
    # Window with a night sky.
    _window(c, pack, rng, 8, 7)
    # Shelves and trinkets.
    _shelf(c, pack, 42, 18, 38, sp)
    _shelf(c, pack, 156, 12, 65, sp)
    _shelf(c, pack, 156, 26, 65, sp)
    stock = []
    for stat, n in shelf_counts(ranked_pcts):
        stock += [stat] * n
    slots = rng.shuffle(range(len(SHELF_SLOTS)))[:len(stock)]
    for stat, slot in zip(stock, sorted(slots)):
        x, y = SHELF_SLOTS[slot]
        t = trinket(pack, stat)
        c.paste(t, x - 1, y - 9)
    # Workbench with the top stat's trinket.
    _bench(c, pack, 44, 32, sp)
    if ranked_pcts:
        c.paste(trinket(pack, ranked_pcts[0][0]), 52, 23)
    if len(ranked_pcts) > 1:
        c.paste(trinket(pack, ranked_pcts[1][0]), 62, 23)
    # Rug in the top stat's colors, then the figure.
    rug = _ramp(pack, look.top) if look.top else pack["wanderer_colors"]
    c.rect(88, 41, 32, 3, rug[1])
    c.rect(86, 42, 36, 1, rug[1])
    c.rect(90, 42, 28, 1, rug[0])
    for x in range(88, 120, 3):
        c.set(x, 41, rug[2])
        c.set(x + 1, 43, rug[2])
    c.paste(figure(pack, look), 88, 13)
    _pennant(c, pack, 134, 5, rug, _ramp(pack, look.item) if look.item else rug)
    # Familiars on the floor in front, right of the figure.
    x = 124
    for h in harnesses[:3]:
        f = familiar(pack, h)
        c.paste(f, x, 46 - f.h + 1)
        x += f.w + 1
    return c


def _window(c, pack, rng, x0, y0):
    w, h = 24, 22
    frame, dark = "#7d5432", "#5a3a22"
    c.rect(x0 - 2, y0 - 2, w + 4, h + 4, dark)
    c.rect(x0 - 1, y0 - 1, w + 2, h + 2, frame)
    for j in range(h):
        c.rect(x0, y0 + j, w, 1, mix("#16213d", "#3a4f80", j / h))
    for _ in range(9):
        c.set(x0 + rng.below(w), y0 + rng.below(h - 4), "#fff3c2")
    c.rect(x0 + 15, y0 + 3, 4, 4, "#f4ecc8")
    c.rect(x0 + 14, y0 + 4, 1, 2, "#f4ecc8")
    c.rect(x0 + 16, y0 + 3, 2, 1, "#ffffff")
    c.rect(x0 + 17, y0 + 4, 2, 2, mix("#f4ecc8", "#3a4f80", 0.5))
    c.rect(x0 + w // 2, y0, 1, h, frame)
    c.rect(x0, y0 + h // 2, w, 1, frame)
    c.rect(x0 - 3, y0 + h + 1, w + 6, 2, "#9a6a42")


def _pennant(c, pack, x, y, ramp, accent):
    """A wall hanging in the top stat's colors with the runner-up's diamond."""
    c.rect(x - 1, y, 14, 1, "#7d5432")
    c.set(x + 6, y - 1, "#7d5432")
    for j in range(14):
        inset = max(0, j - 9)
        c.rect(x + inset, y + 1 + j, 12 - 2 * inset, 1, ramp[1])
        c.set(x + inset, y + 1 + j, ramp[0])
        c.set(x + 11 - inset, y + 1 + j, ramp[2])
    for j, w in enumerate((2, 4, 6, 4, 2)):
        c.rect(x + 6 - w // 2, y + 4 + j, w, 1, accent[0] if j < 2 else accent[1])
    c.rect(x, y + 1, 12, 1, "#f7cf5a")


def _shelf(c, pack, x, y, w, sp):
    c.rect(x, y, w, 2, "#a8744a")
    c.rect(x, y + 1, w, 1, "#6e472c")
    for bx in (x + 3, x + w - 5):
        c.rect(bx, y + 2, 2, 1, "#6e472c")
        c.set(bx + 1, y + 3, "#6e472c")


def _bench(c, pack, x, y, sp):
    c.rect(x, y, 32, 2, "#c08a55")
    c.rect(x, y + 2, 32, 1, "#7d5432")
    for lx in (x + 2, x + 27):
        c.rect(lx, y + 3, 3, 6, "#7d5432")
    c.rect(x + 2, y + 6, 28, 1, "#7d5432")
