"""audit: print every string the share card on disk holds, before anyone shares it.

It reads the card payload saved with the selected build, so it describes that build's card,
and lists strings from the same selection the renderer draws.
"""
from __future__ import annotations

import json
import os

from .render_card import card_strings


def audit_lines(sheet: dict, profile_id: str, card_on_disk: bool | None = None,
                consent_now: bool | None = None) -> list:
    card = sheet["card"]
    lines = []
    if not card.get("enabled"):
        lines += [f"Card for profile {profile_id}: off.", card.get("reason", "")]
    else:
        lines.append(f"Card for profile {profile_id}: on. It holds these strings and nothing else:")
        for field, value in card_strings(card):
            lines.append(f"  {field:<12} {value}")
        lines.append("Fixed labels: LEVEL, ACHIEVEMENTS.")
    if card_on_disk is not None and card_on_disk != bool(card.get("enabled")):
        lines.append("Warning: card.svg on disk does not match this build. Run build again.")
    if consent_now is False and card_on_disk:
        lines.append("Warning: the profile no longer allows a card, but card.svg is still on disk. Run build again.")
    return lines


def audit_build(out_dir: str, profile) -> list:
    """Audit the build saved in out_dir."""
    path = os.path.join(out_dir, "sheet.json")
    try:
        with open(path, encoding="utf-8") as f:
            sheet = json.load(f)
    except (OSError, ValueError):
        raise ValueError(f"no build found in {out_dir}. Run build first, or pass --out") from None
    card_on_disk = os.path.isfile(os.path.join(out_dir, "card.svg"))
    return audit_lines(sheet, profile.id, card_on_disk, profile.card_enabled)
