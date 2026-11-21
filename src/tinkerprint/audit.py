"""audit: print every text string the share card on disk holds, before anyone shares it.

It parses card.svg itself with the local expat XML parser, in document order, and reads nothing
from sheet.json, so it always describes the file that would be shared. Text nodes (CDATA too),
comments and every attribute that is not plain presentation are listed. A file that does not
parse is reported and never certified.
"""
from __future__ import annotations

import os

import pyexpat

# Attributes that only place or paint things. Every other attribute value counts as text.
PRESENTATION = {
    "xmlns", "viewBox", "width", "height", "x", "y", "x1", "y1", "x2", "y2", "cx", "cy", "r", "rx", "ry",
    "fill", "stroke", "stroke-width", "stroke-linejoin", "stroke-linecap", "fill-opacity", "stroke-opacity",
    "opacity", "font-family", "font-size", "font-weight", "text-anchor", "letter-spacing", "points", "d",
    "transform", "role", "version", "preserveAspectRatio", "dominant-baseline", "shape-rendering",
}


class NotSvg(ValueError):
    pass


def svg_strings(svg: str) -> list:
    """Every text node, comment and text-bearing attribute in an SVG, in document order."""
    p = pyexpat.ParserCreate()
    p.ordered_attributes = True
    out: list = []
    buf: list = []

    def flush():
        t = "".join(buf).strip()
        if t:
            out.append(t)
        buf.clear()

    def start(name, attrs):
        flush()
        for k, v in zip(attrs[::2], attrs[1::2]):
            if k not in PRESENTATION and v.strip():
                out.append(v.strip())

    def refuse(*_):
        raise NotSvg("declarations and entities are not allowed in a card")

    p.StartElementHandler = start
    p.EndElementHandler = lambda name: flush()
    p.CharacterDataHandler = buf.append
    p.CommentHandler = lambda data: (flush(), out.append(data.strip()) if data.strip() else None)
    p.StartDoctypeDeclHandler = refuse
    p.EntityDeclHandler = refuse
    p.ProcessingInstructionHandler = lambda target, data: (flush(), out.append(f"{target} {data}".strip()))
    try:
        p.Parse(svg, True)
    except pyexpat.ExpatError as e:
        raise NotSvg(str(e)) from None
    flush()
    return out


def audit_card(out_dir: str, profile=None) -> list:
    path = os.path.join(out_dir, "card.svg")
    if not os.path.isfile(path):
        return [f"No card.svg in {out_dir}. There is no card to share."]
    with open(path, "rb") as f:
        data = f.read()
    try:
        strings = svg_strings(data.decode("utf-8"))
    except (NotSvg, UnicodeDecodeError) as e:
        return [f"{path} is not valid SVG ({e}). It is not certified. Run build again."]
    lines = [f"{path} holds these {len(strings)} strings and nothing else:"]
    lines += [f"  {s}" for s in strings]
    if profile is not None and not profile.card_enabled:
        lines.append("Warning: the profile no longer allows a card, but card.svg is still there. Run build again.")
    return lines
