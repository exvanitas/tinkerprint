"""Hip-length enamel tiles. Joint and garment measurements are relative to the brow."""
from math import hypot

from .._colors import INK
from . import half_head, implements
from .enamel import bedroll, costume_front, stamp
from .paint import WRIST

# Hand centers, from the viewer's left to right. The free hand settles on the belt.
# Equipment and fingers register to the same pair of joints.
REST = (-9, 36)
HIP = (-9, 34)
LONG_TOOLS = {"spanner", "orrery", "foil", "nib", "washbrush", "spade", "crook"}
GRIPS = {
    "pavise": (REST, (12, 30)),
    "codex": ((-10, 31), (10, 31)),
    "mug": (REST, (7, 29)),
    "teapot": (REST, (6, 29)),
    "map": ((-10, 31), (10, 31)),
    "cog": ((-7, 32), (7, 32)),
    "fan": ((-3, 33), (5, 31)),
    "lantern": (REST, (4, 25)),
    "scope": ((-9, 30), (6, 28)),
    "key": (REST, (9, 31)),
    "washbrush": ((-10, 31), (14, 34)),
    "nib": (HIP, (20, 30)),
    None: (REST, (8, 34)),
}


def joints(item):
    return GRIPS.get(item, (HIP, WRIST))


def torso(p, body, mantle, travel):
    # A little negative space between the hips and each elbow makes the bend visible.
    p.patch(mantle, 3, -5,13, 5,13, 14,17, 16,23, 12,31, 12,36, 15,43,
            12,45, -12,45, -15,43, -12,35, -13,27, -16,22, -13,17)
    if mantle == "cape":
        p.patch("cape", 1, -7,14, -13,16, -16,23, -18,31, -23,40,
                -20,40, -21,43, -15,41, -10,43, -8,34, edge=True)
        p.line("cape", 2, -21,39, -17,35, -15,29)
    if travel:
        bedroll(p.local(-1, 3), travel)
    p.patch("cloth", 1, -4,12, 4,12, 8,14, 13,16, 14,21, 12,29, 10,35,
            11,38, 14,43, 11,45, -11,45, -14,43, -11,37, -11,33, -14,24,
            -14,18, -9,15, edge=True)
    p.patch("cloth", 2, 8,17, 13,18, 13,23, 10,32, 9,36, 12,42, 10,44,
            4,44, 6,36, 4,31)
    p.patch("cloth", 2, -12,25, -8,28, -4,31, 3,30, 1,33, -7,35, -10,34)
    p.line("cloth", 0, -11,19, -9,17, -6,16)
    p.line("cloth", 2, -8,43, -5,38)
    p.line("cloth", 3, 0,38, -1,44)
    waist(p, body, travel)
    implements.neck(p)
    costume_front(p.local(0, 1), body, 12, travel)
    if body == "tools-coat":
        belt_hammer(p)


