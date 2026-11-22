"""The party's wind-up instruments. Each is drawn from its harness name alone."""
from textwrap import dedent

from .enamel import tile

# The edition's companion pack. The stable display order also assigns the three
# berths when more harnesses are present than the case can hold.
MEMBERS = {
    "claude": ("Claude Code", "wick lantern"),
    "codex": ("Codex", "typewriter"),
    "agy": ("Antigravity", "orrery"),
    "gemini": ("Gemini CLI", "sand clock"),
    "opencode": ("OpenCode", "bellows"),
    "cline": ("Cline", "screw press"),
    "roo": ("Roo Code", "table loom"),
    "copilot": ("Copilot CLI", "pan scales"),
    "cursor": ("Cursor", "microscope"),
    "aider": ("Aider", "spinning wheel"),
    "default": ("Other", "gramophone"),
}

INSTRUMENTS = {
    "wick lantern": """
         GG
        g  g
        g  g
       YGGGgb
      GGgggggb
       SEEESb
       SEYESb
       SYYGSb
       SYCCSb
       SGRRSb
      YGGGGggb
      gb    gb
    """,
    "typewriter": """
        laaaaaaal
        EPPPPPPEo
        EPooooPEo
        EPPPPPEEo
      sSSEEEEESsS
       TTTTTTTTt
      TItItItIstt
     TStStStStSttf
     TTTISSssTTttf
      ttttttttttf
    """,
    "orrery": """
           Gg
        GGG g
      YG   g Gb
      G  HHhh G
     G  HQHHh  g
     gggHHHhgggG
      Gggggg Gb
       g hh Gb
        GGGgb
          G
         GGg
       YGGGggb
    """,
    "sand clock": """
      LAAAAAAAal
       gSPPPsg
       gSGGSsg
       g sGsg
       g  G g
       g  g g
       g sGSg
       gSGGGSg
       gYGGGGg
      LAAAAAAAal
    """,
    "bellows": """
              ISs
            aSsd
          LAAl
        LAaRRal
      LAAARRRral
     LARRccRRRal
     ARccRCRRAal
     ARCRRRAAal
      AAAAaaal
       aaal  al
       la    la
    """,
    "screw press": """
        GGGGGGG
           ss
      LAAAAssAAl
      Aa   SS al
      Aa   ss al
      Aa  SSSsal
      Aa  EEEeal
      Aa eEEeeal
      LAAAAAAAal
      aaal   aal
    """,
    "table loom": """
       A      A
      LAALAAAaal
       ASrErEsA
       ArErErEA
       ASrErEsA
       AEEECRrA
      LAAAAAAAal
      ACRRCCrrAa
      ARCCRRrrAa
      Aa      aa
    """,
    "pan scales": """
          Y
      GGggGggGG
      S   G   s
     S S  G  s s
    Y   G G G   g
    GGGGg G GGGgb
     ggb  G  ggb
          Gg
         GGGg
       YGGGGGgb
    """,
    "microscope": """
          ss
         ISss
        ISss
       ISSs AA
      ISss   Aa
       ss   AAa
          LAAa
     SSSSssAa
          Aaa
        aaAAa
      SSSSSSss
    """,
    "spinning wheel": """
         GGG
       YG S Gg
       G SsS G
      G  sGS  g
      GSSGYGssg
       G sSs G
       gGS SGg
         GGGaa
        A a  Aa
      LA  a   Aa
     AAAaaAAAAAal
    """,
    "gramophone": """
             YGG
           YGGGg
        YGGGGggg
       GGGGGgggb
        GGGgggb
         Gb
      SSssb
     s     b
     LAAAAAAAal
     ARRRGRRral
     ARRGbGRral
     aaaaaaaaal
    """,
}

CLOCKWORK = ("agy", "gemini", "opencode", "codex", "claude")

# Alternate positions of the working part in the less common instruments.
# Row numbers refer to the unoutlined sprite. Bases stay on the same ledge.
WORKING_ROWS = {
    "screw press": {0:"   GGGGG", 4:"Aa   SS al", 5:"Aa   ss al", 6:"Aa  SSSsal"},
    "table loom": {4:" ASrYGEsA"},                # shuttle through the shed
    "pan scales": {4:"    G G G   g", 5:"Y   G G GGGgb",
                   6:"GGGGg G  ggb", 7:" ggb  Gg"},  # left pan settles
    "microscope": {1:"     ss", 2:"    ISss", 3:"   ISssAA",
                   4:"  ISSs  Aa", 5:" ISss  AAa", 6:"  ss LAAa"},
    "spinning wheel": {2:"  G Ss  G", 3:" G S SGS g", 4:" G  GYG  g",
                       5:"  G SsSsG", 6:"  gG S Gg"},
    "gramophone": {0:"       YGG", 1:"     YGGGg", 2:"  YGGGGggg",
                   3:" GGGGGgggb", 4:"  GGGgggb", 5:"   GGb"},
}


def member(harness, step=0):
    name = MEMBERS.get(harness, MEMBERS["default"])[1]
    pattern = INSTRUMENTS[name]
    if step:
        rows = dedent(pattern).strip("\n").splitlines()
        width = max(map(len, rows))
        if harness == "agy":
            # A brass satellite follows the tilted hoop, behind the globe at
            # the far side. The stand and both ends of the axis stay fixed.
            x, y = ((1,2),(3,1),(6,0),(8,2),(9,4),(8,6),(5,6),(2,5))[step]
            rows[2] = rows[2].replace("Y", "G")
            rows[y] = rows[y][:x] + "YG" + rows[y][x+2:]
        elif harness == "gemini":
            rows[4:7] = ((" g    g", " g  G g", " g sGSg") if step % 3 == 1 else
                         (" g  G g", " g    g", " g sYSg"))
        elif harness == "opencode" and 2 <= step <= 5:
            # Hinge at the lower board. One fold closes and the nozzle drops.
            rows[:7] = ["", *rows[:6]]
        elif harness == "codex" and 2 <= step <= 5:
            rows[:4] = [" " + row for row in rows[:4]]
        elif harness == "claude" and step % 3:
            rows[6:8] = (" SEEGSb", " SYYYSb") if step % 3 == 1 else (" SEPESb", " SEYGSb")
        elif 2 <= step <= 5:
            for y, row in WORKING_ROWS.get(name, {}).items():
                rows[y] = row
        # Keep the original tile dimensions and its registration on the ledge.
        pattern = "\n".join(row.replace(" ", ".").ljust(width, ".") for row in rows)
    return tile(pattern)


def berths(harnesses):
    names = set(harnesses)
    known = [h for h in MEMBERS if h in names and h != "default"]
    return (known + sorted(names.difference(known)))[:3]
