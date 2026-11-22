"""Native pixel patterns for the Keepsake tile. Capitals sample the costume dye."""
CROWNS = {
    "infra-head": "helmlet", "logic-head": "hood", "interface-head": "topper",
    "tools-head": "goggles", "data-head": "field", "models-head": "turban",
    "tests-head": "duelist", "docs-head": "mortar", "systems-head": "lamp",
    "art-head": "beret", "worlds-head": "cowl", "lore-head": "binder",
    "community-head": "toque", "traveler-head": "field", "base": "bare",
}

# Four inks in each material, ordered from lit to deep.
INKS = {"ABCD": "cloth", "XYZH": "sleeve", "stuv": "steel", "gjkl": "gold",
        "pqri": "white", "efnh": "dark", "abcd": "scarf", "mowy": "hair", "@+:L": "skin"}


def stamp(p, x, y, rows):
    colors = {ch: p.colors[material][tone] for symbols, material in INKS.items()
              for tone, ch in enumerate(symbols)}
    p.image.stamp(rows.strip("\n").splitlines(), colors, *p.xy(x, y))


# Crowns register to the brow, leaving both eyes and the silhouette of the cut clear.
# Each row is a native pixel, including the spaces inside brims, folds and buckles.
HATS = {
    "topper": (-15, -16, """
...hhhhhhhhhhhhhhhhhhh
..hfffeeeeeeffffffnnnnh
..hfBBBBBBBBBBBCCCCCnnh
...hBBBBBBBBBBCCCCCCnh
...hBBBBBBBBBBBBCCCCnh
....hBBBBBBBBBBCiqqinh
....hBBBBBBBBBCipppiCh
....hnnnnnnnnnniqpinnh
....hjjjjjjjjkkkikkllh....hh
.hhhffffffffffffnnnnnnhhhffh
hfffeeeeeeeeeffffffffffnnnh
.hhnnnnnnnnnnnnnnnhhhhhhh
...hhhhhhhhhhhhhhh
"""),
    "goggles": (-12, -15, """
...........hhhhh
........hhhnnnnnhh
.....hhhnfffennnnfh
....hnnfffennnhhnnnh
..hhljjjlhhnnljjjllnh
.hlggjjjjlhhlgjjjjjlh
.hljsstuvljjljsstuvlh
.hljsttuvlnnljtttuvlh
.hhluuuvvlnnnluuuvvlh
.hhnljjjlhhnnnljjjlh
..hhllllhnnhhhllllh
..hhhnnhhh
"""),
    "hood": (-15, -16, """
.............DDDDDD
..........DDDAAABBCDD
........DDAABBBBBCCCDDDD
.......DABBBBBBCCCCCBBBD
......DABBBBBCCCCCCDDDD
.....DABBBBCCCCCDDD
....DABBBCCCCDDDCCCD
...DABBCCCDDDCCCBBCCD
...DBBCCDD..DCBBBBBCCD
..DABCDD.....DDCCBBBCCD
..DBCDD.........DDCCCBCD
.DBCDD.............DDDCCD
.DCDD.................DDCD
.DCD....................DD
.DCD
DDCD
DCD
DD
"""),
    "turban": (-12, -16, """
.................ll
................lgj....l
..........DDDDD.lgjl..jl
.......DDDAABBBD.lgjjjl
.....DDABBBBCCCBD.ljjl
....DABBBBCCCDDDBBDllD
...DABBBCCDDDAABBBBBCD
..DABBCCDDAABBBBBBCCCCD
..DBCCDAABBBBBCCCCDDDCD
.DCCDAABBBBCCCDDjjkCCD
.DBABBBCCCCDDDDjssjkD
.DCCCCCDBBBBCCCjttjkD
..DDDDDCCCCCDDDDjjlD
.......DDDDD
"""),
    "field": (-16, -14, """
..........DDDD...DD
.........DABBBDBDBCD
........DABBBBCCBBCD
.......DABBBBBBBBBCD
.......DBBBBBCCCCCCCD
......DnnnnnnnnnnhhCD
.....DjjjjjjjkkkllhCCD..DDD
..DDDAABBBBBBBBBBBBCCCDDBCD
.DABBBBBBBBBBBBBCCCCCCCCDD
DBBBCCCCCCCCCCCCDDDDDDDD
.DDDDDDDDDDDDDDD
"""),
    "cowl": (-13, -16, """
..........DDDDDDDDDDD
........DDABBBAABBBBCD
......DDABBBBCABBBBCCD
.....DABBBBCCABBBBCCCD
....DABBBBCCABBCCCCCBCD
...DABBBCCDAABBCCDDBCCD
...DBBCCDDABCCCDDDDBCCD
..DBBCDDAABCCDD...DBCCD
..DBCDAABCCDD......DBCD
..DCDAABCCD........DCCD
..DDAABCCD.........DCCD
.DAABCCD............DCCD
.DBBBCD.............DCCD
.DBBCCD.............DCCCD
DBBBCCD.............DCCCD
.DBCCD...............DCCCD
.DDCD................DCCCD
...D..................DDCD
........................D
"""),
    "lamp": (-13, -16, """
..........hhhhhhhhhhh
......hhhheefffffffnnh
....hheeffffffffffnnnh
...hfffnvvvvvvvvvvnnnh
...hffnvsssttuuuvvnnnh
...hfnvsssttuutuvnnnh
..hhfnvttuuttuuuvnnnh
.ljjlnvvvvvvvvvvnnnh
.lgjlnfffnnnnnnfnnh
.lgjkhfffnhhnnfnnh
..llhhffnhhnnfnnh
..hfffhffnnnfnnh
..hnnnnhhnnnnnh
...hhhhhhhhhhl
"""),
    "beret": (-16, -15, """
..................DDD
...............DDDABD
...........DDDDACCDD
.......DDDDAAABBBBCD
....DDDAABBBBBBBBBBCD
..DDABBBBBBBBBCCCCCCCD
.DABBBBBBBCCCCCCCCCCCD
DABBBBBBCCCCDDDCCCCCCD
DBBBBCCCCDDDDnnnnDDDD
.DCCCCCDhnneffffnnh
..DDDDDhnnffffffnh
......hhhhhhhhhhh
"""),
    "binder": (-11, -15, """
......dddddddddddddd
....ddaaabbbbbbbbcdd
...dabbbbbbbbcccdiqi
...dbbbbbbccccccipqi
...dbbbccccccccipprid
...dbcccccccccciqridd
...dhhjjjjjkkkkjjkhhd
..dljjjjkkkklllllhhhd
.dcccccccdddddddddd
.dddddddd
"""),
    "duelist": (-15, -16, """
.....................DDD
...................DDABD
...............DDDDAABCD
............DDDAABBBBCD
.........DDDAABBBBBBCCD
.......DDABBBBBBBBCCCD
....DDDBBBBBBBBCCCCCD
..DDABBBBBBCCCCCDCCCD
.DABBBBBCCCCCDDDjjjkCDD
DABBCCCCCCDDDjjjllkDBCCD
.DCCCCCCDDDjjllDDBBBBCCDD
..DDDDDDDllllDDCCCCCCDDDD
.......DDDDDDDDDDDDDD
"""),
    "mortar": (-15, -16, """
..............hhhh
...........hhhffffhhh
........hhhffeeeeffffhhh
.....hhhfffffffBBBBBffffhhh
..hhhfffffBBBBBBBBBBBffffffhhh
.hffffBBBBBBBBBBBBBBffffffffnnh
..hhhnnnnBBBBBffffffffnnhhhhjl
.....hhhnnnfffffffnnhhhh....jl
.......lhhhnnnnnnhhhnh......jl
.......lBBChhhnnhBBnnh......jl
.......lBBBCCChhBBCnnh.....jgjl
.......lCCBBBBBBCCnnh......jgjl
........llllllllllll.......lkkl
"""),
    "toque": (-14, -12, """
...dddd
..dabbbd...........dddd
.dbbbbbddd......dddabbbdd
..dbcddabbd..dddabbbbbbccd
.dccddabbbdddabbbbbbbcccdd
.dddabbbddabbbbbbccccddd
..ddbbbdbbbbbbccccddd
...ddddbbbccccdddd
....ddbcccdddd
.....ddddd
"""),
    "trail": (-14, -15, """
............lllllll
.........lllAABBBBCl
.......llABBBBBBBCCCl
......lABBBBBBBCCCCCll
......lBBBBBCCCCCCll.Bl
.....lBBBCCCCCCllll.BCl
.....lnnnnjjjnnnnhlBBCl
..lllAABBBjljBBBCCBBCCl
.lABBBBBBBjjjBBCCCCCll
lBBBBCCCCCCCCCCCClll
.llllllllllllllll
"""),
    "wrap": (-14, -16, """
.........iiiiiiiiii
......iiippppppppqqii
....iipppppppqqqqqqqqii
...ipppppqqqqqqqrrrrrrqi
..ipppqqqqqqrrrrrrqqqqrqi
..ippqqqrrrrrqqqqqpppqqri
.iqqqrrrqqqqppppppqqqqrri
.iqrrqqqpppppppqqqqrrrri
.irqqppppppqqqqrrrrrrrii
.iqppppqqqqrrrriiiiiiri
.ipppqqrrrriiii......ii
.iqqrrriiii
.iqriii
.iqri
iqqri
iqpri
ipqri
iqqri
.iri
..i
"""),
}


