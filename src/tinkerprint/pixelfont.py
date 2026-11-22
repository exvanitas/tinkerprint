"""A proportional 5 by 7 pixel font, drawn in code, for card.png. No font files.

Each glyph is a list of rows, "#" for ink. Rows 0 to 6 sit on the baseline. Rows 7 and 8 are
descenders. Every row of a glyph has the same width, and the advance is that width plus one.
Letters with accents keep their base letter and gain a mark above it. Anything else the font
lacks is drawn as "?", so a card never fails to draw.
"""
from __future__ import annotations

import unicodedata

CAP = 7        # rows above the baseline
DESCENT = 2    # rows below it
ABOVE = 2      # rows above a capital that accents may use

_RAW = {
    "A": ".###.|#...#|#...#|#####|#...#|#...#|#...#",
    "B": "####.|#...#|#...#|####.|#...#|#...#|####.",
    "C": ".###.|#...#|#....|#....|#....|#...#|.###.",
    "D": "####.|#...#|#...#|#...#|#...#|#...#|####.",
    "E": "#####|#....|#....|####.|#....|#....|#####",
    "F": "#####|#....|#....|####.|#....|#....|#....",
    "G": ".###.|#...#|#....|#.###|#...#|#...#|.####",
    "H": "#...#|#...#|#...#|#####|#...#|#...#|#...#",
    "I": "###|.#.|.#.|.#.|.#.|.#.|###",
    "J": "....#|....#|....#|....#|....#|#...#|.###.",
    "K": "#...#|#..#.|#.#..|##...|#.#..|#..#.|#...#",
    "L": "#....|#....|#....|#....|#....|#....|#####",
    "M": "#...#|##.##|#.#.#|#.#.#|#...#|#...#|#...#",
    "N": "#...#|#...#|##..#|#.#.#|#..##|#...#|#...#",
    "O": ".###.|#...#|#...#|#...#|#...#|#...#|.###.",
    "P": "####.|#...#|#...#|####.|#....|#....|#....",
    "Q": ".###.|#...#|#...#|#...#|#.#.#|#..#.|.##.#",
    "R": "####.|#...#|#...#|####.|#.#..|#..#.|#...#",
    "S": ".####|#....|#....|.###.|....#|....#|####.",
    "T": "#####|..#..|..#..|..#..|..#..|..#..|..#..",
    "U": "#...#|#...#|#...#|#...#|#...#|#...#|.###.",
    "V": "#...#|#...#|#...#|#...#|#...#|.#.#.|..#..",
    "W": "#...#|#...#|#...#|#.#.#|#.#.#|#.#.#|.#.#.",
    "X": "#...#|#...#|.#.#.|..#..|.#.#.|#...#|#...#",
    "Y": "#...#|#...#|.#.#.|..#..|..#..|..#..|..#..",
    "Z": "#####|....#|...#.|..#..|.#...|#....|#####",
    "a": ".....|.....|.###.|....#|.####|#...#|.####",
    "b": "#....|#....|####.|#...#|#...#|#...#|####.",
    "c": "....|....|.###|#...|#...|#...|.###",
    "d": "....#|....#|.####|#...#|#...#|#...#|.####",
    "e": ".....|.....|.###.|#...#|#####|#....|.###.",
    "f": "..##|.#..|####|.#..|.#..|.#..|.#..",
    "g": ".....|.....|.####|#...#|#...#|#...#|.####|....#|.###.",
    "h": "#....|#....|####.|#...#|#...#|#...#|#...#",
    "i": "#|.|#|#|#|#|#",
    "j": "..#|...|..#|..#|..#|..#|..#|#.#|.#.",
    "k": "#...|#...|#..#|#.#.|##..|#.#.|#..#",
    "l": "#.|#.|#.|#.|#.|#.|.#",
    "m": ".....|.....|##.#.|#.#.#|#.#.#|#.#.#|#.#.#",
    "n": ".....|.....|####.|#...#|#...#|#...#|#...#",
    "o": ".....|.....|.###.|#...#|#...#|#...#|.###.",
    "p": ".....|.....|####.|#...#|#...#|#...#|####.|#....|#....",
    "q": ".....|.....|.####|#...#|#...#|#...#|.####|....#|....#",
    "r": "....|....|#.##|##..|#...|#...|#...",
    "s": "....|....|.###|#...|.##.|...#|###.",
    "t": ".#..|.#..|####|.#..|.#..|.#..|..##",
    "u": ".....|.....|#...#|#...#|#...#|#...#|.####",
    "v": ".....|.....|#...#|#...#|#...#|.#.#.|..#..",
    "w": ".....|.....|#...#|#...#|#.#.#|#.#.#|.#.#.",
    "x": ".....|.....|#...#|.#.#.|..#..|.#.#.|#...#",
    "y": ".....|.....|#...#|#...#|#...#|#...#|.####|....#|.###.",
    "z": ".....|.....|#####|...#.|..#..|.#...|#####",
    "0": ".###.|#...#|#..##|#.#.#|##..#|#...#|.###.",
    "1": "..#..|.##..|..#..|..#..|..#..|..#..|.###.",
    "2": ".###.|#...#|....#|...#.|..#..|.#...|#####",
    "3": "#####|...#.|..#..|...#.|....#|#...#|.###.",
    "4": "...#.|..##.|.#.#.|#..#.|#####|...#.|...#.",
    "5": "#####|#....|####.|....#|....#|#...#|.###.",
    "6": "..##.|.#...|#....|####.|#...#|#...#|.###.",
    "7": "#####|....#|...#.|..#..|.#...|.#...|.#...",
    "8": ".###.|#...#|#...#|.###.|#...#|#...#|.###.",
    "9": ".###.|#...#|#...#|.####|....#|...#.|.##..",
    " ": "...|...|...|...|...|...|...",
    ".": ".|.|.|.|.|.|#",
    ",": "..|..|..|..|..|.#|.#|#.",
    ":": ".|.|#|.|.|#|.",
    ";": "..|..|.#|..|..|.#|.#|#.",
    "'": "#|#|.|.|.|.|.",
    '"': "#.#|#.#|...|...|...|...|...",
    "!": "#|#|#|#|#|.|#",
    "?": ".###.|#...#|....#|...#.|..#..|.....|..#..",
    "-": "....|....|....|####|....|....|....",
    "–": ".....|.....|.....|#####|.....|.....|.....",
    "_": ".....|.....|.....|.....|.....|.....|#####",
    "/": "....#|....#|...#.|..#..|.#...|#....|#....",
    "\\": "#....|#....|.#...|..#..|...#.|....#|....#",
    "(": "..#|.#.|#..|#..|#..|.#.|..#",
    ")": "#..|.#.|..#|..#|..#|.#.|#..",
    "[": "###|#..|#..|#..|#..|#..|###",
    "]": "###|..#|..#|..#|..#|..#|###",
    "{": "..#|.#.|.#.|#..|.#.|.#.|..#",
    "}": "#..|.#.|.#.|..#|.#.|.#.|#..",
    "<": "...#|..#.|.#..|#...|.#..|..#.|...#",
    ">": "#...|.#..|..#.|...#|..#.|.#..|#...",
    "&": ".##..|#..#.|#.#..|.#...|#.#.#|#..#.|.##.#",
    "+": ".....|..#..|..#..|#####|..#..|..#..|.....",
    "=": ".....|.....|#####|.....|#####|.....|.....",
    "%": "##...|##..#|...#.|..#..|.#...|#..##|...##",
    "#": ".#.#.|.#.#.|#####|.#.#.|#####|.#.#.|.#.#.",
    "@": ".###.|#...#|#.###|#.#.#|#.###|#....|.###.",
    "*": ".....|#.#.#|.###.|#####|.###.|#.#.#|.....",
    "$": "..#..|.####|#.#..|.###.|..#.#|####.|..#..",
    "^": "..#..|.#.#.|#...#|.....|.....|.....|.....",
    "~": ".....|.....|.#...|#.#.#|...#.|.....|.....",
    "|": "#|#|#|#|#|#|#|#",
    "`": "#.|.#|..|..|..|..|..",
    "·": ".|.|.|#|.|.|.",
    "…": ".....|.....|.....|.....|.....|.....|#.#.#",
    "×": ".....|#...#|.#.#.|..#..|.#.#.|#...#|.....",
}

