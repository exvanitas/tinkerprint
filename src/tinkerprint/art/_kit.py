"""Guild equipment. Hand tools register to (32, 29); shoulder gear is local to the collar."""
from ._drawing import grid_part

# The broad pavise and open codex obscure the hand that holds them.
ITEMS = {
    'fan': grid_part(27, 16, """
       XXXX
  XXXX XwwXZ
  XwwXZwYYwZ
  XwwXZwYYwZ
  XYYXZwwwwZ   ZZ
  XYYXZwYYwZ  ZwwZ
  XwwYZXwwYZ ZwwXY
  XwwYYXwYYZZwXXY
   XwYYYYYZZwwXY
   XwwYYZZZwwYY
   XYwwYZwwXYY
    XYYYYwXYY
    gYYZXXXZ
     yggGZ
      gG
"""),
    'orrery': grid_part(28, 6, """
.........gg
.......ggyyGG
......gG.ZZ.GG
.....gg.XXXX.GG
.....g.XwXXYY.G
.....G.XXYYYZ.G
......G.YYZZ.G
.......GGZZ.G
........GggG
.........gg
.........oL
.........oL
........oL
........oL
.......gL
.......gL
......goL
......gL
.....goL
......oL
.....oL
.....oL
....oL
....oL
....oL
...oL
...oL
...oL
..oL
..oL
.oL
.oL
.oL
oL
oL
"""),
    'pavise': grid_part(28, 21, """
        wwwmm
      wwmXXMMMn
    wwmXXXXYYMn
  wwmXXXXYYYYMn
 wmXXXXYYggYYMn
 mXXXwwYYggYYMn
 mXXwwwggyygYMn
 mXYwwggyyggYMn
  mYYggyyggYYMn
  mYYYgggYYYYn
  mYYYYggYYYMn
   mYYYYZYYMn
   mYYZZZYYn
    mYZZZYn
    mYZZYn
     mYYn
      mn
""", cover=True),
    'spanner': grid_part(28, 12, """
          mm
        mmm
       mmM      s
       mMN     mM
      mMMn    mMN
      mMMn   MMMn
      mMMNNNNMMN
      mMMMMMMMNn
       NMMMMMNN
       NMMMMMN
       mMMNNNN
      mMMNnn
      mMMNn
     mMMNn
     mMMn
    mMMN
    mMMn
   mXXYn
   XYYn
  XYYZn
  YYYn
 YYZn
  ZZ
"""),
    'scope': grid_part(30, 15, """
............G
..........yGwG
.........gGyGwG
..........gGybG
........GGXgyGbG
.......GGXYgGyGG
......GGXYYYgGG
....GGXXYYYY..G
...GGXYYYYY
..GgXYYYYY
..GXgYYY
...YgYY
.GYYYg
GGYYYG
.GGYGG
.GGGG
..G
"""),
    'censer': grid_part(29, 8, """
            X
       XX  XwX
       XwXYwXY
        XwXXY
      XXYYgg
       XYYgXXX
          YXYY
           XY
         bb
        z
        zb
         bb
         b
       zz
       b
   g        g
   gyyyyyyygG
    GgXXXggG
     GYYZZG
      GggG
       gg
     gggggG
"""),
    'foil': grid_part(28, 10, """
...............w
..............wn
..............wn
.............wn
............nwn
............wnn
...........wnnn
..........nwnM
..........wnMn
.........wnnM
........nwnM
.......nwnMn
.......nwMn
......nwnM
.g...nwnMn
..gg.nwMn
...Gggnn
....GGgg.G
...nYnGGG
...Ynn
..nYn
..Y
..Y
ggg
ggg
"""),
    'quill': grid_part(29, 8, """
             www
            wwXw
           wwXXY
          wwXXYY
         wwXXXYY
        wwXXwXYY
       wwXXwXYY
       wXXwY  Y
      wXXwXYYY
      wXwXYYY
     wwXwXYY
      XwXXY
     wXwXY
     XwXY
     wXY
    owY
    og
   og
   og
  oG
  oG
 oG
 G
"""),
    'key': grid_part(27, 9, """
         gyyg
       gyy  yg
      gy    yg
      gy  gyg  gg
      ggyyyg ggYYg
       ggyggyX  YYg
         GgyY   Yg
        mMggYYYYg
        mM ggGGG
       mMN
       mMN
      mMN
      mMN
     mMN
     mMN
    mMN
    mMN
   mMN
   mMN
  mMMNn
  mMMMMn
 mMMNnMm
 mMN  mm
mMN
"""),
    'washbrush': grid_part(29, 9, """
.........Y..l
.........XY.Y..l
.........XYlYlll
.........XYYYll
........lYYYYll
........llaYYll
........llaYlll
........lalYll
.......mMlllll
.......mMMllll
......mMMMMll
.......MMMMM
.......oLMM
......oL..M
......oL
.....oL
.....oL
....oL
....oL
...oL
...oL
...oL
..oL
..oL
.oL
.oL
oL
oL
"""),
    'sapling': grid_part(29, 8, """
.........YY
........YXY
XXXX....YXY
ZXXXX..YXYY
.ZZXXZYYXYY..YYY
.ZZZZXYXYY.YYYXY
..ZZZZYYY..YXXY
...oZZYY...XYYY
....o.YoL.YYYY
.....o.oL.YY
......oL..O
......ooOO
......oO
.....oO
.....oL
.....gL
.....gL
....gL
....oL
....oL
...oL
...oL
...oL
...oL
...oL
...oL
...oL
..oL
..oL
..oL
..oL
..oL
..oL
"""),
    'codex': grid_part(25, 20, """
                 ZZ
            weeeewZ
         eweeeaaewZ
  www    ewweaooewZ
 wwwwwwe ewewweeewZ
 wweeewwecweaaaeewZ
 ZeooooeccweeooeewZ
 ZeeeweeccweeeweewZ
 .ZeeeeecceeeeeewYZ
 .ZwwwwwecwewwwYYZ
 ..ZYYYYeeweYYYZZ
 ..ZZZZYYeYYYYZ
       ZZYYZww
          Z  w
""", cover=True),
    'teapot': grid_part(26, 19, """
            c
           m
          mm
           m
    ggggg
   gy   gG
   g     gG
   g   ggGg
   G  gywwggG     g
    GgggGGGgg  ggG
    gywXXYYYYg gG
  wwYXwXXYYYZZgg
   yYXXYYggYZZG
   gYYYggYYZZG
    GYYYYYZZG
     GGGggGG
"""),
    'crook': grid_part(30, 10, """
.........ooo
........o..o
.......oo..o
.......oL
......oL
......oG
......GLYYY
......GXwwYG
.....GL.XXYG
.....oL..YZ
.....oL
....oL
....oL
....oL
...oL
...oL
...oL
...oL
..oL
..oL
..oL
..oL
.oL
.oL
.oL
.oL
.oL
.oL
oL
oL
oL
"""),
}