def waist(p, body, travel=None):
    if body == "logic-coat":
        # Crossed robe and a broad sash, with one pleat opening over the hip.
        p.patch("cloth", 2, 5,21, 9,18, 5,29, -2,36, -6,35)
        p.line("gold", 1, 7,21, 4,27, -3,35)
        p.patch("cloth", 3, -10,33, -1,35, 10,32, 10,36, 2,39, -10,37)
        p.line("cloth", 0, -9,34, -2,36, 3,36, 9,34)
        p.patch("cloth", 1, 2,38, 5,37, 4,44, 0,44, edge=True)
        p.line("gold", 1, 2,42, 3,42)
    elif body == "infra-coat":
        # Linen surcoat over mail, edged in the guard's dye, with a split front.
        p.patch("white", 2, -8,20, -4,21, 4,21, 8,19, 7,34, 9,44,
                2,45, 0,41, -2,45, -9,44, -7,33, edge=True)
        p.patch("white", 1, -5,22, 0,23, 0,38, -3,43, -6,43, -5,35)
        p.line("cloth", 2, 5,23, 4,33, 6,43)
        belt(p)
    elif body == "community-coat":
        p.patch("white", 1, -7,21, 6,21, 7,32, 12,43, 9,45, -9,45, -12,43,
                -8,33, edge=True)
        p.patch("white", 2, 4,24, 6,24, 6,33, 10,43, 8,44, 5,42, 3,35)
        p.line("white", 0, -9,42, -7,35)
        p.line("scarf", 2, -8,32, -2,33, 6,32)
        p.patch("white", 2, -5,36, 3,36, 3,40, 0,42, -4,40, edge=True)
        p.line("white", 0, -4,36, 2,36)
    elif body == "tools-coat":
        p.patch("dark", 2, -7,22, 6,22, 7,33, 9,43, 6,45, -8,44, -6,32, edge=True)
        belt(p)
        # One steel cross-peen hammer in a wide stitched leather loop.
        pouch(p, -10, 36)
    elif body == "traveler-coat":
        if travel:
            # The shoulder sling continues into the satchel at the far hip.
            p.patch("gold", 2, -2,23, 1,24, 10,36, 8,39, edge=True)
            p.line("gold", 1, 0,26, 6,34)
        else:
            p.patch("dark", 2, -9,22, -3,23, 0,29, -2,34, -5,36, -10,33, edge=True)
            p.line("dark", 1, -8,29, -5,30)
        belt(p)
        pouch(p, 3, 36)
    elif body in ("models-coat", "lore-coat"):
        p.patch("cloth", 2, -5,22, -1,24, 3,39, 3,45, -3,45, -4,34, edge=True)
        p.line("gold", 1, -4,24, -2,31, 0,43)
        p.line("cloth", 0, 9,31, 5,34, 2,34)
    elif body == "systems-coat":
        p.patch("dark", 2, -7,23, 7,23, 8,34, 10,43, 7,45, -8,45, -8,32, edge=True)
        belt(p)
        p.line("steel", 2, 4,39, 8,38, 7,42, 5,43, 3,41)
    elif body in ("data-coat", "worlds-coat", "art-coat"):
        facing = "cloth" if body == "art-coat" else "gold"
        p.patch(facing, 2, 1,24, 4,25, 10,34, 9,37, 6,36, edge=True)
        p.line(facing, 1, 3,27, 8,34)
        belt(p)
        if body == "art-coat":
            # Overlapping pockets in the canvas smock.
            p.line("cloth", 3, 4,39, 9,38, 8,42, 5,43, 3,41)
            p.line("cloth", 0, 4,39, 7,38)
    else:
        # Fitted coats continue below the lapel. The fly overlaps the belt.
        p.patch("cloth", 2, 1,22, 4,21, 3,34, 1,37, -1,34)
        p.line("cloth", 0, 1,27, 1,29)
        p.line("gold", 1, -1,30, 0,30)
        p.line("gold", 2, -1,33, 0,33)
        belt(p)


def belt_hammer(p):
    stamp(p, -1, 27, """
.vvvv
.vsstv..vvvv
.vsttvtstttuv
.vuttsttuvvuv
.vvvvvtuv...v
.....ljkl
.....ljkl
.....ljkl
....ljkl
....ljkl
...lggjkll
...lkjjkkl
....lllkll
...ljkll
...ljkl
..lkkl
...ll
""")


def pouch(p, x, y):
    stamp(p, x, y, """
.llllllll
lkkkjjjkl
ljjjjjjkl
.ljjgkkll
.lkkjkkll
.ljkkklll
..llllll
""")


def belt(p):
    p.patch("gold", 3, -11,34, -3,36, 4,36, 10,34, 11,38, 4,40, -3,40, -11,38)
    p.line("gold", 2, -10,35, -3,37, 3,37, 9,35)
    p.patch("gold", 1, -3,36, 2,36, 2,39, -3,39)
    p.line("dark", 2, -2,37, 0,37, 0,38)


