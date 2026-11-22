"""Equipment for the night shift. Tool sketches use the closed hand as their origin."""
from ._drawing import Drawing, grid_part

HAND = grid_part(30, 27, """
  @+
 @@+:
@+:::
 ++@:
  :~
""",seam=True)


def tool(x, y, sketch, pose='level', *, fingers=None):
    d = Drawing()
    d.grid(32+x, 29+y, sketch)
    if fingers:
        dx,dy,rows = fingers
        d.grid(32+dx,29+dy,rows)
    return d.part(seam=True, sleeve=pose, offset=list(WRISTS[pose]), cover=bool(fingers))


# Hand position relative to the reference grip at (32, 29). Moving the cuff and
# the item by the same vector keeps the fingers closed on every costume.
WRISTS = {'level': (0,0), 'raise': (0,-3), 'offer': (1,-1), 'carry': (0,2), 'read': (0,0)}
ITEMS = {
    # Three fanned pasteboards, each bounded by its own dark edge.
    'fan': tool(-1,-13,"""
       weee
    weewwwc
   weewwrrc
   wrrwwrrc
  weRRwweec
  weeewweec
  wwwewweec
  wRRweeec
  wrrweec
   weeec
   weeZ
   wgG
  ggG
  gG
""",'raise'),
    # Brass sighting ring with an axle and a tilted rule.
    'orrery': tool(-2,-21,"""
       gyyg
     gyyeeygG
    gyG    GgG
    yG    gcgG
    yG   gG gG
    yg  yG  gG
    GggyG  gG
     GggggyG
       GggG
        yG
       yg
       gl
      og
      oO
     lo
     ol
    oo
    ol
   oo
   ol
  aol
  oO
  oO
 oo
 oO
ol
oL
"""),
    # Small kite shield in three-quarter view. The hand wraps the inner rim.
    'pavise': tool(-1,-8,"""
       s
    mmmMNN
  mmsMMXMMN
 mMMMXYYYMn
 MMmXXYYYMn
 MmmXggYYMn
 MmXXggYYMn
 MMXYyyyyYn
 NMMXggYYYn
 nMYYggYYNn
 nMYYYYYYN
  MYYYYZNn
  nYYYYZN
   MYYZNn
   nYYZn
    nYZn
     nZn
      n
""",'offer',fingers=(-2,-1,'@@+\n:+:+\n ::~')),
    'spanner': tool(-4,-16,"""
       mm
     mmM       m
    mmMN      mN
    mMMn     mMN
    mMMN    mMNn
    mMMNNnnMMMN
     mMMMMMMNn
      MMMMMNn
      mMNNn
     mMNn
     mMNn
    mMNn
    mMn
   mMNn
   mMN
   XYYn
   XYZn
  XYYn
  YYZn
  YZn
  gZn
   Z
"""),
    # A storm lantern swings below a solid arched bail.
    'lantern': tool(-1,-2,"""
 ggG
 g  ggg
 G    gG
 G    oG
  gggoG
   ggg
 GgyyygG
ggGGGGGGg
  goaaoG
  gewwoG
  gewwoG
  geeyoG
  gyygoG
  GooooG
 GggyyggG
  GGGGGG
""",'raise',fingers=(-2,-1,'@@+\n:+:+\n :~')),
    # A thin steel foil above a brass bell guard and bowed knuckle guard.
    'foil': tool(-3,-18,"""
             m
             m
            mN
            mN
           mN
           mN
          mN
          mN
         mN
         mN
        mN
        mN
       mN
       mN
      mN
    gyygg
   yyygggG
   GGGggGG
    aO   g
   oO    g
   oL   gG
  oO   gG
  yggggG
  gG
""",'offer'),
    # Posted fountain pen. Its clipped cap sits above the hand and its split
    # nib points down past the fingers, in a writing grip.
    'nib': tool(-4,-15,"""
          mm
         mMN
        gyyG
        gnnf
       yMnnd
       gMnfd
       gMnfd
      ggMnf
       mnfd
       mnfd
      mMnd
      mnfd
      nnd
     mMnd
     nnd
    gyyG
    ggG
   eygG
  ewydG
  wyddG
  wyfg
 wydg
 eyf
 mf
 f
""",'offer'),
    # An oversize winding key. Open bow, solid shank and two cut teeth.
    'key': tool(-2,-16,"""
       gyyyg
     gywwyyggG
    gywg   gygG
    yyg     ygG
    yyG     ygG
    gyG    gygG
     ggg  gggG
      gyyyygG
       gggGG
       gyG
      gyG
      yg
     gyG
     yg
    gyG
    yg
   gyG
   yg
  gygggG
  yggggG
 gyG  gG
 gG
"""),
    'washbrush': tool(-2,-15,"""
         rrr
        riirrr
       riiirrrr
      riiihrrrR
      llaaohhRR
     llaaooolR
     Gllooool
     mMllool
    mmMMlll
    mMMNNN
     MMNn
     ogG
    aoL
    ol
   aoL
   ol
  aoL
  ol
 ol
 oL
oL
""",'raise'),
    'spade': tool(-2,-17,"""
          mm
        mmmMN
       mmMMMNn
       mMMmMNN
      mMMmMMNn
      mMmMMNnn
      MMmMMNn
      nMMNnn
       goG
      aoL
      ol
     aoL
     ol
    aoL
    ol
   aoL
   ol
  aoL
  ol
 aoL
 ol
olo
o ol
 ool
""",'offer'),
    'codex': tool(-2,-10,"""
  ccc     cc
 wwweec ceeeww
 weeeeecweeeacZ
 weOOeccweOoacZ
 weeeeecweeeacZ
 weoooecweooacZ
 ZeeeeeccweaacZ
 ZeeaaeccweaaYZ
  ZYeeeeceeeYZ
   ZZYYeccYYZ
      ZZggZZ
""",'read',fingers=(-2,-1,' @+\n@++::\n +:~~')),
    'teapot': tool(-3,-7,"""
        yG
      gywyg
    GggggggG
  ggggoeeoog
 gG gyaeeaayG  g
 gG gyweeaaoG gy
 gG gyweeaaoGgyG
  gggyaeaaogggG
   GgyooooogG
     GgggggG
      GGGGG
""",'carry',fingers=(-2,-1,'@++\n:+:+\n ::~')),
    'crook': tool(-2,-17,"""
        aao
       aoool
      aoL oO
      ol  oL
     ao   O
     ol
     og
     gG
    ao
    ol
    ol
   ao
   ol
   ol
   ol
  ao
  ol
  ol
  ol
 ao
 ol
 ol
 ol
ao
oL
oL
oL
"""),
}

