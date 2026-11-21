"""Load and check an art pack. A pack is data only: grids, palettes and which part each stat wears.

Packs never carry text that reaches an output. Every color must be #rrggbb and every grid key
must resolve, so a pack can change how a sheet looks and nothing else.
"""
from __future__ import annotations

import copy
import json
import re

from ..achievements import ORDER as ACHIEVEMENTS
from ..sets import SETS
from .default_pack import PACK as DEFAULT
from .pixels import HEX

RAMP = "ABCXYZTUVW"
ALL_STATS = sorted({s for stats in SETS.values() for s in stats})
SET_KEYS = ("plate", "floor", "wall", "wall2", "mortar", "board", "board2")
LOOK_KEYS = ("hat", "body", "item", "trinket")
_NAME = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")


class PackError(ValueError):
    pass


def default_pack() -> dict:
    return copy.deepcopy(DEFAULT)


def load_pack(path: str | None = None) -> dict:
    if not path:
        return default_pack()
    try:
        with open(path, encoding="utf-8") as f:
            pack = json.load(f)
    except (OSError, ValueError) as e:
        raise PackError(f"art pack {path}: {e}") from None
    check_pack(pack)
    return pack


def export_pack(path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(DEFAULT, f, indent=1, sort_keys=True)
        f.write("\n")


def _color(v, where):
    if not isinstance(v, str) or not HEX.match(v):
        raise PackError(f"{where}: {v!r} is not a #rrggbb color")


def check_pack(pack: dict) -> None:
    if not isinstance(pack, dict):
        raise PackError("a pack is a JSON object")
    for key in ("canvas", "hand", "ink", "outline", "stat_colors", "wanderer_colors", "sets", "looks",
                "generalist", "familiars", "icons", "parts"):
        if key not in pack:
            raise PackError(f"pack has no {key!r}")
    if pack["canvas"] != [32, 32]:
        raise PackError("canvas must be [32, 32]")
    ink = pack["ink"]
    for k, v in ink.items():
        if len(k) != 1 or k in RAMP or k == ".":
            raise PackError(f"ink key {k!r} must be one character outside {RAMP} and '.'")
        _color(v, f"ink {k}")
    _color(pack["outline"], "outline")
    for s in ALL_STATS:
        ramp = pack["stat_colors"].get(s)
        if not isinstance(ramp, list) or len(ramp) != 3:
            raise PackError(f"stat_colors {s} needs three colors")
        for c in ramp:
            _color(c, f"stat_colors {s}")
    for c in pack["wanderer_colors"]:
        _color(c, "wanderer_colors")
    for name in SETS:
        sp = pack["sets"].get(name) or {}
        for k in SET_KEYS:
            _color(sp.get(k), f"sets {name} {k}")
    parts = pack["parts"]
    if not isinstance(parts, dict):
        raise PackError("parts must be an object")
    for name, part in parts.items():
        if not isinstance(name, str) or not _NAME.match(name):
            raise PackError(f"part name {name!r}")
        at = part.get("at")
        if not (isinstance(at, list) and len(at) == 2 and all(isinstance(v, int) and -64 <= v <= 256 for v in at)):
            raise PackError(f"part {name}: at must be two integers")
        local = part.get("palette", {})
        for k, v in local.items():
            if len(k) != 1 or k in RAMP or k == ".":
                raise PackError(f"part {name}: palette key {k!r}")
            _color(v, f"part {name} palette {k}")
        rows = part.get("rows")
        if not isinstance(rows, list) or not rows or not all(isinstance(r, str) for r in rows):
            raise PackError(f"part {name}: rows must be strings")
        if len({len(r) for r in rows}) != 1 or len(rows[0]) > 256 or len(rows) > 256:
            raise PackError(f"part {name}: every row needs the same width")
        known = set(ink) | set(local) | set(RAMP) | {"."}
        bad = sorted({ch for r in rows for ch in r} - known)
        if bad:
            raise PackError(f"part {name}: unknown keys {''.join(bad)}")
    for s in ALL_STATS:
        look = pack["looks"].get(s) or {}
        for k in LOOK_KEYS:
            if look.get(k) not in parts:
                raise PackError(f"looks {s} {k}: no part {look.get(k)!r}")
    for k in ("hat", "body", "item", "back"):
        if pack["generalist"].get(k) not in parts:
            raise PackError(f"generalist {k}: no part")
    for k in ("default", "claude", "codex", "agy"):
        if pack["familiars"].get(k) not in parts:
            raise PackError(f"familiars {k}: no part")
    for k in list(ACHIEVEMENTS) + ["milestone"]:
        if pack["icons"].get(k) not in parts:
            raise PackError(f"icons {k}: no part")
    for k in ("base", "hand", "cape", "campfire"):
        if k not in parts:
            raise PackError(f"pack needs a {k!r} part")


check_pack(DEFAULT)
