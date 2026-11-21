"""audit: print every text string the share card on disk holds, before anyone shares it.

It reads card.svg itself, in document order, and nothing from sheet.json, so it always
describes the file that would be shared.
"""
from __future__ import annotations

import os
import re
from html import unescape

_TEXT = re.compile(r'(?:aria-label|title)="([^"]*)"|>([^<>]+)<')


def svg_strings(svg: str) -> list:
    """Every text node and text-bearing attribute in an SVG, in document order."""
    out = []
    for m in _TEXT.finditer(svg):
        value = unescape(m.group(1) if m.group(1) is not None else m.group(2)).strip()
        if value:
            out.append(value)
    return out


def audit_card(out_dir: str, profile) -> list:
    path = os.path.join(out_dir, "card.svg")
    if not os.path.isfile(path):
        lines = [f"No card.svg in {out_dir}. There is no card to share."]
        return lines
    with open(path, encoding="utf-8", errors="replace") as f:
        strings = svg_strings(f.read())
    lines = [f"{path} holds these {len(strings)} strings and nothing else:"]
    lines += [f"  {s}" for s in strings]
    if not profile.card_enabled:
        lines.append("Warning: the profile no longer allows a card, but card.svg is still there. Run build again.")
    return lines
