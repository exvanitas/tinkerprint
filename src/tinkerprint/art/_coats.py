"""Hand-cut coats and work clothes. The near arm comes from the tool's pose."""
from ._drawing import Drawing

# Grip and far shoulder. The near shoulder sits seven pixels inboard of the grip.
POSES = {
    'Interface': ((32,28), (13,24)), 'Logic': ((31,29), (13,24)),
    'Infra': ((33,31), (11,25)), 'Tools': ((32,31), (13,25)),
    'Data': ((33,27), (13,23)), 'Models': ((31,28), (14,24)),
    'Tests': ((34,28), (14,23)), 'Docs': ((31,30), (14,24)),
    'Systems': ((33,31), (12,25)), 'Art': ((32,29), (13,24)),
    'Worlds': ((32,30), (12,25)), 'Lore': ((31,29), (13,24)),
    'Community': ((33,31), (11,25)),
}


def leg(d, hip, knee, ankle, boot, *, facing=1):
    """A trouser leg tapering into a turned foot. The ankle marks the shoe topline."""
    hx,hy = hip
    kx,ky = knee
    x,y = ankle
    d.shape('f',(hx-2,hy),(hx+3,hy),(kx+2,ky),(x+2,y+1),
            (x-2,y+1),(kx-2,ky+1))
    d.shape('n',(hx-2,hy),(hx+1,hy),(kx+1,ky),(x,y),
            (x-2,y),(kx-2,ky))
    rows = {
        'boot': ('ooolL','lOOLP','lOOLL','OOolooO','PLOOOOOP'),
        'shoe': ('sssNN','NNNnn','OOOOL','lOOlooo','POOOOLOP'),
        'iron': ('smMMn','NNnnf','sMNNn','nMsMNNnf','fNNnnfff'),
        'wrap': ('llllL','eaaaO','OooOL','OOaoooo','PLOOOOOP'),
        'slip': ('CCFFF','BCCCF','CCCFF','ggGoooo','LLOOOOOP'),
    }[boot]
    if facing < 0:
        rows = tuple(s[::-1].rjust(8) for s in rows)
    d.grid(x-2 if facing>0 else x-5,y,'\n'.join(rows))


