"""card.png: the share card as a PNG, for sites and chats that do not preview SVG.

It draws exactly visible()'s fields, like card.svg, in the same layout, with a pixel font made in
code (pixelfont.py). The portrait and instruments are pasted at integer scales, so their pixels stay
crisp. The PNG holds image data only: no text chunks, no metadata.
"""
from __future__ import annotations

import functools
import math
import struct
import zlib

from . import art, pixelfont, radar
from .art.pixels import Canvas, mix
from .render_card import (ACH_STEP, ACH_Y, BG, BOTTOM_Y, CLASS_Y, COL_RIGHT, FOOT_Y, H, INK, INK2, LANTERN,
                          LANTERN2, LINE, MUTED, NAME_RIGHT, NAME_Y, PX, PY, RADAR_CLIP, RADAR_CX, RADAR_CY,
                          RADAR_LEFT, RADAR_R, RULE_Y, SET_Y, TX, W, MEMBER_SCALE, members, multiclass_room,
                          portrait_box, portrait_plate, visible)

GLOW = "#3a2a1c"
TRACK = "#2d2b34"
FRAME = "#0b0a0e"
SEAL = ("#fbe2a4", "#e0a447", "#b8731f")
SEAL_LINE, SEAL_INK = "#6e4214", "#2b1606"
# A 4 by 4 ordered dither, so gradients step in a pixel pattern instead of bands.
BAYER = ((0, 8, 2, 10), (12, 4, 14, 6), (3, 11, 1, 9), (15, 7, 13, 5))


def render_card_png(card: dict, pack: dict | None = None) -> bytes:
    return encode(draw_card(card, pack))


def encode(c: Canvas) -> bytes:
    """An indexed PNG, or RGB when the card holds more than 256 colors. Image chunks only:
    IHDR, PLTE, IDAT, IEND. No text, no time, no metadata of any kind."""
    colors = sorted({x for row in c.px for x in row})
    if None in colors:
        raise ValueError("the card has a clear pixel")
    rgb = {x: bytes.fromhex(x[1:]) for x in colors}
    if len(colors) <= 256:
        index = {x: i for i, x in enumerate(colors)}
        rows = b"".join(b"\x00" + bytes(map(index.__getitem__, row)) for row in c.px)
        head, extra = struct.pack(">IIBBBBB", c.w, c.h, 8, 3, 0, 0, 0), _chunk(b"PLTE", b"".join(rgb[x] for x in colors))
    else:
        rows = b"".join(b"\x00" + b"".join(map(rgb.__getitem__, row)) for row in c.px)
        head, extra = struct.pack(">IIBBBBB", c.w, c.h, 8, 2, 0, 0, 0), b""
    return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", head) + extra + _chunk(b"IDAT", zlib.compress(rows, 9))
            + _chunk(b"IEND", b""))