CAPE = grid_part(2, 20, """
.U
.TU.............UU
.TTTU.........UUUUTU
UUTTTTUU....UUUUTTUUUU
UUTTTTTTTTUUUUTTTUUUUU
UUUTTTTTTTTTTTTTTUUUUU
.UUTTTTTTTTTTTTTTUUUUUU
.UUUUTTTTTTTTTTTUUUUUUU
..UUUUUUTTTUUTTUUUUUUUU
..UUUUUVVVVVVTTUUUUUUU
..UUVVVVVVVVTTUUUUUUU
.UVVVVVVVVTTUUWUUUUU
VVVVVVVVTTUUWWUUUU
VVVVVTTTUUWWWUUUU
UVV.TTUUWWWWWUUU
....WWWWWWWWUUU
..WWWWWWWWUUU
..WWWWWWUUU
""")
PACK = grid_part(3,19,"""
    eXXXYYYeYYY
   XwXXYYGGXYYYZ
  XwZZXYgGXYZZYZ
  XYXXZYgGXYZZYZ
  XYZZZYgGXYZZZZ
   ZYYZZGGZZZZZ
    aaaaaolll
   looooloolll
  llooaaloooll
  llooogglooll
  LollogGllolL
  LOOllloooLlL
   LLOOOOOOLL
""")