def spyglass():
    """A pocket telescope carried across the palm, with the eyepiece left exposed."""
    d = Drawing()
    # Brass drawtubes step from a narrow ocular to the wide, leather-clad objective.
    d.shape('G',(22,32),(32,27),(34,30),(23,35))
    d.line('y',(22,32),(32,27))
    d.grid(21,32,'mG\nmgG\n nG')
    d.shape('o',(28,28),(36,24),(38,27),(30,31))
    d.line('e',(28,28),(36,24))
    d.line('G',(29,30),(37,26))
    d.shape('J',(33,25),(39,22),(42,26),(36,29))
    d.shape('u',(33,25),(39,22),(40,24),(35,27))
    d.line('z',(34,25),(39,23))
    d.line('g',(33,25),(35,29))
    # The rim rises above the tube. The convex face of the lens looks to the right.
    d.grid(37,19,'  yg\n gyGb\n gyGzb\n  yg4b\n  gyGzb\n   ygub\n   GgGu\n    GG')
    d.grid(30,28,'  @+\n@++:+\n :+~')
    return d.part(seam=True, sleeve='level', offset=list(WRISTS['level']), cover=True)


ITEMS['scope'] = spyglass()

# Model each sleeve as a bent cylinder with the fold at the elbow and a contrasting cuff.
def sleeve(pose, shift):
    d = Drawing()
    wx,wy = 32+shift[0],29+shift[1]
    elbow = {'raise': (27,29), 'offer': (28,30), 'carry': (27,32),
             'level': (27,31), 'read': (28,31)}[pose]
    ex,ey = elbow
    d.shape('C',(23,23),(26,23),(27,25),(ex+1,ey-2),(wx-2,wy-2),
            (wx,wy),(ex+1,ey+1),(ex-2,ey+1),(24,ey-2),(23,26))
    # Small shoulder cap, then the gathered upper sleeve, then the colored cuff.
    d.shape('B',(23,24),(25,23),(26,24),(27,27),(ex,ey-1),(ex-2,ey),(24,ey-2))
    d.line('A',(23,25),(24,24),(26,24))
    d.line('C',(24,26),(25,26),(27,25))
    d.line('A',(25,27),(26,28))
    d.shape('Z',(ex-1,ey-1),(wx-2,wy-2),(wx-1,wy),(ex+1,ey+1))
    d.shape('Y',(ex,ey-2),(wx-2,wy-2),(wx-2,wy),(ex+1,ey))
    d.line('X',(wx-3,wy-2),(wx-2,wy))
    return d.part(seam=True)


