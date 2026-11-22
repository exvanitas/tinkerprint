"""sheet.html: the private sheet. One file, no network, a content policy that blocks every request."""
from __future__ import annotations

import base64
from html import escape

from . import art, look as looks, radar
from .art import keepsake
from .art.pixels import Canvas, mix
from .art.keepsake import berths as keepsake_berths
from .party import HARNESS_NAMES
from .render_card import visible as card_visible
from .timeutil import day_label

CSP = "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:"

CSS = """
:root {
  color-scheme: light;
  --page: #efe6d4; --glow: rgba(226,150,60,.20); --surface: #fbf6ec; --surface-2: #f3ebdc; --ink: #24190f; --ink-2: #5b4a39;
  --muted: #736253; --ring: #b5a283; --grid: #e2d6c1; --axis: #cbbca2; --border: rgba(70,45,20,.13); --border-2: rgba(70,45,20,.24);
  --lantern: #c27a26; --lantern-ink: #93500e; --lantern-wash: rgba(214,140,50,.17); --frame: #3a2a1e;
  --sans: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  --serif: "Iowan Old Style", "Palatino Linotype", Palatino, "Book Antiqua", P052, "URW Palladio L", Georgia, serif;
  --mono: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    color-scheme: dark;
    --page: #121117; --glow: rgba(235,160,70,.11); --surface: #1b1a21; --surface-2: #24222b; --ink: #f3eadb; --ink-2: #c9bda8;
    --muted: #998f7d; --ring: #57525f; --grid: #2d2b34; --axis: #3d3a45; --border: rgba(255,236,200,.09); --border-2: rgba(255,236,200,.17);
    --lantern: #eba84f; --lantern-ink: #f2bb6c; --lantern-wash: rgba(235,168,79,.17); --frame: #0b0a0e;
  }
}
:root[data-theme="dark"] {
  color-scheme: dark;
  --page: #121117; --glow: rgba(235,160,70,.11); --surface: #1b1a21; --surface-2: #24222b; --ink: #f3eadb; --ink-2: #c9bda8;
  --muted: #998f7d; --ring: #57525f; --grid: #2d2b34; --axis: #3d3a45; --border: rgba(255,236,200,.09); --border-2: rgba(255,236,200,.17);
  --lantern: #eba84f; --lantern-ink: #f2bb6c; --lantern-wash: rgba(235,168,79,.17); --frame: #0b0a0e;
}
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) :is(.stat, .share-stats .row) { --hue-fill: var(--hue-1); } }
:root[data-theme="dark"] :is(.stat, .share-stats .row) { --hue-fill: var(--hue-1); }
* { box-sizing: border-box; }
html, body { margin: 0; }
body { background: var(--page) radial-gradient(ellipse 90% 520px at 50% 0, var(--glow), transparent) no-repeat;
  color: var(--ink); font: 15px/1.5 var(--sans); -webkit-font-smoothing: antialiased; }
.wrap { max-width: 1160px; margin: 0 auto; padding: 16px 16px 64px; }
h2 { font: 600 25px/1.2 var(--serif); margin: 52px 0 4px; display: flex; align-items: center; gap: 12px; }
h2::before { content: ""; width: 10px; height: 10px; background: var(--lantern); transform: rotate(45deg); flex: none; }
h2::after { content: ""; flex: 1; height: 1px; background: linear-gradient(90deg, var(--border-2), transparent); }
.lede { color: var(--ink-2); margin: 0 0 16px; max-width: 72ch; font-size: 14px; }
.top { display: flex; align-items: center; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.eyebrow { font-size: 12px; letter-spacing: .14em; text-transform: uppercase; color: var(--ink-2); min-width: 0; }
.eyebrow b { color: var(--lantern-ink); font-weight: 600; }
.ghost-btn { background: var(--surface); border: 1px solid var(--border-2); border-radius: 6px; padding: 4px 10px; font: inherit; font-size: 12px; cursor: pointer; color: var(--ink-2); flex: none; }
.card { background: var(--surface); border: 1px solid var(--border); border-radius: 12px; padding: 16px; position: relative; }
.empty { color: var(--muted); font-size: 14px; }
.px { display: block; image-rendering: pixelated; }
svg.defs { position: absolute; width: 0; height: 0; }
code { font-family: var(--mono); font-size: .92em; }
.bar { display: block; height: 8px; border-radius: 4px; background: var(--grid); position: relative; overflow: hidden; }
.bar i { position: absolute; inset: 0 auto 0 0; border-radius: 0 4px 4px 0; background: var(--lantern); }

/* Hero: one scene. The Keepsake room is the stage, the figure works its counter, the nameplate hangs below.
   Every layer is the full 252 x 72 room, drawn at a whole-number scale --k so no pixel is wider than its
   neighbour. A narrow screen crops the room around --fx, between the figure and the party's case, and never
   past --lx, the figure's left edge. */
.hero { position: relative; overflow: hidden; border-radius: 16px; background: var(--surface); border: 3px solid var(--frame);
  box-shadow: 0 22px 44px -28px rgba(40,20,0,.6); }
.banner { --k: 1; position: relative; overflow: hidden; height: calc(72px * var(--k)); background: var(--frame); }
@media (min-width: 289px) { .banner { --k: 2; } }
@media (min-width: 541px) { .banner { --k: 3; } }
@media (min-width: 795px) { .banner { --k: 4; } }
@media (min-width: 1047px) { .banner { --k: 5; } }
.set { --f: var(--fx); position: absolute; top: 0; height: 100%; width: calc(252px * var(--k));
  left: min(max(100% - 252px * var(--k), 50% - var(--f) * var(--k) * 1px, var(--lx) * var(--k) * -1px),
             max(0px, (100% - 252px * var(--k)) / 2)); }
.set img { position: absolute; inset: 0; width: 100%; height: 100%; display: block; image-rendering: pixelated; pointer-events: none; }
.set .hit { position: absolute; z-index: 1; }
/* A close call swaps the costume: figure, hands and counter trade places together, never both at once.
   The room keeps running underneath. */
.flip .wear.main { animation: costume-a 6s steps(1) infinite; }
.flip .wear.alt { animation: costume-b 6s steps(1) infinite; }
@keyframes costume-a { 0% { opacity: 1; } 50% { opacity: 0; } }
@keyframes costume-b { 0% { opacity: 0; } 50% { opacity: 1; } }
.flip .hit:hover ~ .wear.main, .flip.worn .wear.main { animation: none; opacity: 0; }
.flip .hit:hover ~ .wear.alt, .flip.worn .wear.alt { animation: none; opacity: 1; }
.flip.held .wear.main { animation: none; opacity: 1; }
.flip.held .wear.alt { animation: none; opacity: 0; }
@media (prefers-reduced-motion: reduce) {
  .flip .wear.main { animation: none; opacity: 1; }
  .flip .wear.alt { animation: none; opacity: 0; }
}
.plaque { position: relative; display: grid; gap: 16px 28px; align-items: center;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 430px); grid-template-areas: "who xp";
  padding: 20px 24px 22px; border-top: 3px solid var(--lantern); }
.seal { width: 76px; height: 76px; flex: none; border-radius: 50%; display: grid; place-content: center; text-align: center;
  background: radial-gradient(circle at 38% 30%, #fbe2a4, #e0a447 55%, #b8731f); color: #2b1606;
  border: 3px solid #6e4214; box-shadow: 0 0 0 3px var(--surface), 0 0 0 4px var(--border-2), 0 0 22px var(--lantern-wash); }
.seal .n { font: 700 32px/1 var(--serif); }
.seal .l { font-size: 9px; letter-spacing: .2em; text-transform: uppercase; font-weight: 700; margin-top: 2px; }
.lv { display: grid; grid-template-columns: auto minmax(0, 1fr); gap: 16px; align-items: center; }
.who { grid-area: who; min-width: 0; }
.who h1 { font: 700 42px/1.05 var(--serif); margin: 0; overflow-wrap: anywhere; letter-spacing: -.01em; }
.cls { font: 600 21px/1.25 var(--serif); color: var(--lantern-ink); margin-top: 4px; }
.cls .multi { color: var(--ink-2); font-weight: 500; }
.cls-why { font-size: 13px; color: var(--muted); margin-top: 3px; }
.costume { margin-top: 8px; font: inherit; font-size: 12px; color: var(--lantern-ink); background: var(--lantern-wash); border: 1px solid var(--border-2); border-radius: 999px; padding: 3px 12px; cursor: pointer; }
.jump { display: inline-block; margin-top: 8px; margin-right: 10px; font-size: 12px; color: var(--lantern-ink); }
.xp { grid-area: xp; min-width: 0; }
.next { margin: 0 0 6px; font-size: 12px; color: var(--ink-2); display: flex; justify-content: space-between; gap: 8px; }
.xp .bar { height: 10px; border-radius: 5px; }
.vitals { display: grid; grid-template-columns: 1fr 1fr; gap: 8px 16px; margin: 14px 0 0; }
.vitals.n3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.vitals div { border-top: 1px solid var(--border); padding-top: 5px; min-width: 0; }
.vitals dt { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; }
.vitals dd { margin: 0; font-weight: 700; font-size: 17px; line-height: 1.2; }
.vitals dd small { font-weight: 400; color: var(--ink-2); font-size: 12px; display: block; }
@media (max-width: 860px) {
  .plaque { grid-template-columns: minmax(0, 1fr); grid-template-areas: "who" "xp"; }
}
@media (max-width: 560px) {
  .hero { border-width: 2px; border-radius: 12px; }
  .plaque { padding: 14px; gap: 12px 14px; }
  .seal { width: 64px; height: 64px; border-width: 2px; }
  .seal .n { font-size: 27px; }
  .seal .l { font-size: 8px; }
  .who h1 { font-size: 30px; }
  .cls { font-size: 18px; }
  h2 { font-size: 22px; margin-top: 44px; }
}

/* The build: radar beside the stat cards. */
.build { display: grid; gap: 14px; grid-template-columns: minmax(0, 450px) minmax(0, 1fr); align-items: start; }
@media (max-width: 1007px) { .build { grid-template-columns: minmax(0, 1fr); } }
.radar-card { position: sticky; top: 12px; }
@media (max-width: 1007px) { .radar-card { position: relative; top: 0; } }
.radar-card h3 { margin: 0; font: 600 18px/1.25 var(--serif); }
.radar-card .sub { margin: 2px 0 0; font-size: 13px; color: var(--ink-2); }
svg.radar { width: 100%; max-width: 560px; height: auto; display: block; margin: 6px auto 0; overflow: visible; }
svg.radar .ring { fill: none; stroke: var(--ring); stroke-width: 1.25; }
svg.radar .spoke { stroke: var(--ring); stroke-width: 1; }
svg.radar .area { fill: var(--lantern-wash); stroke: var(--lantern); stroke-width: 2.5; stroke-linejoin: round; }
svg.radar .pt { stroke: var(--surface); stroke-width: 2.5; }
svg.radar .lab { fill: var(--ink); font-size: 23px; font-weight: 600; }
@media (max-width: 560px) { svg.radar .lab { font-size: 29px; } }
svg.radar .lab.zero { fill: var(--muted); font-weight: 400; }
.key { margin: 4px 0 0; font-size: 12px; color: var(--muted); text-align: center; }
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
.stat { --hue-fill: var(--hue-2); border-top: 3px solid var(--hue-fill); padding-top: 14px; }
.stat header { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: 12px; align-items: center; }
.trinket { width: 60px; height: 60px; border-radius: 10px; display: grid; place-items: center; background: var(--hue-wash);
  border: 1px solid var(--border); }
.stat h3 { margin: 0; font: 600 19px/1.2 var(--serif); }
.stat .pts { font: 700 26px/1 var(--serif); text-align: right; }
.stat .pts small { display: block; font: 400 11px/1.4 var(--sans); color: var(--muted); }
.stat .def { color: var(--ink-2); font-size: 13px; margin: 10px 0; }
.stat .bar i { background: var(--hue-fill); }
.ev { list-style: none; padding: 0; margin: 0; font-size: 13px; }
.ev-h { display: flex; justify-content: space-between; margin-top: 12px; padding-bottom: 2px; font-size: 10px; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); }
.ev li { display: flex; justify-content: space-between; gap: 8px; padding: 3px 0; border-top: 1px dashed var(--border); }
.ev li span:first-child { overflow-wrap: anywhere; }
.ev li span:last-child { color: var(--ink-2); font-variant-numeric: tabular-nums; white-space: nowrap; }
.unlit { display: flex; flex-direction: column; justify-content: center; gap: 10px; font-size: 13px; color: var(--muted);
  border: 1px dashed var(--border-2); border-radius: 12px; padding: 10px 14px; }
.unlit > span { display: inline-flex; gap: 8px; align-items: center; }
.unlit .trinket { width: 34px; height: 34px; border-radius: 8px; filter: grayscale(1); opacity: .7; }
.unlit b { color: var(--ink-2); }

/* Party: each familiar on its own patch of floor. */
.party { display: grid; gap: 12px; grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr)); }
.comp { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: 12px 14px; align-items: center; }
.comp .fam { width: 96px; height: 84px; display: flex; align-items: flex-end; justify-content: center; padding-bottom: 8px;
  border-radius: 10px; background: linear-gradient(var(--surface-2) 72%, var(--lantern-wash) 72%); border: 1px solid var(--border); }
.comp .nm { font: 600 20px/1.2 var(--serif); }
.comp .role { font-size: 11px; letter-spacing: .12em; text-transform: uppercase; color: var(--ink-2); margin-top: 2px; }
.comp .big { text-align: right; font: 700 32px/1 var(--serif); }
.comp .big small { display: block; font: 400 11px/1.4 var(--sans); color: var(--muted); }
.comp .facts { grid-column: 1 / -1; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 6px; margin: 0; }
.comp .facts div { background: var(--surface-2); border-radius: 8px; padding: 5px 8px; min-width: 0; }
.comp .facts dt { font-size: 10px; letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
.comp .facts dd { margin: 0; font-weight: 700; font-variant-numeric: tabular-nums; }
.comp .when { grid-column: 1 / -1; display: flex; flex-wrap: wrap; gap: 6px 10px; align-items: center; font-size: 12px; color: var(--ink-2); }
.comp .when span.m { font-size: 11px; border: 1px solid var(--border-2); border-radius: 4px; padding: 1px 6px; font-family: var(--mono); }

/* Achievements: a pin on each. */
.achs { display: grid; gap: 12px; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); }
.ach { display: grid; grid-template-columns: 76px minmax(0, 1fr); gap: 0 14px; align-items: start; }
.ach .ic { width: 76px; height: 76px; border-radius: 50%; display: grid; place-items: center; background: var(--surface-2);
  border: 2px solid var(--lantern-wash); box-shadow: 0 0 0 1px var(--border) inset; }
.ach .t { font: 600 18px/1.2 var(--serif); }
.ach .d { font-size: 12px; color: var(--lantern-ink); font-variant-numeric: tabular-nums; margin-top: 2px; }
.ach .x { font-size: 13px; margin-top: 4px; }
.ach .src { font-size: 12px; color: var(--muted); margin-top: 2px; overflow-wrap: anywhere; }
@media (max-width: 560px) {
  .achs { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
  .ach { grid-template-columns: minmax(0, 1fr); text-align: center; padding: 14px 10px; }
  .ach .ic { width: 68px; height: 68px; margin: 0 auto 8px; }
  .ach .t { font-size: 16px; }
}
.ms { list-style: none; padding: 0; margin: 12px 0 0; }
.ms li { display: grid; grid-template-columns: 120px 1fr; gap: 8px; padding: 6px 0; border-top: 1px solid var(--border); font-size: 14px; }
.ms li span:first-child { color: var(--ink-2); font-variant-numeric: tabular-nums; }
.ms li .ic { display: inline-block; vertical-align: -6px; margin-right: 8px; }
.ms li .ic svg { display: inline-block; }

/* Chronicle: a road of chapters, oldest first. */
.chron { list-style: none; margin: 0; display: flex; overflow-x: auto; padding: 4px 2px 10px; scroll-snap-type: x proximity; }
.chap { flex: 1 0 140px; scroll-snap-align: start; display: flex; flex-direction: column; align-items: center; text-align: center;
  position: relative; padding: 0 6px; }
.chap::before { content: ""; position: absolute; left: 0; right: 0; top: 90px; height: 4px; background: repeating-linear-gradient(90deg, var(--axis) 0 10px, transparent 10px 16px); }
.chap:first-child::before { left: 50%; }
.chap:last-child::before { right: 50%; }
.chap .q { font-size: 11px; letter-spacing: .12em; text-transform: uppercase; color: var(--ink-2); font-variant-numeric: tabular-nums; height: 18px; }
.chap .pic { position: relative; padding: 4px; border-radius: 10px; background: var(--surface); border: 1px solid var(--border-2); margin: 4px 0 8px; }
.chap .pic svg { border-radius: 6px; }
.chap .c { font: 600 16px/1.2 var(--serif); }
.chap .n { font-size: 12px; color: var(--muted); }
.chap.rest .c { color: var(--ink-2); font-weight: 500; }
.chap.now .pic { border: 2px solid var(--lantern); box-shadow: 0 0 22px var(--lantern-wash); }
.chap.now .q { color: var(--lantern-ink); font-weight: 700; }

.changes p { margin: 0; }
.changes ul { margin: 0; padding: 0; list-style: none; columns: 2 260px; column-gap: 28px; }
.changes li { padding: 4px 0 4px 18px; position: relative; break-inside: avoid; }
.changes li::before { content: ""; position: absolute; left: 2px; top: 12px; width: 6px; height: 6px; background: var(--lantern); transform: rotate(45deg); }
.method { columns: 2 320px; column-gap: 28px; font-size: 14px; color: var(--ink-2); }
.method p { margin: 0 0 10px; break-inside: avoid; }
.method b { color: var(--ink); }
.foot { margin-top: 36px; font-size: 12px; color: var(--muted); }

/* Share view: a checkbox before the page, so CSS alone can hide everything the card would not show.
   No script. The box stays focusable; its label shows the focus ring and the state. */
.top .tools { display: flex; gap: 8px; align-items: center; flex: none; }
.top a.ghost-btn { text-decoration: none; }
.share-toggle { position: absolute; top: 0; left: 0; width: 1px; height: 1px; margin: 0; opacity: 0; }
.share-btn { user-select: none; -webkit-tap-highlight-color: transparent; }
.share-btn .on, .share-only { display: none; }
.share-toggle:focus-visible ~ .wrap .share-btn { outline: 2px solid var(--lantern); outline-offset: 2px; }
.share-toggle:checked ~ .wrap .share-btn { background: var(--lantern-wash); color: var(--lantern-ink); border-color: var(--lantern); }
.share-toggle:checked ~ .wrap .share-btn .on { display: inline; }
.share-toggle:checked ~ .wrap .share-btn .off { display: none; }
.share-toggle:checked ~ .wrap .private { display: none !important; }
.share-toggle:checked ~ .wrap .share-only { display: block; }
.share-toggle:checked ~ .wrap span.share-only { display: inline; }
.share-toggle:checked ~ .wrap .plaque { align-items: start; }
.share-toggle:checked ~ .wrap .set { --f: var(--fx-share, var(--fx)); }
.share-stats { display: grid; gap: 8px; margin-top: 14px; }
.share-stats .row { --hue-fill: var(--hue-2); display: grid; grid-template-columns: 92px 1fr 48px; gap: 8px; align-items: center; font-size: 14px; font-weight: 600; }
.share-stats .row .v { text-align: right; font-variant-numeric: tabular-nums; color: var(--ink-2); }
.share-stats .bar i { background: var(--hue-fill); }
.share-foot { margin: 12px 0 0; font-size: 12px; color: var(--muted); }
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
  // The close-call costume: each press wears the other one and stops the automatic swap.
  var cb = document.getElementById('costumeBtn'), fig = document.querySelector('.set.flip');
  if (cb && fig) cb.addEventListener('click', function () {
    var worn = !fig.classList.contains('worn');
    fig.classList.toggle('worn', worn); fig.classList.toggle('held', !worn);
    cb.textContent = 'Close call: try the ' + (worn ? cb.dataset.a : cb.dataset.b) + ' costume';
  });
  // The chronicle opens on its latest chapter; the page itself does not move.
  var chron = document.querySelector('.chron');
  if (chron) chron.scrollLeft = chron.scrollWidth;
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


def _radar(stats: list, hues: dict | None = None) -> str:
    cx, cy, r = 280, 262, 182
    n = len(stats)
    hues = hues or {}

    def pt(i, frac):
        return radar.point(cx, cy, r, i, n, frac)

    # Wide enough for 9-letter labels at the phone's larger label size.
    out = ['<svg class="radar" viewBox="-100 0 760 520" role="img" aria-label="Radar of stat shares">']
    for ring_share in radar.RINGS:
        fr = radar.radius(ring_share)
        ring = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, fr) for i in range(n)))
        out.append(f'<polygon class="ring" points="{ring}"/>')
    for i in range(n):
        x, y = pt(i, 1.0)
        out.append(f'<line class="spoke" x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}"/>')
    area = " ".join(f"{x:.1f},{y:.1f}" for x, y in (pt(i, radar.radius(s["share"])) for i, s in enumerate(stats)))
    out.append(f'<polygon class="area" points="{area}"/>')
    for i, s in enumerate(stats):
        x, y = pt(i, radar.radius(s["share"]))
        fill = hues.get(s["key"], ["", "", "#c27a26"])[2]
        out.append(f'<circle class="pt" cx="{x:.1f}" cy="{y:.1f}" r="6" fill="{fill}"><title>{e(s["key"])}: {pct(s["share"])}, '
                   f'{pts(s["points"])} points</title></circle>')
    for i, s in enumerate(stats):
        x, y = pt(i, radar.LABEL_AT)
        cls = "lab" if s["points"] > 0 else "lab zero"
        out.append(f'<text class="{cls}" x="{x:.1f}" y="{y + 6:.1f}" text-anchor="{radar.anchor(i, n)}">{e(s["key"])}</text>')
    out.append("</svg>")
    rings = ", ".join(f"{round(x * 100)}%" for x in radar.RINGS[:-1]) + f" and {round(radar.RINGS[-1] * 100)}%"
    out.append(f'<p class="key">Rings, from the center out: {rings} of the season\'s points.</p>')
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
    head = f'<h2 id="changed">What changed</h2><p class="lede">Since the sheet as of {day_label(ch["against"])}.</p>'
    if ch.get("method_changed"):
        return (head + f'<section class="card changes"><p>That sheet was made by method version '
                f'{e(str(ch.get("method_from")))}, and this one by version {e(str(ch.get("method_to")))}. The rules '
                'changed between them, so the two are not compared. The next build compares again.</p></section>')
    items = []
    if ch.get("scope_changed"):
        what = _and([e(x) for x in ch["scope_changed"]])
        items.append(f"The profile's {what} changed since then, so these differences include history newly "
                     "added or removed, not only new activity.")
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
    return head + f'<section class="card changes"><ul>{lis}</ul></section>'


def _and(words: list) -> str:
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def _uri(kind: str, data: bytes) -> str:
    return f"data:image/{kind};base64," + base64.b64encode(data).decode("ascii")


def _layer(frames: tuple, alt: str, cls: str) -> str:
    """One banner layer: the idle loop as a GIF, or frame zero for viewers who asked for less motion."""
    loop = keepsake.encode(frames, keepsake.DELAYS_MS)
    still = frames[0].png(1, indexed=True)
    return (f'<picture class="{cls}"><source media="(prefers-reduced-motion: reduce)" srcset="{_uri("png", still)}">'
            f'<img src="{_uri("gif", loop)}" alt="{e(alt)}"></picture>')


def _worn(figure, foreground, box: tuple) -> tuple:
    """A costume as one layer per beat: the figure, then the counter with its hands and tools in front.
    One image keeps the hands on the arms whatever the browser does with its clocks."""
    x, y, _, _ = box
    frames = []
    for fig, front in zip(figure.frames, foreground.frames):
        c = Canvas(front.w, front.h)
        c.paste(fig, x, y)
        c.paste(front)
        frames.append(c)
    return tuple(frames)


def _hero_scene(sheet: dict, pack: dict, main, alt, name: str, ranked: list, harnesses: list,
                shown: list | None = None) -> dict:
    """The Keepsake room with the figure at its counter and the party in the case, idling.
    A close call adds the other costume, which swaps with the first one. shown is the party the share
    view keeps, when it differs: that room is drawn again with only those members.
    Also the phone crop: --fx is the native x to centre, between the figure and the party's case, and
    --lx the figure's left edge, which stays in view."""
    seed, tokens = looks.of_sheet(sheet)
    layers = keepsake.banner_layers(pack, main, ranked, harnesses, seed, alternate=alt, **looks.options(tokens))
    shelf = ", ".join(s for s, _ in ranked[:4]) or "nothing yet"
    room = f"A workshop. Its shelves hold {shelf}"
    x, y, w, h = layers.figure_box

    # Every costume draws inside x + 8 to x + 56. The case's third berth ends by 246.
    left = x + 8

    def focus(party):
        return (left + (246 if keepsake_berths(party) else x + w - 8)) // 2

    html = _layer(layers.background.frames, room + _party_words(harnesses), "room" + (" private" if shown is not None else ""))
    style = f"--lx:{left};--fx:{focus(harnesses)}"
    if shown is not None:
        bare = keepsake.banner_layers(pack, main, ranked, shown, seed, **looks.options(tokens))
        html += _layer(bare.background.frames, room + _party_words(shown), "room share-only")
        style += f";--fx-share:{focus(shown)}"
    flip = ""
    if alt:
        html += f'<div class="hit" style="left:{x / 2.52:.3f}%;top:{y / .72:.3f}%;width:{w / 2.52:.3f}%;height:{h / .72:.3f}%"></div>'
        flip = " flip"
    html += _layer(_worn(layers.figure, layers.foreground, layers.figure_box), f"{name} at the counter", "wear main")
    if alt:
        html += _layer(_worn(layers.alternate_figure, layers.alternate_foreground, layers.figure_box),
                       f"{sheet['class']['close']['name']} at the counter", "wear alt")
    return {"style": style, "html": f'<div class="set{flip}">{html}</div>'}


