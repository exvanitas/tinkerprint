"""Little workshop mechanisms and the kettle fire. All stand on a visible base."""
from ._drawing import grid_part

SKETCHES = {
# Brass storm lantern on turned feet. A divided pane surrounds one white flame.
'nightlight': """
      gyyyG
     gy   gG
     yg   oG
      ggggG
       gGg
     gyyyygG
   gyggggggggG
  GGgooooaoGGGG
    gGuuzuLG
    gGuubuoG
    gybuuyJG
    gybuyhJG
    gyuywyJG
    gyhwwyhG
    gGgyygGG
   gyyyyyyggG
   gggGggGGGG
    gG    gG
   GGG    GGG
""",
# A portable typewriter. Rolled sheet, platen, staggered keys and long space bar.
'typewriter': """
      eeewwwww
      weeeeeww
      weNNNaew
      weeeeeeec
      weNNaeeec
   gG meeeeeeec g
  gyyNffffffffffngG
   gnbbbbbbbuun g
     zbbbbbbbbb
    zuJJJJJJJub
   zbmeJmeJmeJub
  zbuJJJJJJJJJub
 zbJmeJmeJmeJmeub
 bbuJJJJJJJJJJuub
 buuuummmmmmuuuub
 uuuuuuuuuuuuuuuJ
   nnn      nnn
""",
# The tilted orbit passes behind the amethyst sphere, then in front of it.
'orrery-mobile': """
           gG
          gyG
      ggggygG
    gyG  yG  gg
   yg  87778  gG
  yg  8ww8777  gG
  yg 8ww877667 gG
  gG 887776667ygG
   gG7777666gyG
    gG6666gyG
     gggyyG
       ggG
       gyg
      gyggG
    gyygGgggG
   GgggG GggGG
""",
# A hand-cranked gramophone. A curved tonearm connects the horn to its cabinet.
'gramophone': """
       gyyg
     gyyewyg
   gyyggywyyG
 gyyyGOGywwyg
  gggOOGgyygg
   GGGgGgyggG
     GGGGggG
        gOG
        gG
     ggggG
    yg
   gG     nnn
   gG  nNMssMNn
  aaaooooooolll   oo
 aeeeeeeaaaaaool  oo
  ollLLLLLLLool   gG
  oLgggggGGLoolGGggG
  lLOyyggGGLlOL
  lLLLLLLLLLLOL
   OOL     LOO
""",
'campfire': """
      loo
    looooollll
    oaaO   l  OOOOOO
    ooO    g
    ooO   gGg
    ooO  g   G
    ooO  omMMn
    ooO mmssMNn
    ooO MNMMnnf
    ooO  Mnnnf
    ooO   fff
    ooO       r
    ooO    h  rh   h
    ooO   rh rhy  rh
    ooO   rhiwyh rhh
   lloo  rhiywwhhhhr
   lLOO rhiywwwwyhr
  lllL  Oorhyyyhrooo
       aeooOrhroOlaool
       oolLOoooooollLO
       LOlL  lloool
                lllO
""",
}
PARTS = {name: grid_part(0, 0, sketch) for name, sketch in SKETCHES.items()}