def arm(p, side, hand, body):
    """Cut the sleeve from shoulder to elbow, then turn the cuff across the forearm."""
    q = p.local(0, 0)
    q.flip = side
    fabric = "sleeve" if side == 1 else "cloth"
    ex, ey = 18, 35
    # The cuff ends on the outside heel of the palm.
    wx, wy = side*hand[0]+2, hand[1]+1
    q.patch(fabric, 2, 9,15, 13,15, 16,17, 17,20, ex+2,ey-4, ex+2,ey+1,
            ex,ey+3, ex-3,ey+3, ex-5,ey, 12,25, 10,22, 9,18, edge=True)
    q.patch(fabric, 1, 10,16, 13,16, 15,18, 16,21, ex,ey-1,
            ex-2,ey, 13,25, 11,22)
    if side == -1:
        q.line(fabric, 0, 12,16, 15,18, 16,21, 16,23)
    else:
        q.line(fabric, 0, 10,17, 12,16, 14,17)
    q.line(fabric, 3, 13,24, 15,26, 16,26)
    if body == "infra-coat":
        q.patch("steel", 2, 9,17, 11,15, 14,15, 17,18, 17,21,
                14,23, 10,21, edge=True)
        q.line("steel", 1, 10,17, 12,16, 14,16, 16,18)
        q.line("steel", 0, 11,17, 13,16)
    dx, dy = wx-ex, wy-ey
    length = max(1, hypot(dx, dy))
    ux, uy = dx/length, dy/length
    nx, ny = -uy, ux

    def across(x, y, offset, along=0):
        return (round(x+offset*nx+along*ux), round(y+offset*ny+along*uy))

    a, b = across(ex, ey, -3), across(ex, ey, 3)
    c, d = across(wx, wy, 2), across(wx, wy, -2)
    q.patch(fabric, 1, *a, *across(ex, ey, 0, -3), *b, *c, *d, edge=True)
    q.line(fabric, 2, *across(ex, ey, 2), *across(wx, wy, 1))
    q.line(fabric, 0, *across(ex, ey, -2), *across(wx, wy, -1, -2))
    q.patch("dark", 2, *across(wx, wy, -3, -2), *across(wx, wy, 3, -2),
            *across(wx, wy, 2, 1), *across(wx, wy, -2, 1), edge=True)
    q.line("steel", 1, *across(wx, wy, -2, -2), *across(wx, wy, 1, -2))
    if body == "community-coat":
        q.patch("white", 1, *across(ex, ey, -3, 1), *across(ex, ey, 3, 1),
                *across(ex, ey, 2, 4), *across(ex, ey, -2, 4), edge=True)
        q.line("white", 0, *across(ex, ey, -2, 2), *across(ex, ey, 1, 2))


# Each pattern faces in from the viewer's left sleeve. Mirroring the rows also
# mirrors the thumb, while the top edge keeps the light in either hand.
HANDS = {
    "rest": """
..LLL....
.L@@+LL..
L++++@@L.
L++::+++L
.L++L++:L
..L+:L+:L
...LL.LL.
""",
    "hip": """
....LLLL..
..LL@@++L.
.L@@+++++L
L+++++L+:L
.L++++L.L.
..L@+++L..
..L++:+:L.
...L++L+:L
....L+:L:L
.....LL.L.
""",
    "palette": """
..LLL...
.L@@+L..
.L++:L..
..LLL...
L+:L....
.L+:LL..
..LLLL..
""",
    "cup": """
...LL...
..L@@L..
.L++:L..
L+++LL.L
L++++++L
.L:+++L.
..LLLL..
""",
    "pinch": """
...LLL..
..L@@+L.
.L+:+:LL
L++L++@L
L+++++L.
.L:++L..
..LLL...
""",
    "under": """
........
......LL
..LL.L+L
.L@@L++L
L+++++L.
.L:++L..
..LLL...
""",
    "grip": """
...LLLL.
..L+@@+L
.L++:LL.
L+++L++L
L+++:LL.
.L:+++L.
..LLLL..
""",
}


def hand(p, center, side, shape):
    x, y = center
    rows = HANDS[shape].strip().splitlines()
    if side == 1:
        rows = [r[::-1] for r in rows]
    stamp(p, x-4, y-3, "\n".join(rows))


def shield(q):
    # Convex heater profile, central ridge and an enamel compass boss.
    q.patch("steel", 2, -9,-8, -3,-10, 1,-12, 9,-9, 9,-1, 7,5,
            4,9, 0,12, -4,10, -8,5, -10,-1, edge=True)
    q.patch("sleeve", 1, -8,-7, -3,-8, 0,-10, -1,9, -5,5, -8,0, edge=True)
    q.patch("sleeve", 2, 1,-10, 7,-8, 7,-1, 5,5, 0,10)
    q.line("steel", 0, -9,-7, -4,-9, 1,-11, 6,-9)
    q.line("steel", 1, -8,2, -5,7, -1,10)
    q.line("steel", 1, 1,-9, 0,7)
    q.patch("gold", 1, 0,-7, 2,-3, 6,-2, 2,0, 0,5, -2,0, -6,-2, -2,-3)
    q.line("gold", 0, -5,-2, -1,-3, 0,-5)
    q.line("gold", 2, 0,2, 1,-1, 4,-2)


