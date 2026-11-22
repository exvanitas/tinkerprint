"""Overnight quarters at the foot of the builder ridge or beside the tinkerer lake."""
from .._anime.traits import _pick
from .._drawing import Drawing
from ..pixels import mix
from .furniture import disk


def night(d, site, ridge, moon_x, high_pass):
    # Keep the warmest value for the hearth. The sky reflects in a quiet strip
    # of water between two land masses, with the moon's glint directly below it.
    sky = mix(site["plate"], "#171b38", .48)
    haze = mix(sky, "#a490a0", .39)
    far = mix(haze, site["wall2"], .52)
    near = mix(site["plate"], "#34364e", .34)
    water = mix(haze, "#aca5ae", .32)
    moon = "#e5cfaf" if ridge else "#e9c2aa"
    d.rect(0, 0, 64, 64, sky)
    d.rect(0, 19, 64, 10, mix(sky, haze, .56))
    d.rect(0, 25, 64, 9, haze)
    disk(d, moon_x, 8, 4, moon)
    if ridge:
        disk(d, moon_x+2, 6, 4, sky)
    else:
        d.line("#d6b0a4", (moon_x+1,10), (moon_x+3,9))
    for x, y in ((5,8), (15,4), (26,13), (34,5), (45,9), (57,4), (61,15)):
        if abs(x-moon_x) > 6:
            d.set(x, y, water)
    d.line(haze, (2,17), (10,17), (12,16), (18,16))
    d.line(haze, (42,19), (48,19), (50,18), (57,18))
    peak = 15 if high_pass else 42
    if ridge:
        d.shape(far, (0,28),(9,21),(peak-8,24),(peak,14),(peak+8,23),
                (53,18),(63,22),(63,36),(0,36))
        d.line(water,(peak-5,20),(peak,14),(peak+3,18),(peak+1,17),(peak-1,19))
        d.shape(near, (0,28),(9,25),(18,27),(27,26),(43,31),(55,23),
                (63,23),(63,37),(0,37))
        # A small masonry viaduct in silhouette in the saddle.
        d.rect(19,26,27,2,far)
        d.rect(19,25,27,1,haze)
        for x in (21,28,35,42):
            d.rect(x,27,2,6,far)
            d.rect(x-1,27,4,2,far)
    else:
        d.shape(far,(0,22),(9,19),(19,22),(28,19),(38,22),(49,18),
                (58,19),(63,17),(63,34),(0,34))
        d.shape(near,(0,27),(13,23),(24,26),(36,25),(46,28),(56,24),
                (63,23),(63,35),(0,35))
        # Sails break the far bank's contour against the plum sky.
        mill = peak-4 if high_pass else peak+8
        d.shape(far,(mill-2,23),(mill,17),(mill+2,17),(mill+3,23))
        for dx,dy in ((-4,-2),(2,-4),(4,2),(-2,4)):
            d.line(haze,(mill+1,17),(mill+1+dx,17+dy))
    d.rect(0,32,64,5,water)
    d.rect(0,32,64,1,far)
    d.line(moon,(moon_x-3,33),(moon_x+2,33))
    d.line(haze,(moon_x-5,35),(moon_x-1,35))
    d.line(far,(45,34),(54,34))


def bedroll(d, cloth):
    lit, field, shade, edge = cloth
    # Unrolled wool in perspective. The rolled head shows the wound end.
    d.shape(edge,(11,44),(25,45),(25,49),(21,60),(18,62),(3,59),(3,56))
    d.shape(field,(12,45),(24,46),(19,60),(5,57))
    d.shape(shade,(20,46),(24,46),(19,60),(16,59))
    d.line(lit,(11,47),(7,55),(5,57))
    d.line(lit,(7,54),(19,56))
    d.line(edge,(6,56),(18,58))
    d.line(lit,(5,58),(17,60))
    d.shape(edge,(10,42),(13,40),(26,42),(28,44),(27,47),(24,49),
            (11,47),(9,45))
    d.shape(field,(11,42),(14,41),(25,43),(23,47),(12,46),(10,44))
    d.line(lit,(12,42),(15,42),(22,43))
    d.line(shade,(11,45),(20,46))
    d.shape(shade,(23,44),(25,43),(27,44),(26,47),(24,48),(22,46))
    d.line(lit,(23,46),(24,44),(26,44),(26,45),(25,46))


def knapsack():
    d = Drawing(22, 18)
    # Handle, overhanging flap, brass buckle, side pocket and cast shadow.
    d.line("#423646",(9,5),(10,2),(14,1),(16,3),(16,5))
    d.line("#d3a27c",(10,4),(11,2),(14,2))
    d.shape("#443542",(6,6),(9,3),(17,3),(20,6),(20,13),(18,16),
            (7,16),(4,14))
    d.shape("#a36d59",(7,7),(17,6),(18,13),(16,15),(7,14))
    d.shape("#77515a",(16,5),(19,6),(19,13),(17,15),(15,14))
    d.shape("#5b414b",(5,6),(8,3),(16,3),(19,5),(18,8),(11,10),(6,9))
    d.shape("#bd8361",(6,6),(9,4),(16,4),(18,5),(16,7),(10,9),(6,8))
    d.line("#e4b88a",(7,6),(10,4),(15,4))
    d.rect(10,8,3,5,"#68474b")
    d.rect(10,9,3,2,"#edc989")
    d.set(11,10,"#845953")
    d.line("#d59a72",(6,12),(8,13),(9,13))
    d.rect(16,11,4,3,"#614551")
    d.line("#d0956c",(16,11),(19,11))
    return d


