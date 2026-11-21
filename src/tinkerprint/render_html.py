"""sheet.html: the private sheet. One file, no network, a content policy that blocks every request."""
from __future__ import annotations

import math
from html import escape

from . import radar
from .timeutil import day_label

CSP = "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:"

CSS = """
:root {
  color-scheme: light;
  --page: #f3f1ea; --surface: #fcfcfb; --surface-2: #f5f4ef; --ink: #0b0b0b; --ink-2: #4a4943;
  --muted: #7a7872; --grid: #e1e0d9; --axis: #c3c2b7; --border: rgba(11,11,11,.10); --border-2: rgba(11,11,11,.18);
  --me: #2a78d6; --me-wash: rgba(42,120,214,.14); --good: #2f8a4c; --warn: #b8641c; --dot: rgba(11,11,11,.06);
  --sans: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --page: #0d0d0d; --surface: #1a1a19; --surface-2: #222220; --ink: #f0efec; --ink-2: #c2c0b8;
    --muted: #8f8d86; --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,.10); --border-2: rgba(255,255,255,.18);
    --me: #3987e5; --me-wash: rgba(57,135,229,.18); --good: #5cbf7a; --warn: #e39550; --dot: rgba(255,255,255,.05);
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --page: #0d0d0d; --surface: #1a1a19; --surface-2: #222220; --ink: #f0efec; --ink-2: #c2c0b8;
  --muted: #8f8d86; --grid: #2c2c2a; --axis: #383835; --border: rgba(255,255,255,.10); --border-2: rgba(255,255,255,.18);
  --me: #3987e5; --me-wash: rgba(57,135,229,.18); --good: #5cbf7a; --warn: #e39550; --dot: rgba(255,255,255,.05);
}
* { box-sizing: border-box; }
html, body { margin: 0; }
body { background: var(--page); background-image: radial-gradient(var(--dot) 1px, transparent 1px); background-size: 18px 18px;
  color: var(--ink); font: 15px/1.5 var(--sans); -webkit-font-smoothing: antialiased; }
.wrap { max-width: 1160px; margin: 0 auto; padding: 20px 16px 64px; }
h2 { font-size: 13px; text-transform: uppercase; letter-spacing: .14em; color: var(--ink-2); margin: 40px 0 6px; font-weight: 600; }
.lede { color: var(--ink-2); margin: 0 0 14px; max-width: 72ch; }
.top { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; margin-bottom: 14px; }
.eyebrow { font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: var(--ink-2); }
.eyebrow b { color: var(--ink); font-weight: 600; }
.ghost-btn { background: var(--surface); border: 1px solid var(--border-2); border-radius: 6px; padding: 4px 10px; font: inherit; font-size: 12px; cursor: pointer; color: var(--ink-2); }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 18px; position: relative; }
.card.framed::before, .card.framed::after { content: ""; position: absolute; width: 12px; height: 12px; border: 2px solid var(--ink-2); opacity: .55; }
.card.framed::before { top: -1px; left: -1px; border-right: 0; border-bottom: 0; border-top-left-radius: 10px; }
.card.framed::after { bottom: -1px; right: -1px; border-left: 0; border-top: 0; border-bottom-right-radius: 10px; }
.changes { margin-bottom: 14px; border-left: 3px solid var(--me); }
.changes h3 { margin: 0 0 6px; font-size: 15px; }
.changes ul { margin: 0; padding-left: 18px; }
.hero { display: grid; gap: 14px; grid-template-columns: minmax(280px, 390px) 1fr; align-items: start; }
@media (max-width: 860px) { .hero { grid-template-columns: 1fr; } }
.tagline { font-size: 11px; text-transform: uppercase; letter-spacing: .16em; color: var(--ink-2); }
.nameplate { display: flex; align-items: flex-end; justify-content: space-between; gap: 12px; margin-top: 6px; }
.nameplate h1 { font-size: 32px; line-height: 1.05; margin: 0 0 4px; font-weight: 700; overflow-wrap: anywhere; }
.cls { font-size: 19px; font-weight: 600; }
.cls .multi { color: var(--ink-2); font-weight: 500; }
.cls-why { font-size: 12px; color: var(--muted); margin-top: 2px; }
.lvl { text-align: center; min-width: 82px; border: 1px solid var(--border-2); border-radius: 8px; padding: 6px 8px 5px; background: var(--surface-2); }
.lvl .n { font-size: 40px; line-height: 1; font-weight: 700; }
.lvl .l { font-size: 10px; letter-spacing: .18em; text-transform: uppercase; color: var(--ink-2); }
.next { margin: 14px 0 4px; font-size: 12px; color: var(--ink-2); display: flex; justify-content: space-between; gap: 8px; }
.bar { height: 8px; border-radius: 4px; background: var(--grid); position: relative; overflow: hidden; }
.bar i { position: absolute; inset: 0 auto 0 0; border-radius: 0 4px 4px 0; background: var(--me); }
.vitals { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 14px; margin: 14px 0 0; }
.vitals div { border-top: 1px solid var(--border); padding-top: 6px; }
.vitals dt { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; }
.vitals dd { margin: 0; font-weight: 600; }
.vitals dd small { font-weight: 400; color: var(--ink-2); font-size: 12px; display: block; }
.radar-card h3 { margin: 0; font-size: 16px; }
.radar-card .sub { margin: 2px 0 0; font-size: 13px; color: var(--ink-2); }
svg.radar { width: 100%; max-width: 620px; height: auto; display: block; margin: 6px auto 0; overflow: visible; }
svg.radar .ring { fill: none; stroke: var(--grid); stroke-width: 1; }
svg.radar .spoke { stroke: var(--axis); stroke-width: 1; }
svg.radar .area { fill: var(--me-wash); stroke: var(--me); stroke-width: 2; stroke-linejoin: round; }
svg.radar .pt { fill: var(--me); stroke: var(--surface); stroke-width: 2; }
svg.radar .lab { fill: var(--ink); font-size: 15px; font-weight: 600; }
svg.radar .lab.zero { fill: var(--muted); font-weight: 400; }
svg.radar .tick { fill: var(--muted); font-size: 10px; }
@media (max-width: 520px) { svg.radar .lab { font-size: 19px; } svg.radar .tick { font-size: 13px; } }
.bars { display: grid; gap: 8px; margin-top: 12px; }
.bars .row { display: grid; grid-template-columns: 92px 1fr 48px; gap: 8px; align-items: center; font-size: 13px; }
.bars .row .v { text-align: right; font-variant-numeric: tabular-nums; color: var(--ink-2); }
details { margin-top: 10px; font-size: 13px; }
details summary { cursor: pointer; color: var(--ink-2); }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--border); vertical-align: top; }
th { font-weight: 600; color: var(--ink-2); font-size: 12px; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
.scroll-x { overflow-x: auto; }
.stats { display: grid; gap: 12px; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); }
.stat { display: flex; flex-direction: column; }
.stat header { display: flex; align-items: center; gap: 10px; }
.code { font-weight: 700; font-size: 11px; letter-spacing: .06em; width: 38px; height: 34px; display: grid; place-items: center; background: var(--surface-2); border: 1px solid var(--border-2); clip-path: polygon(25% 0, 75% 0, 100% 50%, 75% 100%, 25% 100%, 0 50%); }
.stat h3 { margin: 0; font-size: 18px; flex: 1; }
.stat .pts { font-weight: 700; font-size: 22px; text-align: right; line-height: 1; }
.stat .pts small { display: block; font-weight: 400; font-size: 11px; color: var(--muted); }
.stat .def { color: var(--ink-2); font-size: 13px; margin: 8px 0 10px; }
.stat.zero { opacity: .62; }
.ev { list-style: none; padding: 0; margin: 12px 0 0; font-size: 13px; }
.ev li { display: flex; justify-content: space-between; gap: 8px; padding: 3px 0; border-top: 1px dashed var(--border); }
.ev li span:first-child { overflow-wrap: anywhere; }
.ev li span:last-child { color: var(--ink-2); font-variant-numeric: tabular-nums; white-space: nowrap; }
.ev-title { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; margin-top: 10px; }
.party { display: grid; gap: 10px; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); }
.comp { display: grid; grid-template-columns: 1fr auto; gap: 2px 10px; align-content: start; }
.comp .nm { font-weight: 700; font-size: 17px; }
.comp .role { font-size: 11px; letter-spacing: .12em; text-transform: uppercase; color: var(--ink-2); }
.comp .big { grid-row: 1 / span 2; grid-column: 2; text-align: right; font-weight: 700; font-size: 26px; line-height: 1; }
.comp .big small { display: block; font-weight: 400; font-size: 11px; color: var(--muted); }
.comp .facts { grid-column: 1 / -1; display: flex; gap: 14px; flex-wrap: wrap; font-size: 12px; color: var(--ink-2); margin-top: 8px; font-variant-numeric: tabular-nums; }
.comp .models { grid-column: 1 / -1; display: flex; gap: 4px; flex-wrap: wrap; margin-top: 8px; }
.comp .models span { font-size: 11px; border: 1px solid var(--border-2); border-radius: 4px; padding: 1px 6px; color: var(--ink-2); font-family: var(--mono); }
.achs { display: grid; gap: 10px; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); }
.ach { padding: 12px 14px; }
.ach .t { font-weight: 600; font-size: 15px; }
.ach .d { font-size: 12px; color: var(--ink-2); font-variant-numeric: tabular-nums; }
.ach .x { font-size: 13px; color: var(--ink); margin-top: 4px; }
.ach .src { font-size: 12px; color: var(--muted); margin-top: 2px; }
.ms { list-style: none; padding: 0; margin: 12px 0 0; }
.ms li { display: grid; grid-template-columns: 120px 1fr; gap: 8px; padding: 6px 0; border-top: 1px solid var(--border); font-size: 14px; }
.ms li span:first-child { color: var(--ink-2); font-variant-numeric: tabular-nums; }
.method { columns: 2 320px; column-gap: 28px; font-size: 14px; color: var(--ink-2); }
.method p { margin: 0 0 10px; break-inside: avoid; }
.method b { color: var(--ink); }
.foot { margin-top: 36px; font-size: 12px; color: var(--muted); }
.empty { color: var(--muted); font-size: 14px; }
"""