# A second discipline is visible at the opposite hip as well as in the hand.
# All coordinates below are local to the far shoulder.
GEAR = {
    'logic-gear': grid_part(-8,-1,"""
          XXYY
         XYYYY
        XYYZZ
       XYYZYZ
      XYYZYYZ
     XYYZYYZZ
     XYYYXYYZ
    XYYZgYYZ
   XYYZyyYYZ
  XYYZZgYYZ
 XYYZZYYYZ
XZZZYYZZZ
ZZZZZZ
"""),
    'infra-gear': grid_part(-6,-1,"""
       mmMMM
     mmmXXYYY
   mmXXXXYYYZZ
  mXXYYYYYZZZZ
 mXXYYZZZZZnnn
  mmNNNNnnn
  mmXXXYYZn
   NMMYYZn
   msMMNNn
    MMNnf
    nff
"""),
    'tools-gear': grid_part(-5,0,"""
         XXXg
        XYYg
       XYYg
  m n XYYg
  mmnXYYg
  .nMYYg
  lnMMYgg
 ooooXYYG
 lollXXXG
 loLloOOG
 lllLgglL
 LOllGGlL
 .LOlllL
"""),
    'data-gear': grid_part(-7,-2,"""
        ccwwa
       eeeaao
       eaaoGO
      eaGYZg
      aGYZY
     aGYZYG
     GXYZY
    aXYZYG
   aXYZYG
   XYgYGG
  aooYO
 eewao
 eaeao
  ooO
"""),
    'models-gear': grid_part(-8,-2,"""
     XX    XX
     XwX.XXYY
      XwXYYZ
    XXXwwYZ
   XXwXXYYZZ
  XwXXYYZYZ
   XYYZZYZZ
    ZZYYZZ
    YXYYZ
   XwYYZ
   YYZZ
  YYZ
  YZ
"""),
    'tests-gear': grid_part(-9,2,"""
          XXYYY
          XwYYZ
          XYYZZgg
         XXZYZ
        XYYZY
       XYYZZZ
     XXYYZYZ
  XXXYYYZZYZ
 XXYYZZZ.YZ
XZZZZZ  ZZ
"""),
    'docs-gear': grid_part(-6,0,"""
        a   ee
      c ca ewa
      ee caeo
      ewaeea.
      oeeea
     gXXYYg
     XYYYZ
    XYYYZO
    XYYYZO
   gYYYZO
   XXYZG
  oaoZGG
  aaoOG
   OO
"""),
    'systems-gear': grid_part(-8,-2,"""
     mm  MM
   mmNNnnMN
   mM.gggn.N
   nggyyygNN
  gyyg..gGNN
  gyg..ggG
  GggggGG
   GGgGNN
     nMMN
      NGGGg
      gYYggG
      GYYZG
       GGG
"""),
    'art-gear': grid_part(-6,-1,"""
     m    r
     mN .jr
    .mN jo
     oo o
   oooaaoo
  oaaeeeaoo
 oaXXeaaaGoo
 aXXYeaJJoao
 aeYYojjlooO
 oeeoooloolO
  oaapploOl
   oaqplol
    oolll
"""),
    'worlds-gear': grid_part(-7,-2,"""
         XX
     X  XwY
     XX XYY
     XwXYZZ
  XX .XXZYXX
  XwXXYYZYYX
   XXYYZZYY
    YYZZZZ
  XXZXXYZ
 XXYXXYYZ
 XYYZYYZ
 YZZZZZ
 .ZZ
"""),
    'lore-gear': grid_part(-5,0,"""
           oo
         ooO
       ooO
      oO
     oO
  XXXXYZ
 XXXYYYZZ
 XYYggYYZ
 XYYgYYYZ
 XYYYYYYZ
 XZZZZZZZ
  ceeeeao
  ZZZZZZ
"""),
    'community-gear': grid_part(-6,0,"""
       aeeawo
      eeRReao
    aaeeRReao
   eeaeeRReO
   eRReeRRo
  aaeeeeaao
  eeRReeRRo
 aaeRReeRRO
 aeeaaeeaao
 eeRReeRRo
 aaRReeRRo
 .OaaaeeO
"""),
    'interface-gear': grid_part(-8,-1,"""
       XXXXYYY
     XXwXYYYYZ
    XwwXXYYYZZ
   XXYYZYZZZZ
    ZZYYZYZ
     XYYZZZ
    XXYZZZ
   XYYYZZ
 XXYYYZZ
XXYYZZZ
XZZZ
"""),
}

# Sleeves are registered to the neutral grip. Hand and tool move together.
SLEEVES = {
    'ease': grid_part(23,24,"""
  AAAB
 AABBBB
 BBBBBC
  BBBCC  gg
  BBBBBXYGG
   CBBBXXYG
    CCCCYYG
      FFFC
"""),
    'lift': grid_part(24,21,"""
        a
      Xgg
     BXYg
  AABBBYZ
 AABBBBC
  BBBBC
  BBBC
   CC
"""),
    'reach': grid_part(23,24,"""
   AAB
  ABBBB
  BBBBC     gg
   BBBBBBXYYgg
    CBBBBBXXYG
     CCCCCYYG
       FFFC
"""),
    'read': grid_part(23,24,"""
  AABB
  ABBB  Xg
  BBBBBXYg
   BBBBXYg
   CCCCCZ
    FFFC
"""),
    'idle': grid_part(22,25,"""
  AABB
 ABBBB
  BBBB
  BBCC
  BBCC
  BYYZ
   ggg
   +@@
   :++
"""),
}

for tool, pose, walk in (
    ('fan','lift',(0,-6)), ('orrery','ease',(0,0)), ('pavise','ease',(0,0)),
    ('spanner','ease',(0,0)), ('scope','lift',(-1,-6)), ('censer','reach',(2,-1)),
    ('foil','reach',(1,-1)), ('quill','ease',(0,0)), ('key','ease',(0,0)),
    ('washbrush','lift',(0,-5)), ('sapling','ease',(0,0)), ('codex','read',(-3,-2)),
    ('teapot','reach',(1,-1)), ('crook','ease',(0,0)),
):
    ITEMS[tool].update(sleeve=pose, offset=list(walk))
