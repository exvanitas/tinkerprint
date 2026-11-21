"""card.svg: the share card. It draws only the card's allowlisted fields."""
from __future__ import annotations

import math
from html import escape

W, H = 1200, 630
FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif"


def _t(x, y, text, size, weight=400, fill="#f2f1ec", anchor="start", spacing=None) -> str:
    sp = f' letter-spacing="{spacing}"' if spacing else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" font-weight="{weight}" fill="{fill}" '
            f'text-anchor="{anchor}"{sp}>{escape(str(text))}</text>')


def _clip(s: str, n: int) -> str:
    s = str(s)
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def render_card(card: dict) -> str:
    if not card.get("enabled"):
        raise ValueError("card is off for this profile")
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
           f'font-family="{FONT}" role="img" aria-label="{escape(_clip(card["name"], 40))} stat card">']
    out.append(f'<rect width="{W}" height="{H}" rx="28" fill="#141413"/>')
    out.append(f'<rect x="14" y="14" width="{W - 28}" height="{H - 28}" rx="20" fill="none" stroke="#3a3936"/>')

    # Left column: who and what.
    out.append(_t(64, 96, f"{card['set']} set".upper(), 18, 600, "#9c9a92", spacing="3"))
    out.append(_t(64, 168, _clip(card["name"], 22), 60, 700))
    cls = card["class"] + (f" / {card['multiclass']}" if card.get("multiclass") else "")
    out.append(_t(64, 222, _clip(cls, 34), 34, 600, "#7fb0f0"))

    out.append('<rect x="64" y="256" width="150" height="104" rx="14" fill="#1f1f1d" stroke="#3a3936"/>')
    out.append(_t(139, 322, card["level"], 56, 700, anchor="middle"))
    out.append(_t(139, 348, "LEVEL", 14, 600, "#9c9a92", anchor="middle", spacing="3"))

    top = sorted((s for s in card["stats"] if s["pct"] > 0), key=lambda s: -s["pct"])[:4]
    y = 286
    for s in top:
        out.append(_t(246, y, s["stat"], 22, 600))
        out.append(_t(470, y, f"{s['pct']}%", 22, 600, "#9c9a92", anchor="end"))
        y += 26

    ach = card.get("achievements", [])[-4:]
    if ach:
        out.append(_t(64, 412, "ACHIEVEMENTS", 14, 600, "#9c9a92", spacing="3"))
        y = 446
        for a in ach:
            out.append(_t(64, y, _clip(a["title"], 24), 22, 600))
            out.append(_t(470, y, a["when"], 18, 400, "#9c9a92", anchor="end"))
            y += 32
    party = card.get("party", [])
    if party:
        out.append(_t(64, H - 52, "PARTY  " + "  ·  ".join(party), 16, 600, "#9c9a92", spacing="1"))
    if card.get("projects"):
        out.append(_t(W - 64, H - 52, _clip("  ·  ".join(card["projects"]), 60), 16, 400, "#9c9a92", anchor="end"))

    # Right column: radar of rounded shares, eight spokes in the set's order.
    cx, cy, r = 850, 300, 190
    stats = card["stats"]
    n = len(stats)
    peak = max([s["pct"] for s in stats] + [20])
    vmax = min(100, int(math.ceil(peak / 10.0)) * 10)

    def pt(i, v):
        a = math.radians(-90 + i * 360 / n)
        return cx + math.cos(a) * r * v / vmax, cy + math.sin(a) * r * v / vmax

    for k in (1, 2, 3, 4):
        pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, vmax * k / 4) for i in range(n)))
        out.append(f'<polygon points="{pts}" fill="none" stroke="#2e2e2b" stroke-width="1.5"/>')
    for i in range(n):
        x, y = pt(i, vmax)
        out.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#3a3936" stroke-width="1.5"/>')
    poly = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, s["pct"]) for i, s in enumerate(stats)))
    out.append(f'<polygon points="{poly}" fill="#3987e5" fill-opacity="0.22" stroke="#5a9de9" stroke-width="3" '
               f'stroke-linejoin="round"/>')
    for i, s in enumerate(stats):
        x, y = pt(i, s["pct"])
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#5a9de9"/>')
        lx, ly = pt(i, vmax * 1.16)
        c = math.cos(math.radians(-90 + i * 360 / n))
        anchor = "middle" if abs(c) < 0.2 else ("start" if c > 0 else "end")
        out.append(_t(lx, ly + 7, s["stat"], 19, 600, "#d9d7d0", anchor=anchor))
    out.append("</svg>")
    return "\n".join(out) + "\n"


FIXED_LABELS = ("SET", "LEVEL", "ACHIEVEMENTS", "PARTY", "/", "%", "·", "stat card")


def card_strings(card: dict) -> list:
    """Every data string the card can draw, as (field, value) pairs. audit prints these."""
    if not card.get("enabled"):
        return []
    out = [("name", card["name"]), ("set", card["set"]), ("class", card["class"])]
    if card.get("multiclass"):
        out.append(("multiclass", card["multiclass"]))
    out.append(("level", str(card["level"])))
    for s in card["stats"]:
        out.append(("stat", f"{s['stat']} {s['pct']}%"))
    for a in card.get("achievements", []):
        out.append(("achievement", f"{a['title']} · {a['when']}"))
    for p in card.get("party", []):
        out.append(("party", p))
    for p in card.get("projects", []):
        out.append(("project", p))
    return out
