"""Hand-cut portraits. @ + : ~ are the four shared face inks, light to dark.

The other marks are pelage, feathers, shell, headwear, eyes and noses. Each
sketch is a single layer so a face can be edited at its actual pixel size.
"""
from ._drawing import grid_part

PARTS = {
    # Mouse illusionist, caught just before the reveal.
    'interface-head': grid_part(7, 4, """
      ssss
    smmmmss       sss
   sm@@++@ss    smmMMs
  sm@+++++:Ms  sm@++:M
  s@+++::::Ms  sm++:MM
  s@++:::::Ms  s:::MM
   MM:::::MM  BBCCMM
    MMMMMMABBBBBBCC
      AAABBBBBBBBBCCC
    AAABBBBBBBBCCCCCCF
   BBBBBBBCCgggggGFFFF
   FCCCggggGMMMMMss
      MMMMMMsssmmmMM
      MMMssssm@@++MMM
     MMsssssmm@wkk+sM
     MMMssssmm+kkk++sM
      MMMsssmmm::+++++sMM
       MMMssssmm@@@++@@qq
       nMMMMsssm@@++Pkk
         nMMMMMss++PP
           nnnMMMMM
"""),
    # Hare logician, one ear cocked and one listening ahead.
    'logic-head': grid_part(8, 2, """
               aa
              a@@a
        ooo   a++a
     ooa@@@oo a++:o
   oa@@+++:oooa++:o
   o++:o   oooa+::l
    oo       oa+:l
             oa+:l
            oaaao
          ooaaaool
         aaaaaaaool
       aa@@@@@aaaoo
      aa@@@@++++++ol
      a@@@+++~~P++:o
     aa@@++++@@kk++:o
     a@@++::+wwkk+++o
     aa++:::+++@+++++o
     oo+++@@@@++++++qq
     ooo++@@@@@+++PP9
      ooo+++@@+++PP
       lloooo+++::o
       AABBBBBBgG
     AAABBBCCggG
   ABBBCC  gG
"""),
    # Badger warden. Two diagonal mask stripes run up to the brim of the sallet.
    'infra-head': grid_part(8, 6, """
              mm
       mm    mM
     mMMNs  mMN    sm
     mNkkN mMMN   skkm
     MNkkNmmmMNNNmkkkM
      NmmmmMMMNNNNkkM
     mmmmMMNNNNnnnNN
    mmMMMMNNNNnnnf
     gggggGGGGGMMM
     mmmmmmmmmkkNNn
    mmmmmMkkkkkkmmMN
    mmmMkkkk@@kkkmmMN
   mmmMkkkk@wkkk++mmMN
   mMMkkkdd+wkk:+++mmMN
   MMkkddd::+++++@@@mmNk
   Nkkd:::+++++@@@mmmmkk
   Nd::+++@@@@@@mmmmkk
    N::++@@@mmmmmNNn
    NNNNmmmmmmNNnn
      nNNNNNNn
"""),
    # Beaver smith. Goggles sit above the brow and the square incisors clear the lip.
    'tools-head': grid_part(9, 8, """
       ooo         oo
     oa@@@ao     oa@@o
     oa+++aooooooa+:oo
      oooaaaoaaaaooool
       GggggGGGggggGl
     GggzzzgGGgzzzgGll
    GgzwbbzgGgzwbbzgGo
    GgzbuujgGgzbuujgGl
     GgbujjGGGgbujjGl
      GGGGGoooGGGGGl
     lloooaa@@++~++ol
     lloaaa@@++kk++:l
     looaaa@@+wkk+++ol
     Olooaa@@++++@@@@@P
      lloaaa++++@@@@:Pk
       Ooooo++++@@++Pl
        OOooooPwwOww
          OOolllmwOmw
            LLOOomm
"""),
    # Kingfisher surveyor. Long blade bill, swept wing-blue crest, white throat.
    'data-head': grid_part(7, 5, """
            b
         bzzb  b
      bzzzbbbzbb
    zzbbbuubbbuu
  zzbbbuubzbbbuu
    bbuuzzzbbuuu
   uuuuzzzbbuJJJu
    uuubbbbuJkkJJJ
     Ju@@@++@wkkJJJ
      @@++++@wkkJsssM
      ++++++++ssmmmmmmMNN
       +++@@@@@NNNNnnnffffff
      Ooo@@@@@@@o
      oo@@@@@@@oo
     Ooo@@@@++o
     ooo+++::o
      lloooo
        AABBBC
      AABBBCCgG
      BBC  gG
"""),
    # Silkmoth alchemist with comb antennae and large, forward-facing eye patches.
    'models-head': grid_part(7, 2, """
   88                   8
    788               887
   876788           88767
     87678         87678
      87678       87678
     77 6678     8766 77
       77667     76677
          567   765
            67 76
            @@@@
         @@@@++@@@
        @@@@@++@@@@
       @@@@++++++@@@
      @@@555+++555@@
      @@57765+57765@
      @57wkk6+5wkk65
      @57kkk6+5kkk65
      ++5666+++5666+
       +++6+@@++6++
        :++@@@@++:
         ::++++::
           :++:
"""),
    # Fox duelist, chin up; a black ear tip and a flat, intent brow.
    'tests-head': grid_part(7, 4, """
    kk              k
    dkP            dk
    drrP          rrd
    rhrrP        rirr
     hiirP     rriihr
     hiiiPrrrrriiihR
      hiihhiiihhhhRR
      rihhiiiihhhrrR
      rhhiiihhhhhhrr
     OhiiiihhrrhhhhhR
     hhiiihPPPrhhPPhR
    Ohiihh@@@kkh+kkRo
    Ohhhhh@@wkk++wk+o
   hhiiiih@@@+++h+++:o
    rriih++@@@@++@@@@@k
     hh++@@@@@@+++@@@k
     +@@@@@+++++++PP
       +@@@@++++P
        ::++++P
          :++
"""),
    # Owl scribe looks up over half-moon spectacle frames.
    'docs-head': grid_part(10, 6, """
          SSSSS
      ccccceeeeS
    ccceeeeeaaSS
   ccaaSSSSoooaaSS
     OOOgggggGGGoo
      a@@@aa@@@@aa
    aa@@@@++@@@@@@aa
   oa@@@@++++++@@@@ao
   a@@++~~+++~PP++@@a
   a@@+@wwk++@wwk+@@a
   a@@++kkk++@kkk+@@a
   oa@g+++gGyG+++g@ao
   oaaggggGygGgggGaol
    oa@@++ygG++@@ao
     oa+++gG::++ao
      oo+++++++oo
      lloo+++ool
        OOOOO
"""),
    # Ram mechanist. The horn is a single bold spiral behind a lowered brow.
    'systems-head': grid_part(6, 5, """
           ggggg       o
         ggyyyggG     oao
         GgggggGG    oaaol
      oaaaaaaooooooloaaol
    oaaeeeeaaaaaoooolaaol
   aaeeeeeeaaaaoooOooool
  aaeeaaaooooaaaooLooool
  aeeaaoLLLLooaaaoLoooao
 aeeaoLLoooolloaaolaaaaol
 aeaolLoaaaaooloaolaaaaol
 aeaoLloaaaoooloaol@++++o
 aaooLloaoOollloaol@@PPPPl
 oaooLlooooLllooaol@+wwkkl
  oooLLLllLLloooal+@@wkkl
  lloooLLLLloooal+@+++++:o
   llooooooooool+++@@@@++:o
     lllooooool+++++@@@+++P
        Llllll:::+++++++P
           looo::::+++P
             llooooool
"""),
    # Calico painter with a beret pulled over one ear.
    'art-head': grid_part(8, 5, """
    kk              o
    odk            oao
    oaakk        oa++o
    oa+akk      oa++:o
   AABBBBCCCC  oa+::ol
  AAABBBBBBBCCCoaaaool
 AABBBBBBBBBBCCCooool
  CCBBBBBBgggGGFoooo
    FFFgggGooooooddd
     ooaaooo+++oddkk
    ooaa@@@+++++ddkko
    oaa@@++~P+++dP~ko
    oa@@++@wk+++@wkkko
    o@@+++kkk+++kkkdko
    o@@++@@@@+++@@@++o
     ooo@@@@@@+@@@qP
      oo+++++P+P+++o
       lloo++++++ol
          looooool
"""),
    # Deer gardener. The antler forks leave sky between their branches.
    'worlds-head': grid_part(6, 2, """
      o              o
      o       o     oo
   o  ao     oo     o  o
   oo oo     o     oo oo
    oo ao  oo      o oo
      ooao oo   o ooo
        oooo    ooo
          lo   oo
    aa    lo  oo    aa
    o@@a   oooo   a@@o
     o++aaoaoooaa++:o
      oooaa@@@aaaooo
         a@@@@++aol
        a@@@++++++ol
        a@@++~PP~+ol
        a@+++@@kk++o
       oa@++@wkkk+++o
       oa@@++@@+++++o
       oaa@@+++++@@++o
       ooaa+++++@@@@+o
       loo++::::+@@@+k
        lo+:::+++++Pk
         o++++++:o
           oooo
"""),
    # Raven lorekeeper. The near eye and monocle lean down toward the book.
    'lore-head': grid_part(9, 4, """
          s      N
        sMMN   MMN
      sMMMNN MMMN
    sMMMNNNnMMNN
   MMMNNNnnnNNn
    NNNnnnnnNNn
   NNNNNnnnggggg
   nNNNnnngy@@@+g
   nNMMnnng@@@++G
   nMMNnnng@wwkkG
   nNNnnnng++kkkGNN
   fnnnnfffGgggGsssM
    fnnnff@@+:NmmmmMMN
   fnNNnf@@+++:nnMMMMnn
    fnNn@@@++::ffnnnnffk
     fnn++:::Pf    fffk
      fnfff::f       fk
      fNNnff
       fnff
"""),
    # Hedgehog innkeeper. Quills form three large stepped fans around the face.
    'community-head': grid_part(5, 7, """
        a        a
        aal    aal
     o  aool aaooL  a
     oao oooloollL oa
      oaooooloolLOaao
   ao  ooolLolLPoool
   oaaoollPooLPOOaool
    oaaolLPoLPOOooool
  oo oolLPoLPOOllaaaoo
   oooLLPoLPOoa@@@++o
    oLLOllLOoa@@++PP~l
  oooLOllLOoa@@++@++ol
   ooOllLOOoa@@+wwkkoo
    OLLOOlloa@+++kkk+o
   oOOLLOOoa@++++++++o
     OLLOOoa@@++++@@@+o
      lLOOoa@@@@+++@@@+k
        OOOo@@@+PPPPPk
          Ooo++@@++P
             Oooo
"""),
    'traveler-head': grid_part(8, 8, """
          lllll
       loaaaaaaol
      loaaeaaaaaol
     looaaaaoooooll
    ooaaaOOggGGGOollo
  oaaeeeaaaaaaoooooool
    OlooooollllloooL
       jjtttttjj
      jttvvvttttjj
      jtvvvJJJtttjj
      jttt@@@++tttjj
      jtt@@@wkk++ttj
       jt@@+kkk+++tj
       jj@@@++++@@@+j
        jj+++++@@@++J
         Jj:::+++JJJ
           j+++++j
"""),
    'base': grid_part(14, 12, """
      jjtttt
    jjttvvttjj
   jttvvvtttttj
  jttvvvJJJtttjj
  jttt@@@++tttjj
  jtt@@@wkk++ttj
   jt@@+kkk+++tj
   jj@@@++++@@@+j
    jj+++++@@@++J
     Jj:::+++JJJ
       j+++++j
"""),
}
