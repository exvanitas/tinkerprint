"""Half-body guild artwork on the 16-beat Keepsake clock.

SKINS maps profile names to four colors from highlight to shadow. Omit skin to
use the pack's own ramp. EXPRESSIONS and EYES list valid names. HAIRSTYLES
lists the cuts for each presentation. DELAYS_MS gives the duration of each
native frame in milliseconds, including the hold before the loop repeats.
"""
from dataclasses import dataclass

from ._anime import _render
from ._anime.traits import EXPRESSIONS, EYE_RAMPS, HAIRSTYLES, keepsake_traits
from ._colors import ramp
from ._drawing import Drawing
from ._keepsake_gif import encode
from ._keepsake_idle import BEATS, DELAYS_MS, figure_frames as _figure_frames
from ._keepsake_room import camp as _camp, companions, room, tokens
from .compose import banner_figure_box
from .pack import PackError
from .pixels import Canvas


SKINS = {
    "light": tuple(ramp("e<>L")),
    "medium": ("#e6ab78", "#bc8058", "#925b49", "#67404a"),
    "deep": ("#b47f65", "#8b5c4c", "#654049", "#453143"),
}
EYES = tuple(EYE_RAMPS)

__all__ = ["figure", "figure_frames", "plate", "plate_frames", "camp", "camp_frames",
           "banner_layers", "berths", "pin", "trinket", "instrument", "traits", "encode",
           "SKINS", "EXPRESSIONS", "HAIRSTYLES", "EYES", "DELAYS_MS"]


def _skin(skin):
    if isinstance(skin, str):
        if skin not in SKINS:
            raise PackError(f"unknown Keepsake skin {skin!r}")
        return SKINS[skin]
    return skin


def traits(seed, look, presentation="neutral"):
    """Choose expression, hair and iris by user seed, with cuts fitted to presentation."""
    return keepsake_traits(seed, look, presentation)


def figure(pack, look, *, presentation="neutral", expression=None, hair=None, eyes=None, skin=None):
    """Draw a transparent 64 × 64 half-body from a class look and optional profile choices."""
    return _render(pack, look, _skin(skin), presentation,
                   expression=expression, hair=hair, eyes=eyes)


def figure_frames(pack, look, *, presentation="neutral", expression=None, hair=None, eyes=None, skin=None):
    """Draw the same dressed figure breathing and blinking, one transparent Canvas per beat."""
    return _figure_frames(pack, look, presentation=presentation, expression=expression,
                          hair=hair, eyes=eyes, skin=_skin(skin))


def _plates(pack, look, seed, presentation, expression, hair, eyes, skin, beats):
    plan = room.plan_room(pack, look, (), seed)
    touches = dict(plan.touches)
    options = room.portrait_options(seed, look, presentation, expression, hair, eyes)
    # Face the jamb with the clearest landmark: sail and peaks to the west,
    # mill and viaduct to the east. Keep every architectural pixel at 1x.
    west = touches["view"] in ("harbor", "peaks")
    left = 29 if west else 145
    skin = _skin(skin)
    for beat in beats:
        wall = Drawing(252, 72)
        room.architecture(wall, pack, look, touches, beat.wisp)
        room.plant(wall, touches, beat.bend)
        tile = Canvas(64, 64)
        tile.px = [row[left:left+64] for row in wall.px[:64]]
        tile.paste(_render(pack, look, skin, presentation, motion=beat, **options))
        yield tile


def plate(pack, look, seed, *, presentation="neutral", expression=None, hair=None, eyes=None, skin=None):
    """Draw a 64 × 64 still at the user's workshop window, with seeded or explicit features."""
    return next(_plates(pack, look, seed, presentation, expression, hair, eyes, skin, BEATS[:1]))