def _party_words(harnesses: list) -> str:
    shown = keepsake_berths(harnesses)
    if not shown:
        return "."
    return ". The party's instruments stand in the case: " + _and([HARNESS_NAMES.get(h, "another harness") for h in shown]) + "."


def _art(sheet: dict, pack: dict) -> dict:
    """Every picture on the sheet. All of it comes from sheet.json and the pack."""
    set_name = sheet["profile"]["set"]
    main, alt = art.sheet_looks(sheet)
    cls = sheet.get("class")
    name = cls["name"] if cls else "Unclassed"
    a = {}
    a["costume"] = ""
    if alt:
        a["costume"] = (f'<button class="costume" id="costumeBtn" type="button" data-a="{e(name)}" '
                        f'data-b="{e(cls["close"]["name"])}">Close call: try the {e(cls["close"]["name"])} costume</button>')
    pcts = art.sheet_pcts(sheet)
    ranked = [(s, pcts[s]) for s in art.art_rank(pcts, set_name)]
    harnesses = [m["harness"] for m in sheet["party"]]
    card = card_visible(sheet.get("card") or {})
    # The share view's room holds only the party members the card shows.
    shown = [m["harness"] for m in sheet["party"] if card and m["name"] in card["members"]]
    differs = card and keepsake_berths(shown) != keepsake_berths(harnesses)
    a["scene"] = _hero_scene(sheet, pack, main, alt, name, ranked, harnesses, shown if differs else None)
    # Party members are presence only: each instrument depends on the harness name alone.
    a["familiar"] = {m["harness"]: keepsake.instrument(m["harness"]).svg(4, f"{m['name']}'s instrument", "px")
                     for m in sheet["party"]}
    a["icon"] = {x["id"]: keepsake.pin(pack, x["id"]).svg(4, "", "px") for x in sheet["achievements"]}
    a["milestone"] = keepsake.pin(pack, "milestone").svg(2, "", "px")
    a["trinket"] = {r["key"]: keepsake.trinket(pack, r["key"]).svg(5, "", "px") for r in sheet["stats"]}
    a["small_trinket"] = {r["key"]: keepsake.trinket(pack, r["key"]).svg(3, "", "px") for r in sheet["stats"]}
    a["hue"] = {r["key"]: art.stat_ramp(pack, r["key"]) for r in sheet["stats"]}
    a["chronicle"] = _chronicle(sheet, pack)
    return a


