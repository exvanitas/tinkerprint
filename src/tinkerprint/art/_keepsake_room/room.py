"""The 252 by 72 workshop fitted around Keepsake Half's existing portrait registration."""
from dataclasses import dataclass
from hashlib import sha256

from .._anime import _render
from .._anime.traits import _pick, keepsake_traits
from .._drawing import Drawing
from ..compose import banner_figure_box, shelf_counts
from ..pixels import mix
from . import companions, furniture, tokens

# Each choice has its own rendezvous axis. These fixtures persist when the
# occupant changes trade, including a move between the two guilds.
TOUCHES = {
    "view": ("harbor", "viaduct", "windmill", "peaks"),
    "light": ("amber dawn", "blue hour", "rose dusk", "overcast"),
    "drapery": ("swag", "linen", "bare", "valance"),
    "finish": ("plaster", "stone", "paneling"),
    "plant": ("fern", "bells", "succulent", "ivy"),
    "pot": ("celadon", "rose", "indigo"),
    "sill": ("near", "far"),
    "weave": ("diamonds", "stripes", "steps"),
    "wool": ("teal", "madder", "heather"),
    "hanging": ("herbs", "keys", "lamp", "bells"),
    "arrangement": ("left", "right"),
}
# Sky, horizon, two landscape planes, water/light, sun or moon.
LIGHT = {
    "amber dawn": ("#b29085","#e5bc91","#ac9793","#797b83","#d9b59a","#f1d8ac"),
    "blue hour": ("#36465e","#778397","#64718a","#454e66","#8f9aaa","#ddddd0"),
    "rose dusk": ("#896f81","#c89a93","#a38792","#736d82","#c49b9f","#f0c4a0"),
    "overcast": ("#859a9e","#bcc6b8","#91a5a2","#697e84","#acbcb2","#e2dcc3"),
}
CASE = {"line":"#473b4b", "deep":"#5c4852", "shade":"#765653", "wood":"#a47562",
        "edge":"#c69a79", "warm":"#d4ab83", "brass":"#bd9568"}


@dataclass(frozen=True)
class RoomPlan:
    touches: tuple
    fixture: str
    object: str
    stock: tuple


# Six columns on three rails. Ten pixels of drawing fit each eleven-pixel bay.
CUBBIES = tuple((183+11*col, bottom) for bottom in (17,31,45) for col in range(6))


def family(pack, look, stat):
    if look.kind in ("specialist", "pair"):
        return pack["looks"][stat]["trinket"]
    if look.kind == "generalist":
        return {"builder":"trail", "tinkerer":"wander"}[look.set_name]
    return "arrival"


def plan_room(pack, look, stats, seed):
    if not isinstance(seed, str):
        raise TypeError("seed must be a string")
    touches = tuple((k, _pick(seed, "room/"+k, options)) for k,options in TOUCHES.items())
    primary = family(pack, look, look.top)
    tray = family(pack, look, look.item) if look.kind == "pair" else primary
    fixture = furniture.FURNISHINGS[primary][0]
    obj = _pick(seed, "room/tray", furniture.FURNISHINGS[tray][1])
    # One ranking for the cubbies. The count and identity of the stock come
    # exclusively from the shipped share allocator, including its 18-slot cap.
    order = sorted(CUBBIES, key=lambda cell: _slot_score(seed, cell))
    stock = [s for s,n in shelf_counts(stats) for _ in range(n)]
    return RoomPlan(touches, fixture, obj, tuple(zip(stock, order)))


def _slot_score(seed, cell):
    x, y = cell
    return sha256(f"{seed}|room/cubby|{x},{y}".encode()).digest(), cell