def book(q):
    # Sloping upper edges and a dipping gutter describe two open signatures.
    q.patch("scarf", 3, -12,-9, -9,-10, -3,-9, 0,-7, 4,-9, 11,-10,
            12,-9, 12,1, 5,2, 1,4, -2,4, -6,2, -12,1)
    q.patch("white", 1, -11,-9, -7,-9, -2,-7, 0,-6, 0,2, -5,0, -11,-1)
    q.patch("white", 0, 1,-6, 5,-8, 11,-9, 10,-1, 5,0, 1,2)
    q.line("gold", 2, 0,-6, 0,2)
    q.patch("scarf", 2, -9,-7, -7,-7, -7,-4, -5,-4, -5,-3, -9,-4)
    q.line("dark", 1, 4,-5, 8,-6)
    q.line("gold", 2, 4,-3, 7,-4)
    q.patch("scarf", 1, 6,0, 8,-1, 8,4, 7,3, 6,4)


def tankard(q):
    # The open pewter handle sits on the hand side, the staves hang inboard.
    stamp(q, -13, -8, """
..vvvvvvvvvv
.vssqqpssttuv
.vstttttuuuuvvvvv
.vgjjjjjkkllvsttuv
.vgjkkjjkjklvu..tuv
.vgjkkjjkjklv...tuv
.vgjkkjjkjklv...tuv
.vgjkkjjkjklv..vtuv
.vgjkkjjkjklvvvttv
.vgjkkjjkjklvttuv
.vsttttttttuvvvv
.vsssttttuuuv
..vvvvvvvvvv
""")


def staff(q):
    q.patch("gold", 2, -2,13, 0,-3, 3,-18, 5,-18, 2,-2, 0,13, edge=True)
    q.line("gold", 1, -1,11, 0,3, 2,-9, 3,-15)
    q.line("steel", 1, -2,12, 0,12)
    stamp(q, -1, -29, """
....HHHHH
..HHYYZZZH
.HXppYYYZZH
.HXpXYYYZZH
HXXYYYYZZZHH
HYYYYYZZZZHH
HYYZZZZZZHHH
.HZZZZZZHHH
l.HZZZHHHH.l
ljlHHHHH.ljl
.lgjlllljjl
..lgjjjjkl
....ljjkl
....lggjl
.....lll
""")


def brush(q):
    # Wide flat sash brush: blue paint, pale bristles, a steel ferrule
    # and a turned handle. The straight chisel edge is broadside to the viewer.
    q.patch("gold", 2, -6,-11, -4,-11, 0,-4, 2,2, 5,7, 4,9,
            2,8, -1,1, -3,-3, edge=True)
    q.line("gold", 1, -5,-9, -2,-4, 0,0, 3,6)
    # Lacquer-blue paint wets the outside third of the bristles. Deliberate
    # steps break the cut edge. The narrow ferrule meets the handle at its heel.
    q.patch("dark", 3, -15,-12, -11,-16, -11,-15, -7,-19, -6,-19,
            -4,-16, -1,-12, -2,-10, -7,-5, -9,-6, edge=True)
    q.patch("gold", 1, -13,-12, -7,-17, -5,-16, -2,-12, -7,-7, -9,-7)
    q.line("gold", 0, -12,-12, -9,-9)
    q.line("gold", 2, -10,-14, -6,-10)
    q.line("white", 1, -8,-15, -5,-12)
    q.image.shape(INK["2"], *q.points((-15,-12, -11,-16, -11,-15, -7,-19, -6,-19,
            -5,-16, -7,-15, -8,-15, -9,-13, -11,-13, -12,-11, -13,-10)))
    q.image.line(INK["1"], q.xy(-14,-12), q.xy(-12,-14))
    q.image.line(INK["3"], q.xy(-10,-15), q.xy(-8,-17))
    q.patch("steel", 1, -9,-7, -3,-13, -1,-12, -1,-10, -6,-5, -8,-5, edge=True)
    q.line("steel", 0, -8,-7, -4,-11)
    q.line("steel", 2, -6,-6, -2,-10)