def _chronicle(sheet: dict, pack: dict) -> str:
    chapters = sheet.get("chronicle") or []
    if not chapters:
        return ""
    set_name = sheet["profile"]["set"]
    # Every chapter is the person in their own look and room, dressed for that quarter's class.
    seed, tokens = looks.of_sheet(sheet)
    cards = []
    cache: dict = {}
    defs: list = []
    camp = None
    for i, ch in enumerate(chapters):
        now = " now" if i == len(chapters) - 1 else ""
        if ch.get("rest"):
            if camp is None:
                camp = keepsake.camp(pack, set_name, seed).svg(2, "A camp under the night sky", "px")
            span = ch["label"] if ch["quarters"] == 1 else f'{ch["label"]} to {ch["label_to"]}'
            latest = ' · <span class="tag">Latest</span>' if now else ""
            cards.append(f'<li class="chap rest{now}"><div class="q">{e(span)}{latest}</div>'
                         f'<div class="pic">{camp}</div><div class="c">Resting at camp</div>'
                         f'<div class="n">{plural(ch["quarters"], "quiet quarter")}</div></li>')
            continue
        look = art.chapter_look(ch, set_name)
        if look not in cache:
            # Each look is drawn once in <defs>. Chapters that share it reuse it.
            ref = f"look-{len(cache)}"
            tile = keepsake.plate(pack, look, seed, **looks.options(tokens))
            data = base64.b64encode(tile.png(2, indexed=True)).decode("ascii")
            defs.append(f'<g id="{ref}"><image width="{tile.w}" height="{tile.h}" style="image-rendering:pixelated" '
                        f'href="data:image/png;base64,{data}"/></g>')
            cache[look] = (f'<svg class="px" viewBox="0 0 {tile.w} {tile.h}" width="{tile.w * 2}" height="{tile.h * 2}" '
                           f'shape-rendering="crispEdges" aria-hidden="true"><use href="#{ref}"/></svg>')
        c = ch.get("class")
        name = c["name"] if c else "Unclassed"
        close = f'<div class="n">close to {e(ch["close"])}</div>' if ch.get("close") else ""
        latest = ' · <span class="tag">Latest</span>' if now else ""
        cards.append(f'<li class="chap{now}"><div class="q">{e(ch["label"])}{latest}</div><div class="pic">{cache[look]}</div>'
                     f'<div class="c">{e(name)}</div>{close}<div class="n">{plural(ch["active_days"], "active day")}</div>'
                     f'</li>')
    return ('<h2>Chronicle</h2><p class="lede">One chapter per calendar quarter, over all history. Each shows the class '
            'that quarter\'s points would give on their own. Quiet quarters rest at camp.</p>'
            f'<svg class="defs" width="0" height="0" aria-hidden="true"><defs>{"".join(defs)}</defs></svg>'
            f'<ol class="chron card">{"".join(cards)}</ol>')


