"""Trade fixtures for the west workbench. A kit chooses a fixture and a tray of objects."""
from .._drawing import Drawing
from ..pixels import Canvas
from .enamel import MATERIALS, tile

# The key is the equipped kit's shelf symbol. A new class can reuse any fixture
# and any stock here. Pairs keep the primary fixture and borrow the second tray.
FURNISHINGS = {
    "helmlet": ("arms", ("shield", "helm", "gauntlet", "whetstone")),
    "paints": ("easel", ("canvases", "brushes", "pigments", "palette")),
    "candle": ("library", ("scrolls", "folios", "candle", "ink")),
    "mug": ("cellar", ("mugs", "bottles", "pitcher", "bread")),
    "map": ("atlas", ("globe", "scrolls", "compass", "charts")),
    "cog": ("pipe organ", ("gears", "gauge", "bellows", "oiler")),
    "books": ("lectern", ("ink", "quill", "folios", "scrolls")),
    "runebook": ("observatory", ("compass", "lens", "folios", "crystal")),
    "hammer": ("forge", ("bellows", "gauntlet", "oiler", "whetstone")),
    "flask": ("retort", ("crystal", "bottles", "candle", "lens")),
    "frame": ("theatre", ("cards", "mirror", "crystal", "masks")),
    "hourglass": ("balance", ("weights", "lens", "ink", "hourglass")),
    "sprout": ("terrarium", ("seedlings", "oiler", "charts", "pitcher")),
    "trail": ("trail chest", ("compass", "bedroll", "charts", "helm")),
    "wander": ("loom", ("bedroll", "yarn", "pitcher", "folios")),
    "arrival": ("luggage", ("bread", "boots", "candle", "bedroll")),
}

# Palette-key drawing on the fixture's native grid. Keep the accents below the
# paper and gold highlights of the figure in front of the window.
PIGMENT = {k: v for keys, ramp in MATERIALS.items() for k, v in zip(keys, ramp)}


def panel(d, x, y, w, h, edge, field, light):
    d.rect(x, y, w, h, edge)
    d.rect(x+1, y+1, w-2, h-2, field)
    d.rect(x+1, y+1, w-2, 1, light)
    d.rect(x+1, y+1, 1, h-2, light)


