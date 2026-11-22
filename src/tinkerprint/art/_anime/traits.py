"""Stable character traits for the optional half-body portrait."""
from hashlib import sha256
from math import log

from ..pack import PackError
from .paint import HONEY

EXPRESSIONS = ("smile", "grin", "calm", "determined", "joy", "curious")
HAIRSTYLES = {
    "neutral": ("bob", "curtains", "shag"),
    "man": ("crop", "curls", "side part"),
    "woman": ("braid", "waves", "chignon"),
}

# The darkest key draws lashes and pupils, including the closed eye in joy.
# It stays ink-dark on every skin. Each iris has its own catchlight and two facets.
EYE_RAMPS = {
    "honey": HONEY,
    "moss": ("#e4e7c6", "#9dae77", "#526e56", "#473446"),
    "slate": ("#e0e6e5", "#92adbd", "#51677f", "#473446"),
    "chestnut": ("#f3d6b6", "#c18c6e", "#805343", "#473446"),
    "plum": ("#ecdae3", "#b09ab6", "#755b79", "#473446"),
    "lagoon": ("#deeadb", "#89b4a7", "#4c7875", "#473446"),
}


def _pick(seed, axis, options):
    """A rendezvous pick: each option scores on its own, so a new option takes users only for itself."""
    def priority(option):
        digest = sha256(f"{seed}|{axis}|{option}".encode("utf-8")).digest()
        # Midpoints of 2**52 equal bins are exactly representable and strictly
        # inside (0, 1). The shortest exponential waiting time wins.
        u = ((int.from_bytes(digest[:8], "big") >> 12) + 0.5) / (1 << 52)
        return -log(u), option

    return min(options, key=priority)


def keepsake_traits(seed: str, look=None, presentation="neutral") -> dict:
    """Pick by user seed alone, uniformly. The look never sways a pick, so a person keeps
    their face, cut and eyes when their class changes."""
    if not isinstance(seed, str):
        raise TypeError("seed must be a string")
    if presentation not in HAIRSTYLES:
        raise PackError(f"unknown presentation {presentation!r}")
    return {"expression": _pick(seed, "expression", EXPRESSIONS),
            "hair": _pick(seed, "hair", HAIRSTYLES[presentation]),
            "eyes": _pick(seed, "eyes", EYE_RAMPS)}
