"""gallery: one page with every class portrait of both sets, every familiar, icon and trinket, and a
few banners, so a pack can be judged at a glance. Everything on it is invented."""
from __future__ import annotations

import os
from html import escape

from . import art
from .achievements import RULES
from .art.compose import look_for
from .datadir import _write
from .party import HARNESS_NAMES
from .render_html import CSS, JS, _chronicle
from .sets import GENERALIST, PAIR, SETS, SPECIALIST

GALLERY_CSS = """
.grid { display: grid; gap: 10px; grid-template-columns: repeat(auto-fill, minmax(120px, 1fr)); }
.tile { padding: 10px; display: flex; flex-direction: column; align-items: center; text-align: center; gap: 4px; }
.tile svg { width: 96px; height: 96px; border-radius: 6px; }
.tile .portrait { margin: 0 auto; }
.tile.small svg { width: 54px; height: 54px; border-radius: 0; }
.tile .nm { font-weight: 600; font-size: 14px; }
.tile .why { font-size: 11px; color: var(--muted); }
.banners { display: grid; gap: 12px; }
.banners figure { margin: 0; }
.banners svg { width: 100%; height: auto; border-radius: 10px; border: 1px solid var(--border-2); }
.banners figcaption { font-size: 12px; color: var(--muted); margin-top: 4px; }
"""

BANNERS = (
    ("tinkerer", "pair", ["Art", "Worlds"], [("Art", 30), ("Worlds", 25), ("Lore", 15), ("Community", 10),
                                             ("Systems", 10), ("Tools", 10)], ["Lore", "Community"],
     ["claude", "codex", "agy"], "A tinkerer pair with a multiclass and a full party"),
    ("builder", "pair", ["Logic", "Tests"], [("Logic", 40), ("Tests", 20), ("Data", 15), ("Infra", 15), ("Docs", 10)],
     ["Data", "Infra"], ["claude", "codex"], "A builder pair with two harnesses"),
    ("builder", "specialist", ["Infra"], [("Infra", 60), ("Tools", 25), ("Docs", 15)], None, ["codex"],
     "A builder specialist"),
    ("tinkerer", "generalist", [], [("Tools", 20), ("Art", 15), ("Systems", 15), ("Worlds", 15), ("Lore", 15),
                                    ("Interface", 10), ("Community", 10)], None, [], "A generalist with no party"),
)


def _e(x) -> str:
    return escape(str(x), quote=True)