# Three silhouettes registered to the same glowing bed of coals. The winding
# outer tongue and its pale core move together, leaving the log ends planted.
FLAMES = (
    (".......r....", "......rf....", "......ff....", ".....ffr....",
     "..r..ffr..r.", "..frfffr.rr.", "..ffffgf.ff.", ".rffgggfff..",
     ".ffggwggff..", ".rfggwwggf..", "..rfggwgfr..", "...rrfffr..."),
    ("........r...", ".......rr...", "......rf....", ".....rff....",
     "...r.ffr....", "...ffffr..r.", "..rffggf.rf.", "..ffgggfff..",
     ".rffgwggff..", ".ffggwwggf..", "..rfggwgfr..", "...rrfffr..."),
    ("............", ".....r......", ".....fr.....", ".....ffr....",
     "..r..rff....", "..fr.rff..r.", "..ffffgfrff.", ".rffggggff..",
     ".ffggwgggfr.", ".rfggwwggf..", "..rfggwgfr..", "...rrfffr..."),
)


def hearth(d, x, phase):
    # A ring of flat stones has a dark interior, with two split logs above it.
    d.shape("#483c49",(x-12,51),(x-7,48),(x+6,48),(x+12,51),(x+12,54),
            (x+5,57),(x-7,56),(x-13,53))
    for dx,dy in ((-11,51),(-7,49),(5,49),(9,51),(7,54),(-9,54),(-2,55)):
        d.shape("#897a7a",(x+dx-1,dy),(x+dx+2,dy-1),(x+dx+4,dy),
                (x+dx+3,dy+2),(x+dx,dy+2))
        d.line("#cba58c",(x+dx,dy),(x+dx+2,dy-1))
    d.shape("#654349",(x-8,49),(x-6,47),(x+8,51),(x+9,53),(x+6,54),(x-8,51))
    d.line("#cc8260",(x-6,48),(x+6,52))
    d.shape("#71494a",(x-7,52),(x+6,47),(x+8,48),(x+7,50),(x-6,55),(x-8,54))
    d.line("#dfa071",(x-7,52),(x+5,48))
    d.line("#edbb81",(x-7,53),(x-6,54))
    d.stamp(FLAMES[phase], dict(r="#be5650", f="#ee8453", g="#ffc66d", w="#fff1ae"), x-6,39)


def campsite(pack, set_name, seed):
    """Paint the still night landscape, bedding and pack. Return its hearth's x position."""
    if not isinstance(seed, str):
        raise TypeError("seed must be a string")
    site = pack["sets"][set_name]
    moon_x = _pick(seed, "camp/moon", (13, 32, 51))
    high_pass = _pick(seed, "camp/pass", ("west","east")) == "west"
    x = _pick(seed, "camp/hearth", (41, 47, 49))
    cloth = _pick(seed, "camp/wool", ("teal", "rose", "heather"))
    wool = {"teal": ("#b8c9b0","#6e9890","#54757a","#3c505e"),
            "rose": ("#e4b899","#b78077","#8e6066","#5e4856"),
            "heather": ("#d0bbcc","#a38ba7","#756883","#514b64")}
    d = Drawing(64,64)
    night(d, site, site["scene"] == "ridge", moon_x, high_pass)
    soil = mix(site["floor"], "#816362", .59)
    d.shape(soil,(0,35),(7,34),(16,36),(24,35),(35,37),(48,36),(62,33),
            (63,33),(63,63),(0,63))
    # The pale pool of firelight fades into the cool bank in two broad planes.
    d.shape(mix(soil,"#b37a65",.34),(x-15,45),(x+1,43),(x+13,46),
            (min(63,x+17),53),(x+13,58),(x-4,60),(x-17,55),(x-21,49))
    d.shape(mix(soil,"#d59468",.48),(x-13,49),(x-4,46),(x+8,47),(x+14,52),
            (x+9,56),(x-4,58),(x-14,54))
    # Windswept grass traces the waterline. Small rocks catch a cool edge
    # at the far side of the bed, leaving the ochre firelight uninterrupted.
    bank = mix(soil, site["plate"], .55)
    for xx, yy in ((2,36), (56,36), (61,35)):
        d.line(bank,(xx-2,yy-2),(xx,yy),(xx+1,yy-4))
        d.line(bank,(xx,yy),(xx+3,yy-2))
    d.line(bank,(3,38),(9,38),(11,37))
    d.line(bank,(25,44),(29,45),(34,44))
    d.shape(bank,(29,58),(32,57),(35,59),(34,60),(29,60))
    d.line(mix(soil, "#e2b297", .38),(29,58),(32,57))
    d.line(site["plate"],(4,47),(8,48),(16,48))
    d.line(site["plate"],(4,59),(17,62),(21,61))
    d.paste(knapsack(), 14, 28)
    bedroll(d, wool[cloth])
    return d, x