def _share_view(sheet: dict, pix: dict) -> dict:
    """The share view: a CSS-only switch that leaves the banner, name, class, level and the card's
    stats, from the card's visible fields. With the card off there is nothing to mirror, so no switch."""
    prof_name = e(sheet["profile"]["name"])
    v = card_visible(sheet.get("card") or {})
    if not v:
        return {"toggle": "", "button": "", "name": prof_name, "seal_class": "", "stats": ""}
    name = prof_name
    if v["name"] != sheet["profile"]["name"]:
        name = f'<span class="private">{prof_name}</span><span class="share-only">{e(v["name"])}</span>'
    rows = []
    for stat, p in v["stats"]:
        hue = pix["hue"][stat]
        rows.append(f'<div class="row" style="--hue-1:{hue[1]};--hue-2:{_deep(hue)}"><span>{e(stat)}</span>'
                    f'<span class="bar"><i style="width:{p}"></i></span><span class="v">{e(p)}</span></div>')
    foot = "".join(f"<span>{e(line)}</span><br>" for line in v["footer"])
    stats = (f'\n      <div class="share-only"><div class="share-stats" aria-label="Top stats, as the card shows them">'
             f'{"".join(rows)}</div><p class="share-foot">{foot[:-4]}</p></div>')
    return {
        "toggle": '<input class="share-toggle" type="checkbox" id="share-view">\n',
        "button": ('<label class="ghost-btn share-btn" for="share-view"><span class="off">Share view</span>'
                   '<span class="on">Leave share view</span></label>'
                   '<a class="ghost-btn private" href="card.png">card.png</a>'),
        "name": name,
        "seal_class": "" if v["level"] else " private",
        "stats": stats,
    }


