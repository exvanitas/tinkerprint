"""Authoring tools for the built-in pack. Only the finished character grids are exported."""
from __future__ import annotations

from math import ceil, floor

from .pixels import Canvas


class Drawing(Canvas):
    """A drawing in palette keys, on an integer lattice."""

    def __init__(self, w=48, h=48):
        super().__init__(w, h)

    def line(self, ink, *points):
        for (x, y), (ex, ey) in zip(points, points[1:]):
            dx, dy = abs(ex - x), -abs(ey - y)
            sx, sy = (1 if x < ex else -1), (1 if y < ey else -1)
            err = dx + dy
            while True:
                self.set(x, y, ink)
                if (x, y) == (ex, ey):
                    break
                step = 2 * err
                if step >= dy:
                    err += dy
                    x += sx
                if step <= dx:
                    err += dx
                    y += sy

    def shape(self, ink, *points):
        """Scan convert a hand-placed closed contour, including its boundary pixels."""
        edges = list(zip(points, points[1:] + points[:1]))
        for y in range(min(p[1] for p in points), max(p[1] for p in points) + 1):
            cuts = sorted(x + (y - a) * (xx - x) / (b - a) for (x, a), (xx, b) in edges
                          if min(a, b) <= y < max(a, b))
            for low, high in zip(cuts[::2], cuts[1::2]):
                for x in range(ceil(low), floor(high) + 1):
                    self.set(x, y, ink)
        self.line(ink, *points, points[0])

    def grid(self, x, y, sketch):
        for j, row in enumerate(sketch.strip('\n').splitlines()):
            for i, ch in enumerate(row):
                if ch not in ' .':
                    self.set(x + i, y + j, ch)

    def part(self, **options):
        dots = [(x, y) for y, row in enumerate(self.px) for x, c in enumerate(row) if c]
        x0, y0 = min(x for x, _ in dots), min(y for _, y in dots)
        x1, y1 = max(x for x, _ in dots), max(y for _, y in dots)
        rows = [''.join(c or '.' for c in row[x0:x1+1]) for row in self.px[y0:y1+1]]
        return dict(at=[x0, y0], rows=rows, **options)


def grid_part(x, y, sketch, **options):
    rows = sketch.strip('\n').splitlines()
    width = max(map(len, rows))
    return dict(at=[x, y], rows=[s.replace(' ', '.').ljust(width, '.') for s in rows], **options)
