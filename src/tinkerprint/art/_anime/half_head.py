"""Hair, expression and fitted millinery for the hip-length Keepsake."""
from .._drawing import Drawing
from ..pack import PackError
from .enamel import CROWNS, HATS, headgear, stamp
from .paint import Pen
from .enamel_face import bob, face_plane, smiling_features, swept_fringe
from .traits import EXPRESSIONS, HAIRSTYLES

# Eye shapes on the seven-pixel socket. Both open irises track the same point.
EYES = {
    "grin": (".......", ".ddddd.", "dwWbdww", ".wggbw."),
    "calm": (".......", "dddddd.", ".wWdbww", "..ggbw."),
    "determined": ("ddd....", "dwWbddd", ".wbdbww", ".wggbw.", "..bg..."),
    "joy": (".......", "..ddd..", ".dd.dd.", "dd...dd"),
    "curious": ("..ddd..", ".dWbdd.", "dwgdbww", ".wgbbww", "..www.."),
}
MOUTHS = {  # Upper corners, lower lip and enamel highlights are symmetric about x=1.
    "grin": ("LpppppL", ".LqqqL.", "..LLL.."),
    "calm": ("LLLLL",),
    "determined": (":...:", ".LLL."),
    "joy": ("L...L", ".LLL."),
    "curious": (".L.", "L:L", ".L."),
}


LIDS = (None, (".......", ".......", ".ddddd.", ".wbdbw."),
        (".......", ".......", "d.....d", ".ddddd."))


