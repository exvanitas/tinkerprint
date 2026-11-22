"""Shared fixtures for the Keepsake art tests: the cast, native pens and pixel helpers."""
from tinkerprint import art
from tinkerprint.art._anime import implements
from tinkerprint.art._anime.paint import ORIGIN, Pen, materials
from tinkerprint.art._drawing import Drawing
from tinkerprint.art.compose import palette
from tinkerprint.art.keepsake import SKINS as SKIN_RAMPS
from tinkerprint.sets import GENERALIST, PAIR, SETS, SPECIALIST

# A flat, impossible skin, so a test can tell skin from every other ink.
SKIN = ("#01fe01",) * 4
DYE = "#351bfa"
MODES = ("neutral", "man", "woman")
SKINS = (None, SKIN_RAMPS["medium"], SKIN_RAMPS["deep"])


def cast():
    """One look per class name: every specialist, both generalists and the unclassed Traveler."""
    looks = {}
    for s, trades in SPECIALIST.items():
        for stat, name in trades.items():
            looks.setdefault(name, art.look_for(s, "specialist", [stat], [stat]))
    for s, name in GENERALIST.items():
        looks[name] = art.look_for(s, "generalist", [], [SETS[s][0]])
    looks["Traveler"] = art.look_for("tinkerer", None, [], [])
    return looks


def equipped_looks():
    """The cast, then every pair in both stat orders."""
    yield from cast().values()
    for s, pairs in PAIR.items():
        for a, b in pairs:
            yield art.Look(s, "pair", a, b)
            yield art.Look(s, "pair", b, a)


def pixels(pic):
    return {(x, y): c for y, row in enumerate(pic.px) for x, c in enumerate(row) if c}


def connected(sprite):
    """All painted pixels reachable from one seed, including diagonal ink strokes."""
    points = {(x, y) for y, row in enumerate(sprite.px) for x, value in enumerate(row) if value}
    start = min(points)
    points.remove(start)
    todo = [start]
    while todo:
        x, y = todo.pop()
        for xx in range(x-1, x+2):
            for yy in range(y-1, y+2):
                if (xx, yy) in points:
                    points.remove((xx, yy))
                    todo.append((xx, yy))
    return not points


def adjacent(x, y):
    return ((x-1, y), (x+1, y), (x, y-1), (x, y+1))


def mark(pattern, ink):
    """Draw a part in one flat ink, to see which of its strokes survive the later layers."""
    def marked(p, *args):
        layer = p.local(0, 0)
        layer.colors = dict.fromkeys(p.colors, (ink,)*4)
        pattern(layer, *args)
    return marked


def kit_parts(pack, look):
    """(hat, travel cut, held item) as the portrait resolves them."""
    top = pack["looks"][look.top] if look.kind in ("specialist", "pair") else pack["generalist"]
    kit = pack["looks"].get(look.item, top)
    hat = top["hat"] if look.kind else "base"
    travel = None
    if hat == "traveler-head":
        travel = "wrap" if look.set_name == "tinkerer" else "trail"
    item = kit["item"] if look.kind else None
    if item in implements.ALTERNATES and kit.get("trinket") == implements.ALTERNATES[item]:
        item = kit["trinket"]
    return hat, travel, item


def native_pen(pack, look, padding=0):
    """A blank 64-pixel tile in the look's dyes and the test skin, registered like the portrait."""
    pal = palette(pack, look)
    colors = materials([pal[k] for k in "ABCF"], [pal[k] for k in "XYZH"], SKIN)
    x, y = ORIGIN
    return Pen(Drawing(64+2*padding, 64+2*padding), colors, (x+padding, y+padding))


def stats_for(look):
    """Plausible ranked shares for a look, so its room has stock."""
    others = [s for s in SETS[look.set_name] if s not in (look.top, look.item)]
    if not look.kind:
        return []
    if look.kind == "generalist":
        return [(s, 15 if i < 4 else 10) for i, s in enumerate(SETS[look.set_name])]
    if look.kind == "pair":
        return [(look.top, 47), (look.item, 38), (others[0], 15)]
    return [(look.top, 65), (others[0], 20), (others[-1], 15)]
