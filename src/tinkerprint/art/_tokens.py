"""Cabinet miniatures and the enamel pins awarded for achievements."""
from ._drawing import grid_part

SKETCHES = {
'sunrise': """
     222222
   22ggyygg22
  22g222222g22
  2g222yy222g2
 12g2gwwwwg2g21
 122gywwwwyg221
 11yywwwwwyyy11
  fbbbbbbzzbbf
   uuuzzbbbuu
    JuubbuuJ
""",
'flag': """
    yg
    Go.iiir
    ooirwiirrr
    olirriirrrR
    olrrRrrRRr
    olriirRR
    olR
    ol
    ol
   bosM
  bbMmsMM
 bMsmMMNnnJ
  NNnNnnJJ
    ffJJ
""",
'coins': """
       gyyyg
      gywwygG
      ygGgygG
      ygggygG
       ggggG
  gyyyyggGGgg
 gywwyyygGgGGG
 yyyyyygGyyggG
 GgggggGGgggGG
 gyyyyygGyyyggG
 GgggggGgggggGG
  GGGGG GGGGGG
""",
'ship': """
        oo
        orrR
       woO
      wwo Oc
     wweo  wc
    wweeo  wwcc
   wweeao  wweec
  weeaaao  eecc
        ol
 aooaaaaoloooooa
  rrrRRRRRRRRRR
   RRRRPLLLLP
 bzzzbbuuubzzbb
   uubbbzzzbu
""",
'signpost': """
      allo
      oolL
  eeaaaaaaao
 eaaaoooooool
  OOOOllOOOO
      olL
      olL
    oaaaaooooo
   aoaaaolllOOl
    OOOOLOOOOO
      olL
      olL
   jt olL  j
  jtjNNNnnjJ
   JJnnnffJ
""",
'mail': """
     ubbbbbbb
     bzzzzzzbJ
     buubbuubJ
    yyyyyyyyyJ
    ywaaaawyG
    ygggggggG
 cwwwweeeeecG
 wecweeeececG
 weacweeccaeG
 weeacrrcaeeG
 weeerrRceeeG
 weeccRRaceeG
 wccceeeeaccG
  eeeeeecccc
""",
'skull': """
         tvv
    vt  tvj
     jjjj
     .eeec
   eeewwwwea
  eeewwwwwcea
 .eeccwwweccea
 eePkkeeePkkca
 ecPkkewwkkkca
 aeeeceeecceao
 .aaeeePeeaao
   aoePPeao
   .eeaeae
    aoaoao
""",
'bubbles': """
    iiiiirrr
  iwwwwwwirrrR
  iwrrrrrrirrR
  iwwwwwiiirrR
  iwrrrrirrRRR
  iiiiiirrRRRR
   rrr rRRbbbbu
    rR  bzzzzbbu
    R   bJbbbJJbu
        bzzzzzzbu
        bJJbbJbbu
        bbbbbbbuu
         uuuu uu
               u
""",
'pennants': """
   y
   ooo   g
   orrr. oo   y
   oriR  obb  oo
   orRR  obu  ojj
   oR.R  obb  ojv
   o     ouu  ojj
   l     o.u  oJj
   l     o    o J
   l     l    o
   l     l    l
  .loo   l    l
  MssMsMMsM  sl
 nNMMMNsMssMsssn
   fNNnNnnNNNnf
""",
'wheel': """
     gyyyg
   gywwwwyyg
  gytvvGyggyg
 gytttvGyyggyg
 gtttvvGyygggG
gytttvvGyyggggG
yGGGGGgygGGGGGy
wbbbbgywygllllg
ybuubGgygGOoolg
 gyubbuGoooooG
 gybbbuGoooolG
  gybbuGoolgG
   gyyyggggG
     ggggG
""",
'star': """
   rrr   rrr
   riiR riir
    riiRiiR
     riirR
      ggG
    gyyyygG
   gymmymmGG
  gyNNyyyNNgG
  ygNyyyyyNgG
  ggNgyyygNgG
   GgNgNgNgG
    GgggggG
      GGG
""",
'frame': """
   gyyg
  gyzzgG
 gywzzugG
 gyzzbugG
 GgzbbugG
  GguugG
   GggG
     gG
     gy
      G
""",
'runebook': """
  XXXYYY
 XwXYYZYG
 XYYggYYG
 XYYgyYYG
 XYYYgYYG
 XecccaoG
  ZZZZZZG
""",
'helmlet': """
      s
    smMs
   mmMMnn
  mmmmMMNn
 smmmMNnnn
 nggggGGGG
 NnkkkNkkf
  NM..Nnf
  f...nf
""",
'hammer': """
   smmM
  smmMMN
 mmMNNnNn
  nMXo.Nn
   XYo
  XYo
 XYo
 YZ
""",
'map': """
  aaa  ee
 eweeaewe
 ewwaeece
 wjtajcwe
 wjjaeewe
 webabbee
 weaubbce
 weeawece
 eaa eeaa
""",
'flask': """
   oo
  smmN
   mN
   mN
  mwMN
 mwwwMN
 mXYYYYN
 mXXYYYn
  nYYYn
   nnn
""",
'hourglass': """
 oaaaaao
 Geweeeg
  mwYYM
   mYs
    g
   Msg
  meYYs
 GsYYYZg
 oooooll
""",
'books': """
  Rrrrrrr
 Rwwwceea
 RRRRRRRR
  uuuuuuu
 uweeecao
 uJJJJJJJ
  looolll
 leeeecco
 LLLLLLLL
""",
'cog': """
   XXX
 X XMX X
 XXMMMNX
 MMygyMN
XMyG.GyNX
XMg...gNX
XNyG.GynX
 nNygyNn
 nZNNNZZ
 Z ZNZ Z
   ZZZ
""",
'paints': """
 r.  b
 rr  bb  j
  o  Ob jj
  o  O.o
  mmmMMN
  mXYYYZ
  NXXYYZ
  nYYYZZ
   nnnn
""",
'sprout': """
    X
   XwY  XX
   XYY XYY
    ZXYYZ
     Y Z
   aaoool
    ollL
    lLLL
""",
'candle': """
    y
   ywh
   .h
   wec
   wwo
   eec
  Ycecg
  YYYZgG
   gggG
""",
'mug': """
  c
   c
   c
  wwwww
 XwwXXXggG
 XYYYYZGgg
 XYYYYZkkG
 XYYYZZggG
  YZZZG
   ZZZ
""",
}
PARTS = {name: grid_part(0, 0, sketch) for name, sketch in SKETCHES.items()}
