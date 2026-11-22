"""Load and check an art pack. A pack is data only: colors, and which named piece each trade wears.

The Keepsake drawings are code. A pack recolors them and reassigns their named pieces: every color
must be #rrggbb and every name one the built-in art draws, so a pack can change how a sheet looks
and nothing else. Packs never carry text that reaches an output.
"""
from __future__ import annotations

import copy
import json

from ..achievements import ORDER as ACHIEVEMENTS
from ..sets import SETS
from .default_pack import PACK as DEFAULT
from .pixels import HEX

ALL_STATS = sorted({s for stats in SETS.values() for s in stats})
LOOK_KEYS = ("hat", "body", "item", "trinket", "gear")
GENERALIST_KEYS = ("hat", "body", "item")
SET_COLORS = ("plate", "floor", "wall2")
SCENES = ("ridge", "vale")
# Version 2 packs from before the Keepsake art still load: their sprite parts are ignored.
VERSIONS = (2, 3)


class PackError(ValueError):
    pass


def _names() -> dict:
    """Every piece the built-in art draws, by slot."""
    looks = list(DEFAULT["looks"].values())
    names = {k: {look[k] for look in looks} for k in LOOK_KEYS}
    for k in GENERALIST_KEYS:
        names[k].add(DEFAULT["generalist"][k])
    names["icon"] = set(DEFAULT["icons"].values())
    return names


NAMES = _names()


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


def _ramp(v, where):
    if not isinstance(v, list) or len(v) != 4:
        raise PackError(f"{where} needs four colors from highlight to shadow")
    for c in v:
        _color(c, where)


def check_skin(skin):
    if not isinstance(skin, (list, tuple)) or len(skin) != 4:
        raise PackError("skin needs four colors from highlight to shadow")
    for color in skin:
        _color(color, "skin")


def _name(v, slot, where):
    if not isinstance(v, str) or v not in NAMES[slot]:
        raise PackError(f"{where}: {v!r} is not a {slot} the art draws")


def check_pack(pack: dict) -> None:
    if not isinstance(pack, dict):
        raise PackError("a pack is a JSON object")
    version = pack.get("version", 1)
    if type(version) is not int or version not in VERSIONS:
        raise PackError("unsupported pack version: export the built-in pack again and start from that")
    for key in ("stat_colors", "wanderer_colors", "skin_colors", "sets", "looks", "generalist", "icons"):
        if key not in pack:
            raise PackError(f"pack has no {key!r}")
    for key in ("stat_colors", "sets", "looks", "generalist", "icons"):
        if not isinstance(pack[key], dict):
            raise PackError(f"{key} must be an object")
    check_skin(pack["skin_colors"])
    _ramp(pack["wanderer_colors"], "wanderer_colors")
    for s in ALL_STATS:
        _ramp(pack["stat_colors"].get(s), f"stat_colors {s}")
    for name in SETS:
        sp = pack["sets"].get(name)
        if not isinstance(sp, dict):
            raise PackError(f"sets {name}: expected an object")
        for k in SET_COLORS:
            _color(sp.get(k), f"sets {name} {k}")
        if sp.get("scene") not in SCENES:
            raise PackError(f"sets {name}: scene must be one of {', '.join(SCENES)}")
    for s in ALL_STATS:
        look = pack["looks"].get(s)
        if not isinstance(look, dict):
            raise PackError(f"looks {s}: expected an object")
        for k in LOOK_KEYS:
            _name(look.get(k), k, f"looks {s} {k}")
    for k in GENERALIST_KEYS:
        _name(pack["generalist"].get(k), k, f"generalist {k}")
    for k in list(ACHIEVEMENTS) + ["milestone"]:
        _name(pack["icons"].get(k), "icon", f"icons {k}")


check_pack(DEFAULT)
