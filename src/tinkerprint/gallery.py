"""gallery: one page with the Keepsake art a pack draws, so a pack can be judged at a glance.

Every class of both sets in the neutral presentation, the three presentations, every expression,
hairstyle, eye color and skin, every pair in both orders, a room for each set, the pins, trinkets
and party instruments, and the camp. Everything on it is invented.
"""
from __future__ import annotations

import base64
import os
from html import escape

from . import art
from .achievements import RULES
from .art import keepsake
from .art.compose import look_for
from .art.pixels import Canvas
from .datadir import _write
from .render_html import CSP, CSS, JS, _chronicle, _layer, _worn
from .sets import GENERALIST, PAIR, SETS, SPECIALIST

GALLERY_CSS = """
.grid { display: grid; gap: 10px; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); }
.grid.small { grid-template-columns: repeat(auto-fill, minmax(96px, 1fr)); }
.tile { padding: 10px; display: flex; flex-direction: column; align-items: center; text-align: center; gap: 4px; }
.tile img { width: 128px; height: 128px; image-rendering: pixelated; border-radius: 6px; background: var(--surface-2); }
.grid.small .tile img { width: auto; height: auto; background: none; border-radius: 0; }
.tile .nm { font-weight: 600; font-size: 14px; }
.tile .why { font-size: 11px; color: var(--muted); }
.rooms { display: grid; gap: 12px; }
.rooms figure { margin: 0; }
.rooms .room-box { position: relative; aspect-ratio: 252 / 72; border-radius: 10px; overflow: hidden; border: 1px solid var(--border-2); }
.rooms img { position: absolute; inset: 0; width: 100%; height: 100%; image-rendering: pixelated; }
.rooms figcaption { font-size: 12px; color: var(--muted); margin-top: 4px; }
"""

# Each room: set, class, stats with their rounded shares, multiclass, party and caption.
ROOMS = (
    ("builder", "pair", ["Logic", "Data"], [("Logic", 40), ("Data", 30), ("Tests", 15), ("Docs", 15)],
     ["Tests", "Docs"], ["claude", "codex"], "Marigold Loom", "A builder pair with a multiclass and two party members"),
    ("tinkerer", "specialist", ["Art"], [("Art", 55), ("Worlds", 25), ("Lore", 20)], None,
     ["claude", "codex", "agy"], "Tansy Forge", "A tinkerer specialist with a full case"),
)

SAMPLE = ("builder", "Logic")  # the class that models expressions, hair, eyes and skins


def _e(x) -> str:
    return escape(str(x), quote=True)


def _img(pic: Canvas, scale: int = 1, alt: str = "") -> str:
    data = base64.b64encode(pic.png(scale, indexed=True)).decode("ascii")
    return f'<img src="data:image/png;base64,{data}" width="{pic.w * scale}" height="{pic.h * scale}" alt="{_e(alt)}">'


def _tile(img: str, name: str, why: str = "") -> str:
    w = f'<div class="why">{_e(why)}</div>' if why else ""
    return f'<article class="card tile">{img}<div class="nm">{_e(name)}</div>{w}</article>'


def _grid(tiles: list, small: bool = False) -> str:
    return f'<div class="grid{" small" if small else ""}">{"".join(tiles)}</div>'


def class_looks(set_name: str) -> list:
    """(class name, look, note) for every class of a set: specialists, pairs, then the generalist."""
    out = []
    for stat, name in SPECIALIST[set_name].items():
        out.append((name, look_for(set_name, "specialist", [stat], [stat]), f"{stat} specialist"))
    for (a, b), name in PAIR[set_name].items():
        out.append((name, look_for(set_name, "pair", [a, b], [a, b]), f"wears {a}, holds {b}"))
    out.append((GENERALIST[set_name], look_for(set_name, "generalist", [], [SETS[set_name][0]]), "no stat over 20%"))
    return out


