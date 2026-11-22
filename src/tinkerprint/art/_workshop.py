"""Panoramic workshop interiors, built as editable pack layers."""
from ._drawing import Drawing, grid_part
from ._landscape import pine

W, H = 252, 72


def mountains(d, warm):
    sky, haze, peak, near, woods = ('}', ';', '|', ';', '{') if warm else ('?', '/', '%', '/', '!')
    d.rect(0,0,W,H,sky)
    if warm:
        d.grid(137, 13, """
    xxx
  xx000xx
 x0000000x
 x0000000x
x000000000x
x000000000x
 x0000000x
  x00000x
    xxx
""")
    else:
        d.grid(53, 7, """
    MMM
  Mss
 Mss
 ss
 ss
 ss
  ss     M
   sssssM
     MM
""")
    for x, y, w in ((26, 19, 9), (32, 18, 13), (116, 11, 13), (125, 10, 7), (160, 17, 12)):
        d.rect(x, y, w, 1, peak)
    d.shape(peak,(0,30),(18,21),(27,24),(42,17),(55,25),(67,21),(77,22),
            (96,9),(101,13),(105,12),(124,25),(135,21),(140,23),(158,13),
            (163,15),(167,13),(183,21),(206,15),(215,30),(250,35),(250,54),(0,54))
    d.shape(haze,(79,21),(96,9),(101,13),(105,12),(113,18),(106,15),
            (103,16),(99,14),(97,15),(95,12),(90,17),(88,16))
    d.shape(haze,(145,21),(158,13),(163,15),(167,13),(173,17),(168,15),
            (165,16),(161,16),(158,15))
    d.shape(near,(0,24),(19,28),(31,25),(40,26),(58,34),(71,32),(84,28),
            (101,32),(116,35),(129,29),(143,26),(153,27),(163,23),
            (177,25),(188,19),(201,25),(201,51),(0,51))
    # A switchback river catches the window light between the wooded slopes.
    d.shape(haze,(79,31),(85,31),(98,34),(98,35),(87,38),(88,39),(107,41),
            (113,45),(93,45),(83,41),(78,39),(81,37),(94,35),(93,34))
    if warm:
        d.grid(65,22,"""
      .w.
       wa
    e.  w
    ee..O.eee
      eOGOee
       llo
     eeOaO
    ee.lao
       Oaol
      looll
""")
    else:
        d.rect(78,25,31,2,'!')
        d.rect(78,25,31,1,'M')
        for x in range(80,109,6):
            d.rect(x,27,2,5,'!')
            d.rect(x-1,27,4,1,'!')
    d.shape(woods,(0,33),(13,31),(27,35),(40,36),(55,42),(68,40),(79,43),
            (100,46),(123,43),(142,36),(162,37),(183,30),(199,28),(200,51),(0,51))
    for x,y,h in ((20,35,8),(26,36,6),(30,36,5),(39,38,6),(60,43,5),
                  (145,39,8),(151,38,6),(156,39,5),(177,34,9),(183,33,10)):
        pine(d,x,y,h,woods)


def timber(d, warm):
    wall,side,stone = ('O','L','l') if warm else ('n','f','N')
    # Recesses on either side and a broad arch overlooking the valley.
    d.rect(0,0,25,54,wall)
    d.rect(189,0,63,54,side)
    d.rect(0,45,W,11,wall)
    d.shape('P',(16,0),(70,0),(55,3),(40,9),(32,16),(28,24),(28,45),(16,45))
    d.shape('l',(21,0),(66,0),(53,3),(39,9),(32,15),(26,25),(26,45),(21,45))
    d.line('a',(27,28),(29,20),(33,14),(41,8),(55,2),(63,0))
    d.shape('P',(148,0),(198,0),(198,46),(187,46),(187,27),(184,20),(179,14),(167,6))
    d.shape('O',(151,0),(191,0),(191,45),(188,45),(188,25),(184,18),(177,11),(165,5))
    d.line('l',(158,1),(172,6),(181,13),(187,21))
    # Narrow joints in the arch blocks or in the pegged wooden braces.
    for x,y in ((26,17),(32,10),(40,5),(178,6),(184,12)):
        d.line('P',(x-2,y-2),(x+1,y))
    d.rect(79,0,3,45,'O')
    d.rect(79,0,1,45,'a')
    d.rect(82,0,1,45,'L')
    d.rect(23,45,169,3,'l')
    d.rect(24,45,168,1,'a')
    d.rect(24,48,169,2,'L')
    if warm:
        for x in (2,12,20,201,215,232,247):
            d.rect(x,3,1,42,'L')
            d.line('l',(x+4,16),(x+3,22),(x+3,30))
    else:
        for x,y,length in ((0,9,16),(10,17,12),(0,29,8),(194,7,29),(225,33,14),(7,37,12)):
            d.rect(x,y,length,1,stone)
            d.rect(x+length-2,y+1,1,4,side)
    d.shape('P',(0,0),(W-1,0),(W-1,4),(191,4),(182,2),(66,2),(50,4),(0,6))
    d.line('l',(0,5),(51,3),(63,1))
    d.rect(0,53,W,3,'P')