def _chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def draw_card(card: dict, pack: dict | None = None) -> Canvas:
    if not card.get("enabled"):
        raise ValueError("card is off for this profile")
    v = visible(card)
    pack = pack or art.default_pack()
    c = Canvas(W, H)
    c.px = [list(row) for row in _base()]

    # Who: set, then the name, then the class. The name and class shrink to fit, never cut.
    text(c, TX, SET_Y, v["set"], LANTERN, 2, track=2, bold=True)
    s = pixelfont.fit(v["name"], NAME_RIGHT - TX, 7, 2, bold=True)
    text(c, TX, NAME_Y, pixelfont.clip(v["name"], NAME_RIGHT - TX, s, bold=True), INK, s, bold=True)
    s = pixelfont.fit(v["class"], NAME_RIGHT - TX, 5, 2, bold=True)
    text(c, TX, CLASS_Y, pixelfont.clip(v["class"], NAME_RIGHT - TX, s, bold=True), LANTERN2, s, bold=True)

    # Portrait in its frame, at an integer scale.
    scale, padding, frame = portrait_box(pack)
    _rounded_fill(c, PX - 3, PY - 3, PX + frame + 3, PY + frame + 3, 16, mix(BG, LANTERN, 0.55))
    _rounded_fill(c, PX - 1, PY - 1, PX + frame + 1, PY + frame + 1, 14, FRAME)
    paste(c, portrait_plate(card, pack), PX + padding, PY + padding, scale)
    if v["level"]:
        _seal(c, PX + frame + 14, PY + frame - 14, v["level"])

    # Beside the portrait: the multiclass under its label, then the top shares with bars.
    cx0 = PX + frame + 58
    room = COL_RIGHT - cx0
    y = PY + 30
    if v["multiclass"]:
        text(c, cx0, PY + 18, "MULTICLASS", MUTED, 2, track=2)
        wide = multiclass_room(cx0)
        s = pixelfont.fit(v["multiclass"], wide, 3, 2)
        first, close, rest = v["multiclass"].partition(", close to ")
        if pixelfont.width(v["multiclass"], s) <= wide or not close:
            text(c, cx0, PY + 46, pixelfont.clip(v["multiclass"], wide, s), INK2, s)
        else:
            # Too long for one line: the close runner-up goes on a second.
            text(c, cx0, PY + 40, pixelfont.clip(first + ",", wide, 2), INK2, 2)
            text(c, cx0, PY + 60, pixelfont.clip("close to " + rest, wide, 2), INK2, 2)
        y = PY + 82
    for stat, pct in v["stats"]:
        hue = art.stat_ramp(pack, stat)
        name_room = room - pixelfont.width(pct, 2, bold=True) - 8
        text(c, cx0, y, pixelfont.clip(stat, name_room, 2, bold=True), INK, 2, bold=True)
        text(c, COL_RIGHT, y, pct, INK2, 2, bold=True, anchor="end")
        fill(c, cx0, y + 7, room, 4, TRACK)
        fill(c, cx0, y + 7, round(room * int(pct.rstrip("%")) / 100), 4, hue[1])
        y += 31

    if v["achievements"]:
        text(c, TX, ACH_Y, "ACHIEVEMENTS", MUTED, 2, track=2)
        y = ACH_Y + 24
        for title, when in v["achievements"]:
            _diamond(c, TX + 4, y - 7, 4, LANTERN)
            w_when = pixelfont.width(when, 2)
            text(c, 84, y, pixelfont.clip(title, COL_RIGHT - 84 - w_when - 12, 2, bold=True), INK, 2, bold=True)
            text(c, COL_RIGHT, y, when, MUTED, 2, anchor="end")
            y += ACH_STEP

    # Party in the radar's column after its instruments, projects in the left column.
    fx = RADAR_LEFT
    for f in members(v["members"]):
        paste(c, f, fx, BOTTOM_Y + 4 - f.h * MEMBER_SCALE, MEMBER_SCALE)
        fx += f.w * MEMBER_SCALE + 6
    # The pixel font's space is wide, so the double spaces between members draw as one.
    if v["party"]:
        x, room = fx + 6, W - 64 - fx - 6
        party = _squeeze(v["party"])
        bold = pixelfont.width(party, 2, bold=True) <= room
        if not bold:
            # Too long for one line: the label goes above the members, like the achievements heading.
            label, _, party = party.partition(" ")
            text(c, x, BOTTOM_Y - 20, label, MUTED, 2, track=2)
        text(c, x, BOTTOM_Y, pixelfont.clip(party, room, 2, bold=bold), MUTED, 2, bold=bold)
    if v["projects"]:
        text(c, TX, BOTTOM_Y, pixelfont.clip(_squeeze(v["projects"]), RADAR_LEFT - 20 - TX, 2), MUTED, 2)

    if v["chart"] == "radar":
        _radar(c, v["spokes"], pack)
    else:
        _bars(c, v["bars"], pack)

    fill(c, TX, RULE_Y, W - 2 * TX, 2, LINE)
    for line, y, color, bold in zip(v["footer"], FOOT_Y, (INK2, MUTED), (True, False)):
        text(c, TX, y, pixelfont.clip(line, W - 2 * TX, 2, bold=bold), color, 2, bold=bold)
    return c


