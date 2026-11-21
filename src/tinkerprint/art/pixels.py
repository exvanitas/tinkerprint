"""A tiny pixel canvas: stamp character grids, outline, and write crisp SVG or PNG.

Pixels hold "#rrggbb" strings or None for clear. Output is byte-identical for the same canvas:
colors and runs are emitted in a fixed order and PNG compression uses fixed settings.
"""
from __future__ import annotations

import base64
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

    def material_edges(self, edges: dict, fallback: str) -> "Canvas":
        """A one-pixel contour. Top and left edges borrow the lit material's line color."""
        marks = []
        for y, row in enumerate(self.px):
            for x, value in enumerate(row):
                if value is not None:
                    continue
                for dx, dy, side in ((0, -1, 1), (-1, 0, 1), (1, 0, 0), (0, 1, 0)):
                    neighbor = self.get(x + dx, y + dy)
                    if neighbor is not None:
                        marks.append((x, y, edges.get(neighbor, (fallback, fallback))[side]))
                        break
        for x, y, color in marks:
            self.set(x, y, color)
        return self

    def colors(self) -> list:
        return sorted({c for row in self.px for c in row if c is not None})

    # ------------------------------------------------------------ SVG

    def svg_paths(self, scale: float = 1, ox: float = 0, oy: float = 0) -> list:
        """One compound path per ink. Each strip has one unbroken span per row."""
        # Runs on successive rows can share an outline even when their ends move.
        # At a fork only one branch continues the strip. The others begin new ones.
        by_color = {}
        previous = []
        for y, row in enumerate(self.px):
            current = []
            first = 0
            x = 0
            while x < self.w:
                start, color = x, row[x]
                x += 1
                while x < self.w and row[x] == color:
                    x += 1
                if color is None:
                    continue
                while first < len(previous) and previous[first][1] <= start:
                    first += 1
                best = 0
                strip = None
                i = first
                while i < len(previous) and previous[i][0] < x:
                    left, right, ink, candidate = previous[i]
                    overlap = min(right, x) - max(left, start)
                    if ink == color and overlap > best and candidate[-1][0] < y:
                        strip, best = candidate, overlap
                    i += 1
                if strip is None:
                    strip = []
                    by_color.setdefault(color, []).append(strip)
                strip.append((y, start, x))
                current.append((start, x, color, strip))
            previous = current

        out = []
        for color, strips in sorted(by_color.items()):
            data = "".join(_strip_path(strip, scale, ox, oy) for strip in strips)
            out.append(f'<path fill="{color}" d="{data}"/>')
        return out

    def svg(self, scale: int = 1, label: str = "", cls: str = "px") -> str:
        """A self-contained SVG for the HTML page, with native pixels and nearest-neighbor scaling."""
        aria = f' role="img" aria-label="{_attr(label)}"' if label else ' aria-hidden="true"'
        if scale in (1, 2, 3, 4):
            # Match the requested display resolution even in viewers that ignore image-rendering.
            image = base64.b64encode(self.png(int(scale), indexed=True)).decode("ascii")
            content = (f'<image width="{self.w}" height="{self.h}" style="image-rendering:pixelated" '
                       f'href="data:image/png;base64,{image}"/>')
        else:
            content = "".join(self.svg_paths())
        return (f'<svg class="{cls}" viewBox="0 0 {self.w} {self.h}" width="{self.w * scale}" height="{self.h * scale}" '
                f'shape-rendering="crispEdges"{aria}>{content}</svg>')

    # ------------------------------------------------------------ PNG

    def png(self, scale: int = 1, background: str | None = None, *, indexed: bool = False) -> bytes:
        """Write RGBA, or a lossless indexed PNG for compact inline artwork."""
        header_type = 6  # RGBA
        table = b""
        pixels = {color: _rgba(color) for color in self.colors()}
        clear = _rgba(background) if background else bytes(4)
        if indexed and len(set(pixels.values()) | {clear}) <= 256:
            header_type = 3
            # Index zero carries the background or transparency. All other entries are opaque.
            entries = [clear] + sorted(set(pixels.values()) - {clear})
            index = {rgba: bytes([i]) for i, rgba in enumerate(entries)}
            pixels = {color: index[rgba] for color, rgba in pixels.items()}
            table = _chunk(b"PLTE", b"".join(rgba[:3] for rgba in entries))
            if background is None:
                table += _chunk(b"tRNS", b"\x00")
            clear = bytes(1)
        pixels[None] = clear
        raw = bytearray()
        for row in self.px:
            scanline = b"\x00" + b"".join(pixels[color] * scale for color in row)
            raw.extend(scanline * scale)
        w, h = self.w * scale, self.h * scale
        header = struct.pack(">IIBBBBB", w, h, 8, header_type, 0, 0, 0)
        return (b"\x89PNG\r\n\x1a\n" + _chunk(b"IHDR", header) + table
                + _chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + _chunk(b"IEND", b""))


def _strip_path(strip, scale, ox, oy):
    """Walk down the right bank, across the base, and up the left bank."""
    top, left, right = strip[0]
    path = [f"M{_n(ox + left * scale)} {_n(oy + top * scale)}h{_n((right - left) * scale)}"]
    last_y = top
    for y, _, end in strip:
        if end != right:
            path.append(f"v{_n((y - last_y) * scale)}h{_n((end - right) * scale)}")
            last_y, right = y, end
    bottom, left, _ = strip[-1]
    path.append(f"v{_n((bottom + 1 - last_y) * scale)}h{_n((left - right) * scale)}")
    last_y = bottom + 1
    for y, start, _ in reversed(strip):
        if start != left:
            path.append(f"v{_n((y + 1 - last_y) * scale)}h{_n((start - left) * scale)}")
            last_y, left = y + 1, start
    path.append("z")
    return "".join(path)


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