# Accent marks, two rows tall, keyed by combining character.
_MARKS = {
    "́": ("..#", ".#."),     # acute
    "̀": ("#..", ".#."),     # grave
    "̂": (".#.", "#.#"),     # circumflex
    "̈": ("#.#", "..."),     # diaeresis
    "̃": (".#.#", "#.#."),   # tilde
    "̊": (".#.", "#.#"),     # ring (drawn like a small cap)
    "̌": ("#.#", ".#."),     # caron
}

# Letters that do not decompose into a base and a mark.
_SPELL = {"ß": "ss", "æ": "ae", "Æ": "AE", "œ": "oe", "Œ": "OE", "ø": "o", "Ø": "O", "ł": "l", "Ł": "L",
          "đ": "d", "Đ": "D", "ı": "i", "þ": "th", "Þ": "Th", "ð": "d", "Ð": "D",
          "’": "'", "‘": "'", "“": '"', "”": '"', "—": "–", "−": "-", " ": " "}

GLYPHS = {ch: tuple(spec.split("|")) for ch, spec in _RAW.items()}
for _ch, _rows in GLYPHS.items():
    assert len({len(r) for r in _rows}) == 1, _ch
    assert 7 <= len(_rows) <= 9, _ch


_DOTLESS_I = (".", ".", "#", "#", "#", "#", "#")