JS = """
(function () {
  var btn = document.getElementById('themeBtn');
  var key = 'tinkerprint-theme';
  function get() { try { return localStorage.getItem(key) || 'auto'; } catch (e) { return 'auto'; } }
  function put(v) { try { localStorage.setItem(key, v); } catch (e) {} }
  function apply(t) {
    if (t === 'auto') delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme = t;
    btn.textContent = 'Theme: ' + t;
  }
  var t = get(); apply(t);
  btn.addEventListener('click', function () { t = t === 'auto' ? 'light' : t === 'light' ? 'dark' : 'auto'; put(t); apply(t); });
})();
"""


def e(x) -> str:
    return escape(str(x), quote=True)


def pct(x: float) -> str:
    v = x * 100
    if 0 < v < 1:
        return "<1%"
    return f"{round(v)}%"


def plural(n: int, word: str, many: str | None = None) -> str:
    return f"{n} {word if n == 1 else (many or word + 's')}"


def pts(x: float) -> str:
    return f"{x:.1f}" if x < 100 else f"{round(x)}"


def _radar(stats: list) -> str:
    cx, cy, r = 280, 262, 182
    n = len(stats)

    def pt(i, frac):
        return radar.point(cx, cy, r, i, n, frac)

    out = ['<svg class="radar" viewBox="0 0 560 520" role="img" aria-label="Radar of stat shares">']
    for ring_share in radar.RINGS:
        fr = radar.radius(ring_share)
        ring = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, fr) for i in range(n)))
        out.append(f'<polygon class="ring" points="{ring}"/>')
        a = math.radians(-90) + math.pi / n
        out.append(f'<text class="tick" x="{cx + math.cos(a) * r * fr:.1f}" y="{cy + math.sin(a) * r * fr - 4:.1f}" '
                   f'text-anchor="middle">{round(ring_share * 100)}%</text>')
    for i in range(n):
        x, y = pt(i, 1.0)
        out.append(f'<line class="spoke" x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}"/>')
    area = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, radar.radius(s["share"])) for i, s in enumerate(stats)))
    out.append(f'<polygon class="area" points="{area}"/>')
    for i, s in enumerate(stats):
        x, y = pt(i, radar.radius(s["share"]))
        out.append(f'<circle class="pt" cx="{x:.1f}" cy="{y:.1f}" r="4"><title>{e(s["key"])}: {pct(s["share"])}, '
                   f'{pts(s["points"])} points</title></circle>')
    for i, s in enumerate(stats):
        x, y = pt(i, radar.LABEL_AT)
        cls = "lab" if s["points"] > 0 else "lab zero"
        out.append(f'<text class="{cls}" x="{x:.1f}" y="{y + 5:.1f}" text-anchor="{radar.anchor(i, n)}">{e(s["key"])}</text>')
    out.append("</svg>")
    return "\n".join(out)