def paint_palette(p, joint):
    # The thumb comes through the hole. The outer edge scoops in beside it.
    x, y = joint
    stamp(p, x-6, y-8, """
........lllllll
.....llllkkjjkkll
...lljjjjjjjjjjkkl
..ljjjjjjjjjjjjjjkl
.ljjjjjjjjjjjjjjjkl
ljjlljjjjjjjjjjjjkl
ljl..lkjjjjjjjjjkkl
lkl..ljjjjjjjjjkkl
.lkllljjjjjjjjkkl
..llljjjjjjjjkkl
....lljjjkkklll
......llllll
""")
    for dx, dy, light, dark in ((0,-5,"w","e"), (6,-5,"3","2"), (7,-1,"r","R")):
        p.image.stamp((".aa", "abb", "bb."), {"a": INK[light], "b": INK[dark]},
                      *p.xy(x+dx, y+dy))


def foil(q):
    # A continuous cool edge survives against the cream ground. The warm
    # reflection stops short of the point, leaving its silhouette intact.
    q.patch("steel", 3, 0,-6, 1,-13, 7,-27, 7,-24, 4,-13, 3,-6)
    q.line("steel", 1, 2,-8, 3,-14, 6,-22)
    q.line("steel", 0, 2,-10, 3,-13)
    q.patch("dark", 2, -3,6, -2,1, 0,-7, 3,-7, 1,1, -1,7, edge=True)
    q.patch("steel", 2, -4,-6, -2,-9, 1,-10, 4,-10, 7,-7, 8,-5,
            5,-4, -1,-4, edge=True)
    q.line("steel", 0, -3,-7, 0,-9, 3,-9)
    q.line("gold", 2, -4,-5, 1,-4, 7,-4, 6,1, 3,5, -1,6)
    q.line("gold", 1, 7,-3, 6,1, 4,3)
    q.patch("gold", 1, -4,5, -2,4, 0,6, -1,8, -4,8, edge=True)


def lantern(q):
    # The brass bail meets both roof pivots. There is daylight under the hand.
    stamp(q, -10, -2, """
.....lllllll
....ljjjjjjkl
...ljl....ljkl
..ljl......lkl
..ljl......lkl
..ljl..vv..lkl
...llvsttuvll
...vssttttuuuv
.vsssttttttuuuv
..vgjpppqqjjlv
...ljpjjpjjkl
...ljjjppjjkl
...ljjpggpjkl
...lgppggpjkl
...ljpggggpkl
..vstttttttuuv
..vssttttttuuv
...vvuuuuuuvv
""")


def fan(q):
    q.patch("white", 2, -12,-7, -8,-13, 3,-4, -2,2, edge=True)
    q.line("dark", 2, -9,-8, -8,-10, -6,-8)
    q.patch("white", 1, -8,-12, -2,-15, 4,-3, 0,1, edge=True)
    q.patch("scarf", 2, -5,-10, -4,-12, -2,-11, -2,-9)
    q.patch("white", 0, -2,-13, 4,-14, 6,-2, 1,1, edge=True)
    q.patch("dark", 2, 0,-9, 2,-12, 4,-9, 2,-7)
    q.patch("white", 0, 5,-13, 12,-11, 8,1, 1,-1, edge=True)
    q.patch("scarf", 2, 6,-8, 8,-11, 10,-8, 8,-4)
    q.dot("scarf", 1, 8,-9)


def cog(q):
    # Eight substantial teeth and a bored axle. The top and bottom teeth
    # remain clear of the two hands holding the sides.
    stamp(q, -10, -12, """
........lllll
........lggjl
...lll..lgjjl..lll
..lgjjllggjjjllgjjl
...ljjgggkkkkjjjjl
....lggjklvvvljkl
...lgjjklvsttvljkl
lllggjklvst.utvljjllll
lgjjjjklvt...uvlkjjjjl
ljjkkkklvt...uvlkkjjkl
lllljjklvut.tuvljkllll
...ljjkklvttvlkjkl
....ljjkkllllkkkl
...ljjkkjjkkkkjjjl
..lgjkllljjjllljjkl
...lll..ljjkl..lll
........ljjkl
........lllll
""")


def quill(q):
    # The split metal nib flares below the grip and narrows to an ink point.
    q.patch("gold", 2, -3,5, -2,1, 1,-7, 4,-11, 3,-5, 0,2, edge=True)
    stamp(q, -6, 2, """
....vvv
...vssuv
..vstsuv
.vsstutv
.vstvtuv
.vtvttv
.vtvuv
.vuvv
.vvv
.h
""")
    stamp(q, 0, -23, """
.........ii
.......ippqi
.....ippqqi
....ippqqri
...ippqqqri
...ippqqqri
..ippqqqri
..ipqqrii
.ipqqqri
.ipqqqri
.ipqqri
ipqqrii
ipqqri
ipqqi
iqrii
.qri
.ri
""")
    q.line("gold", 2, 0,-5, 3,-12, 7,-18)