def expression_marks(p, mode, expression, blink=0):
    lid = LIDS[0 if expression == "joy" else blink]
    if expression == "smile":
        smiling_features(p, mode, lid)
        return
    colors = dict(zip("dbgwW", (p.colors["eye"][3], p.colors["eye"][2], p.colors["eye"][1],
                                 p.colors["white"][0], p.colors["eye"][0])))
    for left in (True, False):
        x = -7 if left else 3
        eye = EYES[expression]
        if expression == "determined" and not left:
            # Only the inward slope of the lid reverses. Both pupils and
            # catchlights keep the same alignment in their sockets.
            eye = ("....ddd", "ddWbdwd", *eye[2:])
        p.image.stamp(lid or eye, colors, *p.xy(x, -1))
        # The curious brow arches higher on the side of the lifted gaze.
        outer = x if left else x+6
        sign = 1 if left else -1
        height = -4 if expression in ("curious", "joy", "grin") else -3
        inner = height + (2 if expression == "determined" else 0)
        if expression == "curious" and not left:
            height -= 1
        tone = 2 if mode == "woman" else 3
        p.line("hair", tone, outer,height+1, outer+2*sign,height,
               outer+4*sign,height, outer+5*sign,inner)
        if mode == "man":
            p.line("hair", tone, outer+sign,height+1, outer+3*sign,height+1, outer+5*sign,inner+1)
        elif mode == "woman" and lid is None:
            lash_y = 1 if expression in ("joy", "grin") else 0
            p.line("eye", 3, outer,lash_y+1, outer-sign,lash_y)
    p.dot("skin", 0, 0,4)
    p.dot("skin", 2, 1,4)
    mouth = MOUTHS[expression]
    y = 6 if len(mouth) > 1 else 7
    stamp(p, 1-len(mouth[0])//2, y, "\n".join(mouth))


# Alternative silhouettes. The far fall and nape are behind the skin plane.
# The three defaults still use the original bob, man's crest and tied plait.
def hair_back(p, mode, hair):
    if hair == HAIRSTYLES[mode][0]:
        bob(p, mode)
        return
    if hair == "waves":
        stamp(p, -19, -4, """
.......yyyyyyy
.....yyooowwyy
....yommowwwyy
...yommoowwwy
...yomoowwwwy
...yooowwyywy
....yoowwyywy
....yoowwyywy
....yoowwyywy
...yomoowwywy
..yommoowwywy
.yommoowwwyy
.yomoowwywy
.yooowwyywy
..yowwwy.ywy
..yoowwy..yy
...yoowy
....yowy
.....yyy
""")
    elif hair == "chignon":
        stamp(p, -18, -3, """
.......yyyy
.....yyooowy
...yyommoowy
..yomoowwwy
.yomoowwyy
yomoowwomwy
yooowwomowy
yoowwomowwy
.yowwomowwy
.yywoowwyy
...yyyyy
""")
        p.line("gold", 1, -15,0, -12,2)
        p.dot("gold", 0, -15,0)
    elif hair == "shag":
        for side in (-1, 1):
            q = p.local(0, 0)
            q.flip = side
            q.patch("hair", 2, 8,-8, 11,-6, 12,-1, 12,2, 13,4, 14,5, 11,5,
                    11,6, 9,5, 7,3, 7,-3, edge=True)
            q.line("hair", 1, 10,-2, 10,1, 12,4)
    # A compact skull lets headwear settle in the same place in every cut.
    p.patch("hair", 2, -11,-3, -10,-7, -7,-11, -3,-13, 3,-14, 7,-12,
            10,-9, 12,-5, 11,0, 9,2, 7,-3, -6,-4, -10,2, edge=True)
    p.patch("hair", 1, -9,-6, -6,-10, -2,-12, 2,-12, 4,-11, 0,-10, -5,-7)
    if hair == "curtains":
        for side in (-1, 1):
            q = p.local(0, 0)
            q.flip = side
            q.patch("hair", 2, 7,-10, 11,-7, 13,-3, 13,3, 11,5, 9,5, 8,2, edge=True)
            q.line("hair", 1, 10,-7, 12,-3, 12,2, 11,3)
    elif hair == "curls":
        for x,y in ((-11,-2), (-10,-9), (-6,-12), (-1,-14), (4,-12), (8,-9), (9,-2)):
            stamp(p, x-2, y, """
..yyyy
.yooowy
yomowwy
yowwwy
.ywwy
""")


def fringe(p, mode, hair):
    if hair == HAIRSTYLES[mode][0]:
        swept_fringe(p, mode)
    elif hair == "curtains":
        # The part opens onto the forehead; both tips sweep out to the ears.
        for side in (-1, 1):
            q = p.local(0, 0)
            q.flip = side
            q.patch("hair", 2, 0,-11, 4,-12, 9,-9, 11,-6, 11,1, 9,4, 8,1,
                    8,-3, 5,-4, 2,-6, 0,-8, edge=True)
            q.line("hair", 1, 1,-10, 2,-8, 5,-6, 8,-5, 10,-3)
            q.line("hair", 0, 3,-8, 5,-7)
    elif hair == "shag":
        p.patch("hair", 2, -11,-4, -8,-10, -2,-12, 5,-11, 10,-7, 11,-2,
                7,-4, 8,-2, 3,-5, 2,-2, -1,-4, -4,0, -4,-3, -8,-1,
                -10,2, edge=True)
        p.line("hair", 1, -9,-4, -5,-7, -2,-7, -4,-4)
        p.line("hair", 0, -7,-6, -5,-7)
        p.line("hair", 1, 1,-8, 4,-8, 7,-5)
    elif hair == "curls":
        for x,y in ((-11,-5), (-8,-7), (-4,-7), (0,-6), (4,-7), (7,-5)):
            stamp(p, x, y, """
.yyyy
yomowy
yowwwy
.yywy
""")
    elif hair == "side part":
        p.patch("hair", 2, -10,-4, -8,-10, -3,-13, 4,-13, 9,-10, 11,-5,
                10,-1, 7,-6, 6,-8, 4,-5, 0,-3, -5,-1, -9,1, edge=True)
        p.line("hair", 1, -9,-1, -6,-3, 0,-5, 4,-9)
        p.line("hair", 0, -6,-6, -3,-7, -1,-7)
        p.line("hair", 1, 7,-9, 9,-7, 10,-4)
    elif hair == "waves":
        p.patch("hair", 2, -11,2, -11,-5, -7,-11, 1,-13, 7,-11, 10,-7,
                10,-3, 7,-5, 4,-8, 2,-7, 0,-4, -5,-2, -8,-2, edge=True)
        p.line("hair", 1, -10,-1, -7,-4, -2,-5, 2,-9)
        p.line("hair", 0, -8,-4, -5,-5, -3,-5)
    else:  # The chignon pulls back both temples, away from the arched brows.
        p.patch("hair", 2, -10,0, -10,-7, -6,-11, 1,-13, 8,-10, 10,-6,
                10,-1, 8,-4, 5,-6, 1,-7, -5,-6, -9,-3, edge=True)
        p.line("hair", 1, -9,-5, -7,-7, -3,-9, 2,-10)
        p.line("hair", 0, -7,-8, -4,-10)


def goggles(p):
    # A narrow leather strap turns down around both temples. The lens rims
    # face the viewer and the short bridge lies over the hair between them.
    p.patch("dark", 2, -10,-5, -7,-9, -4,-10, 5,-10, 9,-8, 11,-5,
            10,-2, 8,-4, 4,-7, -4,-7, -8,-4, -9,-2, edge=True)
    p.line("gold", 2, -10,-3, -8,-5, -6,-6)
    p.line("gold", 2, 8,-6, 10,-4)
    p.line("gold", 2, -2,-8, 0,-9, 2,-8)
    for x in (-8, 1):
        stamp(p, x, -12, """
..llll
.lgsskl
lgpsttkl
lgsttukl
ljttuvkl
.lkuukl
..llll
""")


def hood(p):
    # The point, central seam and peak of the face opening share an axis.
    p.patch("cloth", 1, -13,6, -13,-3, -11,-9, -7,-13, -2,-15, 0,-16, 3,-15,
            8,-13, 11,-9, 13,-4, 13,6, 12,8, 11,5, 10,1, 8,-4, 4,-7, 0,-9,
            -5,-6, -9,-3, -10,3, -11,8, edge=True)
    p.patch("cloth", 2, 1,-15, 7,-12, 10,-8, 12,-4, 12,5, 11,4, 10,0,
            9,-5, 4,-9, 2,-10)
    p.line("cloth", 0, -11,-4, -10,-8, -7,-11, -2,-14, 0,-14)
    p.line("cloth", 0, -8,-5, -4,-8, 0,-10)
    p.line("cloth", 2, -12,5, -11,1, -10,-2)
    p.line("cloth", 2, 0,-14, 0,-11)
    p.line("cloth", 3, 1,-9, 5,-7, 9,-4, 10,-1)


# A hat's original insignia, brim and folds sit over its fitted side band.
# Offset the asymmetric crowns so their openings register to the temples.
BANDS = {
    "topper": ("dark", 2), "turban": ("cloth", 1), "field": ("cloth", 2),
    "cowl": ("cloth", 1), "lamp": ("dark", 1), "beret": ("dark", 2),
    "binder": ("scarf", 0), "duelist": ("cloth", 1), "mortar": ("dark", 1),
    "toque": ("scarf", 1), "trail": ("cloth", 1), "wrap": ("white", 1),
}


def fitted_hat(p, kind, hat):
    if kind == "goggles":
        goggles(p)
    elif kind == "hood":
        hood(p)
    elif kind == "helmlet":
        headgear(p, hat, None)
    elif kind in BANDS:
        mat, dx = BANDS[kind]
        p.patch(mat, 2, -11,-3, -10,-8, -5,-12, 2,-13, 7,-11, 10,-8, 12,-4,
                12,-1, 9,-3, 5,-5, -3,-6, -8,-4, -11,-1, edge=True)
        p.line(mat, 1, -10,-4, -7,-6, -3,-7)
        p.line(mat, 1, 6,-7, 9,-5, 11,-4)
        x,y,rows = HATS[kind]
        stamp(p, x+dx, y, rows)


def head(p, mode, hat, travel, expression=None, hair=None, blink=0):
    expression = EXPRESSIONS[0] if expression is None else expression
    hair = HAIRSTYLES[mode][0] if hair is None else hair
    if expression not in EXPRESSIONS:
        raise PackError(f"unknown Keepsake expression {expression!r}")
    if hair not in HAIRSTYLES[mode]:
        raise PackError(f"unknown {mode} hairstyle {hair!r}")

    # Local layers include the plait all the way to the shoulder. Keep the
    # face plane and default features registered on every cut and hat.
    ox, oy = 21, 17
    face = Pen(Drawing(42, 36), p.colors, (ox, oy))
    hair_back(face, mode, hair)
    face_plane(face, mode)
    expression_marks(face, mode, expression, blink)
    fringe(face, mode, hair)
    kind = travel if hat == "traveler-head" else CROWNS.get(hat, "bare")
    crown = Pen(Drawing(42, 36), p.colors, (ox, oy))
    fitted_hat(crown, kind, hat)
    if kind not in ("bare", "goggles"):
        # Tuck the crown of each cut into the actual outline of this hat. At
        # the outer temples the uncovered nape emerges below the band.
        for x in range(face.image.w):
            top = next((y for y in range(oy+1) if crown.image.get(x, y)), oy-2)
            for y in range(top):
                face.image.px[y][x] = None
    face.image.paste(crown.image, 0, 0)
    if hat in ("lore-head", "docs-head"):
        for x in (-7, 2):
            face.line("gold", 2, x,-1, x,2, x+2,4, x+5,3, x+6,0)
        face.line("gold", 2, -1,0, 2,0)
    p.image.paste(face.image, *p.xy(-ox, -oy))
