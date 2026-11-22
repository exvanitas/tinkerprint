"""Faces of the night guild. Coordinates in a head are relative to the temple.

The four skin keys are shared by the face, neck, ears and fingers. Hair, beards,
caps and spectacles are independent ink layers, illuminated from the left.
"""
from ._colors import INK
from ._drawing import Drawing

# The ear sits at the left, the nearer eye is the wider of the pair.
FACES = {
    'oval': """
    +++++++
  ++@@@+++++:
  +@@@+++++++:
 :+@@++::+++:+
:++:++PPP++PP:
@+:++wwdk+wdk:
@::++@wk++@k+:
 ::+@@++++@+++:
  ~:+@@+++@@@::
    :++++:::+:
    :+++:~~+:
     ::++++:
       :++:
""",
    'square': """
    ++++++++
   +@@@+++++:
  +@@@+++++++:
 :++@++++++++:
 ::+++ddd++dd:
@+:++wwkk++wk:
++:++@wk+++@k:
 ::+++@@++@@++:
  ~:+++++:@@@::
   :+++++::::
   ::+++~~++:
    :+++++++:
     ~~:::::
""",
    'keen': """
     +++++++
   +@@@@+++++:
  :+@@@++++++:
  ++@@+++++++:
 :++++PPP+++PP
@+:++wwdk++wdk
+:+++@wk+++@k:
 ::++@@+++++@+:
  ~:+++++++:@@+:
   :+++++++::::
    :+++:+~~+:
     ::+++++:
       :++:
""",
    'round': """
     +++++++
   ++@@@+++++:
  ++@@@@++++++:
 :++@@@+++++++:
 :+++PPP+++PP+:
@+:++wwdk++wdk:
+::++@wk+++@k+:
 :::+@@@+++@@++:
  :+++++++:@@@::
   :+++++++::++:
    :++++~~++:
     ::+++++:
       ~::::
""",
    'elder': """
    ++++++++
  :+@@@+++++:
  ++@@+++::++:
 :+@@@++:::++:
 ::+++mmm++mm:
@+:++wwkk++wk:
+:+++@wk+:+@k:
 ::+:@@++++@@+:
  ~:+:++++:@@@+:
   :++@+++::::
   ::++::~++:
    :++++++:
      :::::
""",
}


# Hair sketches sit behind the ear or sweep across the temple. H, S and I
# step from shade to light. Each crown covers the top of the finished cut.
HAIR = {
    'dark': 'dLO', 'copper': 'POh', 'silver': 'fNm',
    'auburn': '9Rl', 'gold': 'Ooe', 'ink': 'kfn', 'pewter': 'dL=',
}

FRINGE = {
    'neutral': """
      IIIIISSS
    IIIISSSSSHH
  SIISSSSSSHH
 ISSSSSSHHH
 ISSSSSH
 SSISH
  ISH
  SH
""",
    'man': """
     IIISSSS
   IISSSSIISS
  ISSSHHIIISHH
 SSSHHH  SHH
 ISSHH
 SSH
""",
    'woman': """
      IIIIISSS
   IIIISSSSSSHH
  IISSSHHIISSHH
 IISSHH   ISSH
 ISSSH     SH
 SISH
 ISSH
  ISH
  SH
""",
}

# Each nape has its own outline. The short cuts expose the ear. The longer
# ones fall to the far shoulder so the front hand and equipment stay clear.
NAPE = {
    'tuck': (-2, 0, """
    IIIISS
   IISSSSH
  IISSSHHH
 ISSSSHH
 ISSHHH
 SSSHH
 SHSHH
  SSHH
   SHH
"""),
    'curl': (-2, 0, """
    ISSSS
  IISSISSH
 IISSSSHHH
  SSHSSHH
 IISHHH
 SSHSHH
  ISSSH
   SHH
"""),
    'crop': (-1, 0, """
    IIISSS
  IISSSSHH
 ISSSHHH
 SSSHHH
  SSHH
   SH
"""),
    'bob': (-4, 0, """
     IIISSSS
   IISSISSSHH
  IISSISSSSHH
  ISSISSSHHH
 ISSISSSHHHH
 ISSSSSSHHHH
 ISIISSSHHHH
 ISSISSSHHHH
 SSIISSSHHHH
 SSIISSSHHHH
  SSSISSHHHH
  HSSSISSHHH
   HHSSSSHHH
     HHHHH
"""),
    'braid': (-4, 0, """
     IIISSSSS
   IIISSSSSSH
  ISSSISSSHHH
  IISHHSSHHH
   SSISSHHH
    SSSHHH
   ISISHH
  IISSHH
   SSSSH
    ISISH
   IISSH
    SSHH
    gGH
    ISH
   SSH
"""),
    'tail': (-5, 0, """
      IIIISSS
    IIISSSSSHH
   IISSISSSHHH
    SSHHSSHHHH
     HggHHHH
    IISS
   IISSSH
  ISSISSH
  ISIISSH
 ISSISSSH
 ISSISSH
  SISSSH
  SSSSH
   SHH
"""),
    'waves': (-4, 0, """
     IIIISSS
   IISSISSSSH
  IISSISSSSHH
  ISSISSSHHHH
 ISIISSHHHHH
 ISSSSSSHHH
  SISSSHHHH
  IISSISSHH
 IISSSSHHHH
 ISSSHHSSHH
  SHISSSSHH
   IISSSHHH
   SSSHHHH
     SHH
"""),
}