def disk(d, x, y, r, ink):
    for dy in range(-r, r+1):
        dx = int((r*r + r//2 - dy*dy)**.5)
        d.rect(x-dx, y+dy, 2*dx+1, 1, ink)


def book(d, x, y, w, cover):
    d.rect(x, y, w, 4, cover)
    d.rect(x+2, y+1, w-3, 2, "e")
    d.rect(x+2, y+1, w-4, 1, "E")
    d.set(x+1, y+2, "g")


def jug(d, x, y, glaze="S"):
    d.grid(x,y,"""
  ssss
   Es
   Es
  SSSs
 SESSss
 SEESss
 SSSsss
  ssss
""".replace("S", glaze))


def hoop(d, x, y, w, h):
    # An elliptical coopering profile with iron bands and bowed staves.
    d.shape("l",(x+3,y),(x+w-3,y),(x+w,y+4),(x+w,y+h-4),(x+w-3,y+h),
            (x+3,y+h),(x,y+h-4),(x,y+3))
    d.shape("a",(x+3,y+1),(x+w-4,y+1),(x+w-2,y+4),(x+w-2,y+h-4),
            (x+w-4,y+h-1),(x+3,y+h-1),(x+1,y+h-4),(x+1,y+4))
    for dx in (4, w//2+2, w-3):
        d.line("A",(x+dx,y+2),(x+dx-1,y+5),(x+dx-1,y+h-4),(x+dx,y+h-2))
    for yy in (y+3, y+h-4):
        d.rect(x,yy,w+1,2,"d")
        d.rect(x+1,yy,w-1,1,"s")
    d.rect(x+4,y+1,w-7,1,"L")


def arms(d):
    for x in (3,28):
        d.rect(x,9,2,19,"l")
        d.set(x,10,"g")
    for y in (11,23):
        panel(d,1,y,31,4,"l","a","A")
    for x,h in ((5,3),(12,0),(18,4)):
        d.line("d",(x+3,8+h),(x+2,21))
        d.shape("s",(x,7+h),(x+2,4+h),(x+3,8+h),(x+2,22),(x,25))
        d.line("S",(x+2,6+h),(x+1,19))
        d.rect(x-2,22,7,2,"g")
        d.rect(x+1,24,2,7,"a")
        d.rect(x,30,4,2,"G")
    # A substantial convex buckler hangs by its leather strap. Its bright
    # spine and boss separate it even from a similarly colored masonry wall.
    d.line("a",(23,17),(27,12),(30,17))
    d.shape("d",(20,17),(26,15),(33,17),(32,24),(30,28),(26,31),(22,27),(20,24))
    d.shape("G",(21,18),(26,16),(32,18),(31,24),(26,29),(23,26),(21,23))
    d.shape("s",(22,18),(26,17),(31,18),(30,23),(26,28),(23,24))
    d.line("S",(22,19),(26,17),(29,18))
    d.line("S",(26,18),(26,26))
    disk(d,26,22,2,"g")
    d.set(25,21,"Y")



def easel(d):
    d.line("l",(4,34),(14,5),(18,3),(29,34))
    d.line("A",(5,34),(15,3),(18,3),(27,34))
    d.rect(15,0,3,9,"a")
    panel(d,5,6,24,20,"l","e","L")
    d.rect(5,26,25,2,"a")
    d.rect(5,26,24,1,"L")


def library(d):
    for x,y,w,cover in ((2,30,19,"v"),(3,26,17,"r"),(1,22,19,"t"),(3,18,17,"a"),
                        (2,14,16,"q"),(4,10,15,"r"),(17,30,15,"a"),(18,26,14,"h")):
        book(d,x,y,w,cover)
    for x,y,h,cover in ((20,13,13,"t"),(24,12,14,"r"),(28,15,11,"v")):
        d.rect(x,y,4,h,cover)
        d.rect(x,y,1,h,"l")
        for yy in (y+2,y+h-3):
            d.rect(x+1,yy,2,1,"G")


def cellar(d):
    # One cask stands upright. The tapped keg shows its circular head and
    # a section of the staves behind the front hoop.
    hoop(d,1,15,15,17)
    disk(d,23,24,9,"l")
    disk(d,24,24,8,"a")
    disk(d,21,24,8,"d")
    disk(d,21,24,7,"A")
    disk(d,21,24,6,"a")
    d.line("A",(17,20),(24,20))
    d.line("l",(16,23),(26,23))
    d.line("l",(16,26),(25,26))
    d.rect(20,25,4,2,"G")
    d.rect(23,26,2,3,"g")
    d.rect(16,32,12,2,"l")
    d.rect(3,4,27,2,"a")
    for x in (5,14,23):
        d.line("g",(x+2,5),(x+2,8),(x,9))
        d.rect(x,8,5,5,"S")
        d.rect(x+1,9,3,4,"s")
        d.rect(x+5,9,2,3,"G")
        d.set(x+5,10,"l")


def atlas(d):
    d.shape("l",(2,6),(17,4),(31,7),(30,29),(15,27),(1,30))
    d.shape("e",(3,6),(17,5),(30,7),(29,27),(15,26),(2,28))
    d.shape("T",(5,9),(12,8),(15,12),(13,16),(9,17),(7,21),(5,19))
    d.shape("t",(21,12),(27,10),(28,15),(24,17),(24,22),(21,21),(20,16))
    d.line("V",(6,26),(13,21),(17,21),(20,19),(27,18))
    d.line("A",(17,6),(16,16),(15,25))
    for x,y in ((3,6),(29,7),(2,27),(29,26)):
        d.set(x,y,"g")
    d.rect(6,30,18,3,"A")
    d.rect(5,30,2,4,"E")


def pipes(d):
    for x,h,end in ((3,12,10),(12,4,19),(21,8,31)):
        d.line("d",(x+2,32),(x+2,h+3),(x+4,h+1),(end,h+1))
        d.line("d",(x+1,32),(x+1,h+2),(x+3,h),(end,h))
        d.line("s",(x,32),(x,h+2),(x+2,h),(end,h))
        d.line("S",(x-1,32),(x-1,h+2),(x+2,h-1),(end,h-1))
        d.rect(x-2,21,5,3,"g")
        d.rect(x-2,21,4,1,"G")
        d.rect(end,h-2,3,5,"s")
    for x,y,r in ((10,27,6),(21,24,5)):
        disk(d,x,y,r,"g")
        for dx,dy in ((0,-r),(-r,0),(r,0),(0,r)):
            d.rect(x+dx-1,y+dy-1,3,3,"A")
        disk(d,x,y,r-2,"d")
        d.line("g",(x-r+1,y-1),(x+r-1,y+1))
        d.line("g",(x-1,y+r-1),(x+1,y-r+1))
        disk(d,x,y,1,"S")


def lectern(d):
    d.rect(15,18,5,15,"l")
    d.rect(15,19,2,14,"A")
    d.rect(10,32,16,2,"a")
    d.shape("a",(1,22),(6,8),(19,6),(31,9),(29,23),(18,21),(4,25))
    d.shape("E",(3,21),(7,8),(14,7),(18,9),(15,20),(11,19))
    d.shape("e",(16,20),(19,9),(24,7),(30,9),(27,20),(23,18))
    for y in (11,14,17):
        d.line("A",(8,y),(12,y-1),(15,y))
        d.line("A",(21,y),(24,y-1),(27,y))
    d.line("r",(20,10),(18,19),(17,24))


def observatory(d):
    for x in (8,23):
        d.line("a",(16,21),(x,33))
    d.rect(14,21,5,6,"g")
    d.shape("d",(3,18),(25,5),(31,11),(8,24))
    d.shape("s",(4,18),(23,7),(27,12),(8,22))
    d.line("S",(7,17),(23,8))
    for x,y in ((4,18),(11,14),(20,9),(26,6)):
        d.line("g",(x,y),(x+3,y+5))
    d.line("G",(25,5),(30,11))
    d.line("V",(27,4),(32,10))


def forge(d):
    panel(d,8,23,19,10,"l","a","A")
    d.shape("d",(1,12),(31,12),(30,17),(22,19),(21,23),(27,26),(8,26),
            (14,22),(13,18),(6,17))
    d.rect(8,12,22,3,"s")
    d.rect(7,12,23,1,"S")
    d.line("l",(6,28),(17,6))
    d.line("A",(6,27),(16,6))
    d.shape("s",(8,7),(11,2),(21,7),(21,10),(17,12))
    d.line("S",(11,3),(18,6))


def retort(d):
    d.rect(3,30,29,3,"a")
    d.rect(5,7,2,23,"s")
    d.rect(4,11,14,2,"s")
    d.line("S",(13,15),(16,6),(21,6),(25,14),(28,15),(29,21))
    d.line("s",(15,15),(18,8),(20,8),(24,16),(27,17),(28,21))
    disk(d,11,21,8,"s")
    disk(d,11,21,6,"V")
    d.shape("h",(5,22),(9,20),(17,22),(16,25),(12,28),(8,27))
    d.line("E",(6,20),(7,17),(10,16))
    jug(d,25,22,"V")


def theatre(d):
    panel(d,2,5,30,27,"l","n","g")
    d.rect(4,7,26,23,"q")
    for x,flip in ((4,1),(29,-1)):
        d.shape("r",(x,7),(x+10*flip,7),(x+8*flip,12),(x+4*flip,17),(x+3*flip,20),
                (x+6*flip,28),(x,29))
        d.line("R",(x+2*flip,8),(x+2*flip,12),(x+flip,17))
        d.rect(min(x,x+4*flip),19,5,2,"G")
    d.rect(1,31,32,3,"a")
    d.shape("G",(17,12),(18,16),(21,17),(18,18),(16,22),(15,18),(12,17),(15,16))


def balance(d):
    d.line("l",(4,12),(16,8),(29,11))
    d.rect(15,7,3,25,"g")
    d.rect(15,8,1,24,"G")
    d.rect(10,31,14,3,"a")
    d.line("G",(3,11),(16,7),(30,10))
    for x,y in ((5,11),(28,10)):
        for dx in (-5,5):
            d.line("s",(x,y),(x+dx,y+11))
        d.line("l",(x-5,y+12),(x-2,y+15),(x+2,y+15),(x+5,y+12))
        d.shape("g",(x-5,y+11),(x+5,y+11),(x+2,y+14),(x-2,y+14))
        d.rect(x-5,y+11,11,1,"G")
    disk(d,16,6,2,"G")


def terrarium(d):
    d.shape("s",(1,17),(10,7),(22,7),(32,16),(31,31),(3,31))
    d.shape("v",(3,17),(11,9),(21,9),(30,17),(29,29),(4,29))
    for x,y in ((7,19),(17,16),(23,21)):
        d.line("t",(x+1,29),(x+1,y))
        d.shape("T",(x+1,y+5),(x-3,y+3),(x-4,y),(x-1,y+1))
        d.shape("T",(x+1,y+8),(x+5,y+3),(x+7,y+3),(x+5,y+7))
    d.line("S",(2,16),(31,16))
    d.line("s",(16,30),(16,16),(20,8))
    panel(d,1,29,32,5,"l","a","A")


def trail_chest(d):
    d.line("a",(7,31),(11,2))
    d.shape("r",(12,3),(27,5),(20,8),(12,10))
    panel(d,2,18,29,15,"l","a","A")
    d.rect(2,22,29,3,"l")
    for x in (6,24):
        d.rect(x,18,3,14,"g")
        d.rect(x,18,1,14,"G")
    panel(d,14,22,5,5,"l","G","A")


def loom(d):
    for x in (4,27):
        d.rect(x,5,3,29,"a")
        d.rect(x,5,1,28,"A")
    for y in (8,26):
        panel(d,2,y,30,4,"l","a","A")
    for x in range(8,27,3):
        d.rect(x,12,1,14,"e")
    d.rect(8,17,18,10,"h")
    for x in range(8,25,5):
        d.line("E",(x,18),(x+2,21),(x,24))
    d.rect(7,27,20,2,"q")


def luggage(d):
    panel(d,3,22,29,11,"l","r","R")
    d.rect(6,30,24,1,"c")
    panel(d,5,11,24,12,"l","A","L")
    for x in (9,23):
        d.rect(x,12,2,10,"g")
    d.line("l",(13,11),(13,8),(19,8),(20,11))
    d.shape("e",(20,14),(23,12),(27,16),(24,19))
    d.set(23,14,"a")


FIXTURES = {
    "arms": arms, "easel": easel, "library": library, "cellar": cellar, "atlas": atlas,
    "pipe organ": pipes, "lectern": lectern, "observatory": observatory, "forge": forge,
    "retort": retort, "theatre": theatre, "balance": balance, "terrarium": terrarium,
    "trail chest": trail_chest, "loom": loom, "luggage": luggage,
}


def painted_view(d, subject):
    """The painter works from their window. Keep the subject larger than a pin."""
    d.rect(8,8,18,15,"V")
    d.rect(8,17,18,6,"T")
    if subject == "peaks":
        d.shape("v",(8,18),(15,11),(20,16),(23,13),(25,15),(25,20),(8,20))
        d.line("E",(13,14),(15,11),(17,14))
        d.shape("t",(8,19),(15,17),(19,19),(25,16),(25,22),(8,22))
        d.line("E",(12,22),(18,20),(17,19))
    elif subject == "windmill":
        d.shape("E",(15,20),(16,13),(19,13),(21,20))
        d.rect(17,17,2,3,"a")
        d.line("a",(13,9),(22,17))
        d.line("a",(14,17),(21,9))
        d.line("G",(13,10),(15,12))
        d.line("G",(20,9),(19,11))
        d.line("t",(8,22),(12,20),(23,21))
    elif subject == "harbor":
        d.rect(8,18,18,5,"v")
        d.shape("E",(12,16),(16,10),(16,16))
        d.shape("e",(18,12),(21,16),(18,16))
        d.shape("r",(11,17),(22,17),(19,19),(14,19))
        d.rect(14,20,6,1,"S")
    else:
        d.rect(8,17,18,6,"v")
        d.rect(8,13,18,2,"a")
        d.rect(8,13,18,1,"L")
        for x in (10,16,22):
            d.rect(x,15,2,4,"a")
            d.rect(x-1,15,4,1,"a")
        d.line("S",(13,21),(20,20))


def fixture(name, view="peaks"):
    d = Drawing(35,35)
    FIXTURES[name](d)
    if name == "easel":
        painted_view(d,view)
    c = Canvas(d.w, d.h)
    c.px = [[PIGMENT[k] if k else None for k in row] for row in d.px]
    return c

# Objects for the second, narrower place on the bench. Several trades share
# these working materials. Rows use '/' as a line break and '.' as open air.
OBJECTS = {
    "shield": "....GGG/..GGGGGGG/GGSSISSSsgg/GSSSISSSssg/GSSGISGSssg/GSGGGGGGssg/GSssGSsssdg/.GssGSssdg/..GsGSsdg/...GGGgg/.....Gb",
    "helm": ".....SS/....ISSSs/..ISSSSSss/.SSSSSSSsss/SSGGGGGGGGss/.sdddssddds/.sd..ss..ds/.d...s....d",
    "gauntlet": "...Ss.Ss.s/...Ss.Ss.ss/..SSsSSsSss/S.SSSSSSSss/SSSSSSSSSss/.SSSSSSSss/..sSSSSsss/...GGGGGg/...ssSSss",
    "whetstone": "....SSSSS/..ISssSSss/.ISsSSSSsss/SssSSSsssdds/SSsssSSssdds/.sssssSSsss/...AA...Aa/..AAAaaaAaa",
    "canvases": ".......AAAAAAA/......AEEEEEea/.AAAAAAEeeEEea/.APEEEEeeEeEea/AEPPEEEeeEeEea/APPEEEEeeEeEea/APPEEEEeeAaaaa/AEEEEEeela/AAAAAAAAaa",
    "brushes": "...R.....SS/...RR...SSs..G/....A...SS...Gg/....A...A...Aa/.....A..A...A/.....A.A...A/...SSSSSSSSss/...STTTTTTtts/....TTTTTttt/....tttttttt",
    "pigments": "...aa....gg/...SS....Ss/..SRRs..SVVs/..SRRs..SVVs/..srrs..svvs/SSSSSSSSSSSSss/.aaaaaaaAAAaa",
    "palette": ".....AAAAA/...ALLRRRAaa/..ALCCCRRRAaa/.ALVVVAATTTAa/ALVVVAAATTTAaa/AAAaaAAaAAAaal/Aaa..aARRRaaal/.aa..aACRraal/..aaaaaaaal",
    "scrolls": "...EEEE...EEEE/..EaAEE..EaAEE/..EeeEe..EeeEe/..EeeEe..EeeEe/..EeeEe..ErrEe/..EeeEe..ErrEe/.LAAAAAAAAAAAAa/.AaaaaaaAaaaaaa/.Al..EeeE...Aal",
    "folios": "...vvvvvvvvvvvv/..vPEEEEEEEEEev/..vvvvvvvvvvvvv/.rrrrrrrrrrrr/.rEEEEEEEEeer/.rrrrrrrrrrrr/...AAAAAAAAAAAA/...AEEEEEEEEEea/...aaaaaaaaaaaa",
    "ink": "....AAAA.....aa/....SSSS.....ss/...SSSSss...SSss/..VsSSSSss.SSSSss/..VVVvVsss.sSSSss/..SSSSSSss..ssss/..sssssssd",
    "mugs": "LAAAAAAAAAAAAAal/..g....g....g/..g....g....g/.SSSG.SSSG.SSSG/.SssG.SssG.SssG/.Sss..Sss..Sss/..ss...ss...ss",
    "bottles": "..AA.....aa/..Ss.....ss/..Ss.....ss/.TTTT...HHHH/TTTTTt.HHHHHh/TFTTtt.HQHHhh/TFTTtt.HQHHhh/TEEEet.HEEEeh/tttttt.hhhhhh",
    "pitcher": "....EEES/....ESTssTT/...SSTTs..T/..SSTTTs..t/.STTTTttsTt/STTTTTTtts/STTTTTTtts/.STTTTtts/..ssssss",
    "bread": ".......LLAAA/.....LALAAAAaa/..LAALAAALAAAaa/LAALAAALAAAaaaa/AAAAALAAAaaaaaa/.aaaaaaaaaaaal",
    "globe": "......gg/....GgSSSs/..GgSVVTTss/.GgSVTTTTTts/GgSVVTTVTTTs/GSVVVTVVVVVs/gSVVVVVTVVvs/g.VVVVTTTvs/.g.vvTTTvs/..gggsss/...ggGg/.....Gg/...GGGGgg",
    "compass": "...GGGGG/..GEEPEEg/.GEEERRPEg/GEEERRSEEEg/GEEESSSEEEg/GEEESssEEEg/.GEEsSEEeg/..GEEeEeg/...ggggg",
    "charts": "..EEEEEe..EE/..EPPEEe.EPEe/.ETTTEEeEEETe/.ETtEeEEEETTe/EPPEeeEeESEEe/EEVEeEEESEEEe/EVEeEEEeEEeee/EEEeeee..eee",
    "gears": "...SSS/...SsS..s/SSSSSSSSs/.SsGGGSSs/SSG...GSs/SSG...GSSS/.SsGGGsSS/SSSSSSSSs/...SsS..s/...sss",
    "gauge": "....GGGG/...GEEPEEg/..GEEPPEEEg/..GEEEESSEg/..GEEEssEEg/...GEEeEeg/....ggggg/......ss/..SSSSSSsss",
    "bellows": ".........SSs/.......aSs/.....LAaa/..LAAARrral/.AARRccRrra/ARccRRCRRAa/ARCRRRAAaal/.AAAAaaal/..Aa...al/.Aa....al",
    "oiler": ".......gGG/......s...g/..Ss.SSSTTTg/..sSSSTTTTTs/....SSTTTTts/....STTTTTts/.....tttttts",
    "quill": ".........PPP/.......PPEEe/......PEEEE/.....PEEeE/.....EEEe/....EeEe/...Eee./...ae/..g/...gg/..SSSS/.SVVVVs/.vvvvvs",
    "lens": ".....GGGGG/...GGVSSSVg/..GGVISSSVvg/..GVISSSVVvg/..GVSSSVVvvg/...GVVVVvvg/....GGGGGg/...AA/..AA/.aa",
    "crystal": "......V/.....BVV/...BVVVVv/..BVVVVBVv/V.BVVVVVVv/VV.VVVVVVv/vVv.VVVVv.V/.vVvvvvv.VV/..vvGgGgvv/...gggggg",
    "cards": "EEEEE..EEE/ERRRE.EVVE/ERCRE.EVVE/ERRRE.EVVE/EEEEE.EEEE/...EEEEE/...EEREE/...ERRRE/...EEREE/...EEEEE",
    "mirror": "....GGGG/...GVVSVg/..GVVSSVVg/..GVSSVVVg/..GVSVVVvg/...GVVVvg/....GGGg/.....Gg/.....Gg/...GGGGgg",
    "masks": "EEe...EEE.E/EEPEEEPEE.E/EqqEEEqqE.hhh/EEEeEeEEE.HqH/...ErrE.HHHHH/....Ee..HqqH/.........hh",
    "weights": "...SS......GG/..S..s....G..g/..SSss....GGgg/.ISSSss..YGGGgg/ISSSSsss.GGGGgg/SSSSSsssGGGGGggg/ssssssdsGGgggggg",
    "hourglass": "LAAAAAAAAa/.gSPPEEsg/.g.SGGs.g/.g..Ss..g/.g..gg..g/.g.SGGS.g/.gSGGGGSg/LAAAAAAAAa",
    "seedlings": "..FT.....T/..TTt..FTT/...tTTTTt/...t..t...FT/..AAa.t.FTT/.LAAAaaaTTt/.AAAAaaaaaa/.al......al",
    "bedroll": "..TTTTTTTTTTT/.TFTGTTTTTGTTt/TFftGTTTTTGTTTt/TtTtGTTTTTGTTtt/TtttGTTTTTGTTtt/.tttGtttttGttt",
    "yarn": "....A.....A/.....A...A/...HHQHAH/.HHQHQQHhh/HQHQQHHQHhh/HQQHHQHHHhh/.HHQHHQHhh/...hhhhhh",
    "boots": ".aaaa....aaa/.Alll....All/.Alll....All/.Aaal....Aal/.Aaaal...Aaal/AAAaaaalAAAaaal/lllllll.lllllll",
    "candle": "......G/.....YYR/......r/....PEEE/....EPEe/....EPEe/....EEEe..GG/....EEEe.G.g/..YGGGGGGggg/...ggggggg",
}


def accessory(name):
    return tile(OBJECTS[name].replace("/", "\n"))