def _wash(color: str, alpha: str = "2e") -> str:
    return color + alpha


def _luminance(color: str) -> float:
    c = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


LIGHT_TRACK = "#e2d6c1"  # --grid in the light theme: the empty part of a bar


def _deep(ramp: list) -> str:
    """The stat's shade for bars on the light page: its ramp's third color, deepened toward its
    darkest until it holds 3:1 against the bar's track."""
    track = _luminance(LIGHT_TRACK)
    for step in range(21):
        c = mix(ramp[2], ramp[3], step / 20)
        if (track + 0.05) / (_luminance(c) + 0.05) >= 3:
            return c
    return ramp[3]


def render_html(sheet: dict, built_at: str = "", changes: dict | None = None, pack: dict | None = None) -> str:
    pack = pack or art.default_pack()
    pix = _art(sheet, pack)
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
    evidence = ""
    if cls:
        # How much the class rests on: a one-day share should not read as a strong class.
        cd, ad = tot.get("classified_days", tot["active_days"]), tot["active_days"]
        evidence = (f'<div class="cls-why evidence">Based on {cd} of {plural(ad, "active day")}. '
                    f'The rest changed only unclassified files.</div>' if cd < ad else
                    f'<div class="cls-why evidence">Based on {cd} of {plural(ad, "active day")}.</div>')

    lo = hist["level"] ** 2
    need = hist["next_level_at"] - hist["points"]
    # On an all-history sheet the season's active days are the level points: say it once.
    whole = season.get("from") is None and season.get("to") is None and tot["active_days"] == hist["points"]
    days = ([("Active days", f'{tot["active_days"]}<small>all history, one level point each</small>')] if whole else
            [("Active days", f'{tot["active_days"]}<small>in this season</small>'),
             ("Level points", f'{hist["points"]}<small>all history</small>')])
    vitals = days + [
        ("Projects", f'{len(sheet["projects"])}<small>with points this season</small>'),
        ("Unclassified", f'{pct(tot["unclassified_share"])}<small>of season points, kept out of stats</small>'),
    ]
    vit = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in vitals)

    if sheet["chart"] == "radar":
        chart = _radar(stats, pix["hue"])
        chart_note = ("Eight spokes in the set's order on a square-root scale that is the same on every sheet, "
                      "so two sheets of the same set overlay.")
    else:
        chart = _bars(stats)
        chart_note = "Fewer than three stats have points, so the sheet shows ranked bars instead of a radar."
    table_rows = "".join(f'<tr><td>{e(s["key"])}</td><td class="num">{pts(s["points"])}</td>'
                         f'<td class="num">{pct(s["share"])}</td></tr>' for s in stats)

    # Lit stats get a card each, strongest first. Stats with no points share one line below.
    cards = []
    unlit = []
    for s in sorted(stats, key=lambda s: -s["share"]):
        hue = pix["hue"][s["key"]]
        if s["points"] <= 0:
            unlit.append(f'<span><span class="trinket">{pix["small_trinket"][s["key"]]}</span>'
                         f'<span><b>{e(s["key"])}</b>: {e(s["description"])}</span></span>')
            continue
        projs = "".join(f'<li><span>{e(p["name"])}</span><span>{pts(p["points"])}</span></li>'
                        for p in s["projects"][:5])
        more = len(s["projects"]) - 5
        if more > 0:
            projs += f'<li><span>{more} more</span><span></span></li>'
        body = (f'<div class="ev-h" aria-hidden="true"><span>Project</span><span>Points</span></div>'
                f'<ul class="ev" aria-label="Projects behind it">{projs}</ul>' if projs else "")
        cards.append(
            f'<article class="card stat" style="--hue-1:{hue[1]};--hue-2:{_deep(hue)};--hue-wash:{_wash(hue[1])}">'
            f'<header><span class="trinket">{pix["trinket"][s["key"]]}</span>'
            f'<h3>{e(s["key"])}</h3><div class="pts">{pct(s["share"])}<small>{pts(s["points"])} pts</small></div>'
            f'</header><p class="def">{e(s["description"])}</p>'
            f'<span class="bar"><i style="width:{s["share"] * 100:.1f}%"></i></span>{body}</article>')
    unlit_html = (f'<div class="unlit"><span>No points this season:</span>{"".join(unlit)}</div>' if unlit else "")

    party = []
    for m in sheet["party"]:
        models = "".join(f'<span class="m">{e(x)}</span>' for x in m["models"][:6])
        if len(m["models"]) > 6:
            models += f'<span class="m">+{len(m["models"]) - 6} more</span>'
        facts = [("Sessions", m["sessions"])]
        party.append(
            f'<article class="card comp"><div class="fam">{pix["familiar"][m["harness"]]}</div>'
            f'<div><div class="nm">{e(m["name"])}</div><div class="role">{e(m["role"])}</div></div>'
            f'<div class="big">{m["days_together"]}<small>days together</small></div>'
            f'<dl class="facts">{"".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in facts)}</dl>'
            f'<div class="when"><span>{day_label(m["first_day"])} to {day_label(m["last_day"])}</span>{models}</div></article>')
    party_html = (f'<div class="party">{"".join(party)}</div>' if party
                  else '<p class="empty">No harness sessions inside this profile.</p>')

    achs = []
    for a in sheet["achievements"]:
        count = f" ×{a['count']}" if a.get("count", 1) > 1 else ""
        detail = f'<div class="src">{e(a["detail"])}</div>' if a.get("detail") else ""
        achs.append(f'<article class="card ach"><div class="ic">{pix["icon"][a["id"]]}</div><div>'
                    f'<div class="t">{e(a["title"])}{count}</div>'
                    f'<div class="d">{day_label(a["date"])}</div><div class="x">{e(a["rule"])}</div>{detail}</div></article>')
    ach_html = f'<div class="achs">{"".join(achs)}</div>' if achs else '<p class="empty">None yet.</p>'
    ms = "".join(f'<li><span>{day_label(m["date"])}</span><span><span class="ic">{pix["milestone"]}</span>{e(m["text"])}</span></li>'
                 for m in sheet["milestones"])
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
        un_html = (f'<p class="lede" style="margin-top:12px">Outside every root: {plural(un["sessions"], "session")} in {plural(un["folders"], "folder")} and '
                   f'{plural(un["edits"], "edited file")}. They are not scored. Run <code>tinkerprint build</code> in a terminal to list '
                   f'the folders, then add roots to the profile if they belong.</p>')

    card_note = ('Card on: <a href="card.png">card.png</a> to post, and <a href="card.svg">card.svg</a>. '
                 "Run <code>tinkerprint audit</code> to see every string they hold."
                 if sheet["card"].get("enabled") else e(sheet["card"].get("reason", "Card off.")))
    share = _share_view(sheet, pix)
    work = " · work profile" if prof.get("work") else ""
    as_of = f" · as of {day_label(season['as_of'])}" if season.get("as_of") else ""
    built = f"Built {e(built_at)}. " if built_at else ""
    scene = pix["scene"]
    jump = ""
    if changes and changes.get("against"):
        jump = f'<a class="jump" href="#changed">What changed since {day_label(changes["against"])}</a>'

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
{share["toggle"]}<div class="wrap">
<div class="top">
  <div class="eyebrow">tinkerprint · <b>{e(set_title)} set</b><span class="private"> · {e(season["label"])}{as_of}{work}</span></div>
  <div class="tools">{share["button"]}<button class="ghost-btn" id="themeBtn" type="button">Theme: auto</button></div>
