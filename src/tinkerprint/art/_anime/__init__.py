"""The Keepsake half-body: a 64-pixel guild portrait with the trade's tools held in front."""
from ..compose import palette
from ..pack import PackError, check_skin
from . import keepsake_half
from .paint import Pen, canvas, materials
from .traits import EYE_RAMPS


def _render(pack, look, skin, presentation, foreground_only=False,
            *, expression=None, hair=None, eyes=None, motion=None):
    if presentation not in ("neutral", "man", "woman"):
        raise PackError(f"unknown presentation {presentation!r}")
    flesh = pack.get("skin_colors") if skin is None else skin
    if flesh is None or "skin_colors" not in pack:
        raise PackError("the Keepsake portrait needs a pack with skin_colors")
    check_skin(flesh)
    costume = pack["looks"][look.top] if look.kind in ("specialist", "pair") else pack["generalist"]
    kit = pack["looks"][look.item] if look.kind and look.item else costume
    tool = kit["item"] if look.kind else None
    pal = palette(pack, look)
    colors = materials(tuple(pal[k] for k in "ABCF"), tuple(pal[k] for k in "XYZH"), flesh)
    if eyes is not None:
        if not isinstance(eyes, str) or eyes not in EYE_RAMPS:
            raise PackError(f"unknown Keepsake eye color {eyes!r}")
        if expression != "joy":
            colors["eye"] = EYE_RAMPS[eyes]
    p = Pen(canvas(), colors)
    hat = costume["hat"] if look.kind else "base"
    mantle = "cape" if look.trim else "cloth"
    if look.trim:
        colors["cape"] = (pal["T"], pal["U"], pal["W"], colors["cloth"][3])
    keepsake_half.portrait(p, costume, hat, presentation, tool, mantle, look, kit,
                           foreground_only, expression, hair, motion)
    return p.image
