"""card.svg: the share card. It draws only the card's allowlisted fields, through visible()."""
from __future__ import annotations

import re
from html import escape

from . import art, radar
from .party import HARNESS_NAMES

W, H = 1200, 630
FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"


def _t(x, y, text, size, weight=400, fill="#f3eadb", anchor="start", spacing=None, family=None) -> str:
    sp = f' letter-spacing="{spacing}"' if spacing else ""
    fam = f' font-family="{family}"' if family else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}"{sp}{fam}>{escape(str(text))}</text>')


def _clip(s: str, n: int) -> str:
    s = str(s)
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


MAX_STATS = 4
MAX_ACHIEVEMENTS = 4
MAX_MEMBERS = 3


def visible(card: dict) -> dict:
    """Exactly what the card draws. render_card, render_card_png and audit use only this."""
    if not card.get("enabled"):
        return {}
    named = card.get("named") or []
    order = [s["stat"] for s in card["stats"]]
    # Highest rounded share first. On a tie, the stats the class and multiclass are named for come
    # first, so the bars never drop one of them; then the set's order.
    ranked = sorted((s for s in card["stats"] if s["pct"] > 0),
                    key=lambda s: (-s["pct"], s["stat"] not in named, order.index(s["stat"])))
    members = list(card.get("party") or [])
    days = card.get("days") if "level" in card else None
    v = {
        "set": f"{card['set']} set".upper(),
        "name": _clip(card["name"], 22),
        "class": card["class"],
        "multiclass": card.get("multiclass") or "",
        "level": str(card["level"]) if "level" in card else "",
        "stats": [(s["stat"], f"{s['pct']}%") for s in ranked[:MAX_STATS]],
        "achievements": [(_clip(a["title"], 24), a["when"]) for a in card.get("achievements", [])[-MAX_ACHIEVEMENTS:]],
        "party": "PARTY  " + "  ·  ".join(members) if members else "",
        "members": members[:MAX_MEMBERS],
        "projects": _clip("  ·  ".join(card["projects"]), 60) if card.get("projects") else "",
        "chart": card.get("chart", "radar"),
        "footer": _footer(card, days),
    }
    if v["chart"] == "radar":
        v["spokes"] = [(s["stat"], s["pct"]) for s in card["stats"]]
    else:
        v["bars"] = [(s["stat"], s["pct"]) for s in ranked]
    v["alt"] = alt_text(v, card["set"])
    return v


def _days(n: int) -> str:
    return f"{n} active day" if n == 1 else f"{n} active days"


def _footer(card: dict, days: dict | None) -> list:
    """Two lines that say what the card is: the tool, method and month, then what the numbers mean."""
    who = ["tinkerprint"]
    if card.get("method") is not None:
        who.append(f"method {card['method']}")
    if card.get("built"):
        who.append(str(card["built"]))
    if card.get("season"):
        who.append(f"season {card['season']}")
    if days:
        a, c = int(days.get("active", 0)), int(days.get("classified", 0))
        on = f" on {c} of {_days(a)}" if c < a else f" on {_days(a)}"
    else:
        on = ""
    meaning = f"Shares are of classified activity{on}."
    if "level" in card:
        meaning += " Level grows with active days."
    return [" · ".join(who), meaning]


def alt_text(v: dict, set_title: str) -> str:
    """One line for people who cannot see the card, from the visible fields only."""
    head = f"{v['class']}"
    if v["multiclass"]:
        head += f", multiclass {v['multiclass']}"
    if v["level"]:
        head += f", level {v['level']}"
    text = f"tinkerprint card for {v['name']}, {set_title} set: {head}."
    if v["stats"]:
        text += " Top stats " + ", ".join(f"{s} {p}" for s, p in v["stats"]) + "."
    if v["members"]:
        names = v["members"]
        text += " Party " + (names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]) + "."
    return text


def shows(card: dict) -> str:
    """What the card shows, in one line for the terminal after a build."""
    v = visible(card)
    if not v:
        return "nothing: the card is off"
    out = [f'name "{v["name"]}"', "set", "class"]
    if v["multiclass"]:
        out.append("multiclass")
    if v["level"]:
        out.append("level and active days")
    out.append(f"{len(v['stats'])} top stat{'s' if len(v['stats']) != 1 else ''}")
    out.append("radar of rounded shares" if v["chart"] == "radar" else "bars of rounded shares")
    if v["achievements"]:
        exact = any(re.search(r"\d, \d{4}$", w) for _, w in v["achievements"])
        n = len(v["achievements"])
        out.append(f"{n} achievement{'s' if n != 1 else ''} with {'dates' if exact else 'months'}")
    if v["members"]:
        out.append("party (" + ", ".join(v["members"]) + ")")
    if v["projects"]:
        out.append("projects (" + v["projects"] + ")")
    out += ["portrait", "footer"]
    return ", ".join(out)


