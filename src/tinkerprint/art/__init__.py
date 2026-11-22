"""Generated pixel art, drawn by keepsake: the room, portraits, party instruments, pins, trinkets and camps.

A pack (see default_pack.py and docs/ART.md) holds the colors and which named piece each trade wears.
The sheet's art reads sheet.json. The card's art reads only the card's allowlisted fields: name, set,
class, multiclass, rounded shares and the look tokens.
"""
from __future__ import annotations

from ..classes import card_pct
from .compose import Look, art_rank, banner_figure_box, class_by_name, look_for, shelf_counts, stat_ramp
from .pack import PackError, default_pack, export_pack, load_pack
from . import keepsake

__all__ = ["keepsake", "Look", "PackError", "default_pack", "export_pack", "load_pack", "sheet_looks", "card_look",
           "art_rank", "banner_figure_box", "look_for", "shelf_counts", "stat_ramp", "chapter_look", "sheet_pcts"]


def sheet_pcts(sheet: dict) -> dict:
    """Rounded shares for the art. The card's own numbers when it has them, so both match."""
    card = sheet.get("card") or {}
    if card.get("enabled"):
        return {s["stat"]: s["pct"] for s in card["stats"]}
    return {r["key"]: card_pct(r["share"]) for r in sheet["stats"]}


def sheet_looks(sheet: dict) -> tuple:
    """(look, close look or None) for the sheet's class."""
    set_name = sheet["profile"]["set"]
    ranked = art_rank(sheet_pcts(sheet), set_name)
    cls = sheet.get("class")
    multi = (sheet.get("multiclass") or {}).get("stats")
    if not cls:
        return look_for(set_name, None, [], ranked), None
    main = look_for(set_name, cls["kind"], cls["stats"], ranked, multi)
    close = cls.get("close")
    alt = look_for(set_name, close["kind"], close["stats"], ranked, multi) if close else None
    return main, alt


def chapter_look(chapter: dict, set_name: str) -> Look:
    ranked = art_rank(chapter.get("shares") or {}, set_name)
    c = chapter.get("class")
    if not c:
        return look_for(set_name, None, [], ranked)
    return look_for(set_name, c["kind"], c["stats"], ranked, chapter.get("multiclass"))


def _base_name(display: str) -> str:
    return (display or "").split(", close to ", 1)[0].lstrip("/ ").strip()


def card_look(card: dict) -> Look:
    """The portrait from allowlisted card fields only: set, class, multiclass and rounded shares."""
    set_name = str(card.get("set", "")).lower()
    ranked = art_rank({s["stat"]: s["pct"] for s in card.get("stats", [])}, set_name)
    found = class_by_name(set_name, _base_name(card.get("class", "")))
    if not found:
        return look_for(set_name, None, [], ranked)
    kind, stats = found
    multi = class_by_name(set_name, _base_name(card.get("multiclass", "")))
    return look_for(set_name, kind, stats, ranked, multi[1] if multi and multi[0] == "pair" else None)