# These items register directly to the working hand.
HANDHELD = {"mug": tankard, "lantern": lantern, "orrery": staff, "washbrush": brush,
            "foil": foil, "nib": quill}


def equipment(p, item, left, right, travel):
    """The bare object. Its outer contour is independent of the pose's fingers."""
    x, y = right
    grip = p.local(x, y)
    middle = (left[0]+x)//2
    if item in HANDHELD:
        HANDHELD[item](grip)
    elif item == "pavise":
        shield(p.local(x-6, y))
    elif item == "codex":
        book(p.local(middle, y))
    elif item == "fan":
        fan(p.local(x-4, y+1))
    elif item == "map":
        implements.chart(p.local(middle-4, y))
    elif item == "cog":
        cog(p.local(middle, y))
    elif item == "scope":
        stamp(p.local(middle-3, y+1), *implements.TOOL_HEADS[item])
    elif item == "teapot":
        # Handle on the working side and spout toward the free hand.
        _, top, grid = implements.TOOL_HEADS[item]
        rows = grid.strip().splitlines()
        width = max(map(len, rows))
        stamp(grip, 4-width, top, "\n".join(row.ljust(width, ".")[::-1] for row in rows))
    elif item == "key":
        implements.instrument(grip, item, {})
    elif item:
        # Stand the forged heads upright on their shanks.
        stock = grip.local(0, 0, scale=1.08, turn=-32)
        if item == "spanner":
            implements.wrench(stock)
        else:
            implements.instrument(stock, item)
        if item == "crook":
            grip.patch("gold", 2, -3,6, -1,5, -2,13, -4,13, edge=True)
            grip.line("gold", 1, -3,12, -2,7)
            if travel == "trail":
                implements.trail_pennon(stock)


def hands(p, item, left, right, *, palette=False):
    if item in ("codex", "map", "cog", "scope"):
        hand(p, left, -1, "cup")
        hand(p, right, 1, "cup")
    elif item == "fan":
        hand(p, left, -1, "under")
        hand(p, right, 1, "pinch")
    else:
        if palette:
            hand(p, left, -1, "palette")
        else:
            hand(p, left, -1, "hip" if item in LONG_TOOLS else "rest")
        if item != "pavise":
            hand(p, right, 1, "grip" if item else "rest")


def portrait(p, costume, hat, mode, tool, mantle, look, kit, foreground_only=False,
             expression=None, hair=None, motion=None):
    travel = None
    if hat == "traveler-head":
        travel = "wrap" if look.set_name == "tinkerer" else "trail"
    alternate = implements.ALTERNATES.get(tool)
    item = alternate if alternate and kit.get("trinket") == alternate else tool
    left, right = joints(item)
    if not foreground_only:
        torso(p, costume["body"], mantle, travel)
        arm(p, -1, left, costume["body"])
        arm(p, 1, right, costume["body"])
        if look.kind == "pair":
            implements.trade_shoulder(p, 13, kit.get("gear"))
        if motion and motion.breath:
            # Lift the garment and shoulder caps together. The extra row opens
            # first above the chest, then farther down the ribs. The waist,
            # cuffs and equipment stay anchored as the fabric settles.
            seam = p.xy(0, 20 if motion.breath == 1 else 25)[1]
            p.image.px[:seam] = p.image.px[1:seam] + [p.image.px[seam][:]]
        half_head.head(p, mode, hat, travel, expression, hair, motion.blink if motion else 0)
    # The shield hand is fully behind its face. A small wrist connects it to the cuff.
    if item == "pavise":
        x, y = right
        p.patch("skin", 1, x-2,y-1, x+3,y-2, x+5,y, x+4,y+2, x,y+3, edge=True)
    equipment(p, item, left, right, travel)
    if item == "lantern" and motion and motion.ember:
        wick = p.local(*right)
        wick.line("gold", 1, -3,9, -3,10)
        wick.line("white", 0, -2,10, -2,11)
        if motion.ember == 2:
            wick.dot("white", 0, -1,9)
    palette = item == "washbrush" and kit.get("trinket") == "paints"
    if palette:
        paint_palette(p, left)
    hands(p, item, left, right, palette=palette)