def headgear(p, hat, travel_cut):
    kind = CROWNS.get(hat, "bare")
    if hat == "traveler-head":
        kind = travel_cut
    if kind == "helmlet":
        # The polished dome has an axial rib, broad reflected plane and a riveted brow.
        p.patch("steel", 2, -12,-4, -12,-8, -9,-12, -5,-15, 1,-16,
                6,-15, 10,-12, 12,-8, 12,-4, 8,-3, -9,-2, edge=True)
        p.patch("steel", 1, -11,-7, -9,-11, -5,-14, -1,-15, 3,-15,
                1,-12, -1,-9, -1,-7)
        p.line("steel", 0, -9,-10, -7,-12, -3,-14, 0,-14)
        p.patch("steel", 0, 2,-15, 4,-15, 6,-12, 7,-8, 5,-8, 4,-12)
        p.line("steel", 3, 6,-14, 8,-11, 9,-8)
        p.patch("steel", 1, -13,-5, -6,-7, 6,-8, 12,-7, 12,-4, 6,-5,
                -7,-4, -12,-2, edge=True)
        p.line("steel", 0, -11,-5, -6,-6, 3,-7)
        p.patch("steel", 2, -12,-3, -9,-4, -9,0, -11,2, -12,1, edge=True)
        p.line("gold", 1, -11,-3, -10,-3)
        p.dot("gold", 0, 9,-6)
    elif kind != "bare":
        stamp(p, *HATS[kind])
    if hat in ("lore-head", "docs-head"):
        for x in (-7, 2):
            p.line("gold", 2, x,-1, x,2, x+2,4, x+5,3, x+6,0)
        p.line("gold", 2, -1,0, 2,0)