def _bars(stats: list) -> str:
    rows = sorted(stats, key=lambda s: -s["share"])
    out = ['<div class="bars">']
    for s in rows:
        out.append(f'<div class="row"><span>{e(s["key"])}</span><span class="bar"><i style="width:{s["share"] * 100:.1f}%">'
                   f'</i></span><span class="v">{pct(s["share"])}</span></div>')
    out.append("</div>")
    return "\n".join(out)


def _changes(ch: dict | None) -> str:
    """The what-changed panel, from changes.json. It names the sheet it compared against."""
    if not ch or not ch.get("against"):
        return ""
    items = []
    n = ch["points_since"]
    items.append(f"{n:+d} {'point' if abs(n) == 1 else 'points'}.")
    if ch.get("level_from") is not None and ch["level_to"] != ch["level_from"]:
        items.append(f"Level {ch['level_from']} to level {ch['level_to']}.")
    if ch.get("set_changed"):
        items.append(f"Set changed from {e(ch.get('set_from') or 'another set')}. Class and shares are not compared.")
    elif ch.get("new_class"):
        items.append(f"New class: {e(ch['class_from'])} to {e(ch['class_to'])}.")
    else:
        items.append(f"Same class: {e(ch['class_to'])}.")
    for d in ch.get("drift", [])[:4]:
        items.append(f"{e(d['stat'])} {pct(d['from'])} to {pct(d['to'])}.")
    for name in ch.get("party_joined", []):
        items.append(f"{e(name)} joined the party.")
    for name in ch.get("party_left", []):
        items.append(f"{e(name)} left the party.")
    for p in ch.get("party_sessions", []):
        items.append(f"{e(p['name'])}: {p['sessions_since']:+d} sessions.")
    for t in ch.get("achievements_new", []):
        items.append(f"New achievement: {e(t)}.")
    lis = "".join(f"<li>{i}</li>" for i in items)
    return (f'<section class="card changes"><h3>What changed since the sheet as of {day_label(ch["against"])}</h3>'
            f'<ul>{lis}</ul></section>')


