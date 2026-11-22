"""Small fired-enamel objects. Each material has a warm glint and a cool rim."""
from textwrap import dedent

from ..pixels import Canvas

# Four tones from the Keepsake portrait materials, with softer wood and colored glaze.
MATERIALS = {
    "PEeo": ("#fff6df", "#f2e3cc", "#d3bc9a", "#876876"),  # parchment
    "ISsd": ("#fff0c3", "#b3d2c3", "#668c89", "#364c56"),  # tin
    "YGgb": ("#fff0b8", "#e3ac61", "#ac7554", "#654a54"),  # brass
    "CRrc": ("#ffbe98", "#dc7368", "#9b485b", "#55364f"),  # lacquer
    "LAal": ("#f0cd97", "#c99469", "#926253", "#5c4250"),  # pearwood
    "FTtf": ("#e3e9bc", "#a0bd92", "#638978", "#3d5961"),  # green glaze
    "BVvn": ("#ece4dc", "#9eb6ce", "#647d9f", "#45465f"),  # blue glaze
    "QHhq": ("#f6dada", "#c099ac", "#946e86", "#564258"),  # heather
}


def tile(pattern, tint=None):
    """Trim only the enclosing whitespace, then give each edge its material's ink."""
    rows = dedent(pattern).strip('\n').splitlines()
    inks, edges = {}, {}
    ramps = MATERIALS if tint is None else {**MATERIALS, "0123": tint}
    for keys, ramp in ramps.items():
        inks.update(zip(keys, ramp))
        for color in ramp:
            edges[color] = (ramp[2], ramp[3])
    c = Canvas(max(map(len, rows))+2, len(rows)+2)
    c.stamp(rows, inks, 1, 1)
    return c.material_edges(edges, "#483746")