def _tile(svg: str, name: str, why: str = "", small: bool = False) -> str:
    cls = "card tile small" if small else "card tile"
    w = f'<div class="why">{_e(why)}</div>' if why else ""
    return f'<article class="{cls}">{svg}<div class="nm">{_e(name)}</div>{w}</article>'


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
    for set_name in SETS:
        tiles = []
        for name, look, why in class_looks(set_name):
            pic = art.portrait(pack, look)
            pngs[f"{set_name}-{name.lower()}.png"] = pic
            tiles.append(_tile(pic.svg(3, f"Portrait of a {name}", "px"), name, why))
        sections.append(f'<h2>{set_name.capitalize()} set</h2><p class="lede">Every class: 8 specialists, 28 pairs and '
                        f'the generalist. A pair wears its top stat and holds its runner-up, so the same pair '
                        f'with the order swapped looks different.</p><div class="grid">{"".join(tiles)}</div>')
    extra = []
    for set_name, kind, stats, ranked, multi, why in (
            ("tinkerer", "pair", ["Systems", "Tools"], ["Systems", "Tools", "Art", "Lore"], ["Art", "Lore"],
             "Engineer / Toymaker"),
            ("builder", "pair", ["Logic", "Data"], ["Data", "Logic", "Tests", "Docs"], ["Tests", "Docs"],
             "Alchemist / Arbiter"),
            ("builder", "specialist", ["Tools"], ["Tools", "Logic"], None, "Artificer holding Logic's staff"),
            ("tinkerer", None, [], [], None, "Unclassed")):
        look = look_for(set_name, kind, stats, ranked, multi)
        extra.append(_tile(art.portrait(pack, look).svg(3, why, "px"), why,
                           "multiclass cape" if multi else ""))
    sections.append('<h2>Multiclass and more</h2><p class="lede">A multiclass adds a cape in its first stat\'s colors '
                    f'with a hem in its second.</p><div class="grid">{"".join(extra)}</div>')
    # A close call: the hero portrait changes costume every few seconds, or on hover.
    a = look_for("builder", "pair", ["Logic", "Tools"], ["Logic", "Tools", "Data"])
    b = look_for("builder", "pair", ["Logic", "Data"], ["Logic", "Tools", "Data"])
    flip = (f'<article class="card tile"><div class="portrait flip">{art.portrait(pack, a).svg(3, "Engineer", "px main")}'
            f'{art.portrait(pack, b).svg(3, "Alchemist", "px alt")}</div><div class="nm">Engineer, close to Alchemist'
            f'</div><div class="why">flips between both costumes</div></article>')
    sample = {"profile": {"set": "tinkerer"}, "chronicle": [
        {"label": "2025 Q1", "active_days": 31, "class": {"kind": "pair", "stats": ["Tools", "Art"], "name": "Toymaker"},
         "shares": {"Tools": 40, "Art": 30, "Systems": 20}},
        {"label": "2025 Q2", "active_days": 44, "class": {"kind": "pair", "stats": ["Systems", "Tools"], "name": "Engineer"},
         "close": "Clockmaker", "shares": {"Systems": 35, "Tools": 25, "Art": 25}},
        {"rest": True, "label": "2025 Q3", "label_to": "2025 Q4", "quarters": 2},
        {"label": "2026 Q1", "active_days": 12, "class": {"kind": "specialist", "stats": ["Lore"], "name": "Lorekeeper"},
         "shares": {"Lore": 60, "Worlds": 25, "Art": 15}},
        {"label": "2026 Q2", "active_days": 38, "class": {"kind": "generalist", "stats": [], "name": "Wanderer"},
         "shares": {"Lore": 20, "Worlds": 20, "Art": 15, "Tools": 15, "Systems": 15, "Community": 15}}]}
    sections.append(f'<h2>Sheet pieces</h2><p class="lede">A close call on the hero portrait, and a chronicle with a '
                    f'quiet stretch. Invented data.</p><div class="grid">{flip}</div>'
                    + _chronicle(sample, pack).replace("<h2>Chronicle</h2>", ""))
    fams = []
    for h in ("claude", "codex", "agy", "other"):
        f = art.familiar(pack, h)
        pngs[f"familiar-{h}.png"] = f
        fams.append(_tile(f.svg(3, "", "px"), HARNESS_NAMES.get(h, "Any other harness"),
                          pack["familiars"].get(h, pack["familiars"]["default"]), small=True))
    sections.append(f'<h2>Familiars</h2><p class="lede">One creature per harness, mapped in the pack.</p>'
                    f'<div class="grid">{"".join(fams)}</div>')
    icons = []
    for key, (title, rule) in list(RULES.items()) + [("milestone", ("Milestone", "Written by hand."))]:
        ic = art.icon(pack, key)
        pngs[f"icon-{key}.png"] = ic
        icons.append(_tile(ic.svg(3, "", "px"), title, rule, small=True))
    fire = art.campfire(pack)
    icons.append(_tile(fire.svg(3, "", "px"), "Resting at camp", "a quiet chronicle chapter", small=True))
    sections.append(f'<h2>Achievement icons</h2><div class="grid">{"".join(icons)}</div>')
    trinkets = [_tile(art.trinket(pack, s).svg(4, "", "px"), s, pack["looks"][s]["trinket"], small=True)
                for s in sorted(pack["looks"])]
    sections.append(f'<h2>Shelf trinkets</h2><p class="lede">One per stat. The banner\'s shelves hold them in '
                    f'proportion to the stat\'s share.</p><div class="grid">{"".join(trinkets)}</div>')
    banners = []
    for i, (set_name, kind, stats, ranked, multi, harnesses, why) in enumerate(BANNERS):
        look = look_for(set_name, kind, stats, [s for s, _ in ranked], multi)
        b = art.banner(pack, look, ranked, harnesses, f"gallery|{i}")
        pngs[f"banner-{i + 1}.png"] = b
        banners.append(f'<figure>{b.svg(1, why, "px")}<figcaption>{_e(why)}</figcaption></figure>')
    sections.append(f'<h2>Banners</h2><div class="banners">{"".join(banners)}</div>')
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'">
<title>tinkerprint gallery</title>
<style>{CSS}{GALLERY_CSS}</style>
</head>
<body>
<div class="wrap">
<div class="top">
  <div class="eyebrow">tinkerprint · <b>art gallery</b> · pack {_e(pack.get("name", "custom"))}</div>
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
    _write(path, page)
    paths = [path]
    if png:
        folder = os.path.join(out, "png")
        os.makedirs(folder, exist_ok=True)
        for name, pic in sorted(pngs.items()):
            scale = 4 if name.startswith("banner") else 8
            p = os.path.join(folder, name)
            _write(p, pic.png(scale))
        paths.append(folder + os.sep)
    return paths
