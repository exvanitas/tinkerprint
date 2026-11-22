"""Pixel-space scan conversion of costume patterns measured in figure space."""
from math import cos, radians, sin

from .._drawing import Drawing

# The 64-pixel tile, the brow's position on it, and the free wrist's resting joint.
SIZE = 64
ORIGIN = (30, 17)
WRIST = (19, 29)

# Highlight, light, shadow, deep. All lighting rules address materials in that order.
HAIR = ("#ffd495", "#db8764", "#a65350", "#673f48")
HONEY = ("#fff4c3", "#f0bf65", "#945748", "#473446")
STEEL = ("#fff0c3", "#b3d2c3", "#668c89", "#364c56")


def materials(outfit, sleeve, skin):
    """Every material ramp the portrait paints with, from the look's dyes and a skin ramp."""
    return dict(ink=("#24243c",)*4, skin=tuple(skin), cloth=outfit, sleeve=sleeve,
                steel=STEEL, hair=HAIR, white=("#fff6df", "#f2e3cc", "#c6bbc1", "#715f73"),
                eye=HONEY, gold=("#fff0b8", "#e3ac61", "#ac7554", "#654a54"),
                scarf=("#ffbe98", "#dc7368", "#9b485b", "#55364f"),
                dark=("#a49a9c", "#736575", "#4a465c", "#303045"))


class Pen:
    """Draws in figure space: coordinates relative to an origin, turned, sheared or mirrored as asked."""

    def __init__(self, image, colors, origin=ORIGIN, zoom=1, flip=1, lean=0, angle=0):
        self.image, self.colors = image, colors
        self.origin, self.zoom, self.flip, self.lean, self.angle = origin, zoom, flip, lean, angle
        self.cs, self.sn = cos(radians(angle)), sin(radians(angle))

    def xy(self, x, y):
        ox, oy = self.origin
        x, y = x*self.cs-y*self.sn, x*self.sn+y*self.cs
        return (round(ox + (x + y*self.lean)*self.zoom*self.flip), round(oy + y*self.zoom))

    def local(self, x, y, scale=1, shear=0, turn=0):
        return Pen(self.image, self.colors, self.xy(x, y), self.zoom*scale,
                   self.flip, self.lean + shear, self.angle+turn)

    def points(self, coords):
        return tuple(self.xy(x, y) for x, y in zip(coords[::2], coords[1::2]))

    def line(self, mat, tone, *coords):
        self.image.line(self.colors[mat][tone], *self.points(coords))

    def dot(self, mat, tone, x, y):
        self.image.set(*self.xy(x, y), self.colors[mat][tone])

    def patch(self, mat, tone, *coords, edge=False):
        pts = self.points(coords)
        self.image.shape(self.colors[mat][tone], *pts)
        if edge:
            # Each material outlines itself in its own deepest tone.
            self.image.line(self.colors[mat][3], *pts, pts[0])


def canvas():
    return Drawing(SIZE, SIZE)