def render_html(sheet: dict, built_at: str = "", changes: dict | None = None) -> str:
    prof = sheet["profile"]
    hist = sheet["history"]
    tot = sheet["season_totals"]
    season = sheet["season"]
    stats = sheet["stats"]
    cls = sheet.get("class")
    multi = sheet.get("multiclass")
    set_title = prof["set"].capitalize()

    cls_html = e(cls["display"]) if cls else "Unclassed"
    if multi:
        cls_html += f' <span class="multi">/ {e(multi["display"])}</span>'
    why = e(cls["why"]) if cls else "No classified points yet."
    if multi:
        why += f" Multiclass: {e(multi['stats'][0])} and {e(multi['stats'][1])} each hold 10% or more."

    lo = hist["level"] ** 2
    need = hist["next_level_at"] - hist["points"]
    vitals = [
        ("Active days", f'{tot["active_days"]}<small>in this season</small>'),
        ("Level points", f'{hist["points"]}<small>all history</small>'),
        ("Projects", f'{len(sheet["projects"])}<small>with points this season</small>'),
        ("Unclassified", f'{pct(tot["unclassified_share"])}<small>of season points, kept out of stats</small>'),
    ]
    vit = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in vitals)

    if sheet["chart"] == "radar":
        chart = _radar(stats)
        chart_note = ("Eight spokes in the set's order on a square-root scale that is the same on every sheet, "
                      "so two sheets of the same set overlay.")
    else:
        chart = _bars(stats)
        chart_note = "Fewer than three stats have points, so the sheet shows ranked bars instead of a radar."
    table_rows = "".join(f'<tr><td>{e(s["key"])}</td><td class="num">{pts(s["points"])}</td>'
                         f'<td class="num">{pct(s["share"])}</td></tr>' for s in stats)

    cards = []
    for s in stats:
        projs = "".join(f'<li><span>{e(p["name"])}</span><span>{pts(p["points"])}</span></li>'
                        for p in s["projects"][:5])
        more = len(s["projects"]) - 5
        if more > 0:
            projs += f'<li><span>{more} more</span><span></span></li>'
        body = (f'<div class="ev-title">Projects behind it</div><ul class="ev">{projs}</ul>' if projs
                else '<p class="empty">No points this season.</p>')
        zero = "" if s["points"] > 0 else " zero"
        cards.append(
            f'<article class="card stat{zero}"><header><span class="code">{e(s["key"][:3].upper())}</span>'
            f'<h3>{e(s["key"])}</h3><div class="pts">{pct(s["share"])}<small>{pts(s["points"])} pts</small></div>'
            f'</header><p class="def">{e(s["description"])}</p>'
            f'<span class="bar"><i style="width:{s["share"] * 100:.1f}%"></i></span>{body}</article>')

    party = []
    for m in sheet["party"]:
        models = "".join(f"<span>{e(x)}</span>" for x in m["models"][:6])
        party.append(
            f'<article class="card comp"><div class="nm">{e(m["name"])}</div><div class="role">{e(m["role"])}</div>'
            f'<div class="big">{m["days_together"]}<small>days together</small></div>'
            f'<div class="facts"><span>{plural(m["sessions"], "session")}</span><span>{m["edit_sessions"]} edited</span>'
            f'<span>{m["review_sessions"]} reviewed</span><span>{m["other_sessions"]} other</span></div>'
            f'<div class="facts"><span>{day_label(m["first_day"])} to {day_label(m["last_day"])}</span></div>'
            f'<div class="models">{models}</div></article>')
    party_html = "".join(party) or '<p class="empty">No harness sessions inside this profile.</p>'

    achs = []
    for a in sheet["achievements"]:
        count = f" ×{a['count']}" if a.get("count", 1) > 1 else ""
        detail = f'<div class="src">{e(a["detail"])}</div>' if a.get("detail") else ""
        achs.append(f'<article class="card ach"><div class="t">{e(a["title"])}{count}</div>'
                    f'<div class="d">{day_label(a["date"])}</div><div class="x">{e(a["rule"])}</div>{detail}</article>')
    ach_html = "".join(achs) or '<p class="empty">None yet.</p>'
    ms = "".join(f'<li><span>{day_label(m["date"])}</span><span>{e(m["text"])}</span></li>' for m in sheet["milestones"])
    ms_html = f'<h2>Milestones</h2><p class="lede">Written by hand in the profile\'s milestones file.</p><ul class="ms">{ms}</ul>' if ms else ""

    proj_rows = "".join(f'<tr><td>{e(p["name"])}</td><td class="num">{p["days"]}</td>'
                        f'<td class="num">{pts(p["points"])}</td><td class="num">{pct(p["share"])}</td></tr>'
                        for p in sheet["projects"])
    proj_html = (f'<div class="card scroll-x"><table><thead><tr><th>Project</th><th class="num">Days</th>'
                 f'<th class="num">Points</th><th class="num">Share</th></tr></thead><tbody>{proj_rows}</tbody></table></div>'
                 if proj_rows else '<p class="empty">No project points this season.</p>')
    un = sheet["unassigned"]
    un_html = ""
    if un["sessions"] or un["edits"]:
        un_html = (f'<p class="lede">Outside every root: {plural(un["sessions"], "session")} in {plural(un["folders"], "folder")} and '
                   f'{plural(un["edits"], "edited file")}. They are not scored. Run <code>tinkerprint build</code> in a terminal to list '
                   f'the folders, then add roots to the profile if they belong.</p>')

    card_note = ("Card on. Run <code>tinkerprint audit</code> to see every string it holds."
                 if sheet["card"].get("enabled") else e(sheet["card"].get("reason", "Card off.")))
    work = " · work profile" if prof.get("work") else ""
    as_of = f" · as of {day_label(season['as_of'])}" if season.get("as_of") else ""
    built = f"Built {e(built_at)}. " if built_at else ""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{CSP}">