</div>
<section class="hero">
  <div class="banner" style="{scene["style"]}">{scene["html"]}</div>
  <div class="plaque">
    <div class="who">
      <h1>{share["name"]}</h1>
      <div class="cls">{cls_html}</div>
      <div class="private"><div class="cls-why">{why}</div>{evidence}{pix["costume"]}{jump}</div>
    </div>
    <div class="xp">
      <div class="lv">
        <div class="seal{share["seal_class"]}"><div class="n">{hist["level"]}</div><div class="l">Level</div></div>
        <div class="private">
          <div class="next"><span>{hist["points"] - lo} of {hist["next_level_at"] - lo} to level {hist["level"] + 1}</span><span>{plural(need, "day")} to go</span></div>
          <span class="bar"><i style="width:{hist["level_progress"] * 100:.1f}%"></i></span>
        </div>
      </div>
      <dl class="vitals n{len(vitals)} private">{vit}</dl>{share["stats"]}
    </div>
  </div>
</section>
<div class="private">

<h2>The build</h2>
<p class="lede">Each active day is one point. It splits across the day's projects, then across each project's stats, by the log of files changed. Shares are of classified points.</p>
<div class="build">
  <div class="card radar-card">
    <h3>Where the season's points went</h3>
    <p class="sub">{chart_note}</p>
    {chart}
    <details><summary>Stats as a table</summary><div class="scroll-x"><table><thead><tr><th>Stat</th><th class="num">Points</th><th class="num">Share</th></tr></thead><tbody>{table_rows}</tbody></table></div></details>
  </div>
  <div class="stats">{"".join(cards)}{unlit_html}</div>
