"""A tiny pixel canvas: stamp character grids, outline, and write crisp SVG or PNG.

Pixels hold "#rrggbb" strings or None for clear. Output is byte-identical for the same canvas:
colors and runs are emitted in a fixed order and PNG compression uses fixed settings.
"""
from __future__ import annotations

import re
import struct
import zlib

HEX = re.compile(r"^#[0-9a-f]{6}$")
CLEAR = "."


class Canvas:
    def __init__(self, w: int, h: int, fill: str | None = None):
        self.w, self.h = w, h
        self.px = [[fill] * w for _ in range(h)]

    def get(self, x: int, y: int):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return None

    def set(self, x: int, y: int, color: str | None) -> None:
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = color

    def rect(self, x: int, y: int, w: int, h: int, color: str | None) -> None:
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def stamp(self, rows, palette: dict, x: int = 0, y: int = 0, flip: bool = False) -> None:
        """Draw a character grid. "." is clear. Every other character must be in the palette."""
        for j, row in enumerate(rows):
            if flip:
                row = row[::-1]
            for i, ch in enumerate(row):
                if ch == CLEAR or ch == " ":
                    continue
                color = palette.get(ch)
                if color is None:
                    raise KeyError(f"no color for {ch!r}")
                self.set(x + i, y + j, color)

    def paste(self, other: "Canvas", x: int = 0, y: int = 0) -> None:
        for j in range(other.h):
            for i in range(other.w):
                c = other.px[j][i]
                if c is not None:
                    self.set(x + i, y + j, c)

    def outline(self, color: str, corners: bool = False) -> "Canvas":
        """Every clear pixel next to a drawn one takes the outline color."""
        steps = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        if corners:
            steps += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
        marks = []
        for y in range(self.h):
            for x in range(self.w):
                if self.px[y][x] is None and any(self.get(x + dx, y + dy) is not None for dx, dy in steps):
                    marks.append((x, y))
        for x, y in marks:
            self.px[y][x] = color
        return self

    def colors(self) -> list:
        return sorted({c for row in self.px for c in row if c is not None})

    # ------------------------------------------------------------ SVG

    def svg_paths(self, scale: float = 1, ox: float = 0, oy: float = 0) -> list:
        """One <path> per color, built from horizontal runs merged down into rectangles."""
        rects: dict = {}
        open_runs: dict = {}  # (x0, x1, color) -> [y0, h]
        for y in range(self.h + 1):
            row = self.px[y] if y < self.h else [None] * self.w
            runs = []
            x = 0
            while x < self.w:
                c = row[x]
                if c is None:
                    x += 1
                    continue
                x0 = x
                while x < self.w and row[x] == c:
                    x += 1
                runs.append((x0, x, c))
            now = {}
            for r in runs:
                if r in open_runs:
                    y0, h = open_runs.pop(r)
                    now[r] = [y0, h + 1]
                else:
                    now[r] = [y, 1]
            for (x0, x1, c), (y0, h) in open_runs.items():
                rects.setdefault(c, []).append((x0, y0, x1 - x0, h))
            open_runs = now
        out = []
        for c in sorted(rects):
            d = "".join(f"M{_n(ox + x * scale)} {_n(oy + y * scale)}h{_n(w * scale)}v{_n(h * scale)}h{_n(-w * scale)}z"
                        for x, y, w, h in sorted(rects[c], key=lambda r: (r[1], r[0])))
            out.append(f'<path fill="{c}" d="{d}"/>')
        return out

    def svg(self, scale: int = 1, label: str = "", cls: str = "px") -> str:
        """A standalone inline SVG element."""
        aria = f' role="img" aria-label="{_attr(label)}"' if label else ' aria-hidden="true"'
        return (f'<svg class="{cls}" viewBox="0 0 {self.w} {self.h}" width="{self.w * scale}" height="{self.h * scale}" '
                f'shape-rendering="crispEdges"{aria}>' + "".join(self.svg_paths()) + "</svg>")

    # ------------------------------------------------------------ PNG

    def png(self, scale: int = 1, background: str | None = None) -> bytes:
        """RGBA PNG through zlib and struct. Clear pixels stay clear unless a background is given."""
        bg = _rgba(background) if background else b"\x00\x00\x00\x00"
        cache: dict = {}
        raw = bytearray()
        for row in self.px:
            line = bytearray()
            for c in row:
                if c is None:
                    px = bg
                else:
                    px = cache.get(c)
                    if px is None:
                        px = cache[c] = _rgba(c)
                line += px * scale
            for _ in range(scale):
                raw.append(0)
                raw += line
        w, h = self.w * scale, self.h * scale
        return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
                + _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + _chunk(b"IEND", b""))


def _chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def _rgba(c: str) -> bytes:
    if not HEX.match(c):
        raise ValueError(f"not a #rrggbb color: {c!r}")
    return bytes((int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16), 255))


def _n(v: float) -> str:
    """Short, exact numbers for path data."""
    if v == int(v):
        return str(int(v))
    return f"{v:.2f}".rstrip("0").rstrip(".")


def _attr(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;"))


def mix(a: str, b: str, t: float) -> str:
    """A color between a and b. t = 0 gives a."""
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02x}" for x, y in zip(ca, cb))


def read_png_size(data: bytes) -> tuple:
    """Width and height from a PNG header, after checking the signature and every chunk CRC."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    pos = 8
    size = None
    while pos < len(data):
        n, = struct.unpack(">I", data[pos:pos + 4])
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + n]
        crc, = struct.unpack(">I", data[pos + 8 + n:pos + 12 + n])
        if zlib.crc32(kind + body) & 0xFFFFFFFF != crc:
            raise ValueError(f"bad CRC in {kind!r}")
        if kind == b"IHDR":
            size = struct.unpack(">II", body[:8])
        pos += 12 + n
    if size is None:
        raise ValueError("no IHDR")
    return size
