"""card.svg: the share card. It draws only the card's allowlisted fields."""
from __future__ import annotations

from html import escape

from . import art, radar

W, H = 1200, 630
FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"


def _t(x, y, text, size, weight=400, fill="#f2f1ec", anchor="start", spacing=None) -> str:
    sp = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}"{sp}>{escape(str(text))}</text>')


def _clip(s: str, n: int) -> str:
    s = str(s)
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


MAX_STATS = 4
MAX_ACHIEVEMENTS = 4


def visible(card: dict) -> dict:
    """Exactly what the card draws. render_card draws only this and audit lists only this."""
    if not card.get("enabled"):
        return {}
    ranked = sorted((s for s in card["stats"] if s["pct"] > 0), key=lambda s: -s["pct"])
    v = {
        "set": f"{card['set']} set".upper(),
        "name": _clip(card["name"], 22),
        "class": card["class"],
        "multiclass": f"/ {card['multiclass']}" if card.get("multiclass") else "",
        "level": str(card["level"]),
        "stats": [(s["stat"], f"{s['pct']}%") for s in ranked[:MAX_STATS]],
        "achievements": [(_clip(a["title"], 24), a["when"]) for a in card.get("achievements", [])[-MAX_ACHIEVEMENTS:]],
        "party": "PARTY  " + "  ·  ".join(card["party"]) if card.get("party") else "",
        "projects": _clip("  ·  ".join(card["projects"]), 60) if card.get("projects") else "",
        "chart": card.get("chart", "radar"),
    }
    if v["chart"] == "radar":
        v["spokes"] = [(s["stat"], s["pct"]) for s in card["stats"]]
    else:
        v["bars"] = [(s["stat"], s["pct"]) for s in ranked]
    return v


PX, PY, PS = 64, 52, 4  # portrait plate corner and pixel size
TX = 64 + 32 * 4 + 16 + 24  # text right of the portrait


def render_card(card: dict, pack: dict | None = None) -> str:
    if not card.get("enabled"):
        raise ValueError("card is off for this profile")
    v = visible(card)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
           f'font-family="{FONT}" role="img" aria-label="{escape(v["name"])} stat card">']
    out.append(f'<rect width="{W}" height="{H}" rx="28" fill="#141413"/>')
    out.append(f'<rect x="14" y="14" width="{W - 28}" height="{H - 28}" rx="20" fill="none" stroke="#3a3936"/>')

    # Portrait: pixel art from the allowlisted set, class, multiclass and rounded shares only.
    out.append(f'<rect x="{PX}" y="{PY - 8}" width="{32 * PS + 16}" height="{32 * PS + 16}" rx="14" fill="#1f1f1d" '
               f'stroke="#3a3936"/>')
    out.append('<g shape-rendering="crispEdges">')
    out += art.card_portrait_paths(card, PX + 8, PY, PS, pack)
    out.append("</g>")
    # Left column: who and what.
    out.append(_t(TX, 92, v["set"], 18, 600, "#9c9a92", spacing="3"))
    out.append(_t(TX, 156, v["name"], _fit(v["name"], 60, LEFT_WIDTH - (TX - 64)), 700))
    # Class names are never cut. Each line shrinks until it fits the left column.
    out.append(_t(64, 238, v["class"], _fit(v["class"], 34), 600, "#7fb0f0"))
    if v["multiclass"]:
        out.append(_t(64, 268, v["multiclass"], _fit(v["multiclass"], 24), 500, "#9fc3f2"))

    out.append('<rect x="64" y="288" width="150" height="96" rx="14" fill="#1f1f1d" stroke="#3a3936"/>')
    out.append(_t(139, 348, v["level"], 56, 700, anchor="middle"))
    out.append(_t(139, 372, "LEVEL", 14, 600, "#9c9a92", anchor="middle", spacing="3"))

    y = 312
    for stat, pct in v["stats"]:
        out.append(_t(246, y, stat, 22, 600))
        out.append(_t(470, y, pct, 22, 600, "#9c9a92", anchor="end"))
        y += 26

    if v["achievements"]:
        out.append(_t(64, 420, "ACHIEVEMENTS", 14, 600, "#9c9a92", spacing="3"))
        y = 452
        for title, when in v["achievements"]:
            out.append(_t(64, y, title, 22, 600))
            out.append(_t(470, y, when, 18, 400, "#9c9a92", anchor="end"))
            y += 32
    if v["party"]:
        out.append(_t(64, H - 52, v["party"], 16, 600, "#9c9a92", spacing="1"))
    if v["projects"]:
        out.append(_t(W - 64, H - 52, v["projects"], 16, 400, "#9c9a92", anchor="end"))

    if v["chart"] == "radar":
        out += _radar(v["spokes"])
    else:
        out += _bars(v["bars"])
    out.append("</svg>")
    return "\n".join(out) + "\n"


def _radar(spokes: list) -> list:
    """Rounded shares on the common square-root scale, eight spokes in the set's order."""
    cx, cy, r = 850, 300, 190
    n = len(spokes)
    out = []
    for ring in radar.RINGS:
        fr = radar.radius(ring)
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (radar.point(cx, cy, r, i, n, fr) for i in range(n)))
        out.append(f'<polygon points="{pts}" fill="none" stroke="#2e2e2b" stroke-width="1.5"/>')
    for i in range(n):
        x, y = radar.point(cx, cy, r, i, n, 1.0)
        out.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#3a3936" stroke-width="1.5"/>')
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in
                    (radar.point(cx, cy, r, i, n, radar.radius(p / 100)) for i, (_, p) in enumerate(spokes)))
    out.append(f'<polygon points="{poly}" fill="#3987e5" fill-opacity="0.22" stroke="#5a9de9" stroke-width="3" '
               f'stroke-linejoin="round"/>')
    for i, (stat, p) in enumerate(spokes):
        x, y = radar.point(cx, cy, r, i, n, radar.radius(p / 100))
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#5a9de9"/>')
        lx, ly = radar.point(cx, cy, r, i, n, radar.LABEL_AT)
        out.append(_t(lx, ly + 7, stat, 19, 600, "#d9d7d0", anchor=radar.anchor(i, n)))
    return out


def _bars(bars: list) -> list:
    """Ranked bars when fewer than three stats have points, as on the sheet."""
    out = []
    x0, x1, y = 640, 1100, 200
    for stat, p in bars:
        out.append(_t(x0, y, stat, 22, 600, "#d9d7d0"))
        out.append(_t(x1, y, f"{p}%", 22, 600, "#9c9a92", anchor="end"))
        out.append(f'<rect x="{x0}" y="{y + 14}" width="{x1 - x0}" height="12" rx="6" fill="#2e2e2b"/>')
        out.append(f'<rect x="{x0}" y="{y + 14}" width="{(x1 - x0) * p / 100:.1f}" height="12" rx="6" fill="#5a9de9"/>')
        y += 80
    return out


LEFT_WIDTH = 540  # px from x=64 before the chart begins


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
    out.append(("level", v["level"]))
    out += [("stat", f"{s} {p}") for s, p in v["stats"]]
    out += [("spoke", s) for s, _ in v.get("spokes", [])]
    out += [("bar", f"{s} {p}%") for s, p in v.get("bars", [])]
    out += [("achievement", f"{t} · {w}") for t, w in v["achievements"]]
    if v["party"]:
        out.append(("party", v["party"]))
    if v["projects"]:
        out.append(("projects", v["projects"]))
    return out
