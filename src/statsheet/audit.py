"""audit: print every string the share card would contain, before anyone shares it."""
from __future__ import annotations

from .render_card import card_strings


def audit_lines(sheet: dict, profile_id: str) -> list:
    card = sheet["card"]
    if not card.get("enabled"):
        return [f"Card for profile {profile_id}: off.", card.get("reason", "")]
    lines = [f"Card for profile {profile_id}: on. It holds these strings and nothing else:"]
    for field, value in card_strings(card):
        lines.append(f"  {field:<12} {value}")
    lines.append("Fixed labels: SET, LEVEL, ACHIEVEMENTS, PARTY.")
    return lines
