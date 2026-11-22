"""Native workshop clearances, stable furnishing and verified portrait and cabinet pixels."""
from collections import Counter
from itertools import product
import unittest
from unittest.mock import patch

from keepsake_helpers import MODES, SKINS, cast
from tinkerprint import art
from tinkerprint.art import keepsake
from tinkerprint.art._anime.traits import EYE_RAMPS, EXPRESSIONS
from tinkerprint.art._drawing import Drawing
from tinkerprint.art._keepsake_room import companions, furniture, room, tokens
from tinkerprint.sets import PAIR


def crop(c, x, y, w, h):
    return [r[x:x+w] for r in c.px[y:y+h]]


def occupied(c):
    return {(x,y) for y,row in enumerate(c.px) for x,p in enumerate(row) if p is not None}


def luminance(color):
    rgb = [int(color[i:i+2],16)/255 for i in (1,3,5)]
    linear = [v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4 for v in rgb]
    return sum(a*b for a,b in zip(linear,(.2126,.7152,.0722)))


class RoomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack = art.default_pack()
        cls.looks = cast()

    def test_same_seed_rebuilds_and_seed_sample_changes_the_room_without_the_actor(self):
        look = self.looks["Painter"]
        stats = [("Art",70),("Lore",30)]
        images, stock, objects = set(), set(), set()
        for i in range(40):
            seed = f"tile|{i}"
            plan = room.plan_room(self.pack,look,stats,seed)
            images.add(room.backdrop(self.pack,look,plan).png(indexed=True))
            stock.add(plan.stock)
            objects.add(plan.object)
            self.assertEqual(plan,room.plan_room(self.pack,look,stats,seed))
        self.assertEqual((len(images),len(stock),len(objects)),(40,40,4))
        args = self.pack, look, stats, ("codex","agy"), "🧵"
        self.assertEqual(room.banner(*args).png(),room.banner(*args).png())
        with self.assertRaises(TypeError):
            room.plan_room(self.pack, look, [], 1)

    def test_personal_window_sill_and_rug_survive_every_class_and_set(self):
        for seed in ("north-pier",""):
            reference = self.looks["Warden"]
            base = room.plan_room(self.pack,reference,[],seed)
            original = room.backdrop(self.pack,reference,base)
            fixtures = set()
            for look in self.looks.values():
                plan = room.plan_room(self.pack,look,[],seed)
                self.assertEqual(plan.touches,base.touches)
                fixtures.add(plan.fixture)
                scene = room.backdrop(self.pack,look,plan)
                for region in ((76,4,101,44),(2,63,74,8)):
                    self.assertEqual(crop(original,*region),crop(scene,*region))
            self.assertEqual(len(fixtures),16)

    def test_pairs_in_both_orders_borrow_the_second_trades_pool_and_dye(self):
        for guild,pairs in PAIR.items():
            for a,b in pairs:
                for primary,second in ((a,b),(b,a)):
                    look = art.Look(guild,"pair",primary,second)
                    seed = "workshop"
                    pair = room.plan_room(self.pack,look,[],seed)
                    first = room.plan_room(self.pack,art.Look(guild,"specialist",primary,primary),[],seed)
                    other = room.plan_room(self.pack,art.Look(guild,"specialist",second,second),[],seed)
                    self.assertEqual(pair.fixture,first.fixture)
                    self.assertEqual(pair.object,other.object)
                    fixture = Drawing(252,72)
                    room.furnish_bench(fixture,self.pack,look,pair)
                    self.assertIn(room.mix(self.pack["stat_colors"][second][0],room.CASE["shade"],.36),
                                  fixture.colors())

    def test_growth_only_moves_new_object_or_eye_winners(self):
        look = self.looks["Painter"]
        pack = self.pack
        fixture,pool = furniture.FURNISHINGS["paints"]
        seeds = [str(i) for i in range(1200)]
        old = [room.plan_room(pack,look,[],s) for s in seeds]
        traits = [keepsake.traits(s,look) for s in seeds]
        with patch.dict(furniture.FURNISHINGS, paints=(fixture,(*pool,"new"))), \
             patch.dict(EYE_RAMPS, new=EYE_RAMPS["honey"]):
            moved_eye = moved_prop = 0
            for seed,previous,known in zip(seeds,old,traits):
                new = room.plan_room(pack,look,[],seed)
                got = keepsake.traits(seed,look)
                self.assertEqual(new.touches,previous.touches)
                self.assertEqual(new.fixture,previous.fixture)
                if new.object != previous.object:
                    self.assertEqual(new.object,"new")
                    moved_prop += 1
                self.assertEqual(got["hair"],known["hair"])
                self.assertEqual(got["expression"],known["expression"])
                if got["eyes"] != known["eyes"]:
                    self.assertEqual(got["eyes"],"new")
                    moved_eye += 1
            self.assertAlmostEqual(moved_eye/len(seeds),1/7,delta=.03)
            self.assertAlmostEqual(moved_prop/len(seeds),1/5,delta=.03)

    def test_furniture_and_hangings_clear_figure_counter_stock_and_party(self):
        # Exercise every accent in either bench position. The full portrait
        # box is a stricter reservation than any one hat or outstretched hand.
        desk = Drawing(252,72)
        bx,by = art.banner_figure_box(self.pack,keepsake.figure(self.pack,self.looks["Warden"]))
        room.counter(desk,(bx+16,by+10))
        allowed = {(x,y) for x in range(78) for y in range(61)} - occupied(desk)
        allowed -= {(x,y) for x in range(bx,bx+64) for y in range(by,by+64)}
        for look in self.looks.values():
            plan = room.plan_room(self.pack,look,[],"frame")
            tray = furniture.FURNISHINGS[room.family(self.pack,look,look.top)][1]
            for i,(side,obj) in enumerate(product(("left","right"),tray)):
                touch = dict(plan.touches,arrangement=side,hanging=room.TOUCHES["hanging"][i%4])
                arranged = room.RoomPlan(tuple(touch.items()),plan.fixture,obj,())
                layer = Drawing(252,72)
                room.furnish_bench(layer,self.pack,look,arranged)
                points = occupied(layer)
                self.assertGreater(len(points),120)
                self.assertLessEqual(points,allowed)
                self.assertTrue(all(x < 179 for x,y in points))
        self.assertTrue(all(y < 49 and x >= 180 for x,y in room.CUBBIES))

    def test_actual_cubby_pixels_and_counts_follow_shares(self):
        look = self.looks["Mechanist"]
        stats = list(self.pack["looks"])
        for shares in ([],[("Lore",100)], [("Art",66),("Lore",30),("Tools",4),("Infra",0)],
                       [(s,10) for s in stats],[(s,100) for s in stats]):
            for seed in ("loft","yard"):
                plan = room.plan_room(self.pack,look,shares,seed)
                scene = room.backdrop(self.pack,look,plan)
                empty = room.backdrop(self.pack,look,room.plan_room(self.pack,look,[],seed))
                self.assertEqual(Counter(s for s,_ in plan.stock),dict(art.shelf_counts(shares)))
                self.assertEqual(len(plan.stock),len({cell for _,cell in plan.stock}))
                for stat,(x,bottom) in plan.stock:
                    token = tokens.trinket(self.pack,stat)
                    self.assertIn((x,bottom),room.CUBBIES)
                    self.assertLessEqual(max(token.w,token.h),10)
                    empty.paste(token,x+(10-token.w)//2,bottom-token.h)
                self.assertEqual(scene.px,empty.px)

    def test_easel_carries_the_window_subject_inside_its_canvas(self):
        pictures = [furniture.fixture("easel",view) for view in room.TOUCHES["view"]]
        self.assertEqual(len({p.png() for p in pictures}),len(pictures))
        for p in pictures[1:]:
            for y,row in enumerate(p.px):
                for x,color in enumerate(row):
                    if not (8 <= x <= 25 and 8 <= y <= 22):
                        self.assertEqual(color,pictures[0].get(x,y))
        look = self.looks["Painter"]
        for seed in ("salt-glass", "silver-moss", "silver-quay", "fern-glass"):
            plan = room.plan_room(self.pack,look,[],seed)
            touches = dict(plan.touches)
            layer = room.backdrop(self.pack,look,plan)
            x = 5 if touches["arrangement"] == "left" else 38
            self.assertEqual(crop(layer,x+8,20,18,15),
                             crop(furniture.fixture("easel",touches["view"]),8,8,18,15))

    def test_seeded_banner_face_uses_same_traits_as_standalone(self):
        look = self.looks["Traveler"]
        for seed,mode,skin in zip(("","lichen","silver-quay"),MODES,SKINS):
            traits = keepsake.traits(seed,look,mode)
            fig = keepsake.figure(self.pack,look,skin=skin,presentation=mode,**traits)
            banner = room.banner(self.pack,look,[],(),seed,presentation=mode,skin=skin)
            x,y = art.banner_figure_box(self.pack,fig)
            for i,row in enumerate(fig.px[:32]):
                for j,p in enumerate(row):
                    if p:
                        self.assertEqual(banner.get(x+j,y+i),p)

    def test_party_keys_alone_control_drawings_order_and_limit(self):
        look = self.looks["Warden"]
        crew = ["agy","opencode","codex","claude"]
        args = self.pack,look,[("Infra",100)]
        a = room.banner(*args,crew,"mint")
        b = room.banner(*args,list(reversed(crew))*2,"mint")
        self.assertEqual(a.px,b.px)
        self.assertEqual(companions.berths(crew),["claude","codex","agy"])
        for key in companions.MEMBERS:
            canvas = companions.member(key)
            for look,seed in ((look,"tarn"),(self.looks["Traveler"],"oak")):
                display = room.banner(self.pack,look,[],[key],seed)
                empty = room.banner(self.pack,look,[],[],seed)
                empty.paste(canvas,193-canvas.w//2,67-canvas.h)
                self.assertEqual(display.px,empty.px)
        self.assertEqual(companions.member("unrecognized").px,companions.member("default").px)
        self.assertEqual(len({frozenset(occupied(companions.member(h))) for h in companions.MEMBERS}),
                         len(companions.MEMBERS))

    def test_pins_and_stock_have_individual_silhouettes(self):
        for table,new in ((self.pack["looks"],tokens.trinket),(self.pack["icons"],tokens.pin)):
            masks = set()
            for key in table:
                sprite = new(self.pack,key)
                masks.add(frozenset(occupied(sprite)))
                self.assertGreaterEqual(len(sprite.colors()),5)
                self.assertLessEqual(max(sprite.w,sprite.h),17)
            self.assertEqual(len(masks),len(table))
        self.assertEqual(tokens.pin(self.pack,"other").px,tokens.pin(self.pack,"milestone").px)


class EyeTests(unittest.TestCase):
    def test_native_eye_ramps_contrast_on_all_skins_and_only_recolor_the_iris(self):
        pack = art.default_pack()
        look = cast()["Traveler"]
        self.assertEqual(next(iter(EYE_RAMPS)),"honey")
        for expr,mode,skin in product(EXPRESSIONS,MODES,SKINS):
            def draw(eyes=None):
                return keepsake.figure(pack,look,expression=expr,
                                       presentation=mode,skin=skin,eyes=eyes)
            honey = draw()
            self.assertEqual(honey.px,draw("honey").px)
            for eyes,ramp in EYE_RAMPS.items():
                other = draw(eyes)
                values = list(map(luminance,ramp))
                self.assertEqual(values,sorted(set(values),reverse=True))
                self.assertGreater((values[1]+.05)/(values[3]+.05),3)
                self.assertLess(values[0],luminance("#fff6df"))
                mid_skin = (skin or pack["skin_colors"])[1]
                self.assertGreater((luminance(mid_skin)+.05)/(values[3]+.05),2)
                for x in (23,33):
                    socket = {p for row in crop(other,x,16,7,5) for p in row}
                    self.assertIn(ramp[3],socket)
                    self.assertEqual(ramp[1] in socket,expr != "joy")
                    if expr != "joy":
                        self.assertIn("#fff6df",socket)
                        self.assertIn(ramp[0],socket)
                if expr == "joy":
                    self.assertEqual(other.px,honey.px)
                else:
                    expected = dict(zip(EYE_RAMPS["honey"],ramp))
                    for y,row in enumerate(other.px):
                        base = honey.px[y]
                        for x in range(other.w):
                            allowed = 16 <= y <= 20 and (23 <= x <= 29 or 33 <= x <= 39)
                            c = expected.get(base[x],base[x]) if allowed else base[x]
                            self.assertEqual(row[x],c)
        for eyes in ("", []):
            with self.assertRaises(art.PackError):
                keepsake.figure(pack,look,eyes=eyes)