def floor(d):
    d.rect(0,56,W,16,'O')
    d.rect(0,56,W,1,'l')
    d.shape('o',(26,56),(66,56),(105,71),(44,71))
    d.shape('l',(73,56),(106,56),(154,71),(109,71))
    for y in (59,65):
        d.rect(0,y,W,1,'L')
        d.rect(0,y+1,43 if y==59 else 64,1,'l')
    for x,y,u,v in ((4,56,1,58),(54,56,55,58),(169,56,173,58),(237,56,244,58),
                     (34,60,31,64),(134,60,138,64),(188,60,195,64),(13,66,8,71),
                     (76,66,77,71),(215,66,225,71)):
        d.line('L',(x,y),(u,v))
    d.line('l',(4,68),(21,68),(25,67))
    d.line('l',(172,62),(184,62))
    d.line('l',(196,68),(212,68))


def plant(d,x,y):
    d.grid(x,y,"""
        t
   tv  vt   j
   tvt vt  tj
    jtvj  tj
 vt  jtj jt
  vtj jjj
    jjtj
   aaooll
   ollllL
    lloL
""")


def bench(d):
    # A trestle bench with a drafting board, brass square and rolled paper.
    d.shape('L',(9,57),(74,56),(86,59),(75,61),(13,61))
    for x in (17,66):
        d.shape('P',(x,44),(x+4,44),(x+1,58),(x-3,58))
        d.line('o',(x,47),(x-2,57))
        d.shape('L',(x+2,45),(x+4,44),(x+8,55),(x+5,55))
    d.rect(16,51,55,3,'O')
    d.rect(16,51,55,1,'l')
    d.shape('L',(8,43),(15,39),(73,39),(79,43),(77,46),(9,46))
    d.shape('o',(9,42),(16,39),(72,39),(78,42))
    d.rect(9,43,69,1,'a')
    d.rect(11,45,65,1,'O')
    # A sheet tacked askew. Its diagram is a drawing, with no lettering.
    d.shape('O',(30,39),(37,25),(57,26),(54,41))
    d.shape('e',(32,38),(38,26),(55,27),(52,39))
    d.line('w',(33,38),(38,26),(53,27))
    # The pressed fern on the drafter's page has a central stem and paired pinnae.
    d.line('j', (37, 37), (47, 28))
    for x, y in ((40, 34), (42, 32), (44, 30)):
        d.line('t', (x - 2, y - 2), (x, y))
        d.line('j', (x, y), (x + 3, y))
    d.rect(47, 35, 4, 1, 'o')
    d.rect(46, 37, 3, 1, 'o')
    d.rect(34,39,18,1,'G')
    d.grid(58,34,"""
        oo
     .oaao
   .oaeao
 .oaeaoO
 ooaoOG
 oaeoG
  oO
""")
    d.grid(13,29,"""
   m   o
   mM o   M
    MmO  M
    .OO n
  GggggggG
   gggGgG
   goGGGG
   goGGGG
   GGGGGL
""")
    d.grid(22,37,"""
    oo
    LLn
 .nnNNnn
 nNMMMnn
  nfffn
""")