TX = 64  # the left column's edge
SET_Y, NAME_Y, CLASS_Y = 58, 114, 162  # baselines of the set, the name and the class under it
PX, PY = 64, 184  # portrait frame
ACH_Y = 418  # the achievements heading; rows follow every ACH_STEP px
ACH_STEP = 23
BOTTOM_Y = 540  # baseline of the party (radar column) and the projects (left column)
RULE_Y = 558  # the line above the footer
FOOT_Y = (582, 604)  # baselines of the two footer lines
RADAR_LEFT = 640  # the radar's column starts here
RADAR_CX, RADAR_CY, RADAR_R = 850, 288, 178
RADAR_CLIP = 150  # the widest a spoke label may draw in card.png, so the longest stat names stay on the card
PORTRAIT_PX = 176  # the portrait's target size: an integer scale of the pack's canvas near this
SERIF = "'Iowan Old Style', 'Palatino Linotype', Palatino, 'Book Antiqua', P052, Georgia, serif"
# Lantern palette, shared with the sheet's dark theme.
BG, BG2, LINE, INK, INK2, MUTED, LANTERN, LANTERN2 = ("#121117", "#1d1b23", "#3a3542", "#f3eadb", "#c9bda8",
                                                       "#918774", "#eba84f", "#f2bb6c")


def portrait_box(pack: dict) -> tuple:
    """(scale, padding, frame) of the card's portrait: an integer scale, so pixels stay crisp."""
    resolution = pack["canvas"][0]
    scale = max(1, round(PORTRAIT_PX / resolution))
    padding = 4 if resolution == 48 else 8
    return scale, padding, resolution * scale + 2 * padding


def familiars(members: list, pack: dict) -> list:
    """The party's familiars, from the visible party names. Unknown names get the pack's fallback."""
    by_name = {v: k for k, v in HARNESS_NAMES.items()}
    return [art.familiar(pack, by_name.get(name, "")) for name in members[:MAX_MEMBERS]]


_PATH = re.compile(r'<path fill="(#[0-9a-fA-F]{6})" d="([^"]*)"/>')


def _merge(paths: list) -> list:
    """One path per ink across sprites that never overlap: the portrait and the familiars."""
    by_fill: dict = {}
    for p in paths:
        m = _PATH.fullmatch(p)
        if not m:
            raise ValueError("unexpected sprite path")
        by_fill.setdefault(m.group(1), []).append(m.group(2))
    return [f'<path fill="{fill}" d="{"".join(d)}"/>' for fill, d in sorted(by_fill.items())]