def write_gallery(out: str, pack: dict | None = None, png: bool = False) -> list:
    pack = pack or art.default_pack()
    os.makedirs(out, exist_ok=True)
    pngs: dict = {}
    sections = []

    def figure(key, look, **kw):
        pic = keepsake.figure(pack, look, **kw)
        pngs[key + ".png"] = pic
        return _img(pic)

    for set_name in SETS:
        tiles = [_tile(figure(f"{set_name}-{name.lower()}", look), name, why)
                 for name, look, why in class_looks(set_name)]
        sections.append(f'<h2>{set_name.capitalize()} set</h2><p class="lede">Every class in the neutral '
                        f'presentation: 8 specialists, 28 pairs and the generalist. A pair wears its top stat’s '
                        f'outfit and holds its runner-up’s tool.</p>{_grid(tiles)}')
    # Each pair the other way round: the same two stats, the other outfit and tool.
    for set_name in SETS:
        tiles = [_tile(figure(f"{set_name}-{b.lower()}-{a.lower()}", look_for(set_name, "pair", [a, b], [b, a])),
                       name, f"wears {b}, holds {a}") for (a, b), name in PAIR[set_name].items()]
        sections.append(f'<h2>{set_name.capitalize()} pairs, the other way round</h2><p class="lede">Every pair '
                        f'again with its order swapped, as when the second stat leads.</p>{_grid(tiles)}')
    extra = []
    for set_name, kind, stats, ranked, multi, why in (
            ("tinkerer", "pair", ["Systems", "Tools"], ["Systems", "Tools", "Art", "Lore"], ["Art", "Lore"],
             "Engineer / Toymaker"),
            ("builder", "pair", ["Logic", "Data"], ["Data", "Logic", "Tests", "Docs"], ["Tests", "Docs"],
             "Alchemist / Arbiter"),
            ("tinkerer", None, [], [], None, "Unclassed")):
        look = look_for(set_name, kind, stats, ranked, multi)
        extra.append(_tile(figure(f"extra-{why.split()[0].lower()}", look), why, "multiclass cape" if multi else ""))
    sections.append('<h2>Multiclass and unclassed</h2><p class="lede">A multiclass adds a cape in its first '
                    f'stat\'s colors with a hem in its second.</p>{_grid(extra)}')

    set_name, stat = SAMPLE
    name = SPECIALIST[set_name][stat]
    look = look_for(set_name, "specialist", [stat], [stat])
    modes = [_tile(figure(f"presentation-{mode}", look, presentation=mode), mode.capitalize())
             for mode in ("neutral", "man", "woman")]
    sections.append(f'<h2>Presentation</h2><p class="lede">The {_e(name)} in each presentation. It is set under '
                    f'[look] and never picked at random.</p>{_grid(modes)}')
    faces = [_tile(figure(f"expression-{x}", look, expression=x), x.capitalize()) for x in keepsake.EXPRESSIONS]
    hair = [_tile(figure(f"hair-{x.replace(' ', '-')}", look, presentation=mode, hair=x), x.capitalize(), mode)
            for mode, cuts in keepsake.HAIRSTYLES.items() for x in cuts]
    eyes = [_tile(figure(f"eyes-{x}", look, eyes=x), x.capitalize()) for x in keepsake.EYES]
    skins = [_tile(figure(f"skin-{x}", look, skin=x), x.capitalize()) for x in keepsake.SKINS]
    sections.append(f'<h2>Faces</h2><p class="lede">The {_e(name)} with each expression, hairstyle, eye color and '
                    f'skin. Expression, hair and eyes left unset are picked from the card\'s name.</p>'
                    f'<h3>Expressions</h3>{_grid(faces)}<h3>Hair</h3>{_grid(hair)}'
                    f'<h3>Eyes</h3>{_grid(eyes)}<h3>Skin</h3>{_grid(skins)}')

    rooms = []
    for i, (set_name, kind, stats, ranked, multi, crew, seed, why) in enumerate(ROOMS):
        look = look_for(set_name, kind, stats, [s for s, _ in ranked], multi)
        layers = keepsake.banner_layers(pack, look, ranked, crew, seed)
        worn = _worn(layers.figure, layers.foreground, layers.figure_box)
        still = Canvas(252, 72)
        still.paste(layers.background.still)
        still.paste(worn[0])
        pngs[f"room-{set_name}.png"] = still
        rooms.append(f'<figure><div class="room-box">{_layer(layers.background.frames, why, "room")}'
                     f'{_layer(worn, "", "wear")}</div><figcaption>{_e(why)}</figcaption></figure>')
    sections.append('<h2>Rooms</h2><p class="lede">Each set\'s room idles on one clock. The name picks the view, '
                    'the finish and the plant; the stats stock the shelves; the party stands in the case.</p>'
                    f'<div class="rooms">{"".join(rooms)}</div>')

    pins = []
    for key, (title, rule) in list(RULES.items()) + [("milestone", ("Milestone", "Written by hand."))]:
        pin = keepsake.pin(pack, key)
        pngs[f"pin-{key}.png"] = pin
        pins.append(_tile(_img(pin, 3), title, rule))
    trinkets = []
    for stat in sorted({s for stats in SETS.values() for s in stats}):
        t = keepsake.trinket(pack, stat)
        pngs[f"trinket-{stat.lower()}.png"] = t
        trinkets.append(_tile(_img(t, 4), stat))
    party = []
    for h, (harness, instrument) in keepsake.MEMBERS.items():
        pic = keepsake.instrument(h)
        pngs[f"instrument-{h}.png"] = pic
        party.append(_tile(_img(pic, 4), "Any other harness" if h == "default" else harness, instrument))
    sections.append(f'<h2>Pins</h2>{_grid(pins, True)}'
                    f'<h2>Trinkets</h2><p class="lede">One per stat, on the stat cards and the room\'s shelves.</p>'
                    f'{_grid(trinkets, True)}'
                    f'<h2>Party instruments</h2><p class="lede">One per harness, drawn from its name alone.</p>'
                    f'{_grid(party, True)}')

    camps = []
    for set_name in SETS:
        frames = keepsake.camp_frames(pack, set_name, "Rowan Quill")
        pngs[f"camp-{set_name}.png"] = frames[0]
        camps.append(_tile(_layer(frames, f"The {set_name} camp", "camp"), set_name.capitalize()))
    sample = {"profile": {"set": "tinkerer", "name": "Rowan Quill"}, "chronicle": [
        {"label": "2025 Q1", "active_days": 31, "class": {"kind": "pair", "stats": ["Tools", "Art"], "name": "Toymaker"},
         "shares": {"Tools": 40, "Art": 30, "Systems": 20}},
        {"label": "2025 Q2", "active_days": 44, "class": {"kind": "pair", "stats": ["Systems", "Tools"], "name": "Engineer"},
         "close": "Clockmaker", "shares": {"Systems": 35, "Tools": 25, "Art": 25}},
        {"rest": True, "label": "2025 Q3", "label_to": "2025 Q4", "quarters": 2},
        {"label": "2026 Q1", "active_days": 12, "class": {"kind": "specialist", "stats": ["Lore"], "name": "Lorekeeper"},
         "shares": {"Lore": 60, "Worlds": 25, "Art": 15}}]}
    sections.append('<h2>Camp and chronicle</h2><p class="lede">Quiet quarters rest at camp. A chronicle with a quiet '
                    f'stretch, for an invented person.</p>{_grid(camps)}'
                    + _chronicle(sample, pack).replace("<h2>Chronicle</h2>", ""))
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{CSP}">
<title>tinkerprint gallery</title>
<style>{CSS}{GALLERY_CSS}</style>
</head>
<body>
<div class="wrap">
<div class="top">
  <div class="eyebrow">tinkerprint · <b>art gallery</b></div>
  <button class="ghost-btn" id="themeBtn" type="button">Theme: auto</button>
</div>
<p class="lede">Every picture the pack can draw. Portraits follow class shape only, never level or points.</p>
{"".join(sections)}
</div>
<script>{JS}</script>
</body>
</html>
"""
    path = os.path.join(out, "gallery.html")
    _write(path, page, share=True)
    paths = [path]
    if png:
        folder = os.path.join(out, "png")
        os.makedirs(folder, exist_ok=True)
        for name, pic in sorted(pngs.items()):
            scale = 4 if name.startswith("room") else 8
            p = os.path.join(folder, name)
            _write(p, pic.png(scale), share=True)
        paths.append(folder + os.sep)
    return paths