def bedroll(p, travel_cut):
    # A roll of cloth lashed across the pack, seen over the far shoulder.
    rows = """
....llllhhhhhh
..lleeekkfffllh
.lefnfffkffjjlnh
.lfneefnlfjjllnh
lfffnnefljjlfnnh
lfnneenefllfnnnh
lfefneeflffnnhh
.lfneeeflnnhh
..lfffnhhhh
...lhhh
"""
    if travel_cut == "wrap":
        rows = rows.translate(str.maketrans("efnh", "pqri"))
    stamp(p, -17, 9, rows)


def gorget(p, s):
    p.patch("steel", 2, -s-3,17, -s+1,13, -s+5,14, -s+7,18, -s+3,20, -s-4,20, edge=True)
    p.line("steel", 0, -s-2,17, -s+1,14, -s+3,14)
    p.patch("steel", 2, -9,12, -5,13, 2,14, 8,11, 9,15, 4,19, -2,19, -9,16, edge=True)
    p.line("steel", 1, -8,13, -2,15, 2,15, 7,13)
    p.line("steel", 0, -11,20, -5,23, 1,23)


def crossed_lapels(p, facing, depth):
    p.patch(facing, 1, 5,12, 9,14, 8,17, 1,depth, -1,depth-2, 4,15, edge=True)
    p.patch(facing, 1, -7,12, -4,14, 0,17, 2,depth, -3,depth-2, -10,16, -7,16, edge=True)
    p.line(facing, 0, -6,13, -4,15, -2,17)


