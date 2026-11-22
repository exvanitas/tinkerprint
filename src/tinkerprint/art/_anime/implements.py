"""Forged tools, buckled shoulders and collar details shared by the enamel portraits."""
from .enamel import stamp


def long_axis(grip):
    # Cut the long implements on an outward diagonal above the low hand.
    return grip.local(0, 0, scale=.90, turn=28)


def wrench(q):
    q = long_axis(q)
    # A deep, square-bottomed mouth, two forged flats and a solid diagonal shank.
    shaft(q, "steel", (3,-7))
    q.patch("steel", 2, 1,-6, -1,-9, -1,-14, 2,-17, 5,-18, 6,-18,
            3,-13, 3,-11, 6,-10, 9,-14, 11,-15, 11,-11, 9,-7, 6,-5,
            3,-5, 0,-1, edge=True)
    q.patch("steel", 1, 0,-13, 2,-16, 4,-17, 2,-13, 2,-10,
            5,-8, 8,-9, 6,-7, 3,-7, 1,-8)
    q.line("steel", 0, 0,-13, 1,-15, 4,-17)
    q.line("steel", 1, 7,-10, 10,-13)
    q.line("steel", 0, 2,-7, 0,-3)
    q.dot("steel", 1, -3,5)


# Construction of the second trade's far shoulder, keyed to the pack's gear part.
SHOULDER_CUTS = {
    "infra-gear": "plate", "systems-gear": "plate", "worlds-gear": "plate",
    "logic-gear": "mantle", "models-gear": "mantle", "interface-gear": "mantle",
    "docs-gear": "stole", "lore-gear": "stole", "tests-gear": "stole",
    "tools-gear": "strap", "data-gear": "strap", "art-gear": "strap",
    "community-gear": "roll",
}


def trade_shoulder(p, s, gear):
    q = p.local(-s+1, 18)
    cut = SHOULDER_CUTS.get(gear, "mantle")
    if cut == "plate":
        q.patch("sleeve", 2, -5,4, -3,0, 1,-2, 5,-1, 7,2, 3,5, -2,6, edge=True)
        q.patch("sleeve", 1, -4,3, -2,0, 1,-1, 4,0, 2,2, -2,4)
        q.line("steel", 0, -3,2, -1,0, 2,-1)
        q.line("steel", 1, -3,5, 0,4, 4,2)
    elif cut == "strap":
        q.patch("sleeve", 1, -5,3, 0,-2, 3,-2, 9,6, 7,9, 1,3, -4,6, edge=True)
        q.line("sleeve", 0, -4,3, 0,0, 2,0, 5,4)
        q.patch("gold", 1, 2,2, 4,1, 6,4, 4,5, edge=True)
    elif cut == "stole":
        q.patch("sleeve", 1, -4,2, 1,-2, 4,-2, 4,2, 7,7, 6,10, 0,7, -1,3,
                -4,5, edge=True)
        q.line("sleeve", 0, -2,2, 1,0, 1,3, 4,7)
    elif cut == "roll":
        q.patch("sleeve", 1, -6,4, -3,0, 2,-2, 5,0, 4,3, -3,7, edge=True)
        q.line("white", 1, -4,4, 2,0, 4,0)
    else:
        q.patch("sleeve", 1, -6,5, -3,0, 1,-2, 5,-1, 8,2, 4,4, 2,7, -1,5,
                -5,7, edge=True)
        q.line("sleeve", 0, -4,3, -2,0, 1,-1, 4,0)
        q.dot("gold", 0, 4,1)


def trail_pennon(grip):
    # A trail pennon lashed below the hook flies back over the pack.
    staff = long_axis(grip)
    staff.patch("scarf", 2, 7,-13, 12,-12, 14,-13, 14,-6, 11,-7, 9,-5,
                9,-9, 5,-10, edge=True)
    staff.line("scarf", 1, 8,-12, 11,-11, 13,-12)


def neck(p):
    # The neck narrows beneath the jaw then widens into the collar bones.
    p.patch("skin", 2, -2,10, 3,10, 4,13, 7,15, 3,17, -3,17, -6,15, -2,13)
    p.line("skin", 3, 3,11, 4,13, 6,14)
    p.patch("skin", 1, -1,11, 1,12, 3,12, 3,14, 5,15, 1,16, -4,15, -1,13)