def render_card(card: dict, pack: dict | None = None) -> str:
    if not card.get("enabled"):
        raise ValueError("card is off for this profile")
    v = visible(card)
    pack = pack or art.default_pack()
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
           f'font-family="{FONT}" role="img" aria-label="{escape(v["alt"])}">',
           f'<title>{escape(v["alt"])}</title>']
    out.append('<defs><radialGradient id="glow" cx="0.3" cy="0" r="0.9"><stop offset="0" stop-color="#3a2a1c"/>'
               f'<stop offset="1" stop-color="{BG}"/></radialGradient>'
               '<radialGradient id="seal" cx="0.38" cy="0.3" r="0.75"><stop offset="0" stop-color="#fbe2a4"/>'
               '<stop offset="0.55" stop-color="#e0a447"/><stop offset="1" stop-color="#b8731f"/></radialGradient></defs>')
    out.append(f'<rect width="{W}" height="{H}" rx="28" fill="url(#glow)"/>')
    out.append(f'<rect x="14" y="14" width="{W - 28}" height="{H - 28}" rx="20" fill="none" stroke="{LINE}"/>')
    out.append(f'<rect x="{W // 2 - 60}" y="14" width="120" height="3" fill="{LANTERN}"/>')

    # Who: set, then the name across the top of the left column.
    out.append(_t(TX, SET_Y, v["set"], 16, 700, LANTERN, spacing="3"))
    out.append(_t(TX, NAME_Y, v["name"], name_size(v["name"]), 700, INK, family=SERIF))
    # The class gets its own line, large enough to read on a thumbnail. Never cut: it shrinks to fit.
    out.append(_t(TX, CLASS_Y, v["class"], class_size(v["class"]), 600, LANTERN2, family=SERIF))

    # Portrait: pixel art from the allowlisted set, class, multiclass and rounded shares only.
    scale, padding, frame = portrait_box(pack)
    out.append(f'<rect x="{PX - 3}" y="{PY - 3}" width="{frame + 6}" height="{frame + 6}" rx="16" fill="#0b0a0e" '
               f'stroke="{LANTERN}" stroke-opacity="0.55" stroke-width="2"/>')
    sprites = art.card_portrait_paths(card, PX + padding, PY + padding, scale, pack)
    # The party's familiars stand at the foot of the radar's column, before the party line.
    fx = RADAR_LEFT
    for f in familiars(v["members"], pack):
        sprites += f.svg_paths(2, fx, BOTTOM_Y + 4 - f.h * 2)
        fx += f.w * 2 + 6
    out.append(f'<g shape-rendering="crispEdges">{"".join(_merge(sprites))}</g>')
    if v["level"]:
        # Level: a lantern seal on the portrait's corner.
        sx, sy = PX + frame + 14, PY + frame - 14
        out.append(f'<circle cx="{sx}" cy="{sy}" r="44" fill="{BG}"/>')
        out.append(f'<circle cx="{sx}" cy="{sy}" r="39" fill="url(#seal)" stroke="#6e4214" stroke-width="3"/>')
        out.append(_t(sx, sy + 9, v["level"], 34 if len(v["level"]) < 3 else 26, 700, "#2b1606", anchor="middle",
                      family=SERIF))
        out.append(_t(sx, sy + 25, "LEVEL", 10, 700, "#2b1606", anchor="middle", spacing="2"))

    # Beside the portrait: the multiclass under its label, then the top shares, each with a bar.
    cx0 = PX + frame + 58
    room = COL_RIGHT - cx0
    y = PY + 30
    if v["multiclass"]:
        out.append(_t(cx0, PY + 18, "MULTICLASS", 12, 700, MUTED, spacing="2"))
        out.append(_t(cx0, PY + 46, v["multiclass"], _fit(v["multiclass"], 24, room), 500, INK2, family=SERIF))
        y = PY + 82
    for stat, pct in v["stats"]:
        hue = art.stat_ramp(pack, stat)
        out.append(_t(cx0, y, stat, 18, 600, INK))
        out.append(_t(COL_RIGHT, y, pct, 18, 600, INK2, anchor="end"))
        p = int(pct.rstrip("%"))
        out.append(f'<rect x="{cx0}" y="{y + 8}" width="{room}" height="4" rx="2" fill="#2d2b34"/>')
        out.append(f'<rect x="{cx0}" y="{y + 8}" width="{room * p / 100:.1f}" height="4" rx="2" fill="{hue[1]}"/>')
        y += 31

    if v["achievements"]:
        out.append(_t(TX, ACH_Y, "ACHIEVEMENTS", 13, 700, MUTED, spacing="3"))
        y = ACH_Y + 24
        for title, when in v["achievements"]:
            out.append(f'<rect x="64" y="{y - 11}" width="7" height="7" fill="{LANTERN}" transform="rotate(45 67.5 {y - 7.5})"/>')
            out.append(_t(84, y, title, 19, 600, INK))
            out.append(_t(COL_RIGHT, y, when, 16, 400, MUTED, anchor="end"))
            y += ACH_STEP
    # Party in the radar's column after its familiars, projects in the left column.
    if v["party"]:
        out.append(_t(fx + 6, BOTTOM_Y, v["party"], party_size(v["party"], fx + 6), 700, MUTED, spacing="1"))
    if v["projects"]:
        out.append(_t(TX, BOTTOM_Y, v["projects"], projects_size(v["projects"]), 400, MUTED))

    if v["chart"] == "radar":
        out += _radar(v["spokes"], pack)
    else:
        out += _bars(v["bars"], pack)
    # The footer: what made the card, and what its numbers mean.
    out.append(f'<rect x="{TX}" y="{RULE_Y}" width="{W - 2 * TX}" height="1" fill="{LINE}"/>')
    out.append(_t(TX, FOOT_Y[0], v["footer"][0], footer_size(v["footer"][0]), 600, INK2))
    out.append(_t(TX, FOOT_Y[1], v["footer"][1], footer_size(v["footer"][1]), 400, MUTED))
    out.append("</svg>")
    return "\n".join(out) + "\n"


def _radar(spokes: list, pack: dict) -> list:
    """Rounded shares on the common square-root scale, eight spokes in the set's order."""
    cx, cy, r = RADAR_CX, RADAR_CY, RADAR_R
    n = len(spokes)
    out = []
    for ring in radar.RINGS:
        fr = radar.radius(ring)
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (radar.point(cx, cy, r, i, n, fr) for i in range(n)))
        out.append(f'<polygon points="{pts}" fill="none" stroke="#2d2b34" stroke-width="1.5"/>')
    for i in range(n):
        x, y = radar.point(cx, cy, r, i, n, 1.0)
        out.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="{LINE}" stroke-width="1.5"/>')
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in
                    (radar.point(cx, cy, r, i, n, radar.radius(p / 100)) for i, (_, p) in enumerate(spokes)))
    out.append(f'<polygon points="{poly}" fill="{LANTERN}" fill-opacity="0.2" stroke="{LANTERN}" stroke-width="3" '
               f'stroke-linejoin="round"/>')
    # Empty stats first, so their dots at the center never cover a lit one.
    for i, (stat, p) in sorted(enumerate(spokes), key=lambda t: t[1][1] > 0):
        x, y = radar.point(cx, cy, r, i, n, radar.radius(p / 100))
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="7" fill="{art.stat_ramp(pack, stat)[1]}" stroke="{BG}" stroke-width="2.5"/>')
        lx, ly = radar.point(cx, cy, r, i, n, radar.LABEL_AT)
        out.append(_t(lx, ly + 7, stat, 19, 600, INK if p > 0 else MUTED, anchor=radar.anchor(i, n)))
    return out