def apron(p, s, bib):
    p.patch(bib, 2, -s+2,14, -s+5,14, -4,19, 3,19, 8,14, 10,16, 6,21,
            6,28, -7,28, -7,21, edge=True)
    p.line("gold", 1, -s+3,15, -s+5,17)
    p.line(bib, 1, -5,22, 2,22)


def shawl(p, s, mat, drop):
    p.patch(mat, 2, -7,11, -2,14, 3,14, 8,11, s+1,15, 5,19, 0,drop,
            -8,19, -s-3,18, -s,14, edge=True)
    p.patch(mat, 1, -s,15, -8,12, -4,15, 2,17, 6,15, 1,drop-2, -8,17, -s-2,17)
    p.line(mat, 0, -s,15, -8,13, -4,16)


def costume_front(p, body, s, travel_cut):
    """Shape the neckline, shoulder and chest using the equipped coat part."""
    if body == "infra-coat":
        gorget(p, s)
    elif body == "interface-coat":
        crossed_lapels(p, "cloth", 23)
        p.patch("white", 0, -5,13, 1,15, 6,12, 5,15, 2,18, -2,17, edge=True)
        p.patch("scarf", 2, -2,16, 0,15, 2,17, 0,20, edge=True)
    elif body == "logic-coat":
        shawl(p, s, "cloth", 23)
        p.line("gold", 1, -s-1,18, -7,20, 0,24, 4,21)
        p.patch("gold", 1, -2,19, 0,17, 2,19, 0,22, edge=True)
    elif body == "tools-coat":
        crossed_lapels(p, "cloth", 19)
        apron(p, s, "dark")
        p.line("steel", 1, -4,21, -4,24, -2,24)
    elif body == "data-coat":
        # Storm cape and the map-case baldric passing over its hem.
        shawl(p, s, "cloth", 18)
        p.patch("gold", 2, -s+1,13, -s+4,13, 4,26, 2,28, edge=True)
        p.line("gold", 0, -6,18, -3,21, -5,22, -8,19, -6,18)
    elif body == "models-coat":
        # A gathered, scalloped mantle with two chains meeting the pendant.
        p.patch("dark", 2, -8,11, -4,14, 2,15, 7,11, 11,14, 8,18, 4,18,
                1,21, -3,19, -6,19, -9,17, -14,18, -12,14, edge=True)
        p.line("gold", 1, -12,15, -9,16, -5,16, 0,19, 5,16)
        p.patch("cloth", 1, -2,19, 0,17, 2,19, 0,23, edge=True)
        p.line("gold", 0, -1,19, 0,18)
    elif body == "tests-coat":
        p.patch("white", 1, -7,11, -2,13, 3,13, 8,11, 7,16, 1,18, -5,16, edge=True)
        p.patch("dark", 2, -s-2,13, -8,12, -6,17, -1,24, -9,20, -8,18, -13,17, edge=True)
        p.line("gold", 1, -12,14, -9,14, -7,18, -3,22)
        p.line("cloth", 0, -7,23, -4,24, -2,24)
    elif body == "docs-coat":
        crossed_lapels(p, "dark", 24)
        p.patch("white", 0, -5,13, 1,14, 6,12, 5,15, 3,20, 1,20, 1,16, -1,20, -4,19, -3,15,
                edge=True)
    elif body == "systems-coat":
        p.patch("gold", 2, -7,12, 0,15, 7,12, 8,15, 3,18, -5,17, edge=True)
        # Heavy canvas bib with two brass buckles and a steel pocket stay.
        apron(p, s, "cloth")
        p.line("gold", 1, -9,16, -7,16, -6,18, -8,18, -9,16)
        p.line("steel", 0, -5,22, 2,22)
        p.line("cloth", 3, -5,23, -5,25, -2,26, 2,24)
    elif body == "art-coat":
        p.patch("white", 1, -s-2,15, -8,11, -4,14, 2,15, 7,11, 10,14, 6,17,
                1,19, -6,18, -s-3,20, edge=True)
        p.line("scarf", 1, -s,15, -7,16, -3,18)
        p.patch("cloth", 2, -7,12, -4,13, 4,26, 1,27, edge=True)
        p.line("steel", 1, -5,18, -3,21)
    elif body == "worlds-coat":
        shawl(p, s, "cloth", 20)
        p.patch("dark", 2, -12,16, -8,16, 4,25, 2,28, -11,20, edge=True)
        p.line("steel", 1, -13,15, -10,14, -7,16, -8,18, -11,18, -13,15)
        p.line("cloth", 0, -15,20, -10,22, -6,22)
    elif body == "lore-coat":
        crossed_lapels(p, "white", 18)
        p.patch("cloth", 3, -s,13, -7,12, -4,18, 2,26, -2,28, -10,19, edge=True)
        p.line("gold", 1, -8,14, -6,18, 0,25)
        p.line("cloth", 1, -10,16, -9,19, -4,24)
    elif body == "community-coat":
        # Linen shirt, crossed apron straps and a rolled serving sleeve.
        crossed_lapels(p, "white", 20)
        apron(p, s, "dark")
        p.patch("white", 1, -s-2,17, -s+1,14, -s+4,14, -s+5,17,
                -s+2,20, -s-3,22, edge=True)
        p.line("white", 0, -s-2,18, -s+1,16, -s+3,16)
        p.patch("gold", 1, -8,18, -6,17, -4,18, -4,20, -6,21, -8,20, edge=True)
        p.dot("dark", 3, -6,19)
        p.line("gold", 1, -6,21, -6,25, -3,25, -3,24)
        p.line("gold", 0, -7,19, -7,18)
    elif travel_cut == "wrap":
        shawl(p, s, "white", 22)
        p.line("cloth", 2, -12,16, -6,17, 0,21, 4,18)
        p.line("gold", 2, -12,20, -3,27)
    elif travel_cut == "trail":
        crossed_lapels(p, "cloth", 22)
        p.patch("dark", 2, -12,14, -9,13, 4,25, 1,27, edge=True)
        p.line("gold", 1, -9,16, -7,15, -5,17, -7,19, -9,17)
    else:
        # An open waistcoat separates the empty hand from the sand-colored sleeve.
        p.patch("dark", 2, -s,15, -8,12, -5,14, -2,21, 0,25, -2,28, -10,26,
                -s,21, edge=True)
        p.line("dark", 1, -s+1,17, -s+2,21, -8,24)
        crossed_lapels(p, "white", 18)
        p.line("cloth", 3, 1,18, 0,25)
        p.line("cloth", 0, -s-2,17, -s,15, -s+2,15)