<title>{e(prof["name"])} · tinkerprint</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<div class="top">
  <div class="eyebrow">tinkerprint · <b>{e(set_title)} set</b> · {e(season["label"])}{as_of}{work}</div>
  <button class="ghost-btn" id="themeBtn" type="button">Theme: auto</button>
</div>
{_changes(changes)}
<section class="hero">
  <div class="card framed">
    <div class="tagline">Character</div>
    <div class="nameplate">
      <div>
        <h1>{e(prof["name"])}</h1>
        <div class="cls">{cls_html}</div>
        <div class="cls-why">{why}</div>
      </div>
      <div class="lvl"><div class="n">{hist["level"]}</div><div class="l">Level</div></div>
    </div>
    <div class="next"><span>{hist["points"] - lo} of {hist["next_level_at"] - lo} to level {hist["level"] + 1}</span><span>{plural(need, "day")} to go</span></div>
    <span class="bar"><i style="width:{hist["level_progress"] * 100:.1f}%"></i></span>
    <dl class="vitals">{vit}</dl>
  </div>
  <div class="card framed radar-card">
    <h3>Where the season's points went</h3>
    <p class="sub">{chart_note}</p>
    {chart}
    <details><summary>Stats as a table</summary><div class="scroll-x"><table><thead><tr><th>Stat</th><th class="num">Points</th><th class="num">Share</th></tr></thead><tbody>{table_rows}</tbody></table></div></details>
  </div>
