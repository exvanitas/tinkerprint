"""Pins for the achievement row and tiny stat miniatures for open pigeonholes."""
from .enamel import tile

# Keys are the symbol names in the existing art pack. The pin's contour follows
# the object itself, including free space between poles, spokes and ribbons.
PINS = {
    "sunrise": """
        ......G
        ..G...Y...G
        ...G.....G
        .....YYG
        ...YYYGgG
        ..GYYYGGGg
        .gGYYGGGGgG
        SSSSIIISSSSSs
        vVVVVSSVVVVvv
        .vvvvISvvvvs
        ...vvvvvvvv
    """,
    "flag": """
       G
       ALCCRRr
       ARCCRRRrr
       ARRRccRRr
       ARRrc
       Al
       Al
       Al
       Al  Ss
      ISs SSsd
     SSSsssdsdd
    """,
    "coins": """
        .......GGGG
        ......GYIYGG
        ......GYGGGg
        ......GYGYGg
        .......GGGgg
        ..YYYYGGggg
        .YGGGGGgGGGGg
        .GgggggbYYGGgg
        ..YYGGGGgggggb
        GGGGGGgbYGGGgg
        Gggggggbgggggb
    """,
    "ship": """
            R
           ARR
          EAE
         PEA EE
        PEEA EEE
       PEEeA EEEE
      PEEeeA EEeee
           A
     LAaaaaAaaaL
      rRRRrrrrr
       rrrrrrc
     sSSs  sSSs
    """,
    "signpost": """
        .....G
        .....Aa
        .LAAAAAAaa
        AAAAAALAAAa
        .aaaaAAAAa
        .....Al
        .....Al
        ....Eeeeeeee
        ...EEEeEEEEee
        ....EEEeeeeee
        .....Al
        .....Al
        ...TtAlT
    """,
    "mail": """
        .....TTTTTTT
        .....TEEEETt
        ....TTTTTTTt
        ....EPEEEEeo
        ...EEEEEEEeo
        .EPPEEEEEEEE
        EePPEEEEEPPE
        EeePPEEEPPEe
        EeeePRRRPeee
        EeeecRCRceee
        EeeeeRRreeee
        EEEEEEEEeeee
    """,
    "skull": """
        .......T..TT
        ....T...TTt
        .....ttTt
        ....EEEEEe
        ..EPPPEEEEe
        .EPPPEEEEEEe
        .EEqqqEEqqqe
        .EeqqqEEqqqo
        .eeqqEEEqqeo
        ..EEEEqEEee
        ...EeqqEee
        ...EE.E.E
    """,
    "bubbles": """
        .CCCCRRR
        CRRRRRRRr
        RYGGGGRRr
        RRRRRRRrr
        RRRRRRrr
        .Rr...vSSSSs
        .r...SSSSSSss
        .....SdddSsss
        .....SSSSSsss
        ......sssss.s
        ............s
    """,
    "pennants": """
      G     G
      ARRR  ATT
      ARrr  ATtt
      ARr   ATt
      Al    Al
      Al G  Al
      Al AVVVl
      Al AVvAl
      Al Av Al
      Al Al Al
      LAAAAAal
    """,
    "wheel": """
         GGGGG
       GYFFGGGGg
      GYFFTtGYYGg
      GFFTTtGYYGg
     YFFFtttGYYGGg
     YGGGGYYGGGGGg
     GVVvvGGGRCrrg
      GVVvvGRCCrg
      gVVvvGRRrrg
       ggVvGRrgg
         ggggg
    """,
    "star": """
       CRr   RC
       CRRr CRr
        CRRCRr
         CRRr
          GG
          YG
        GGYYGG
      GGGYYYYGGG
       GYYYYYGg
        GYYYYg
       GYYYGYGg
       GGg   Gg
    """,
}

STOCK = {
    "frame": """
       GG
      Y01G
     Y0112G
     G1122g
      G22g
       gg
        G
        g
    """,
    "runebook": """
        .111112
        0111112
        01Gg112
        0G1GG12
        011G112
        0111122
        0EPEee2
        .222222
    """,
    "helmlet": """
        IS
      ISSSs
     ISSSSss
     SGGGGGg
     sdd ds
     sd  ds
     d    d
    """,
    "hammer": """
        ISSS
       ISSsss
      SSAs ss
       Aa   d
      Aa
     Aa
    """,
    "map": """
     EEe  EE
     EPEeEPE
     ETTeePE
     EeTeeTE
     ESeSsTE
     EPeeEPE
     EE  eee
    """,
    "flask": """
       AA
       Ss
       Ss
      IS Ss
     IS   Ss
     S01112s
     S11222s
      sssss
    """,
    "hourglass": """
     LAAAAAa
      SGGs
       SG
        g
       Sg
      SGGS
     AAAAAaa
    """,
    "books": """
      RRRRR
      EEEeer
     vvvvv
     PEEeev
       AAAAa
      EEEeea
      aaaaaa
    """,
    "cog": """
        ...SS
        .ISSs.S
        .SSGGSS
        SSg..gSs
        SSg..gss
        .SsGGss
        .s.ss.s
        ...ss
    """,
    "paints": """
     RR   S
      R  SS
      A  S
      A A
     SSSSSs
     S0122s
     s1222s
      ssss
    """,
    "sprout": """
     FF   T
     FTT FT
      TtFt
       t
     LAAAAa
      Aaal
      aaal
    """,
    "candle": """
        G
       YR
        r
       PE
       EE
       Ee G
     YGGGGg
      gggg
    """,
    "mug": """
        .EEEe
        PPPEEe
        SSSGGggg
        S01Gg..g
        S11Gg..g
        S12Ggggg
        S22Gs
        Ssssg
    """,
}


def pin(pack, achievement):
    symbol = pack["icons"].get(achievement, pack["icons"]["milestone"])
    return tile(PINS[symbol])


def trinket(pack, stat):
    kit = pack["looks"][stat]
    return tile(STOCK[kit["trinket"]], pack["stat_colors"][stat])
