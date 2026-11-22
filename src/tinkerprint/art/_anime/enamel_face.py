"""The face planes, iris shapes and copper hair of the Keepsake portraits."""
from .enamel import stamp


def bob(p, mode):
    """The tied fall is behind the far shoulder, separated from the jaw by daylight."""
    if mode == "woman":
        # The two ribbons trade sides at each crossing. A brass tie finishes the plait.
        stamp(p, -17, -6, """
.......yyyy
.....yyooowy
....yommoowy
...yomooowwy
...yoowwoowy
..yowwomowy
..ywwomoowy
..yomooowwy
.yomooowwy
.yooowwooy
..yowwoowy
..ywwomooy
...yomoowy
...yooowwy
..yoowwoy
..ymowooy
...yooowy
...yowwy
...ljjkl
....lkl
...yooy
..yowy
..yy
""")
    if mode == "neutral":
        # The blunt bob is wide at the temples and turns in above the jaw.
        p.patch("hair", 3, -11,-6, -8,-10, 4,-11, 10,-7, 12,-3, 12,2, 11,4,
                9,5, 7,-2, -7,-2, -9,6, -11,5, -12,3, -12,-2)
        p.patch("hair", 1, -11,-4, -8,-7, -8,-4, -10,1, -10,4, -11,3)
        p.patch("hair", 2, 9,-5, 11,-3, 11,2, 10,4)
    # The brushed crop opens both temples. Its crest bends away from the part.
    if mode == "man":
        p.patch("hair", 2, -9,-2, -9,-7, -7,-10, -3,-12, -5,-13, 0,-14,
                5,-13, 8,-11, 10,-8, 11,-4, 10,0, 7,-4, -7,-4, edge=True)
        p.patch("hair", 1, -8,-7, -6,-10, -2,-11, -3,-12, 1,-13, 5,-12, 0,-11)
        p.line("hair", 0, -6,-10, -3,-11)
    else:
        end = 4 if mode == "neutral" else 3
        p.patch("hair", 2, -10,end-3, -10,-6, -8,-10, -4,-12, 2,-13, 7,-11,
                10,-7, 11,-4, 11,end-2, 9,end, 6,-3, -6,-3, -9,end, edge=True)
        p.patch("hair", 1, -8,-8, -5,-11, -1,-12, 3,-12, 6,-10, 2,-10, -3,-9)



def face_plane(p, mode):
    # Symmetric half-widths cut the cheek-to-chin curve on the native grid.
    jaws = {"man": (10,10,10,10,10,9,9,8,7,5,3),
            "neutral": (9,9,9,9,9,8,8,7,6,4,2),
            "woman": (9,9,9,9,8,8,7,6,5,3,1)}
    widths = (5,7,8,9,9,9,9) + jaws[mode]
    for y, half in enumerate(widths, -7):
        p.line("skin", 1, 1-half,y, 1+half,y)
        p.dot("skin", 2, 1-half,y)
        p.dot("skin", 3, 1+half,y)
        if 1 <= y <= 7:
            p.dot("skin", 2, half,y)
    for y in range(5, 10):
        half, below = jaws[mode][y:y+2]
        if half > below:
            p.line("skin", 2, 1-half,y, -below,y)
            p.line("skin", 3, 1+half,y, 2+below,y)
    base = widths[-1]
    p.line("skin", 2, 1-base,10, 1+base,10)



def smiling_features(p, mode, eyelid=None):
    # Each iris has a pupil, an amber lower facet and one top-left catchlight.
    # The upper lid and the white corners are shaped together on the native grid.
    eyes = {
        "neutral": (".ddddd.", "dwWbdww", ".wbdbw.", ".wggbw.", "..bg..."),
        "man":     ("..dddd.", "ddWbddw", ".wbdbw.", "..ggbw."),
        "woman":   (".ddddd.", "dwWbdww", ".wbdbww", ".wbggw.", "..bgw.."),
    }
    colors = {"d": p.colors["eye"][3], "b": p.colors["eye"][2], "g": p.colors["eye"][1],
              "w": p.colors["white"][0], "W": p.colors["eye"][0]}
    for x in (-7, 3):
        p.image.stamp(eyelid or eyes[mode], colors, *p.xy(x,-1))
        if mode == "woman":
            outer = x if x < 0 else x+6
            off = -1 if x < 0 else 1
            if eyelid is None:
                p.line("eye", 3, outer-off,-1, outer,-1, outer+off,-2)
            p.line("hair", 2, x+1,-3, x+3,-4, x+4,-4)
        elif mode == "man":
            p.patch("hair", 3, x,-4, x+3,-4, x+5,-3, x+4,-2, x+1,-3, x,-3)
        else:
            p.line("hair", 3, x+1,-2, x+2,-3, x+4,-3)
    p.dot("skin", 0, 0,4)
    p.dot("skin", 2, 1,4)
    p.dot("skin", 2, -1,6)
    p.line("skin", 3, 0,7, 2,7)
    p.dot("skin", 2, 3,6)


def swept_fringe(p, mode):
    # Use broad connected clumps so the part still reads below an opaque brim.
    if mode == "man":
        p.patch("hair", 2, -10,-5, -7,-10, 2,-11, 9,-8, 10,-3,
                7,-5, 4,-6, 1,-6, -1,-5, -1,-7, -5,-5, -8,-4, -9,-1)
        p.line("hair", 1, -8,-6, -4,-8, 0,-8)
    elif mode == "neutral":
        p.patch("hair", 2, -10,1, -10,-5, -6,-10, 4,-11, 9,-7, 10,-2,
                7,-4, 4,-6, 1,-5, -4,-2, -3,-5, -7,-1, -9,5)
        p.patch("hair", 1, -9,-2, -7,-6, -1,-9, 4,-9, -2,-6, -6,-4)
        p.line("hair", 0, -8,-3, -6,-5, -3,-6)
    else:
        p.patch("hair", 2, -10,2, -10,-6, -6,-10, 2,-11, 8,-8, 10,-5,
                11,1, 8,-2, 6,-5, 3,-7, -1,-4, -6,-2, -9,2)
        p.line("hair", 1, -9,-2, -6,-5, -2,-6, 1,-8)
        p.line("hair", 1, 5,-7, 8,-5, 9,-3)