def _bars(bars: list, pack: dict) -> list:
    """Ranked bars when fewer than three stats have points, as on the sheet."""
    out = []
    x0, x1, y = RADAR_LEFT, 1100, 160
    for stat, p in bars:
        out.append(_t(x0, y, stat, 22, 600, INK))
        out.append(_t(x1, y, f"{p}%", 22, 600, INK2, anchor="end"))
        out.append(f'<rect x="{x0}" y="{y + 14}" width="{x1 - x0}" height="12" rx="6" fill="{BG2}"/>')
        out.append(f'<rect x="{x0}" y="{y + 14}" width="{(x1 - x0) * p / 100:.1f}" height="12" rx="6" fill="{art.stat_ramp(pack, stat)[1]}"/>')
        y += 80
    return out


LEFT_WIDTH = 540  # px from x=64 before the chart begins


NAME_RIGHT = 560  # the name ends here, clear of the radar's top-left spoke label
COL_RIGHT = 480  # the class, shares and achievements end here, clear of the radar's left spoke label

# Generous bold glyph widths in em, by class, so the widest system fonts still fit.
_WIDE, _NARROW, _THIN = set("WMmw@"), set("ijlI.,'|!:;"), set("ftr")


def text_em(text: str) -> float:
    """The width of bold text in em: a fixed table, deterministic, on the wide side."""
    em = 0.0
    for ch in text:
        if ch in _WIDE:
            em += 1.05
        elif ch in _NARROW:
            em += 0.36
        elif ch == " ":
            em += 0.35
        elif ch in _THIN:
            em += 0.48
        elif ch.islower():
            em += 0.68
        else:
            em += 0.82
    return em


def name_size(name: str) -> int:
    """The name's font size: 60 px, stepped down until the name fits between the portrait and
    NAME_RIGHT. Deterministic, never cut beyond the card's 22-character clip."""
    return max(12, min(60, int((NAME_RIGHT - TX) / max(1.0, text_em(name)))))


def class_size(text: str) -> int:
    """The class line: up to 44 px, stepped down until it fits between TX and NAME_RIGHT."""
    return max(12, min(44, int((NAME_RIGHT - TX) / max(1.0, text_em(text)))))


def party_size(text: str, x: float) -> int:
    """The party line ends at the right margin. Letter spacing adds 1 px a glyph."""
    return max(7, min(15, int((W - 64 - x - len(text)) / max(1.0, text_em(text)))))


def projects_size(text: str) -> int:
    """The projects line stays in the left column, 20 px before the radar's column."""
    return max(7, min(16, int((RADAR_LEFT - 20 - TX) / max(1.0, text_em(text)))))


def footer_size(text: str) -> int:
    """A footer line: up to 15 px, smaller when it would run past the right margin."""
    return max(8, min(15, int((W - 2 * TX) / max(1.0, text_em(text)))))


def _fit(text: str, size: int, width: int = LEFT_WIDTH) -> int:
    """A font size at which text fits the given width, at about 0.6 em per character."""
    return max(12, min(size, int(width / (0.6 * max(1, len(text))))))


def card_strings(card: dict) -> list:
    """Every data string the card draws, as (field, value) pairs, from the same selection render_card uses."""
    v = visible(card)
    if not v:
        return []
    out = [("set", v["set"]), ("name", v["name"]), ("class", v["class"])]
    if v["multiclass"]:
        out.append(("multiclass", v["multiclass"]))
    if v["level"]:
        out.append(("level", v["level"]))
    out += [("stat", f"{s} {p}") for s, p in v["stats"]]
    out += [("spoke", s) for s, _ in v.get("spokes", [])]
    out += [("bar", f"{s} {p}%") for s, p in v.get("bars", [])]
    out += [("achievement", f"{t} · {w}") for t, w in v["achievements"]]
    if v["party"]:
        out.append(("party", v["party"]))
    if v["projects"]:
        out.append(("projects", v["projects"]))
    out += [("footer", line) for line in v["footer"]]
    out.append(("alt", v["alt"]))
    return out