</section>

<h2>Stats</h2>
<p class="lede">Each active day is one point. It splits across the day's projects, then across each project's stats, by the log of files changed. Shares are of classified points.</p>
<div class="stats">{"".join(cards)}</div>

<h2>Party</h2>
<p class="lede">The agents that worked beside you. The party shows presence, never a share of the work. Sessions with no file change earn no points.</p>
<div class="party">{party_html}</div>

<h2>Achievements</h2>
<p class="lede">Generic rules, the same for everyone. Each shows its rule and the day it was earned.</p>
<div class="achs">{ach_html}</div>
{ms_html}

<h2>Projects</h2>
{proj_html}
{un_html}

<h2>Method</h2>
<div class="method">
<p><b>Method version {sheet["method"]}.</b> Same inputs and profile give the same sheet. No model scores anything.</p>
<p><b>Points.</b> One active day is one point. Level is the square root of all-history points, rounded down. Class and radar cover the season.</p>
<p><b>Days</b> run from {prof["rollover_hour"]:02d}:00 to {prof["rollover_hour"]:02d}:00 in {e(prof["timezone"])}.</p>
<p><b>Class.</b> A stat at 50% or more makes a specialist. No stat over 20% makes a generalist. Otherwise the top two make a pair when the runner-up holds 10%. When the next pair or stat sits within 2 points, the sheet names it too.</p>
<p><b>What this is not.</b> A sheet never claims skill, productivity, seniority, hours worked, or who did how much of the work.</p>
<p><b>Share card.</b> {card_note}</p>
</div>
<p class="foot">{built}{e(sheet["tool"])}, method {sheet["method"]}. Made on this machine. Nothing was uploaded.</p>
</div>
<script>{JS}</script>
</body>
</html>
"""
