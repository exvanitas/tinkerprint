"""One radial scale for every radar, so sheets of the same set overlay share for share.

Distance from the center is the square root of the share: 25% sits halfway out and 100% at the
rim. The square root keeps small shares readable without a per-sheet maximum.
"""
from __future__ import annotations

import math

RINGS = (0.10, 0.25, 0.50, 1.00)
LABEL_AT = 1.13  # spoke labels, as a fraction of the rim radius


def radius(share: float) -> float:
    return math.sqrt(min(1.0, max(0.0, share)))


def point(cx: float, cy: float, r: float, i: int, n: int, frac: float) -> tuple:
    """A point on spoke i of n at frac of the rim radius. Spoke 0 points up."""
    a = math.radians(-90 + i * 360 / n)
    return cx + math.cos(a) * r * frac, cy + math.sin(a) * r * frac


def anchor(i: int, n: int) -> str:
    c = math.cos(math.radians(-90 + i * 360 / n))
    return "middle" if abs(c) < 0.2 else ("start" if c > 0 else "end")