SLEEVES = {p: sleeve(p,shift) for p,shift in WRISTS.items()}
SLEEVES['idle'] = grid_part(23,24,' AAB\n ABBBC\n BBCBC\n  BBC\n  agG\n  @+:\n  :+:',seam=True)

CAPE = grid_part(3,21,"""
                 TT
            TTTTTUUU
  T       TTTTTUUUUU
 TTTT   TTTTTUUUUUUU
 UTTTTTTTTTUUUUUUUUU
  UTTTTTTUUUUUUUUUU
   UUUUUUUUUVVVVUUU
   UUUVVVVVVVWWUUU
  VVVVVVWWWWWUUUU
 VVWWWWWWWUUUUU
 WW    UUUUUUU
       UUUUU
""",seam=True)
PACK = grid_part(6,21,"""
   XXXXXX
  XwwXXXYgG
  XYgYYXYgG
  YYYZZZYgG
   goooGGG
  aooolllO
  oolgoogO
  llLggGLO
  lllllLOL
   LLLLOL
""")

# Equipment for the far shoulder. The first rows are the tie, collar or baldric.
GEAR_SKETCHES = {
    'Interface': """
     XXXYY
    XXYYYY
   XwXYYYZ
  XXYYZZZZ
  YYYYZZZ
   YZYYZ
  XYYZ
 XYYZ
 XYYZ
 YYZ
""",
    'Logic': """
     XXXYYY
    XXYYYYZ
   XYYYYZZ
  XYYZYYZ
  XYYZYYZ
  XYYYYZ
 XYYgYYZ
 XYYYYZ
 YYYZZ
 YYZZ
 ggG
""",
    'Infra': """
    mmM
  smMMNn
 smMMNNn
 mMMNNnf
 MNnnnf
  mMMn
  Nnn
""",
    'Tools': """
     oo
    oO
   oO
   oO
  gygGG
 gYggYG
 lYllYG
 llllOO
 OOOOOG
""",
    'Data': """
     gG
    olG
    oO
   ao
  eccc
 eewwaG
  cgYYG
  XYYZ
 XYYG
 YZZ
""",
    'Models': """
      GG
     og
     g
    oO
   mss
    M
   mXm
  mXYYn
  NYYZn
   nnn
""",
    'Tests': """
     XY
    XYY
   XYYZ
  XYYZ
  gygG
 XgPgG
 YYgG
 YZZ
 ZZ
""",
    'Docs': """
     og
    ol
   go
 m  m
 mN m
 ol o
 gyyg
 YYYG
 YZZG
  ZG
""",
    'Systems': """
     oO
    oO
   oO
  gyyg
 gyG gy
 gG  gG
  gggG
   yg
  yg
  ygg
""",
    'Art': """
     oO
    ol
   oO
  eeao
 ea.eao
 ae.rrol
 beearol
 beejjol
  aoool
""",
    'Worlds': """
     og
    ol
  j v
  tvv
   vj
 v tj
  jjj
  ggg
  YZG
""",
    'Lore': """
     oO
    ol
   oO
  oO
 XXYYZ
 XggYZ
 XYYYZ
 YYYZZ
 eeeao
  ZZZZ
""",
    'Community': """
     ee
    eeeo
   eeeo
  eeRRo
 eeRReo
 eeeeco
 eeRRo
 eRReo
 eccc
""",
}
GEAR = {stat.lower()+'-gear': grid_part(-4,-1,rows,seam=True)
        for stat, rows in GEAR_SKETCHES.items()}