# Only facial hair uses these three local palette keys. A pack editor can
# recolor a beard independently of hair, the skin ramp and metalwork.
BEARDS = {
    'point': (3, 9, """
 $$^^$$$  $$&
  ^^^$&^^$$&
  ^^$$  $$$&
   ^^$$$&&&
    ^$$$&&
     ^$$&
      $&
"""),
    'boxed': (2, 8, """
 $$        $
  $$  $$  $&
  $$^^$$$$$&
   ^$$  $$&
   ^$$$$$&
    $$$&&
"""),
    'whiskers': (4, 9, """
  ^^$$$ $$$
 ^$$&&$$$&&
 $$&    &&
"""),
    'goatee': (6, 10, """
  ^^$ $
    &&
  ^$$&
   $&
"""),
}

# Two quiet expression pixels per face, placed relative to the temple.
# Both brow ends thicken together, or the corner of the smile lifts a pixel.
EXPRESSION = {
    'oval':   ((6, 3), (11, 3), (10, 10)),
    'square': ((6, 3), (11, 3), (10, 10)),
    'keen':   ((7, 3), (12, 3), (12, 10)),
    'round':  ((5, 3), (11, 3), (11, 10)),
    'elder':  ((6, 3), (11, 3), (10, 10)),
}


def head(x, y, face, crown, cap_at, *, hair, long_cut, beard, short_cut='tuck', detail=None):
    variants = {}
    tones = HAIR[hair]
    dye = str.maketrans('HSI', tones)
    for presentation, cut in [('neutral', short_cut), ('man', 'crop'), ('woman', long_cut)]:
        d = Drawing()
        bx, by, locks = NAPE[cut]
        d.grid(x + bx, y + by, locks.translate(dye))
        d.grid(x + 4, y + 9, """
 :++++:
 :+++~:
 ::::~:
 :::~
""")
        d.grid(x, y, FACES[face])
        d.grid(x, y - 2, FRINGE[presentation].translate(dye))
        left, right, smile = EXPRESSION[face]
        options = {}
        if presentation == 'man':
            for bx, by in (left, right):
                d.set(x + bx, y + by, tones[1])
            bx, by, rows = BEARDS[beard]
            d.grid(x + bx, y + by, rows)
            options['palette'] = dict(zip('&$^', (INK[t] for t in tones)))
        elif presentation == 'woman':
            bx, by = smile
            d.set(x + bx, y + by, ':')
            d.set(x + bx - 1, y + by + 1, '@')
        if detail:
            bx, by, rows = detail
            d.grid(x + bx, y + by, rows)
        bx, by = cap_at
        d.grid(x + bx, y + by, crown)
        variants[presentation] = d.part(seam=True, **options)
    return variants