def window(d, t, wisp=0):
    sky, haze, far, near, glint, sun = LIGHT[t["light"]]
    d.rect(62,2,117,45,sky)
    d.rect(62,25,117,20,haze)
    # Two long planes leave still air directly behind the face. Each landmark
    # sits in a side light where it remains visible beside the hair and hat.
    d.shape(far,(62,25),(71,21),(80,22),(89,18),(100,24),(117,27),(131,24),
            (144,21),(154,24),(168,18),(178,23),(178,45),(62,45))
    d.shape(near,(62,32),(77,29),(88,33),(104,31),(119,35),(137,32),(150,30),
            (161,32),(178,27),(178,45),(62,45))
    d.rect(62,36,117,9,glint)
    d.line(far,(69,38),(78,38),(81,39))
    d.line(far,(147,40),(157,40))
    d.line(haze,(134,42),(143,42))
    sun_x = 84 if t["view"] in ("windmill", "harbor") else 151
    furniture.disk(d,sun_x,12,4,sun)
    if t["light"] == "blue hour":
        furniture.disk(d,sun_x+2,10,4,sky)
        for x,y in ((75,13),(86,9),(163,17),(140,7)):
            d.set(x,y,haze)
    else:
        for x,y,w in ((78,14,9),(82,13,4),(158,10,9),(162,9,3)):
            d.rect(x,y,w,1,haze)
    if wisp:
        # A narrow bank of haze drifts across the disc. Feather its ends
        # and dissolve it into the existing sky at both ends of the loop.
        left = sun_x-11+wisp
        strength = min(wisp, 16-wisp, 4) / 6
        for y, start, end in ((11, 2, 7), (12, 0, 10)):
            for dx in range(start, end):
                x = left+dx
                alpha = strength * min(dx-start+1, end-dx, 3) / 3
                d.set(x, y, mix(d.get(x,y), haze, alpha))
    view = t["view"]
    if view == "harbor":
        d.shape(near,(141,35),(147,32),(156,31),(164,33),(175,34),(175,36),(141,36))
        d.shape(haze,(153,31),(154,20),(157,20),(158,31))
        d.rect(154,23,4,2,near)
        d.rect(153,19,6,2,near)
        d.set(155,18,near)
        d.shape(haze,(78,33),(83,25),(83,33))
        d.line(near,(76,34),(86,34),(84,35),(79,35))
    elif view == "viaduct":
        for x in range(134,176,9):
            d.rect(x,26,2,9,near)
            d.rect(x-1,27,4,2,near)
            d.rect(x-2,27,6,1,near)
        d.rect(130,24,46,3,near)
        d.rect(130,24,46,1,glint)
        d.shape(far,(62,30),(73,26),(81,26),(92,30),(87,33),(62,34))
    elif view == "windmill":
        d.shape(haze,(151,32),(153,21),(158,21),(161,32))
        d.shape(near,(151,22),(155,17),(160,22))
        d.rect(155,28,2,4,near)
        for dx,dy in ((-6,-5),(5,-6),(6,5),(-5,6)):
            d.line(near,(155,21),(155+dx,21+dy))
            # Broad sail tips, with a pixel of sky between each blade.
            ox,oy = (1 if dy < 0 else -1), (1 if dx > 0 else -1)
            d.line(glint,(155+dx+ox,21+dy+oy),(155+dx//2+ox,21+dy//2+oy))
        d.set(155,21,near)
        for x in (69,76,80,86):
            d.shape(near,(x-2,29),(x,22-x%4),(x+2,29))
    else:
        for x,y,w in ((79,16,14),(150,15,13),(164,10,17)):
            d.shape(far,(x-w,y+15),(x,y),(x+w,y+14))
            d.shape(haze,(x-6,y+6),(x,y),(x+5,y+5),(x+1,y+3),(x-1,y+5),(x-2,y+4))
        for x in (68,74,145,153,163,170):
            d.shape(near,(x-3,36),(x,25+x%4),(x+3,36))


def drapery(d, set_name, t):
    # A short stretch of colored cloth alters the west bay's silhouette. The
    # timber and the free edge of the cloth end well before the portrait.
    lit, fold, dark = (("#899e9a","#647d80","#4c626c") if set_name == "builder"
                       else ("#c79485","#a57575","#785967"))
    kind = t["drapery"]
    if kind == "swag":
        d.shape(dark,(0,3),(53,3),(48,7),(38,10),(25,10),(15,8),(9,19),(3,26),(0,27))
        d.shape(fold,(0,3),(51,3),(43,7),(31,9),(18,7),(11,6),(7,17),(2,22),(0,23))
        d.line(lit,(5,15),(10,5),(16,5),(24,7),(35,8),(45,5))
        d.line(lit,(1,18),(5,13),(8,6))
        d.rect(1,21,4,2,CASE["brass"])
    elif kind == "linen":
        x = 18 if t["arrangement"] == "left" else 41
        d.shape(dark,(x,5),(x+15,5),(x+15,27),(x+8,32),(x,27))
        d.shape(fold,(x,5),(x+13,5),(x+13,26),(x+8,30),(x,26))
        d.line(lit,(x+2,7),(x+2,25),(x+8,29),(x+12,26))
        d.line(lit,(x+5,12),(x+8,8),(x+11,12),(x+8,16),(x+5,12))
        d.rect(x-3,4,22,2,CASE["brass"])
    elif kind == "valance":
        for x in range(4,59,11):
            d.shape(dark,(x,4),(x+10,4),(x+10,9),(x+5,14),(x,10))
            d.shape(fold,(x,4),(x+9,4),(x+9,9),(x+5,12),(x,9))
            d.line(lit,(x,8),(x+5,11),(x+8,9))
        d.rect(3,4,57,2,CASE["brass"])


def architecture(d, pack, look, t, wisp=0):
    c = CASE
    base = pack["sets"][look.set_name]["wall2"]
    wall = mix(base, "#9c8b8b", .5 if t["finish"] == "plaster" else .32)
    joint = mix(wall,c["deep"],.37)
    d.rect(0,0,252,72,wall)
    # The east return continues behind the display case. The portrait sees
    # its finish when it faces the windmill or viaduct bay.
    for left, width in ((0, 74), (181, 60)):
        if t["finish"] == "stone":
            for row in range(5):
                y = 8+9*row
                d.rect(left,y,width,1,joint)
                for x in range(6+11*(row%2), width, 22):
                    d.rect(left+x,y+1,1,8,joint)
        if t["finish"] == "paneling":
            for x in range(5,width,13):
                d.rect(left+x,4,1,45,joint)
                d.rect(left+x+1,4,1,44,mix(wall,"#e5d4bd",.09))
    drapery(d, look.set_name, t)
    window(d,t,wisp)
    # Segmental arch in two thicknesses, with pegs and chipped joints.
    for x,flip in ((62,1),(178,-1)):
        p = lambda dx, y: (x+dx*flip, y)
        d.shape(c["deep"],p(-3,0),p(28,0),p(19,4),p(11,8),p(6,14),p(3,21),
                p(3,46),p(-3,46))
        d.line(c["edge"],p(18,3),p(9,7),p(4,13),p(1,21),p(1,45))
        d.line(c["wood"],p(6,4),p(8,7))
        d.line(c["wood"],p(-1,13),p(3,15))
        d.rect(*p(0,29),1,15,c["shade"])
    # Mortised corner brace and projecting beam. The lower lip catches the
    # window light above a shadow band that separates it from the plaster.
    d.shape(c["shade"],(0,0),(23,0),(17,4),(8,7),(4,13),(2,24),(0,25))
    d.line(c["wood"],(1,21),(3,12),(7,7),(17,3))
    d.rect(0,0,252,3,c["deep"])
    d.rect(1,2,60,1,c["wood"])
    d.rect(4,3,51,2,c["shade"])
    for x in (5,21,48,56):
        d.set(x,3,c["edge"])
    d.rect(62,45,117,4,c["deep"])
    d.rect(61,45,119,1,c["edge"])
    d.rect(64,46,114,1,c["wood"])
    d.rect(0,53,252,19,c["shade"])
    d.rect(0,53,252,2,c["deep"])
    for y in (61,68):
        d.rect(0,y,252,1,c["deep"])
        for x in range(13+y%11,252,43):
            d.line(c["deep"],(x,y-6),(x-3,y-1))


def workbench(d):
    c = CASE
    # A drawer workbench underneath the trade's vignette.
    d.shape(c["deep"],(2,48),(6,45),(71,45),(76,48),(76,51),(2,51))
    d.rect(3,48,72,1,c["edge"])
    d.rect(5,49,68,2,c["wood"])
    d.line(c["wood"],(16,58),(27,58),(30,57))
    d.line(c["wood"],(152,63),(165,63),(168,62))
    d.shape(c["deep"],(5,60),(67,59),(72,61),(12,63))
    for x in (7,66):
        d.rect(x,51,4,11,c["deep"])
        d.rect(x,51,1,10,c["wood"])
    d.rect(10,51,57,6,c["shade"])
    for x in (11,38):
        d.rect(x,51,26,4,c["wood"])
        d.rect(x+10,52,6,2,c["deep"])
        d.rect(x+11,52,4,1,c["brass"])


def carpet(d, t):
    hi, field, shade = {"teal":("#a5b5a4","#698785","#4b6164"),
                        "madder":("#ce9b84","#a16a70","#735763"),
                        "heather":("#c5a9ae","#918094","#685f77")}[t["wool"]]
    d.shape(shade,(9,62),(63,62),(75,69),(73,70),(2,70),(2,68))
    d.shape(field,(10,63),(62,63),(71,68),(4,68))
    for x in range(4,73,4):
        d.rect(x,70,2,1,hi)
    d.rect(9,64,55,1,hi)
    d.rect(5,68,66,1,hi)
    for x in range(12,63,9):
        if t["weave"] == "diamonds":
            d.line(hi,(x,66),(x+2,65),(x+4,66),(x+2,67),(x,66))
        elif t["weave"] == "steps":
            d.line(hi,(x,67),(x+2,67),(x+2,66),(x+4,66),(x+4,65))
        else:
            d.line(hi,(x,67),(x+4,65))


PLANTS = {
    "fern": ".....F.....T/F....TT...TT/.FT...T..Tt...F/..TT..T..t..TT/...tt..t.t.Tt/.....t.tttt/..TTtt..t..TT/.......tt",
    "bells": "...HH.....HH/...QH..F..QH/....t..T..t/..HH.t.T.t/..QH.t.t.t/....t.ttt/.....ttt/......tt",
    "succulent": "......T..TT/...TT.TT.Tt/....TtTtTt..T/.FT..tTtt.FT/..TT.ttt.Tt/...tt.tttt/.....tttt",
    "ivy": "..TT..FT/..Tt.ttT..FT/...t.tt..TT/....ttt.tt/.....tttt/.Ttttttt/Tt....tt/t",
}


def plant(d,t, bend=0):
    x = 152 if t["sill"] == "near" else 163
    glaze = {"celadon":"FTtf","rose":"CRrc","indigo":"BVvn"}[t["pot"]]
    foliage = PLANTS[t["plant"]].split("/")
    pot = [" "+glaze[0]+glaze[1]*5+glaze[2], "  "+glaze[1]*4+glaze[2]*2,
           "  "+glaze[1]*4+glaze[2]*2, "   "+glaze[2]*4]
    for i, row in enumerate(foliage):
        offset = round(bend * (1-i/(len(foliage)-1))**2)
        d.stamp([row],furniture.PIGMENT,x-3+offset,41-len(foliage)+i)
    d.stamp(pot,furniture.PIGMENT,x,45-len(pot))


def cabinet(d):
    c = CASE
    d.rect(180,2,71,68,c["line"])
    d.rect(181,3,69,45,c["shade"])
    for x,bottom in CUBBIES:
        d.rect(x-1,bottom-11,11,11,c["deep"])
        d.rect(x,bottom-10,10,10,"#67555d")
        d.rect(x-1,bottom,11,2,c["wood"])
        d.rect(x-1,bottom,11,1,c["edge"])
    d.rect(179,2,73,3,c["wood"])
    d.rect(180,2,71,1,c["edge"])
    # Below the stock, an open, felt-lined display case and projecting ledge.
    d.rect(182,49,67,18,"#494753")
    d.rect(184,51,63,16,"#58545d")
    d.rect(180,67,71,3,c["wood"])
    d.rect(179,67,73,1,c["edge"])


HANGINGS = {
    "herbs": "....g/...gg/..tttT/..tTTT/.tTtTFT/ttt.TTT/tt...Tt",
    "lamp": "....g/...GgG/..GgggG/..AEEeg/..EPEeg/..EYEeg/..EEeeg/...Ggg/....g",
    "keys": "...GG/...gG/..Gg.Gg/..g...g/..g...g/..gg..g/..g...gg",
    "bells": "....g/...g.g/..g...g/..G...G/.SGs..G/SGGgs.G/..g..SGs/....SGGgs/......g",
}


def furnish_bench(d, pack, look, plan, ember=0):
    t = dict(plan.touches)
    hero, prop = furniture.fixture(plan.fixture,t["view"]), furniture.accessory(plan.object)
    hx, cx = (5,56) if t["arrangement"] == "left" else (38,18)
    # Suspend a single personal keepsake over the smaller object. Its hook
    # follows the bench layout, so it clears even the tallest trade fixture.
    hook = cx-1
    d.line(CASE["shade"],(hook,3),(hook,9))
    d.stamp(HANGINGS[t["hanging"]].split("/"),furniture.PIGMENT,hook-4,9)
    if t["hanging"] == "lamp" and ember:
        rows = ("YE", "PG", "YE") if ember == 1 else ("EP", "YY", "GE")
        d.stamp(rows, furniture.PIGMENT, hook-1, 12)
    # A short cloth hangs over the workbench lip below the borrowed equipment.
    # Its hem clears the owner's rug. Dye follows the runner-up even where two
    # trades share an object, such as a scroll or an oil can.
    trade = look.item if look.kind == "pair" else look.top if look.kind == "specialist" else None
    dye = pack["stat_colors"].get(trade, pack["wanderer_colors"])
    cloth = [mix(color,CASE["shade"],.36) for color in dye]
    d.shape(cloth[3],(cx-9,47),(cx+8,47),(cx+7,57),(cx+3,59),(cx-9,57))
    d.shape(cloth[1],(cx-9,47),(cx+6,47),(cx+5,56),(cx+2,57),(cx-9,55))
    d.rect(cx-9,47,16,1,cloth[0])
    d.line(cloth[2],(cx-6,49),(cx-6,54),(cx+3,56))
    d.line(cloth[0],(cx-8,54),(cx+2,56),(cx+5,55))
    d.paste(hero,hx,47-hero.h)
    d.paste(prop,cx-prop.w//2,47-prop.h)


def backdrop(pack, look, plan, motion=None):
    t = dict(plan.touches)
    d = Drawing(252,72)
    architecture(d,pack,look,t,motion.wisp if motion else 0)
    workbench(d)
    carpet(d,t)
    plant(d,t,motion.bend if motion else 0)
    furnish_bench(d,pack,look,plan,motion.ember if motion else 0)
    cabinet(d)
    cache = {}
    for stat,(x,bottom) in plan.stock:
        if stat not in cache:
            cache[stat] = tokens.trinket(pack,stat)
        item = cache[stat]
        d.paste(item,x+(10-item.w)//2,bottom-item.h)
    return d


def counter(room, box):
    """A wooden service counter in front of the figure, in the workshop's pixel grid."""
    x, y = box
    oak = Drawing(room.w, room.h)
    left, right, lip = x-20, x+49, y+45
    oak.shape("#493446", (left+5, lip), (right-5, lip), (right, lip+4),
              (right, room.h-1), (left, room.h-1), (left, lip+4))
    oak.shape("#b87a56", (left+5, lip+1), (right-5, lip+1), (right-2, lip+3), (left+2, lip+3))
    oak.rect(left+1, lip+4, right-left-1, 1, "#e9ba85")
    oak.rect(left+2, lip+6, right-left-3, 6, "#925f52")
    for dx in (4, 36):
        oak.rect(left+dx, lip+6, 29, 5, "#70505a")
        oak.rect(left+dx+1, lip+6, 27, 1, "#b87a56")
        oak.rect(left+dx+11, lip+7, 7, 2, "#493446")
        oak.rect(left+dx+12, lip+7, 5, 1, "#e9ba85")
    # A folded work order sits on the lit end of the top, clear of the hands.
    oak.shape("#70505a", (left+8, lip), (left+20, lip-1), (left+24, lip+2), (left+12, lip+3))
    oak.shape("#f6dba5", (left+8, lip-1), (left+19, lip-2), (left+23, lip+1), (left+12, lip+2))
    oak.line("#b87a56", (left+12, lip), (left+17, lip-1))
    oak.rect(left+18, lip, 3, 2, "#913e50")
    room.paste(oak, 0, 0)


def furnished_room(pack, look, plan, berths, motion=None):
    """Draw the trade fixtures, stock and occupied berths behind the portrait."""
    d = backdrop(pack, look, plan, motion)
    player = next((h for h in companions.CLOCKWORK if h in berths), berths[0] if berths else None)
    for i,h in enumerate(berths):
        member = companions.member(h, motion.gear if motion and h == player else 0)
        d.paste(member,193+21*i-member.w//2,67-member.h)
    return d


def portrait_options(seed, look, presentation, expression, hair, eyes):
    options = {} if seed is None else keepsake_traits(seed, look, presentation)
    for name, value in (("expression", expression), ("hair", hair), ("eyes", eyes)):
        if value is not None:
            options[name] = value
    return options


def banner(pack, look, stats, harnesses=(), seed=None, *, presentation="neutral", skin=None,
           expression=None, hair=None, eyes=None, figure_look=None, motion=None):
    """Draw the furnished room for look, optionally dressing its occupant in figure_look."""
    plan = plan_room(pack, look, stats, "" if seed is None else seed)
    d = furnished_room(pack, look, plan, companions.berths(harnesses), motion)
    look = figure_look or look
    traits = portrait_options(seed, look, presentation, expression, hair, eyes)
    fig = _render(pack,look,skin,presentation,motion=motion,**traits)
    x,y = banner_figure_box(pack,fig)
    d.paste(fig,x,y)
    counter(d,(x+16,y+10))
    front = _render(pack,look,skin,presentation,foreground_only=True,motion=motion,**traits)
    d.paste(front,x,y)
    return d
