"""A shared 2.88-second clock for the Keepsake portrait and room."""
from typing import NamedTuple

from ._anime import _render


class Beat(NamedTuple):
    breath: int  # resting, shoulder lift, rib lift
    blink: int   # open, lowering, closed
    ember: int   # three wick shapes
    wisp: int    # eastward travel across the window
    bend: int    # offset at the tip of a leaf
    gear: int    # eighth turns of the party instrument


# Four equal phrases make it possible to stagger the people in a lineup
# without changing a blink's timing. Long holds belong to the open eyes.
DELAYS_MS = (360, 80, 100, 180) * 4
BEATS = tuple(Beat(*parts) for parts in zip(
    (0, 0, 1, 1, 2, 2, 2, 1, 1, 1, 0, 0, 0, 0, 0, 0),
    (0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 2, 0, 0, 0, 0, 0),
    (0, 1, 1, 2, 1, 0, 0, 0, 1, 1, 1, 0, 0, 1, 1, 0),
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9,10,11,12,13,14,15),
    (0, 0, 0, 0, 1, 1, 1, 2, 2, 2, 2, 1, 1, 0, 0, 0),
    (0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5, 6, 6, 7, 7),
))


def figure_frames(pack, look, *, skin=None, presentation="neutral", expression=None,
                  hair=None, eyes=None, beats=BEATS):
    """Native transparent frames. Frame zero is the static portrait."""
    return tuple(_render(pack, look, skin, presentation,
                         expression=expression, hair=hair, eyes=eyes, motion=beat)
                 for beat in beats)

