"""The portrait's look: what the person chose under [look], and the rest picked from a name.

Presentation and skin are never random: a person chooses them, and they default to neutral and
the art pack's skin. Hair, eyes and expression left unset come from keepsake.traits, a uniform
pick by name alone, so they never change with the class or the stats.
"""
from __future__ import annotations

from .art import keepsake

TRAITS = ("hair", "eyes", "expression")
TOKENS = ("presentation", "skin") + TRAITS
NAME_MAX = 22  # the longest name the card shows whole


def public_name(name) -> str:
    """The name exactly as the card shows it, clipped to NAME_MAX. It is the portrait's one seed:
    the label, the picked traits and the room all come from it, so no character the card leaves
    off changes the art."""
    s = str(name)
    return s if len(s) <= NAME_MAX else s[:NAME_MAX - 1].rstrip() + "\u2026"


def resolve(chosen: dict, name: str) -> dict:
    """Every look token, plus "picked": the traits that came from the name."""
    presentation = chosen.get("presentation") or "neutral"
    seeded = keepsake.traits(name, None, presentation)
    out = {"presentation": presentation, "skin": chosen.get("skin")}
    picked = []
    for key in TRAITS:
        if chosen.get(key):
            out[key] = chosen[key]
        else:
            out[key] = seeded[key]
            picked.append(key)
    out["picked"] = picked
    return out


def of_card(card: dict) -> dict:
    """The look tokens a card draws its portrait from. A card without them gets the name's picks."""
    look = card.get("look") or {}
    if all(k in look for k in ("presentation",) + TRAITS):
        return {k: look.get(k) for k in TOKENS}
    full = resolve(look, str(card.get("name", "")))
    return {k: full[k] for k in TOKENS}


def of_sheet(sheet: dict) -> tuple:
    """(seed, look tokens) for the sheet's own pictures. The seed is the name the card shows."""
    look = sheet.get("look") or {}
    seed = look.get("seed")
    if not isinstance(seed, str):
        seed = str((sheet.get("profile") or {}).get("name", ""))
    if not all(k in look for k in ("presentation",) + TRAITS):
        look = resolve(look, seed)
    return seed, {k: look.get(k) for k in TOKENS}


def options(tokens: dict) -> dict:
    """Keyword arguments for keepsake.plate and keepsake.figure."""
    return {k: tokens.get(k) for k in TOKENS}


def skin_name(skin, pack: dict) -> str:
    """The skin's name for the terminal. Unset is the pack's own ramp, named when it matches."""
    if skin:
        return skin
    ramp = tuple(pack.get("skin_colors") or ())
    return next((name for name, r in keepsake.SKINS.items() if tuple(r) == ramp), "from the art pack")


def describe(look: dict, pack: dict, from_card_name: bool = False) -> str:
    """One line after a build: the look in use, and which parts were picked at random."""
    words = [look["presentation"], f"skin {skin_name(look.get('skin'), pack)}", f"hair {look['hair']}",
             f"eyes {look['eyes']}", look["expression"]]
    line = "Look: " + ", ".join(words)
    picked = list(look.get("picked") or [])
    if picked:
        names = picked[0] if len(picked) == 1 else ", ".join(picked[:-1]) + " and " + picked[-1]
        whose = "your card name" if from_card_name else "your name"
        it = "it" if len(picked) == 1 else "them"
        line += f" ({names} picked from {whose}; set {it} under [look] to keep {it})"
    return line