def _cell(c: str):
    """(glyph rows, mark rows or None) for one spelled character, () for a mark drawn on nothing,
    or None when the font has no glyph for it."""
    if c in GLYPHS:
        return GLYPHS[c], None
    parts = unicodedata.normalize("NFD", c)
    base, marks = parts[:1], [m for m in parts[1:] if m in _MARKS]
    if base in GLYPHS and base != c:
        rows = _DOTLESS_I if base == "i" and marks else GLYPHS[base]
        return rows, _MARKS[marks[0]] if marks else None
    if unicodedata.combining(c):
        return ()
    return None


def _cells(text: str) -> list:
    """(glyph rows, mark rows or None) for each drawn character of text."""
    out = []
    for ch in str(text):
        for c in _SPELL.get(ch, ch):
            cell = _cell(c)
            if cell is None:
                out.append((GLYPHS["?"], None))
            elif cell:
                out.append(cell)
    return out


def missing(text: str) -> list:
    """The characters of text the font draws as "?", in order, each once."""
    out = []
    for ch in str(text):
        if any(_cell(c) is None for c in _SPELL.get(ch, ch)) and ch not in out:
            out.append(ch)
    return out


def _bold(scale: int) -> int:
    """Extra pixels bold ink spreads to the right: half a font pixel, so one-pixel gaps stay open."""
    return max(1, scale // 2)


def width(text: str, scale: int = 1, track: int = 1, bold: bool = False) -> int:
    """The drawn width in pixels: glyph widths plus track units between them."""
    cells = _cells(text)
    if not cells:
        return 0
    extra = _bold(scale) if bold else 0
    return sum(len(g[0]) * scale + extra for g, _ in cells) + track * scale * (len(cells) - 1)


def draw(canvas, x: int, baseline: int, text: str, color: str, scale: int = 1, track: int = 1,
         bold: bool = False) -> int:
    """Draw text with its baseline at y = baseline. Returns the x just past the last glyph."""
    top = baseline - CAP * scale
    extra = _bold(scale) if bold else 0
    for rows, mark in _cells(text):
        w = len(rows[0])
        for j, row in enumerate(rows):
            for i, bit in enumerate(row):
                if bit == "#":
                    _fill(canvas, x + i * scale, top + j * scale, scale + extra, scale, color)
        if mark:
            # Lower case leaves rows 0 and 1 free. Capitals take the two rows above the cap.
            lower = rows[0].count("#") == 0 and rows[1].count("#") == 0
            my = top if lower else top - ABOVE * scale - scale
            mx = x + (w - len(mark[0])) // 2 * scale
            for j, row in enumerate(mark):
                for i, bit in enumerate(row):
                    if bit == "#":
                        _fill(canvas, mx + i * scale, my + j * scale, scale, scale, color)
        x += w * scale + extra + track * scale
    return x - track * scale


def _fill(canvas, x: int, y: int, w: int, h: int, color: str) -> None:
    """A rectangle on an art.pixels.Canvas, clipped, a row slice at a time."""
    x0, x1 = max(0, x), min(canvas.w, x + w)
    if x1 <= x0:
        return
    span = [color] * (x1 - x0)
    for yy in range(max(0, y), min(canvas.h, y + h)):
        canvas.px[yy][x0:x1] = span


def fit(text: str, max_width: int, largest: int, smallest: int = 2, track: int = 1, bold: bool = False) -> int:
    """The largest scale from largest down to smallest at which text fits max_width."""
    for s in range(largest, smallest - 1, -1):
        if width(text, s, track, bold) <= max_width:
            return s
    return smallest


def clip(text: str, max_width: int, scale: int, track: int = 1, bold: bool = False) -> str:
    """Text cut with an ellipsis until it fits max_width at scale."""
    if width(text, scale, track, bold) <= max_width:
        return text
    s = str(text)
    while s and width(s.rstrip() + "…", scale, track, bold) > max_width:
        s = s[:-1]
    return s.rstrip() + "…"