def cabinet(d):
    d.rect(193,3,56,48,'P')
    d.rect(197,6,48,41,'L')
    d.rect(199,7,45,39,'O')
    d.rect(200,8,43,37,'L')
    for y in (19,34,48):
        d.rect(194,y,56,3,'O')
        d.rect(194,y,55,1,'o')
        d.rect(198,y+3,47,1,'P')
    d.rect(194,5,2,45,'l')
    d.rect(247,5,1,45,'l')
    # A drawer cabinet below the open, movable shelf stock.
    d.rect(195,51,54,7,'L')
    for x in (198,214,230):
        d.rect(x,52,14,4,'O')
        d.rect(x+5,53,4,1,'g')
    # Volumes and a specimen drawer, not repeated bottles.
    for x,h,cover in ((201,8,'J'),(204,10,'u'),(208,9,'9'),(211,6,'O')):
        d.rect(x,48-h,3,h,cover)
        d.rect(x,46-h+4,2,1,'o')
    d.rect(219,42,20,6,'O')
    d.rect(219,42,20,1,'l')
    d.rect(225,44,6,2,'g')
    d.rect(227,44,2,1,'P')


def studio(warm):
    d=Drawing(W,H)
    mountains(d,warm)
    timber(d,warm)
    if warm:
        # Bracket fungi grow out of the living doorpost. Their pale edges catch the lantern.
        d.grid(0, 14, """
  aaao
aeaaaoo
ggggGGO
   llo
  lo
    l     oo
     l  oaaao
      oeeeaaaoo
     aaoooooll
        OllL
      oo
     oeao
   aoaoool
     OO
""")
    else:
        # A mason keeps a brass plumb bob beside the drawing board.
        d.line('L', (6, 10), (6, 26))
        d.rect(4, 9, 5, 2, 'O')
        d.grid(3, 25, """
   g
  gyg
 gywyg
 gyygG
  ggG
   G
""")
    floor(d)
    cabinet(d)
    bench(d)
    plant(d,155,35)
    # Ivy trails from the left edge and an oil lamp hangs by its chain.
    d.line('J',(0,3),(8,5),(13,4),(19,7),(20,15),(18,19))
    for x,y in ((1,4),(5,6),(9,4),(13,5),(16,7),(18,9),(18,14),(16,18)):
        d.shape('j',(x,y),(x+3,y),(x+2,y+3),(x,y+4))
        d.line('t',(x,y),(x+1,y+1))
    # A broad paper lantern hangs over the trestle, its light on the fern sheet.
    d.line('P', (36, 9), (36, 16))
    d.grid(30, 16, """
     ggg
    GgGgG
   GgggggG
   gooooOG
  gaeweaaoG
  gewewwaoG
  geeewwaoG
  geeewwaoG
  gaeeeaooG
   GoaaoOG
    GggGG
     ggG
      o
""")
    return d.part()


def rug():
    d=Drawing(W,H)
    d.shape('L',(91,59),(142,59),(153,67),(148,69),(80,69),(80,67))
    d.shape('C',(91,59),(141,59),(152,67),(80,67))
    d.shape('B',(92,60),(139,60),(147,65),(85,65))
    # A dark woven field behind the boots, with the trade colors on the binding.
    d.shape('F',(96,61),(136,61),(142,64),(91,64))
    d.line('A',(86,65),(147,65))
    for x in (86,98,138):
        d.shape('C',(x,63),(x+3,61),(x+6,63),(x+3,64))
    for x in range(82,151,5):
        d.rect(x,68,3,1,'a')
    d.shape('F',(99,64),(109,62),(126,62),(133,64),(126,66),(100,66))
    return d.part()


PARTS = {'blue-studio':studio(False),'amber-studio':studio(True),'runner':rug(),
         'standard':grid_part(172,8,"""
 gggggggggggggG
  ABBBCABBBC
  ABBCABBBCF
  ABBBXBBCFF
  ABBXYXBCCF
  ABXYwYXBCF
  ABBXYXBCCF
  ABBBXBBCFF
  ABBBABBCFF
  ABBCABBCCF
  AgBBCCCgCF
   gBBBCCgF
    gBCCgF
     gCgF
      gG
""")}