def plate_frames(pack, look, seed, *, presentation="neutral", expression=None, hair=None, eyes=None, skin=None):
    """Animate the plate's figure, window light and visible foliage on the shared clock."""
    return tuple(_plates(pack, look, seed, presentation, expression, hair, eyes, skin, BEATS))


def camp(pack, set_name, seed):
    """Draw the seeded 64 × 64 night camp in the set's landscape and wood colors."""
    tile, x = _camp.campsite(pack, set_name, seed)
    _camp.hearth(tile, x, BEATS[0].ember)
    return tile


def camp_frames(pack, set_name, seed):
    """Light the same bedroll and pack with three flame shapes timed to the idle clock."""
    site, x = _camp.campsite(pack, set_name, seed)
    frames = []
    for beat in BEATS:
        tile = Drawing(site.w, site.h)
        tile.px = [row[:] for row in site.px]
        _camp.hearth(tile, x, beat.ember)
        frames.append(tile)
    return tuple(frames)


@dataclass(frozen=True)
class Layer:
    """One positioned image sequence sampled at DELAYS_MS."""
    frames: tuple

    @property
    def still(self):
        """The Canvas to use for reduced motion, exactly frame zero."""
        return self.frames[0]


@dataclass(frozen=True)
class BannerLayers:
    """Paste the figure at figure_box (x, y, width, height), then its foreground at (0, 0)."""
    background: Layer
    figure: Layer
    foreground: Layer
    figure_box: tuple
    alternate_figure: Layer | None
    alternate_foreground: Layer | None


def _costume_layers(pack, look, seed, skin, presentation, expression, hair, eyes):
    options = room.portrait_options(seed, look, presentation, expression, hair, eyes)
    figures = figure_frames(pack, look, skin=skin, presentation=presentation, **options)
    fig = figures[0]
    x, y = banner_figure_box(pack, fig)
    oak = Drawing(252, 72)
    room.counter(oak, (x+16, y+10))
    fronts = []
    for beat in BEATS:
        hands = _render(pack, look, skin, presentation,
                        foreground_only=True, motion=beat, **options)
        front = Canvas(oak.w, oak.h)
        front.px = [row[:] for row in oak.px]
        front.paste(hands, x, y)
        fronts.append(front)
    return Layer(figures), Layer(tuple(fronts)), (x, y, fig.w, fig.h)


def banner_layers(pack, look, stats, harnesses=(), seed=None, *, alternate=None,
                  presentation="neutral", expression=None, hair=None, eyes=None, skin=None):
    """Draw a shared 252 × 72 room and one or two registered costumes.

    The main look, ranked stat shares, harness names and seed furnish the room.
    Each costume has a 64 × 64 figure and a banner-sized transparent counter
    with its own fingers and equipment over the lip. Swap both at the same
    frame index. Each layer exposes .frames and .still. With no close look the
    two alternate layers are None. An omitted seed uses the original face.
    """
    plan = room.plan_room(pack, look, stats, "" if seed is None else seed)
    berths = companions.berths(harnesses)
    background = Layer(tuple(room.furnished_room(pack, look, plan, berths, beat) for beat in BEATS))
    options = (seed, _skin(skin), presentation, expression, hair, eyes)
    main, front, box = _costume_layers(pack, look, *options)
    alt = alt_front = None
    if alternate is not None:
        alt, alt_front, _ = _costume_layers(pack, alternate, *options)
    return BannerLayers(background, main, front, box, alt, alt_front)


def berths(harnesses):
    """The harness keys the room's case shows, in its stable order: three at most."""
    return companions.berths(harnesses)


def pin(pack, achievement):
    """Draw the enamel pin for the pack's achievement ID, with the milestone fallback."""
    return tokens.pin(pack, achievement)


def trinket(pack, stat):
    """Draw the shelf miniature from the stat's equipment kit and four-color dye."""
    return tokens.trinket(pack, stat)


def instrument(harness):
    """Draw a party instrument by harness key, with a gramophone for unknown keys."""
    return companions.member(harness)