# Heads of the tools are drawn full size around the grip. Open bows, slots and
# bails expose whatever is actually behind them, including another trade's sleeve.
TOOL_HEADS = {
    "key": (1, -10, """
..lll...lll
.lgjkl.lgjkl
.lj.lklj.lkl
..ljjjjjjjl
...lljjjll
....ljjkl
"""),
    "cog": (-6, -9, """
.......llll
.......lggl
...lll.lgjl..lll
..lggjllgjjllgjjl
...ljjggjjjjjjkl
....ljjjlllljjkl
.lllljjltttuljjllll
.lggjjltv..vuljjjjl
.ljjjjltv..vuljkkkl
.lllljjltttuljjllll
....ljjjlllljjkl
...ljjjjjjjjjjjkl
..lgjjlljjjlljjjkl
...lll.ljjkl.lll
.......ljjkl
.......llll
"""),
    "mug": (-4, -9, """
..........vvvvvvvvv
.........vsspppjjjlv
....vvvvvvuuuuuuuuvv
..vvstttvvggjjjjkllv
.vstuuuvvlggjkkjkllv
.vtu....vlggjkkjkllv
.vtu....vlggjkkjkllv
.vttv...vlggjkkjkllv
..vttvvvvljgjkkjkllv
...vuuttvljgjkkjkllv
.....vvvvussttttttuv
.........vttttttuuv
..........vvvvvvvv
"""),
    "scope": (-10, -8, """
....................llll
..............llllllgjtvl
...........lllgjjjjlgjtstl
.......llllggljjjjjljjtptl
....lllgggjjjlnnnnnljjtptl
..llgjljjjjjjlfffffljjtqtl
.vvlgjljjkkkklnnnnnljjttul
vstljjlkkklllhhhhhhllkttul
vutlklllll.........llkttvl
.vvl................lllll
"""),
    "teapot": (-4, -9, """
..........ll
.........lgjl
.........llkl
.......vvsttv......v
......vssttuuv....vtv
..vvvvvsssttuvv..vstv
.vstttvqqqqpppivvstu
vst..vppppppppqistuv
vtu..vpppqppqqqistuv
vtu..vquttuuuuuttuv
.vtu.vqsttttttuquv
..vtuuvqqpppqqqiv
...vvv.vqqqqqqiv
........vvtttuv
.........vuuuv
"""),
    "lantern": (-2, -3, """
..lllllll
.ljjjjjjkl
.lkl....ljl
.lkl.....ljl
..ll..vv.lll
...llvttvljl
....vssttuuv
..vvsttttuuuv
...lpqpqqjkl
...lpgpqqjkl
...ljqggjjkl
..vstttttuuuv
...vuuuuuuvv
"""),
}


def shaft(p, material, end):
    x, y = end
    p.patch(material, 2, -6,8, x-1,y, x+1,y-1, x+2,y, -3,8, -5,9, edge=True)
    p.line(material, 1, -4,7, x,y)


def trowel(q):
    q = long_axis(q)
    shaft(q, "gold", (2,-6))
    # Cranked steel tang and a pointed triangular blade with a squared heel.
    q.line("steel", 3, 1,-5, 2,-9, 5,-9, 6,-12)
    q.line("steel", 1, 2,-5, 3,-8, 6,-8, 7,-12)
    q.patch("steel", 2, -1,-12, 11,-23, 12,-22, 11,-9, 9,-8, edge=True)
    q.patch("steel", 1, 0,-12, 10,-21, 6,-13, 4,-11)
    q.line("steel", 0, 0,-12, 10,-21)
    q.line("steel", 3, 5,-10, 9,-17)


def chart(q):
    # Three accordion folds, a river crossing the folds and a marked destination.
    q.patch("white", 0, -6,-6, -1,-8, 4,-6, 9,-9, 13,-8, 14,0, 10,-1,
            5,2, 0,0, -5,3, edge=True)
    q.patch("white", 2, 0,-7, 4,-5, 5,1, 1,-1)
    q.patch("white", 1, 9,-8, 12,-7, 13,-1, 10,-2)
    q.line("gold", 2, -1,-7, 0,-1)
    q.line("steel", 2, -5,-4, -3,-4, -2,-6, 1,-5, 4,-2, 7,-2, 10,-4, 12,-3)
    q.line("scarf", 2, 6,-6, 9,-4)
    q.line("scarf", 2, 6,-4, 9,-7)
    q.line("gold", 1, -5,-6, -3,-7)


# These kits already include a larger, recognizable object for a close portrait.
# A look swaps to the larger object only when its kit's trinket is that object,
# so a custom trade can retain the original handheld part.
ALTERNATES = {"scope": "map", "key": "cog", "teapot": "mug"}


def instrument(q, tool, kit=None):
    alternate = ALTERNATES.get(tool)
    if alternate and (kit is None or kit.get("trinket") == alternate):
        tool = alternate
    if tool == "map":
        chart(q)
    elif tool == "spade":
        trowel(q)
    elif tool == "crook":
        q = long_axis(q)
        shaft(q, "gold", (5,-11))
        q.patch("gold", 2, 4,-9, 5,-12, 9,-16, 10,-19, 9,-20, 7,-20, 5,-18,
                4,-15, 2,-15, 2,-18, 4,-21, 7,-23, 10,-23, 13,-21, 13,-17,
                11,-14, 7,-10, 6,-8, edge=True)
        q.line("gold", 0, 3,-17, 5,-20, 8,-22, 10,-22)
        q.line("gold", 1, 6,-11, 10,-15, 11,-18)
    elif tool in TOOL_HEADS:
        if tool == "key":
            q.patch("gold", 2, -4,4, 4,-8, 6,-9, 7,-8, -1,5, -3,6, edge=True)
            q.line("gold", 1, -2,4, 5,-8)
        stamp(q, *TOOL_HEADS[tool])
        if tool == "key":
            # Square socket of a clock key at the heel of the palm.
            q.patch("gold", 1, -4,3, -1,4, -2,6, -6,5, edge=True)
    return tool
