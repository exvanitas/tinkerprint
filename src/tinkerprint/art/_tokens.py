"""Cabinet miniatures and the enamel pins awarded for achievements."""
from ._drawing import grid_part

SKETCHES = {
'sunrise': """
      g   y
       y g
    g   yyy
  J   gywwwyg
  jJ gywwwwyyg J
 jzjJ ywwyyygg jJ
 JjJ  gggggGG jtjJ
jztjJzzzzbbbbbJJJ
 JJJuubbbbbzuujjJ
  JJJJJuuuujJJJJ
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
        gyyy
      gywwyyg
     GyyggyygG
     GygGgyygG
      GgggggG
   gyyyggGGo
  gywwyygGGG
 GyyggyygGyyygg
 GygGgyyGwwyyyyg
  GggggGGgggggG
  gyyyyGgGgGggG
  GgGggGyyyyyyG
   GGGG.GggGggG
""",
'ship': """
         j
         ojttj
        aaojj
       aaao
      aaao ee
     aaoao eae
    aaooao eaee
    aaooao eaae
     ooOoo  a
 vvv  oo o      vt
 jtttvvtooovvvtjj
  jvvtjjtjtjttjj
   JjjjjtttttjJ
  zuuJJJJJJJJbbu
    bbbzzbbbu
""",
'signpost': """
      aaal
      llLO
   aoeaaaaol
  oaaaoooooool
   OOllOllllO
      loLO
      loLO
    ooaaaooooo
  oaaoooooool
    OOOlllO
      ooLO
    t lolo  j
  vtjjloLO tj
  jtjjssNsjjjJ
   JnsMNNnnJ
""",
'hive': """
          mw
   .lllo. wm
  ollLOO.Gkg
    l    gg
   gygg
  gyyyygg
  GyggggG
 gywyyyygg
 GggggggGG
 gywwwyyyyg
 GggGddggGG
  gyGkdggg
   GGGGGG
 wm
 mwgk
   gg
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
   iiirrr
  iwwiirrr
  iiiiirrR
  irrrrrRR
   rrRRRR   bb
    R R   bzzzbb
         bwwzzbbb
         bzzbbbbb
    ttt   bbbbuu
   vtvtjj  .uu
  vwwtttjj   u
  ttvttjjj
   jttjjJ
    jJ J
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
     tj  gyy
   vtjjJ gyyyg
  vvvtjJ gyywyG
 ttvvjjJ.gyyyyG
 jtvjjJ G ggggG
 jjJjj Gyg GGG
  JJJ GwyG  G
   . GgyggG
   b  GgGG .Ooo
  zzbb G. Oooao
 bzzbbJ  looaoO
 bwwbbJ lloooO
  bbbJJ llooO
   JJ    LOO
""",
'star': """
    ir     ir
    irrr rrrR
     iirrriR
      irrRR
       ggG
      gwwyg
    gggwygggg
   gywGGyGGyyg
  gywwGyygGyyGG
  GyygGwwgGggGG
   GggGgyGGggG
    GGGyygGGG
      GggG
       GG
""",
'frame': """
   gggg
  gymmmG
 ggmwXXMG
 gXwXYYZG
 gXXYYYZG
  gYYYZG
   gggG
   .oG
   lll
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
      sM
    mmMNN
   smMNNNn
    nMNnNN
   .XYb. n
   XYZ
  XYZ
  YZ
""",
'map': """
     eee
   eeewaG
  eewYeoG
  eYwYYoG
  egYYXoG
 eaaYego
 wwaygo
 eeaoo
  ooO
""",
'flask': """
    oo
   mmss
    mN
   mmYs
  mwXXYN
 mwXXYYZN
 mXYYYZZN
 nYYYZZZn
  NNNNNn
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
   XXYYYY
  XweeeaZ
   ZZZZZZ
  loooooo
 leeeeaaL
  OOOOOOL
 YYYYXXg
 Yeeecag
  ZZZZZZ
""",
'cog': """
    MM
  X MM X
  XXYYMM
 MMYgggNN
MMYgg.YYNN
 MYY..YZn
  nYYYZn
  n ZZ n
    ZZ
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
    w
   .c w
   .w
  eeeee
  XwwYYZgg
  XXXXYYZG
  XYYYZY.G
  XYYYZZG
  .YZZG
""",
}
PARTS = {name: grid_part(0, 0, sketch) for name, sketch in SKETCHES.items()}
