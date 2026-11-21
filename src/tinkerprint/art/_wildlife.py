"""Companions at the window and camp hearth."""
from ._drawing import grid_part

SKETCHES = {
'owl': """
   .lo.          .o
    loo.      .loo
    looooaooaaoooO
    loaeeeeeeaaooO
   loaeeeaeaaaeeaoO
  .oaewwwaaoaewwwea
  oaewwkkweoewkkwwa
  oaewwkkweoewkkwea
  loaaawwagggaweeal
  OloaaaaagGaaaoool
  Oloaooeeaeeeaooll
 .OlooaoaeaaaeaooOl
 OolOoaaeeeeaaolOl
.OOlOlaaeaaeaaloOl
   LOloaaeeaaaOol
     Oloooaooll
     ggG. .ggG
""",
'cat': """
     n.      .n
    .Mnf    .nN
    .MsNNnnnMsN
    .NnnNNNnnnN
    NnssMNMMNsN
    NMzkkMNszkN
    .NMnnssnnMN
     nMsMqpMsn
     .nNMssNn.
     .gggGGGn        nN
    .nNMyNNnnn      nMN
    nNMMsMMMnnn     .nN
   .NMMMsMMNNnNn     nM
   nNnMMsMNnNNnNn   .NN
   nMnnssnMNnnnnNn nMN
   nMnNssnMnnnNnnnNNn
    MMMmsMMnNnnnnnf
   .sMM. mMsNNnNNn
""",
'jelly': """
           .77
        .778887.
      .788888887
     .788ww888877
    .788w887778877
   .78888777767787
   7888877766777877
  .7888wwk777wk7776
  78888wkk777kk7766
  78887788777787766
  67777887778877666
  .668888768887666
    z.77b..77b..z
   zb..bb..bb...zb
   b..zb..zb.....b
   zb.z...b....bz
    z..b..zb...b
       .z..z
""",
'slime': """
          .tvt
        vtvt
      tvvvvttt.
     tvvzvttttt
    tvvwwvtttttj
   tvvwvvtttttttj
  .tvvvtttttjtjttj
  tvvtttwktttwkttj
 .tvtttwkktttkkttj
 tvvtttttvttttvttjj
 vtvtjjttttJJttttjj
 jttjtttttttttttjJ
 .JjjjtjtttttjjJJ
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
