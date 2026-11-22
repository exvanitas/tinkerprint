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
from ._colors import SKIN_KEYS

RAMP = "ABCXYZTUVW"
EXTENDED_RAMP = RAMP + "FH"
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
    if not isinstance(v, str) or not HEX.fullmatch(v):
        raise PackError(f"{where}: {v!r} is not a #rrggbb color")


def check_skin(skin):
    if not isinstance(skin, (list, tuple)) or len(skin) != len(SKIN_KEYS):
        raise PackError("skin needs four colors from highlight to shadow")
    for color in skin:
        _color(color, "skin")


def _point(v, where):
    if not (isinstance(v, list) and len(v) == 2 and all(type(n) is int and 0 <= n < 64 for n in v)):
        raise PackError(f"{where}: expected a pixel coordinate")


def check_pack(pack: dict) -> None:
    if not isinstance(pack, dict):
        raise PackError("a pack is a JSON object")
    for key in ("canvas", "hand", "ink", "outline", "stat_colors", "wanderer_colors", "sets", "looks",
                "generalist", "familiars", "icons", "parts"):
        if key not in pack:
            raise PackError(f"pack has no {key!r}")
    for key in ("ink", "stat_colors", "sets", "looks", "generalist", "familiars", "icons", "parts"):
        if not isinstance(pack[key], dict):
            raise PackError(f"{key} must be an object")
    version = pack.get("version", 1)
    if type(version) is not int or version not in (1, 2):
        raise PackError("unsupported pack version")
    if "mixed_gear_only" in pack and type(pack["mixed_gear_only"]) is not bool:
        raise PackError("mixed_gear_only must be a boolean")
    modern = version == 2
    reserved = EXTENDED_RAMP if modern else RAMP
    if modern and "skin_colors" in pack:
        check_skin(pack["skin_colors"])
        reserved += SKIN_KEYS
    ramp_lengths = (3, 4) if modern else (3,)
    if pack["canvas"] not in ([[32, 32], [48, 48], [64, 64]] if modern else [[32, 32]]):
        raise PackError("unsupported portrait canvas")
    if modern:
        _point(pack["hand"], "hand")
        edges = pack.get("edges")
        if not isinstance(edges, dict):
            raise PackError("edges must map colors to pairs of colors")
        for key, pair in edges.items():
            _color(key, "edge material")
            if not isinstance(pair, list) or len(pair) != 2:
                raise PackError("edge needs a lit and a shadow color")
            for color in pair:
                _color(color, "edge")
    ink = pack["ink"]
    for k, v in ink.items():
        if not isinstance(k, str) or len(k) != 1 or k in reserved or k == ".":
            raise PackError(f"ink key {k!r} must be one character outside {RAMP} and '.'")
        _color(v, f"ink {k}")
    _color(pack["outline"], "outline")
    for s in ALL_STATS:
        ramp = pack["stat_colors"].get(s)
        if not isinstance(ramp, list) or len(ramp) not in ramp_lengths:
            raise PackError(f"stat_colors {s} has an unsupported ramp")
        for c in ramp:
            _color(c, f"stat_colors {s}")
    if not isinstance(pack["wanderer_colors"], list) or len(pack["wanderer_colors"]) not in ramp_lengths:
        raise PackError("unsupported wanderer ramp")
    for c in pack["wanderer_colors"]:
        _color(c, "wanderer_colors")
    for name in SETS:
        sp = pack["sets"].get(name) or {}
        if not isinstance(sp, dict):
            raise PackError(f"sets {name}: expected an object")
        for k in SET_KEYS:
            _color(sp.get(k), f"sets {name} {k}")
    parts = pack["parts"]
    for name, part in parts.items():
        if not isinstance(name, str) or not _NAME.fullmatch(name):
            raise PackError(f"part name {name!r}")
        if not isinstance(part, dict):
            raise PackError(f"part {name}: expected an object")
        if "seam" in part and type(part["seam"]) is not bool:
            raise PackError(f"part {name}: seam must be a boolean")
        at = part.get("at")
        if not (isinstance(at, list) and len(at) == 2 and all(isinstance(v, int) and -64 <= v <= 256 for v in at)):
            raise PackError(f"part {name}: at must be two integers")
        local = part.get("palette", {})
        if not isinstance(local, dict):
            raise PackError(f"part {name}: palette must be an object")
        for k, v in local.items():
            if not isinstance(k, str) or len(k) != 1 or k in reserved or k == ".":
                raise PackError(f"part {name}: palette key {k!r}")
            _color(v, f"part {name} palette {k}")
        rows = part.get("rows")
        if not isinstance(rows, list) or not rows or not all(isinstance(r, str) for r in rows):
            raise PackError(f"part {name}: rows must be strings")
        if len({len(r) for r in rows}) != 1 or not 1 <= len(rows[0]) <= 256 or len(rows) > 256:
            raise PackError(f"part {name}: every row needs the same width")
        known = set(ink) | set(local) | set(reserved) | {"."}
        bad = sorted({ch for r in rows for ch in r} - known)
        if bad:
            raise PackError(f"part {name}: unknown keys {''.join(bad)}")
    for s in ALL_STATS:
        look = pack["looks"].get(s) or {}
        if not isinstance(look, dict):
            raise PackError(f"looks {s}: expected an object")
        if modern:
            _point(look.get("grip"), f"{s} grip")
            _point(look.get("shoulder"), f"{s} shoulder")
        for k in (LOOK_KEYS + ("gear",) if modern else LOOK_KEYS):
            if not isinstance(look.get(k), str) or look[k] not in parts:
                raise PackError(f"looks {s} {k}: no part {look.get(k)!r}")
    if modern:
        _point(pack["generalist"].get("grip"), "generalist grip")
        for name in SETS:
            for key in ("scene", "studio"):
                if not isinstance(pack["sets"][name].get(key), str) or pack["sets"][name][key] not in parts:
                    raise PackError(f"sets {name}: missing {key}")
        for key in ("runner", "standard", "idle"):
            if key not in parts:
                raise PackError(f"missing {key}")
    for k in ("hat", "body", "item", "back"):
        if not isinstance(pack["generalist"].get(k), str) or pack["generalist"][k] not in parts:
            raise PackError(f"generalist {k}: no part")
    if modern:
        for costume in [pack["looks"][s] for s in ALL_STATS] + [pack["generalist"]]:
            tool = parts[costume["item"]]
            offset = tool.get("offset")
            if (not isinstance(tool.get("sleeve"), str) or tool["sleeve"] not in parts
                    or not isinstance(offset, list) or len(offset) != 2
                    or not all(type(n) is int and -64 <= n <= 64 for n in offset)):
                raise PackError("a tool needs a sleeve and a grip offset")
    for k in ("default", "claude", "codex", "agy"):
        if not isinstance(pack["familiars"].get(k), str) or pack["familiars"][k] not in parts:
            raise PackError(f"familiars {k}: no part")
    for k in list(ACHIEVEMENTS) + ["milestone"]:
        if not isinstance(pack["icons"].get(k), str) or pack["icons"][k] not in parts:
            raise PackError(f"icons {k}: no part")
    for k in ("base", "hand", "cape", "campfire"):
        if k not in parts:
            raise PackError(f"pack needs a {k!r} part")
    if "presentations" in pack:
        variants = pack["presentations"]
        if not modern or not isinstance(variants, dict):
            raise PackError("presentations must be a version 2 head map")
        heads = {"base", pack["generalist"]["hat"]} | {pack["looks"][s]["hat"] for s in ALL_STATS}
        for name, replacements in variants.items():
            if not isinstance(name, str) or not _NAME.fullmatch(name) or name == "neutral":
                raise PackError("invalid presentation name (neutral uses the original heads)")
            if not isinstance(replacements, dict) or replacements.keys() != heads:
                raise PackError(f"presentation {name} needs a replacement for each head")
            if any(not isinstance(ref, str) or ref not in parts for ref in replacements.values()):
                raise PackError(f"presentation {name} references an unknown head part")


check_pack(DEFAULT)