@functools.lru_cache(maxsize=1)
def _base() -> tuple:
    """The parts every card shares: the glow, the inner border and the lantern mark. Drawn once."""
    c = Canvas(W, H)
    _background(c)
    _rounded_outline(c, 14, 14, W - 14, H - 14, 20, 2, LINE)
    fill(c, W // 2 - 60, 14, 120, 4, LANTERN)
    return tuple(tuple(row) for row in c.px)


def fill(c: Canvas, x: int, y: int, w: int, h: int, color) -> None:
    """A filled rectangle, clipped to the canvas, a row slice at a time."""
    x0, x1 = max(0, x), min(c.w, x + w)
    if x1 <= x0:
        return
    span = [color] * (x1 - x0)
    for yy in range(max(0, y), min(c.h, y + h)):
        c.px[yy][x0:x1] = span


# ------------------------------------------------------------------ text and sprites

def text(c: Canvas, x: int, baseline: int, s: str, color: str, scale: int, track: int = 1, bold: bool = False,
         anchor: str = "start") -> int:
    w = pixelfont.width(s, scale, track, bold)
    if anchor == "end":
        x -= w
    elif anchor == "middle":
        x -= w // 2
    return pixelfont.draw(c, round(x), baseline, s, color, scale, track, bold)


def _squeeze(s: str) -> str:
    return " ".join(w for w in s.split(" ") if w)


def paste(c: Canvas, sprite: Canvas, x: int, y: int, scale: int) -> None:
    """A sprite at an integer scale: every pixel becomes a scale by scale square."""
    for j in range(sprite.h):
        for i, color in enumerate(sprite.px[j]):
            if color is not None:
                fill(c, x + i * scale, y + j * scale, scale, scale, color)


# ------------------------------------------------------------------ shapes

def _background(c: Canvas) -> None:
    """The card's radial glow from the top left, stepped in a dither pattern on 2 px cells."""
    steps = 12
    ramp = [mix(GLOW, BG, k / steps) for k in range(steps + 1)]
    gx, rx, ry = 0.3 * W, 0.9 * W, 0.9 * H
    for y in range(0, H, 2):
        row_y = ((y + 1) / ry) ** 2
        bayer = BAYER[(y // 2) % 4]
        row = []
        for x in range(0, W, 2):
            t = min(1.0, math.sqrt(((x + 1 - gx) / rx) ** 2 + row_y)) * steps
            k = int(t)
            if t - k > (bayer[(x // 2) % 4] + 0.5) / 16:
                k += 1
            row += [ramp[min(k, steps)]] * 2
        c.px[y] = row[:W]
        if y + 1 < H:
            c.px[y + 1] = row[:W]


def _inside_round(x: float, y: float, x0: int, y0: int, x1: int, y1: int, r: int) -> bool:
    """Whether the pixel centre (x, y) lies in the rectangle [x0, x1) by [y0, y1) with corner radius r."""
    if not (x0 <= x < x1 and y0 <= y < y1):
        return False
    cx = min(max(x, x0 + r), x1 - r)
    cy = min(max(y, y0 + r), y1 - r)
    return (x - cx) ** 2 + (y - cy) ** 2 <= r * r


def _rounded_fill(c: Canvas, x0: int, y0: int, x1: int, y1: int, r: int, color: str) -> None:
    for y in range(y0, y1):
        if y0 + r <= y < y1 - r:
            fill(c, x0, y, x1 - x0, 1, color)
            continue
        cy = y0 + r if y < y0 + r else y1 - r
        dy = y + 0.5 - cy
        half = math.sqrt(max(0.0, r * r - dy * dy))
        # Pixel centres within half of the corner centres' columns.
        a = math.ceil(x0 + r - half - 0.5)
        b = math.floor(x1 - r + half - 0.5)
        fill(c, a, y, b - a + 1, 1, color)


def _rounded_outline(c: Canvas, x0: int, y0: int, x1: int, y1: int, r: int, t: int, color: str) -> None:
    """A t px line just inside a rounded rectangle. Only the edges are visited."""
    def mark(x, y):
        p = (x + 0.5, y + 0.5)
        if _inside_round(*p, x0, y0, x1, y1, r) and not _inside_round(*p, x0 + t, y0 + t, x1 - t, y1 - t, max(0, r - t)):
            c.set(x, y, color)
    band = r + t
    for y in range(y0, y1):
        xs = range(x0, x1) if y < y0 + band or y >= y1 - band else (*range(x0, x0 + band), *range(x1 - band, x1))
        for x in xs:
            mark(x, y)


def _disc(c: Canvas, cx: float, cy: float, r: float, color) -> None:
    """A filled circle. color may be a function of (x, y)."""
    for y in range(math.floor(cy - r), math.ceil(cy + r) + 1):
        for x in range(math.floor(cx - r), math.ceil(cx + r) + 1):
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                c.set(x, y, color(x, y) if callable(color) else color)


def _diamond(c: Canvas, cx: int, cy: int, r: int, color: str) -> None:
    for dy in range(-r, r + 1):
        half = r - abs(dy)
        fill(c, cx - half, cy + dy, 2 * half + 1, 1, color)


def _line(c: Canvas, x0: float, y0: float, x1: float, y1: float, t: int, color: str) -> None:
    """A line t px wide, stamped as squares along its length."""
    n = max(1, math.ceil(max(abs(x1 - x0), abs(y1 - y0))))
    h = t / 2
    for k in range(n + 1):
        x = x0 + (x1 - x0) * k / n
        y = y0 + (y1 - y0) * k / n
        fill(c, round(x - h), round(y - h), t, t, color)


def _polygon_fill(c: Canvas, pts: list, shade) -> None:
    """Fill a polygon by scanlines at pixel centres. shade maps the pixel's color to its new one."""
    ys = [p[1] for p in pts]
    for y in range(math.floor(min(ys)), math.ceil(max(ys)) + 1):
        yc = y + 0.5
        xs = []
        for (ax, ay), (bx, by) in zip(pts, pts[1:] + pts[:1]):
            if (ay <= yc < by) or (by <= yc < ay):
                xs.append(ax + (yc - ay) * (bx - ax) / (by - ay))
        xs.sort()
        for a, b in zip(xs[::2], xs[1::2]):
            for x in range(math.ceil(a - 0.5), math.floor(b - 0.5) + 1):
                c.set(x, y, shade(c.get(x, y)))


def _seal(c: Canvas, sx: int, sy: int, level: str) -> None:
    """The level seal: a dark ring, a dithered lantern disc, then the number and LEVEL."""
    _disc(c, sx, sy, 44, BG)
    _disc(c, sx, sy, 40, SEAL_LINE)
    gx, gy, gr = sx - 39 + 0.38 * 78, sy - 39 + 0.30 * 78, 0.75 * 78
    ramp = [SEAL[0], mix(SEAL[0], SEAL[1], 0.5), SEAL[1], mix(SEAL[1], SEAL[2], 0.5), SEAL[2]]

    def glow(x, y):
        t = min(1.0, math.hypot(x + 0.5 - gx, y + 0.5 - gy) / gr) * (len(ramp) - 1)
        k = int(t)
        if t - k > (BAYER[y % 4][x % 4] + 0.5) / 16:
            k += 1
        return ramp[min(k, len(ramp) - 1)]
    _disc(c, sx, sy, 37, glow)
    s = 4 if len(level) < 3 else 3
    text(c, sx, sy + 8, level, SEAL_INK, s, bold=True, anchor="middle")
    text(c, sx + 1, sy + 26, "LEVEL", SEAL_INK, 2, track=1, anchor="middle")


# ------------------------------------------------------------------ charts

def _radar(c: Canvas, spokes: list, pack: dict) -> None:
    cx, cy, r = RADAR_CX, RADAR_CY, RADAR_R
    n = len(spokes)
    for ring in radar.RINGS:
        fr = radar.radius(ring)
        pts = [radar.point(cx, cy, r, i, n, fr) for i in range(n)]
        for a, b in zip(pts, pts[1:] + pts[:1]):
            _line(c, *a, *b, 2, TRACK)
    for i in range(n):
        _line(c, cx, cy, *radar.point(cx, cy, r, i, n, 1.0), 2, LINE)
    poly = [radar.point(cx, cy, r, i, n, radar.radius(p / 100)) for i, (_, p) in enumerate(spokes)]
    tint: dict = {}

    def shade(old):
        if old not in tint:
            tint[old] = mix(old or BG, LANTERN, 0.2)
        return tint[old]
    _polygon_fill(c, poly, shade)
    for a, b in zip(poly, poly[1:] + poly[:1]):
        _line(c, *a, *b, 3, LANTERN)
    # Empty stats first, so their dots at the center never cover a lit one.
    for i, (stat, p) in sorted(enumerate(spokes), key=lambda t: t[1][1] > 0):
        x, y = radar.point(cx, cy, r, i, n, radar.radius(p / 100))
        _disc(c, x, y, 9, BG)
        _disc(c, x, y, 7, art.stat_ramp(pack, stat)[1])
        lx, ly = radar.point(cx, cy, r, i, n, radar.LABEL_AT)
        label = pixelfont.clip(stat, RADAR_CLIP, 2, bold=True)
        text(c, lx, round(ly + 7), label, INK if p > 0 else MUTED, 2, bold=True, anchor=radar.anchor(i, n))


def _bars(c: Canvas, bars: list, pack: dict) -> None:
    """Ranked bars when fewer than three stats have points, as on the sheet."""
    x0, x1, y = RADAR_LEFT, 1100, 160
    for stat, p in bars:
        text(c, x0, y, stat, INK, 3, bold=True)
        text(c, x1, y, f"{p}%", INK2, 3, bold=True, anchor="end")
        fill(c, x0, y + 14, x1 - x0, 12, TRACK)
        fill(c, x0, y + 14, round((x1 - x0) * p / 100), 12, art.stat_ramp(pack, stat)[1])
        y += 80