HEADS = {
    'interface-head': head(14, 12, 'oval', """
     888888888
    8AABBBBBCF
     ABBBBCBCF
     ABBBBCBCF
      ABBBBCBF
      ygggggGG
    AAABBBCBBBBB
  ABCCCCCCCCCCCF
  FF         FF
""", (-2, -9), hair='ink', long_cut='waves', beard='whiskers'),
    'logic-head': head(15, 13, 'elder', """
       AA
       ABAA
      ABBBBA
     ABBBCBBA
    ABBBCBBBBC
   ABBBggBBBBCF
  ABBBggBBBBBCCF
 AABBCgggBBBCCCF
 ABBCCBBBBAAAACCF
 ABCCFAAABBBBBC
 ABCCFBBBCCFFF
  BCCF
  BCF
  BF
""", (-3, -10), hair='silver', long_cut='braid', beard='point'),
    'infra-head': head(13, 13, 'square', """
       sssmm
     smmmMssNN
    smmmMMMMNNn
   smmmMMMMMNNnf
   mmmMMNNNNNnnf
  mmmmmsmmmmmMMNn
  MNNMNNnnnnnnnnnf
   nmgNf
   nMMnf
   nMnf
    nf
""", (-2, -7), hair='dark', long_cut='tail', beard='boxed'),
    # A leather work band carries the copper goggles above the brow.
    'tools-head': head(14, 13, 'round', """
       aaoooo
    aaooollllooo
   ollllooolllllL
  oolLLlOllllLLLO
  OggyyyGGyyyggGO
   gywzzggwzzggG
   GgzbuGGzbuGG
    gggGLLgggG
""", (-2, -8), hair='copper', short_cut='curl', long_cut='tail', beard='whiskers'),
    'data-head': head(14, 12, 'keen', """
        XXBBB
      ABBAABBBCC
     ABBBAABBBBC
    ABBBAABBBBBC
    aoooooolllLC
 AAABBBBCCCCCCBBBB
AABBBBBBBBBBBBBBBCC
 CCCCCFFFFFFCCCCCCF
""", (-4, -7), hair='dark', long_cut='braid', beard='goatee'),
    'models-head': head(15, 12, 'oval', """
        ee
       eggG
     AAABBCCC
    ABBBAABBCC
   ABBCBBAABBCC
  AABBBCCCAAABBC
  BBBCCCAAABBCCCF
  CCAAABBBBCCFFF
   CCgCCCCCFF
     yG
""", (-2, -9), hair='ink', long_cut='waves', beard='point', detail=(1, 8, 'yg\ngG')),
    'tests-head': head(16, 12, 'keen', """
           AABBB
         AABBBBCF
       AABBBBBCCF
       BCCCBCCCF
 BBB   gyyyggGG
 ABBBCABBBBBBBBBCC
  ABBCCCCFFFFFFCCC
   CCFF
""", (-5, -7), hair='ink', long_cut='tail', beard='whiskers'),
    'docs-head': head(14, 13, 'oval', """
        gggg
     AAAABBggBBB
  AAAABBBBBBGCCCC
  CCCCCCCCCCGFFF
    ABBBCCCCG
    CCCFFFFFo
           ggG
""", (-2, -7), hair='auburn', long_cut='bob', beard='goatee', detail=(3, 5, """
 gggG  gggG
GNwkGgGwkG
 GGgG  GgG
""")),
    'systems-head': head(13, 13, 'square', """
      mmmMMM
    mmMNnggMMN
   mMNngyyGgMNn
  mMNngywygGMNnf
  sNNngyygGnnnnf
  nNNnngGGNnnnnf
  gyyyygggGGGGGG
   gMMMMMNNnnnnnn
""", (-1, -7), hair='pewter', long_cut='braid', beard='boxed'),
    'art-head': head(13, 12, 'oval', """
       rR
     AABBBBAAA
   AABBBBBBAABBBC
 AABBBBBCCCCBBBCCC
 ABBCCCCCCCCCCCCCF
  CCCCCFFFCCCCCFF
    FFFFFFF
""", (-3, -6), hair='gold', short_cut='curl', long_cut='waves', beard='goatee'),
    'worlds-head': head(14, 13, 'square', """
   vvvvvv
  vAAABBBBBC
  ABBAABBBBBBC
  ABBCBBBBBBBCC
  ABCCCCBBAABBCC
 ABCCFCCCCCAABBCC
 ABCCF   FFFCCCCCF
 BBCCF
 BCCF
 CCF
 CF
""", (-5, -7), hair='auburn', long_cut='braid', beard='boxed'),
    # Bookbinder's oxblood cap with a folded vellum slip tucked in its band.
    'lore-head': head(14, 12, 'keen', """
   rrRRRRRRRR
  rrRRR9999999
  rRRR999999ee9
  rRR999999ewc9
  gggggggggcaGG
   99999999G99P
""", (-2, -6), hair='silver', long_cut='bob', beard='whiskers', detail=(3, 5, """
 yggG  yggG
GzkkGgGzkG
 GggG  GgG
""")),
    'community-head': head(13, 13, 'round', """
    ewww    ee
   ewwwwwweewwcc
  ewwwewwwwwwewcc
  eweecwwweewwecc
   eecwwweeewwecc
    ceecceeeccca
     wwwwweeeecc
     weeeeeeccca
""", (-1, -8), hair='copper', short_cut='curl', long_cut='bob', beard='whiskers'),
    'traveler-head': head(14, 12, 'keen', """
        aaaao
     aaaeaaaaol
    aaaeaaaaollO
    aaaaaooooOlO
    jjJJJJJJJJJO
  eeaaaaaooooooool
 eaaaaaooooooolllll
  lllLLLLLLLLLLLL
""", (-4, -7), hair='dark', long_cut='braid', beard='boxed'),
    'base': head(14, 12, 'keen', '', (0, 0), hair='dark', long_cut='waves', beard='boxed'),
}

PARTS = {}
PRESENTATIONS = {'man': {}, 'woman': {}}
for name, variants in HEADS.items():
    PARTS[name] = variants['neutral']
    for presentation, replacement in PRESENTATIONS.items():
        alternative = f'{name}-{presentation}'
        PARTS[alternative] = variants[presentation]
        replacement[name] = alternative