def belt(d, x, y, width, buckle='g'):
    d.rect(x,y,width,2,'P')
    d.rect(x,y,width-1,1,'O')
    d.grid(x+width//2,y,'y'+buckle+'G\ngP'+'G')


def off_arm(d, shoulder, elbow, hand, sleeve='B', shade='C'):
    sx,sy = shoulder
    ex,ey = elbow
    hx,hy = hand
    d.shape(shade,(sx-1,sy),(sx+3,sy+1),(ex+3,ey),(hx+1,hy-2),
            (hx-1,hy+1),(ex-2,ey+1),(ex-2,ey-2))
    d.shape(sleeve,(sx-1,sy),(sx+1,sy+1),(ex,ey-1),(ex-2,ey))
    d.line('F',(ex,ey+1),(hx-1,hy+1))
    d.grid(hx-1,hy-1,'aGG\n@+:\n:+~')


def body(stat):
    d = Drawing()
    if stat == 'Interface':
        # Tailed velvet frock, narrow waist and one foot turned out for a bow.
        leg(d,(21,32),(20,35),(17,38),'slip',facing=-1)
        leg(d,(25,32),(26,36),(27,39),'slip')
        d.shape('F',(15,21),(24,21),(28,24),(26,31),(30,37),(24,36),(20,33),(12,40),(6,39),(13,30))
        d.shape('B',(15,21),(24,22),(27,25),(24,31),(14,38),(8,38),(15,29))
        d.shape('C',(15,26),(18,24),(18,31),(13,37),(8,38))
        d.shape('e',(19,22),(25,22),(24,29),(22,31),(19,26))
        d.line('A',(14,24),(16,22),(19,22),(18,25),(21,28))
        belt(d,17,30,9)
        off_arm(d,(14,23),(10,28),(14,31))
    elif stat == 'Logic':
        # A long scholarly mantle with a continuous embroidered stole.
        leg(d,(21,34),(19,37),(17,38),'wrap',facing=-1)
        leg(d,(24,33),(25,36),(26,39),'wrap')
        d.shape('C',(17,21),(24,21),(27,25),(26,30),(31,40),(23,41),(17,39),(8,40),(13,30))
        d.shape('B',(17,21),(24,22),(24,28),(19,36),(16,39),(9,39),(15,29))
        d.shape('F',(18,25),(21,25),(20,32),(16,38),(13,39))
        d.shape('e',(23,22),(25,23),(24,30),(27,38),(23,39),(21,32))
        d.line('g',(21,25),(20,30),(19,34))
        d.line('A',(14,27),(15,24),(18,22))
        d.grid(10,35,'    3   g\n   3g  gy\n  3g  gy\n 3ggggy')
        d.line('4',(22,27),(22,30),(23,34))
        off_arm(d,(15,24),(11,30),(14,32))
    elif stat == 'Infra':
        # Articulated greaves and a wide tabard cut away at the hip.
        leg(d,(18,32),(16,35),(14,39),'iron',facing=-1)
        leg(d,(25,32),(28,36),(29,39),'iron')
        d.shape('f',(12,21),(24,21),(29,25),(29,32),(32,36),(25,37),(20,34),(16,37),(9,36),(12,30))
        d.shape('B',(13,22),(25,23),(27,25),(25,33),(21,37),(17,35),(15,30))
        d.shape('N',(11,24),(14,21),(24,21),(27,24),(24,28),(17,29),(12,27))
        d.shape('m',(12,24),(15,22),(23,22),(23,24),(16,26))
        d.line('n',(14,26),(18,27),(25,25))
        d.shape('R',(18,28),(23,27),(24,32),(23,36),(19,35))
        d.line('r',(18,28),(20,28),(20,33))
        d.grid(18,29,'gyg\n g')
        belt(d,12,31,16)
        off_arm(d,(12,24),(9,29),(13,32),'M','f')
        d.grid(9,22,'  mmmm\n mmmMMn\nsMMNNnn\n Nnnnf')
    elif stat == 'Tools':
        leg(d,(20,32),(18,36),(17,39),'wrap',facing=-1)
        leg(d,(25,33),(25,36),(26,39),'boot')
        d.shape('B',(15,22),(24,21),(28,24),(29,35),(23,37),(13,35),(11,29))
        d.shape('A',(14,23),(17,22),(19,22),(16,26),(13,26))
        # Split oxblood smith's apron with hammered pockets and a brass ring.
        d.shape('O',(18,22),(23,22),(24,26),(27,26),(29,36),(24,38),(16,36),(15,28),(18,26))
        d.shape('l',(19,24),(21,24),(22,28),(25,29),(26,33),(17,34),(17,27))
        belt(d,14,30,13)
        d.grid(16,32,'yygg   n\ngGlo  ms\n  lO  nf')
        d.line('a',(18,26),(17,28),(17,29))
        d.line('P',(16,35),(20,36),(23,37))
        off_arm(d,(14,24),(10,30),(15,32))
    elif stat == 'Data':
        leg(d,(19,32),(17,35),(12,38),'wrap',facing=-1)
        leg(d,(25,32),(28,35),(27,39),'boot')
        d.shape('C',(15,21),(24,21),(28,24),(26,29),(29,33),(24,35),(21,33),(16,36),(10,35))
        d.shape('B',(15,22),(23,21),(26,24),(23,30),(21,32),(12,34))
        d.line('A',(12,27),(15,23),(20,22))
        d.shape('a',(15,22),(17,22),(25,30),(25,32),(22,31))
        d.grid(21,29,' gyG\n GPGooo\n  aoooll\n  ollllL\n   lLLL')
        off_arm(d,(14,23),(10,28),(14,30))
    elif stat == 'Models':
        leg(d,(20,34),(20,37),(21,39),'slip',facing=-1)
        leg(d,(25,33),(25,36),(25,38),'slip')
        d.shape('F',(16,21),(23,21),(27,24),(24,32),(31,38),(25,41),(17,39),(9,40),(14,33))
        d.shape('B',(17,21),(23,21),(24,26),(22,30),(18,35),(11,39),(14,31))
        d.shape('C',(20,31),(23,29),(25,34),(29,38),(25,39),(21,35))
        d.line('A',(13,36),(19,31),(23,24))
        d.shape('6',(15,21),(17,22),(14,27),(11,32),(6,35),(7,33),(10,29))
        d.line('7',(7,33),(11,29),(14,23))
        d.grid(23,34,' 7\n 77\n  77\n   8')
        d.grid(17,29,'yyyg\n  gg\n   y')
        d.line('g',(12,38),(19,33),(23,29))
        d.grid(20,24,'g   g\n ygG\n  y\n  G')
        off_arm(d,(15,23),(11,28),(15,30))
    elif stat == 'Tests':
        # Fencer in a forward lunge. A split tab and a wide white collar.
        leg(d,(21,31),(16,36),(11,38),'boot',facing=-1)
        leg(d,(25,31),(29,34),(30,39),'boot')
        d.shape('C',(17,20),(24,20),(29,24),(26,30),(29,33),(25,36),(20,33),(15,36),(11,36))
        d.shape('B',(17,21),(24,21),(27,24),(24,30),(18,31),(13,35))
        d.shape('e',(16,21),(23,21),(26,22),(23,25),(21,24),(18,25))
        d.line('g',(16,25),(22,29),(25,30))
        belt(d,16,30,11)
        off_arm(d,(16,23),(10,26),(12,29))
    elif stat == 'Docs':
        leg(d,(20,33),(20,36),(19,39),'shoe',facing=-1)
        leg(d,(26,33),(26,36),(26,38),'shoe')
        d.shape('C',(16,21),(23,21),(27,23),(26,30),(29,38),(23,39),(19,37),(13,39),(10,37))
        d.shape('B',(16,22),(22,21),(23,26),(19,34),(13,37),(15,29))
        d.shape('f',(18,21),(21,21),(22,27),(19,32),(16,35),(17,29))
        d.line('g',(17,23),(19,26),(18,30))
        d.grid(21,31,'ooogG\nOlllo\nLOOOO')
        off_arm(d,(15,23),(12,30),(17,31))
    elif stat == 'Systems':
        # The mechanist wears a riveted boiler and striped wool under work overalls.
        d.grid(4,18,'  gyg   gyG\n  gPG   gPG\n   gggggg\n  aaoooool\n  olO  lOL\n smMMMMMNNn\n szzbbuuuJn\n szbbuuuuJn\n sbbuuuuuJn\ngyyyyggggGG\n sbbuuuuuJn\n sbbuuuuuJn\n  MMMMNNnn\n   gggGGG')
        leg(d,(18,32),(16,35),(15,39),'boot',facing=-1)
        leg(d,(25,32),(27,35),(28,39),'boot')
        d.shape('n',(13,22),(24,21),(29,24),(27,30),(29,35),(24,37),(20,34),(15,37),(11,34))
        d.shape('B',(14,22),(25,22),(27,25),(25,28),(17,28),(12,26))
        d.shape('f',(16,23),(18,22),(19,25),(23,25),(25,23),(26,24),(25,30),(26,34),(17,35),(15,30))
        d.grid(17,26,'g   g\nMNNNN\n MMMn\n  NNn')
        belt(d,12,32,15)
        off_arm(d,(13,24),(10,30),(14,33),'M','n')
        d.grid(10,27,'mmmN\n nnn\n MMM')
        d.shape('R',(13,22),(21,21),(24,22),(20,25),(16,25),(10,29),(11,25))
        d.line('i',(12,24),(16,22),(21,22))
        d.line('r',(11,27),(15,24),(20,23))
        d.grid(19,30,' yG\n Gy\n  G')
    elif stat == 'Art':
        leg(d,(20,33),(20,36),(18,38),'shoe',facing=-1)
        leg(d,(25,33),(25,36),(27,39),'shoe')
        d.shape('C',(15,21),(24,21),(28,25),(25,31),(29,36),(23,37),(16,35),(10,37),(12,31))
        d.shape('B',(14,22),(23,22),(25,25),(22,29),(17,33),(11,35))
        d.shape('e',(18,22),(20,22),(20,25),(24,25),(24,23),(26,23),(25,29),(28,36),(16,35),(17,29))
        d.grid(20,29,'bb   l\n bu lO\n   r\n  rrR')
        d.shape('r',(15,22),(23,22),(22,24),(20,25),(17,24),(14,26))
        off_arm(d,(14,23),(10,28),(14,31))
    elif stat == 'Worlds':
        leg(d,(19,31),(18,35),(15,39),'wrap',facing=-1)
        leg(d,(25,32),(25,37),(27,39),'wrap')
        d.shape('C',(14,21),(24,21),(28,25),(27,30),(30,36),(23,37),(17,34),(10,36),(12,29))
        d.shape('B',(14,22),(24,22),(25,28),(22,33),(18,34),(11,34))
        d.shape('F',(14,22),(24,21),(26,25),(24,27),(17,26),(11,28))
        d.shape('A',(14,22),(22,21),(24,23),(18,24),(12,26))
        d.line('o',(15,24),(18,25),(24,31))
        belt(d,14,31,14)
        off_arm(d,(13,24),(9,29),(12,32))
    elif stat == 'Lore':
        leg(d,(20,34),(19,37),(17,39),'slip',facing=-1)
        leg(d,(24,34),(24,36),(25,38),'slip')
        d.shape('F',(17,20),(24,21),(27,25),(25,30),(30,40),(23,40),(19,38),(10,40),(13,32))
        d.shape('B',(16,22),(22,21),(23,25),(20,32),(14,38),(11,39),(14,31))
        d.shape('C',(22,24),(25,23),(25,31),(28,39),(23,38),(20,32))
        d.shape('8',(16,22),(20,21),(25,23),(24,25),(20,27))
        d.line('g',(15,25),(18,28),(21,29),(25,26))
        d.line('q',(25,32),(26,36),(28,39))
        d.line('g',(13,37),(15,36),(17,34))
        off_arm(d,(14,23),(11,29),(15,31))
    elif stat == 'Community':
        leg(d,(18,32),(17,35),(16,39),'shoe',facing=-1)
        leg(d,(25,32),(27,36),(28,39),'shoe')
        d.shape('C',(13,22),(24,21),(30,25),(31,33),(30,37),(23,38),(12,37),(9,34),(10,27))
        d.shape('B',(13,23),(24,22),(27,26),(26,33),(22,35),(11,34))
        d.shape('e',(16,22),(18,22),(19,26),(24,26),(25,22),(27,23),(27,29),(30,36),(25,38),(14,36),(15,29))
        d.shape('c',(24,28),(26,27),(27,32),(29,35),(25,36),(22,33))
        d.line('r',(15,34),(23,36),(29,35))
        d.grid(18,28,'aaooo\n eeeo\n  aa')
        off_arm(d,(13,24),(9,29),(13,32),'e','a')
    else:
        leg(d,(20,33),(18,36),(16,38),'wrap',facing=-1)
        leg(d,(26,32),(27,36),(27,39),'boot')
        d.shape('O',(14,21),(24,21),(28,24),(26,31),(30,35),(24,37),(18,35),(11,37),(12,29))
        d.shape('o',(15,22),(23,22),(25,27),(22,32),(14,35))
        d.shape('J',(15,21),(23,21),(27,24),(23,27),(18,26),(11,29))
        d.shape('t',(15,22),(22,22),(24,24),(17,24),(12,27))
        d.line('L',(15,24),(22,30),(26,32))
        belt(d,14,31,12)
        off_arm(d,(14,24),(10,30),(15,32),'o','O')
    return d.part()


PARTS = {stat.lower()+'-coat': body(stat) for stat in (*POSES, 'traveler')}
