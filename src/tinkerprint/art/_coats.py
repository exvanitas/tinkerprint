"""Coat, feet and tail on one editable grid; dots are clear pixels."""
from ._drawing import grid_part

# The working grip and the near collar determine where the tools register.
POSES = {
    'Interface': ((32, 29), (15, 25)),
    'Logic': ((31, 28), (17, 24)),
    'Infra': ((32, 32), (13, 26)),
    'Tools': ((32, 32), (14, 28)),
    'Data': ((31, 28), (15, 24)),
    'Models': ((32, 27), (17, 24)),
    'Tests': ((33, 28), (14, 25)),
    'Docs': ((32, 30), (15, 26)),
    'Systems': ((32, 32), (13, 27)),
    'Art': ((31, 30), (15, 25)),
    'Worlds': ((32, 29), (15, 26)),
    'Lore': ((31, 28), (15, 24)),
    'Community': ((32, 32), (13, 28)),
}

PARTS = {
    'interface-coat': grid_part(4, 21, """
.................CCCCC
............CCCCBBBBeee
............AAAooeeeeeeC
...........CAAAooooeeeeC
...........AAAAooooeeeeCC
...........AAABooooeeeCCCC
..........AAAABBoooeeeCCC
..OOOO....AAABBBooooeeCC
.O.aaa...AAABBBBooooeeCC
O.a......ABBBBBBBogggeC
Oa.......PBBBBBBBBgggC
Oa.......BBBBBBBBBeoCCCPPPP
Oa......PBBBBBBBCCCCCCCPPPP
Oa......BBBBBBBCCCCCCCCCPP
.Oa....CBBBBBCCCCC.CCCCCCP
..OaaaCBBBBBCCCC....CCCCCa
...OOOCBBBCCCCC......CCCCC
.....CBBCCCCCCP......llll
....CCCCCCCCLLPP....PllllP
...CCCCCPPPPPPPP....PPlllllP
....................POOOOOOPP
....................PPPPPPPPP
"""),
    'logic-coat': grid_part(8, 21, """
..........CCCC
..........BBAACeeee
.........CAAABBeeee
.........BAAABFeeeeC
........CAAAFFFeeeeC
........CAAFFFFeeeeCC
.......CAAAFFFBeeeeCC
.......CAAAFFFBeeeCC
......CAAAFFFFBeeeCC
......CAABFFFFBeeeC
.....CABBBFFFFeeeeCPPPP
.....CBBBBFFFFeeeeCPPPP
....CCBBBFFFFBeeeeCCPP
....CBBBBFFFFBeggCCCPP
...CCBBBBFFFFegeeCCCCa
...CBBBBBFFFBeeeBCCCCP
..CBBBBBFFFBBeeeBCCCCC
.CCBBBBBFCCCCCeBBCCCCC
.CBBBCCCCCCCCCCCCCCCCCCP
CCCCCCPLLOOOPCCCCCCCCCCPP
.....PLLLLLLPP..PPPPPPPPP
.....PPPPPPPPP
"""),
    'infra-coat': grid_part(8, 22, """
.....CCCCCCCCCCCCC
.....CAAAAAAAAAAACCC
....CAMMMAAAAAAABBCCCC
....MmmmMMMAAAABBBBBCCCC
...mmMMMMMBBBBBBBBBBBCCC
...MMMMMMMBBBBBBBBBBCCCC
..MMMMMMMBBBBBBBBBBBCCCCC
..MMMMMMMBBBBBBBBBBCCCCCC
.MMMMBBBBBBBBBnnnnBCCCCCC
..BBBBBBnnssgggssnnCCCCCC
.CCCssssssnngggnnnnCCCCC
.CCCnnnnnnnnnnnnnnnnCCP
.CCnnnnnnnnnnnnnnnCCPP
.CCnnnssssCCCCCCCCCCCP
CCCsssCCCCCCCCCCCCCCCa
CCCCCCC.....CCCCCCCCCC
CCCLLL...........lCCCC
.PLLLLP.........PllllP
.PPLLOOOP.......PPlllllP
.PLLLLLLPP......POOOOOOPP
.PPPPPPPPP......PPPPPPPPP
"""),
    'tools-coat': grid_part(3, 24, """
............CCCCCCCCCCC
...........CBAAABllllCCC
..........CAAAlllllllBCCCC
..........CAAAlllllllBBCCCC
.........CAAAAlllllmllnBCCC
.......LCBAAAllllllmllnBCCC
.....LLLCAAAAlllllmllnBBCCC
...LLLLLCAAAAllaaaaaaOBCCC
..LLLOOCAAABBllOOOOOOOlCCCPPP
..LOOOlCCBBBllOOOOOOOOOCCCPPP
.LLOOlOCCBBBllOOOOOOOOOlCCPP
.LOOlOOCCBBlllllOOOOOOOlCCPP
LLOloolCCBBllllllllllllllCaa
LOlOOlCCCBlllllllllllllllCCP
.LLOOLCCCCCCClllllllllllCCC
.LLLLLCCCCLLLLP.CCllllCCCCCP
..LLLLL..PPLLOOOP.....PPlllllP
.........PLLLLLLPP....POOOOOOPP
.........PPPPPPPPP....PPPPPPPPP
"""),
    'data-coat': grid_part(4, 21, """
.............CCCCCCCCC
.............CBAAABBCCC
............CAAAABBBCCC
...........oOOAAABBBCCCC
...........CoOOABBBBCCCC
...........CAoOOBBBBCCCCC
...........AAAoOOBBBCCCC
.........uCAAABgPgBBCCCC
.......uuuAABBBgggOBCCC
......uuuCBBBBBBOoOOCCC
.....uuuuBBBBBBBBOoOOOOO
....uuuuCBBBBBBCCCOaaaaO
...JuuuJBBBBBCCC.COOOOOOO
..JuuJJBBBBBCCC...OOOOOOO
..uJJJCBBBCCCC....OOOOOOCC
.JJJJCBBCCCCL.......OOLL
JJ...CCCCCCGL........oLL
....CCCCCCGGG.......LoL
........GGLLLGGG....LoL
.......LL.....LLL..Looo
..................ooLLLooo
.................LL.....LLL
"""),
    'models-coat': grid_part(3, 14, """
  888
 877778
 78666778
 876556778
  765885677
  765gg856678
  765gg8566777
   765556677776  CCCCCC
   76666677766CCAAABBBCCC
    766777766CCAAABBggCCCC
     7677666CCAAABBBgCCCCCC
      76666CCAAABBBgCCCCCCC
       7666CAAABBBBgCCCCCC
        566CAABBBBggCCCCCC
       6676CAABBBgygCCCC
     677866ABBBBBBggCCCCC
   67788866ABBBBBBBCCCCCCC
   6788776CBBBBBBBBBCCCCC
   677766CBBABBCCCBBBBCCC
    7666CCBAABCCCCCBBBBCCC
    766CCBBABBCCFCCCCBBCCCC
     5CCBBABBCCFCCCCCCBBBCCC
       CBBBBCFFC  CCCFCCBBCC
        CBCCCFF    CCFFC
          88g       88g
         67G         67G
        65            65
"""),
    'tests-coat': grid_part(3, 21, """
..................CCCCC
.............CBBAAACCCCC
.............CAAAABBCCCCC
............oOOAAABBBCCCC
e...........CoOOABBBBCCCCC
eee.........CAoOOBBBBBCCC
eeee.......CAABoOOBBBBCC
eeee.......CBBBBgPgOBCCC
eeeeeR.....CBBBBgggOOCC
eeeeeRRRRRCBBBBBBBOoOO
ReehhhhhRRCBBBBBCCCOoOO
.RehhhhhhCfffBBCCCCCOoOOPPPPP
.RRRhhhhhMffBCCCCCCCCOOCPPPPP
..RRRhhhMffBCCCCCCCCCCCCPPPP
...RRRRMffBCCCCCC.....CCCPPP
.....RMffCCCCCC........Paaaa
.....MffCCCCC..........PlllP
....MffCCOOOP..........llll
...MfPLLLLLLPP........PllllP
..f..PPPPPPPPP........PPlllllP
......................POOOOOOPP
......................PPPPPPPPP
"""),
    'docs-coat': grid_part(8, 22, """
         CCCCCCCC
       CBBAAABBBCCC
     CCBAAAABBBCFCCCC
    CCBAAAABBBCCFAABCC
   CCBBaaaaaaaCCCFAABCC
  CBBaoooooollaCCCFABCCC
 CCaoooollLlooaaCCFABCCC
 CoooollLooOOOlaCCFABC
 ooollLooOOOolaaCCFABC
 oolLooOloOooCBBCCFABC
 ollOollOOOCCBBBCCFABC
 olOOllOOCBBBBBBCCFABC
 OlOOOOCBBBBBBBBCCFABCC
 OOOCBBBBBBBBBBCCCFAABCC
 OCCBBBBBBBBBCCCCCggggCC
  CCCCCCCCCCCCCCggGCCCCC
      CCCCCCCCCCCCCCC
      Ggg     CCooo
    oggOOgg    oOOOooo
   OO     OO  OO    OOO
"""),
    'systems-coat': grid_part(6, 17, """
.oooooo
.oooooo
..OOOO
..OOOOnn
..OOOOnnn
..OOOOnnnnn
.nOOOOnnnnnn
.nnnnnnnnCCCCCCCCCCC
nnMMMMMnCoOOABBBBBCCC
nnMMMMMnAAoOOBBBBBCCCCC
gggggggCAAAoOOBBBBBCCCCC
GGGGGGCAAAAAoOOBBBBCCCCCC
nnMMMMCAAAAABogPgBBBCCCCC
.nMMMCBAAAABBBgggOBBCCCCC
.nMMMCAAAAABBBBOoOOBCCCC
.nMMMCAAABBBBBBBOoOOCCCCPP
.nnnnCBOOOOOOOggggOOOCCCPP
.nnnnCBOOOOOOOgLLgOOOOCCP
...nCCBOOOOOOOggggOOOCCCC
....CCBBBBBBBBBBBBCCCCCCC
....CCCCCCCCBBBBBBCCCCCCCC
....CCCCLL..CCCCCCCCCCCCCC
.....PLLLLP....CCCCCClllP
.....PPLLOOOP......PPlllllP
.....PLLLLLLPP.....POOOOOOPP
.....PPPPPPPPP.....PPPPPPPPP
"""),
    'art-coat': grid_part(4, 20, """
.............CCCC
.............CCCCCCCC
Po..........CBAAABBBBC
.Po.........AAAABeeeeCC
..o........AAAAABeeeeCCC
..Po.......AAAABeeeeBCCCC
..Po......AAAAABeeeeCCCC
..Po......AAAABeeeeeCCC
..ll.....AAABBBeeeeeCC
..Po.....CBBBBeeeeeeeC
..Po....CBBBBBebbbeeeCC
..Po....CBBBBeebbbeeeeC
..P.o..CCBBBBeeeeeeeeeCCPP
...Po..CCBBBeeeeeeppeeeCPP
...P.o.CBBBBeeeeeeppeeeCP
....PPoCBBBeeeeeeeeeeeCCC
......CCCCCCCCCCeeeeCCCCC
......CCCCLLL...CCCCCCllP
........PLLLLP......llll
........PPLLOOOP...PllllP
........PLLLLLLPP..PPlllllP
........PPPPPPPPP..POOOOOOPP
...................PPPPPPPPP
"""),
    'worlds-coat': grid_part(11, 22, """
...AAAAAAAAAAAC
..AAAAAAAAAAAAAC
..AAAAAAAAAAAAACC
.AAAAoOOAAABBCAAC
AAA.AAoOOABBBBCCCC
...AAAAoOOBBBBCCCCC
...AAAABoOOBBBCCCC
..AAABBBBgPgOBCCC
...BBBBBBgggOOCCC
..CBBBBBBBBOoOOC
..CBBBBBBBCClllllOO
..BBBBBBBCCClllllOO
.CBBBBBCCCCllllllO
.BBBBCCCCCCllllllC
.BBCCCCCCCC.lllllC
CCCCCO.CCCC..llOOO
CCOOOO...C...OOOdd
.OOOdd.......Oddddd
.Oddddd......dddLdd
.dddLdd.....dddddddd
dddddddd
"""),
    'lore-coat': grid_part(5, 19, """
.............CCC
.............CCCCCCC
............BBAABBCCC
............AAAABBCFFC
...........BAAABBBFFFCC
...........gAAABBBFFFCCC
..........BAgABBBBFFgCC
..........AAAggBBBggCCC
.........BAAABBgggFFCC
.........AABBBBBBFFFCC
........CBBBBBBBBFFFC
.......fCBBBBBBCCFFFC
.....fffBBBBBBCCCFFFC
...ffffCBBBBBBCCCFFFCC
.fffffNCBBBBBCCCCFFFFC
ff.ffNfCBBBBBCCCFFFFFCC
..ffNffCBBBBBCCCFFFFFCC
..fNfffBBBBBBCCCFFFFFCCC
.fffffCBBBBBCCCCFFFCCCCC
.ffff.CBBBBBCCCCCCCCCCCCC
ff....CCCCCCCCCCCCooo.CCC
.......LGGGCCCCCooLLLooo
......GGLLLGGG.LL.....LLL
.....LL.....LLL
"""),
    'community-coat': grid_part(5, 23, """
           oo
      o   aall LCCCCCC
      lo ooolLCCCAABBCC
     allolllLCCAAAABBBCCC
      lloolLCCAAAAgcceeeBCC
     alllOLCCAABBggceeeeCCCC
      lOOLCCABBBGcceeeecBCCCC
       LCCBBBBBgceceeeeccBCCCCC
      CCCBBBBBgceccceecccBBCCC
     CCAABBBBCeecccccccccBBCCC
    CCABBBBBCceeggggGeecccBCC
    CCBBBBCccceegoooGececccCCC
   CCAABBcceeecceOLLcececcccCCC
   CCBBBcccccceeeecccececcccCCC
   CCBBBccrrccrrccrrccrrcccCCCC
    CCCCcrrrcrrrcrrrcrrrccCCCC
      CCCcccccccccccccccCCCC
        CCCCCCCCCCCCCCCCl
          PLLPPPPP  Plllool
         LOllooOOP  Plloooool
        LLOOOOOOOP  PPllOOOOOP
"""),
    'traveler-coat': grid_part(8, 22, """
..........CCCCCCCCC
........JJAAAABBBCCC
......JJjCAAABBBBCCC
....JJjjjoOOABBBBCCCC
..JJJjjjjAoOOBBBBBCCC
.JJJjjjjCAAoOOBBBBCCCC
.JJjjjjjAAABoOOBBBCCC
.JJjjjjjABBBBgPgBBCC
JJJjjjjjBBBBBgggOCCC
JJJjjjjCBBBBBBOoOOC
JJJjjjjCBBBBBBBOoOOPPPPP
.JJjjjJBBBBBBBBBOoOOPPPP
.JJJJJCBBBBBBBBCCOOCPPP
..JJJJCCCCCBBBBCCCCCCPP
...JJJJPCCCCCCCCCCCCCaa
.......LLLL.CCCCC.PlllP
......PLLLLP......llll
......PPLLOOOP...PllllP
......PLLLLLLPP..PPlllllP
......PPPPPPPPP..POOOOOOPP
.................PPPPPPPPP
"""),
}