</div>

<h2>Party</h2>
<p class="lede">The agents that worked beside you. The party shows presence, never a share of the work. Each label says only what the logs recorded. Sessions with no file change earn no points.</p>
{party_html}

<h2>Achievements</h2>
<p class="lede">Generic rules, the same for everyone. Each shows its rule and the day it was earned. Commits and tags count only where they touch the profile's folders.</p>
{ach_html}
{ms_html}

{pix["chronicle"]}

{_changes(changes)}

<h2>Projects</h2>
{proj_html}
{un_html}

<h2>Method</h2>
<div class="method">
<p><b>Method version {sheet["method"]}.</b> Same inputs and profile give the same sheet. The inputs are your repos, the agent logs on disk and what earlier builds kept from logs that are gone. No model scores anything.</p>
<p><b>Points.</b> One active day is one point. Level is the square root of all-history points, rounded down. Class and radar cover the season.</p>
<p><b>Days</b> run from {prof["rollover_hour"]:02d}:00 to {prof["rollover_hour"]:02d}:00 in {e(prof["timezone"])}.</p>
<p><b>Class.</b> A stat at 50% or more makes a specialist. No stat over 20% makes a generalist. Otherwise the top two make a pair when the runner-up holds 10%. When the next pair or stat sits within 2 points, the sheet names it too.</p>
<p><b>What this is not.</b> A sheet never claims skill, productivity, seniority, hours worked, or who did how much of the work.</p>
<p><b>Share card.</b> {card_note}</p>
</div>
<p class="foot">{built}{e(sheet["tool"])}, method {sheet["method"]}. Made on this machine. Nothing was uploaded.</p>
</div>
</div>
<script>{JS}</script>
</body>
</html>
"""
