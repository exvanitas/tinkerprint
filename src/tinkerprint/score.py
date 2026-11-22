"""Scoring: events + profile + set -> sheet. Pure: no file system, no clock, no randomness.

The sheet depends on the events and the profile alone. `compare` builds "what changed" against an
earlier saved sheet, and that result never enters sheet.json.
"""
from __future__ import annotations

import math
import os
from collections import Counter, defaultdict
from datetime import date

from . import METHOD_VERSION, SHEET_FORMAT, __version__
from .achievements import evaluate
from .chronicle import chronicle
from .classes import card_pct, class_key, multiclass, pick_class, ranked
from .classify import classify, is_code, is_skipped, language_of
from .look import TOKENS as LOOK_TOKENS, public_name, resolve as resolve_look
from .datadir import path_within
from .party import HARNESS_NAMES, build_party
from .projects import Resolver
from .sets import DESCRIPTIONS, TINKERER_CODE_STATS, stats_of
from .timeutil import day_label, day_of, month_label, parse_ts

BULK_LIMIT = 200
ND = 6  # decimals kept for every float in the sheet


def _r(x: float) -> float:
    v = round(x, ND)
    return 0.0 if v == 0 else v


def _season_label(frm, to) -> str:
    if not frm and not to:
        return "All history"
    a = day_label(frm.isoformat()) if frm else "the start"
    b = day_label(to.isoformat()) if to else "now"
    return f"{a} to {b}"


def score_core(inp, profile, priors: dict, season=(None, None), as_of: date | None = None,
               milestones=()) -> tuple:
    """Returns (core sheet, local). `local` holds things only the terminal sees (unassigned folders)."""
    tz = profile.tz
    ro = profile.rollover_hour
    stats = stats_of(profile.set)
    resolver = Resolver(profile.projects)
    by_name = {p.name: p for p in profile.projects}
    frm, to = season

    def dayof(ts: str) -> date:
        return day_of(parse_ts(ts), tz, ro)

    def in_bounds(d: date) -> bool:
        return as_of is None or d <= as_of

    def in_season(d: date) -> bool:
        return in_bounds(d) and (frm is None or d >= frm) and (to is None or d <= to)

    root_ids = getattr(inp, "root_ids", {}) or {}

    def file_key(root: str, rel: str):
        # A file in git is its repository plus its repository-relative path, so clones and roots
        # at any depth agree. Outside git it is the root plus the path under it.
        rid = root_ids.get(root)
        if isinstance(rid, (tuple, list)) and len(rid) == 2:
            return (rid[0], "/".join(x for x in (rid[1], rel) if x))
        return (root, rel)

    # 1. Resolve every event once. Sessions keep dated observations for the party.
    # Everything outside every root is collected here first, before any other filtering, and listed
    # by season: session folders with their distinct sessions, and folders of changed files.
    resolved = []
    sessions: dict = {}   # (harness, session) -> {"obs": [(day, model, edited)], "origin"}
    out_sessions = defaultdict(set)   # folder -> sessions seen there in season
    unassigned_edits = set()          # files changed outside every root in season
    outside_bulk = Counter()          # commit -> added non-code files outside every root
    lines = []
    latest = None
    for ev in sorted(inp.events):
        dt = parse_ts(ev.ts)
        if dt is None:
            continue
        d = day_of(dt, tz, ro)
        if not in_bounds(d):
            continue
        latest = d if latest is None or d > latest else latest
        hit = resolver.resolve_root(ev.path)
        outside = hit is None or (ev.kind != "session" and not hit[2])
        if outside:
            if ev.kind == "commit" and ev.status == "A" and not is_code(ev.path) and not is_skipped(ev.path):
                outside_bulk[ev.commit] += 1
            if in_season(d):
                if ev.kind == "session":
                    out_sessions[ev.path or "(no folder)"].add((ev.harness, ev.session))
                else:
                    unassigned_edits.add(ev.path)
                    if ev.kind == "edit":
                        out_sessions[os.path.dirname(ev.path) or "(no folder)"].add((ev.harness, ev.session))
            continue
        if ev.kind in ("session", "edit"):
            s = sessions.setdefault((ev.harness, ev.session), {"obs": [], "origin": ev.origin})
            s["obs"].append((d, ev.model, ev.kind == "edit"))
            if ev.kind == "session":
                continue
        proj, root, rel = hit
        resolved.append((ev, d, proj, root, rel))

    # 2. Bulk imports: a commit adding more than 200 non-code files counts them once, as one file
    # spread over its projects with the average weights of those files, unclassified share kept.
    bulk_rows = defaultdict(list)
    for ev, d, proj, root, rel in resolved:
        if ev.kind == "commit" and ev.status == "A" and not is_code(rel) and not is_skipped(rel):
            bulk_rows[ev.commit].append((d, proj, root, rel))
    # Eligibility counts the whole commit, files outside the profile included.
    bulk = {h: rows for h, rows in bulk_rows.items() if len(rows) + outside_bulk[h] > BULK_LIMIT}
    in_bulk = {(h, proj.name, root, rel) for h, rows in bulk.items() for _, proj, root, rel in rows}

    touches: dict = defaultdict(dict)  # (day, project) -> {file key: (weights, mass)}
    commits_seen = set()
    counted = Counter()
    for ev, d, proj, root, rel in resolved:
        if ev.kind == "edit":
            counted["edits"] += 1
        elif ev.kind == "commit":
            commits_seen.add(ev.commit)
            if not is_skipped(rel):
                lang = language_of(rel)
                if lang and ev.added:
                    lines.append((d, lang, ev.added))
            if (ev.commit, proj.name, root, rel) in in_bulk:
                continue
        w = classify(rel, proj, profile.set, priors, root)
        if w is None:
            continue
        touches[(d, proj.name)][file_key(root, rel)] = (w, 1.0)
    for h, rows in sorted(bulk.items()):
        per_proj = defaultdict(list)
        for d, proj, root, rel in rows:
            w = classify(rel, proj, profile.set, priors, root)
            if w is not None:
                per_proj[(d, proj.name)].append(w)
        total = len(rows) + outside_bulk[h]
        for (d, pname), ws in sorted(per_proj.items()):
            avg = defaultdict(float)
            for w in ws:
                for k, x in w.items():
                    avg[k] += x / len(ws)
            touches[(d, pname)][("bulk", h)] = (dict(avg), len(ws) / total)
    touches = {k: v for k, v in touches.items() if v}
    counted["commits"] = len(commits_seen)

    # 3. Tinkerer: Data and Tests count with the project's main code stat.
    main_stat = {}
    if profile.set == "tinkerer":
        seen: dict = {}
        for (d, pname), files in touches.items():
            for key, wm in files.items():
                seen[(pname, key)] = wm
        tally = defaultdict(Counter)
        for (pname, key), (w, mass) in seen.items():
            for s, x in w.items():
                if s in TINKERER_CODE_STATS:
                    tally[pname][s] += x * mass
        for p in profile.projects:
            t = tally.get(p.name)
            main_stat[p.name] = (sorted(TINKERER_CODE_STATS, key=lambda s: (-t[s], stats.index(s)))[0]
                                 if t and sum(t.values()) > 0 else "Systems")

    # 4. One point per active day, split by log(1 + files) per project, then per stat.
    days: dict = defaultdict(dict)  # day -> project -> files
    for (d, pname), files in sorted(touches.items()):
        days[d][pname] = files
    day_points: dict = {}
    for d in sorted(days):
        projs = days[d]
        # Every sum is math.fsum over a fixed order, so equal contributions give exactly equal totals.
        pw = {p: math.log1p(math.fsum(m for _, m in sorted(f.values(), key=repr))) for p, f in sorted(projs.items())}
        total = math.fsum(pw[p] for p in sorted(pw))
        out = {}
        for pname in sorted(projs):
            share = pw[pname] / total
            parts = defaultdict(list)
            for key in sorted(projs[pname], key=repr):
                w, mass = projs[pname][key]
                for s, x in w.items():
                    parts[main_stat.get(pname, "Systems") if s is None else s].append(x * mass)
            per = {s: math.fsum(v) for s, v in parts.items()}
            sw = {s: math.log1p(n) for s, n in per.items() if n > 0}
            st = math.fsum(sw[s] for s in sorted(sw, key=str))
            out[pname] = {s: share * v / st for s, v in sorted(sw.items(), key=lambda kv: str(kv[0]))}
        day_points[d] = out

    active = sorted(day_points)
    points_all = len(active)
    level = math.isqrt(points_all)
    nxt = (level + 1) ** 2
    floor_pts = level ** 2

    # 5. Season totals.
    season_days = [d for d in active if in_season(d)]
    stat_parts = {s: [] for s in stats}
    stat_proj_parts = {s: defaultdict(list) for s in stats}
    proj_parts = defaultdict(list)
    proj_days = defaultdict(int)
    unclassified_parts = []
    classified_days = 0  # season days with any classified points: what the class rests on
    for d in season_days:
        if any(v > 0 for per in day_points[d].values() for s, v in per.items() if s != ""):
            classified_days += 1
        for pname in sorted(day_points[d]):
            per = day_points[d][pname]
            proj_days[pname] += 1
            for s in sorted(per, key=str):
                v = per[s]
                proj_parts[pname].append(v)
                if s == "":
                    unclassified_parts.append(v)
                else:
                    stat_parts[s].append(v)
                    stat_proj_parts[s][pname].append(v)
    stat_pts = {s: math.fsum(stat_parts[s]) for s in stats}
    stat_proj = {s: {p: math.fsum(v) for p, v in stat_proj_parts[s].items()} for s in stats}
    proj_pts = {p: math.fsum(v) for p, v in proj_parts.items()}
    unclassified = math.fsum(unclassified_parts)
    classified = math.fsum(stat_pts[s] for s in stats)
    shares = {s: (stat_pts[s] / classified if classified > 0 else 0.0) for s in stats}
    shares_r = {s: _r(v) for s, v in shares.items()}

    stat_rows = []
    for s in stats:
        stat_rows.append({
            "key": s,
            "description": DESCRIPTIONS[profile.set][s],
            "points": _r(stat_pts[s]),
            "share": shares_r[s],
            "projects": [{"name": p, "points": _r(v)} for p, v in
                         sorted(stat_proj[s].items(), key=lambda kv: (-round(kv[1], ND), kv[0])) if _r(v) > 0],
        })

    cls = pick_class(shares, profile.set)
    if cls:
        cls["why"] = _class_why(cls, shares)
    lit = sum(1 for s in stats if stat_pts[s] > 0)

    # 6. Party and unassigned presence. Only observations inside the profile's roots count,
    # and the season filters each observation, not each session.
    mine = {k: v for k, v in sessions.items() if v["obs"]}
    party = build_party(mine, in_season)
    harness_days = defaultdict(set)
    for (h, _), s in mine.items():
        harness_days[h] |= {d for d, _, _ in s["obs"]}
    # Computed once here. sheet.json and the terminal listing both use these totals.
    un_sessions = set().union(*out_sessions.values()) if out_sessions else set()
    edit_folders = {os.path.dirname(p) or "(no folder)" for p in unassigned_edits}
    un_folders = set(out_sessions) | edit_folders

    # 7. Achievements over all history up to as_of.
    def repo_name(top: str) -> str:
        hit = resolver.resolve(top)
        if hit:
            return hit[0].name
        for p in profile.projects:
            if any(path_within(r, top) for r in p.roots):
                return p.name
        return "a repo"

    commits = [c for c in inp.commits if in_bounds(dayof(c.ts))]
    tags = [t for t in inp.tags if in_bounds(dayof(t.ts))]
    achievements = evaluate(active, commits, tags, harness_days, dayof, repo_name, sorted(lines))
    ms = sorted(({"date": d.isoformat(), "text": t} for d, t in milestones if in_bounds(d)),
                key=lambda m: (m["date"], m["text"]))

    projects = [{"name": p, "points": _r(v), "days": proj_days[p],
                 "share": _r(v / len(season_days)) if season_days else 0.0}
                for p, v in sorted(proj_pts.items(), key=lambda kv: (-round(kv[1], ND), kv[0]))]

    core = {
        "format": SHEET_FORMAT,
        "method": METHOD_VERSION,
        "tool": f"tinkerprint {__version__}",
        "profile": {"name": profile.name, "set": profile.set, "work": profile.work,
                    "timezone": profile.timezone, "rollover_hour": profile.rollover_hour},
        # The portrait's look. Its seed is the name the card shows, so the face follows a field
        # already on the card.
        "look": portrait_look(profile),
        "season": {"from": frm.isoformat() if frm else None, "to": to.isoformat() if to else None,
                   "as_of": as_of.isoformat() if as_of else None, "label": _season_label(frm, to)},
        "history": {
            "points": points_all,
            "active_days": points_all,
            "first_day": active[0].isoformat() if active else None,
            "last_day": active[-1].isoformat() if active else None,
            "level": level,
            "next_level_at": nxt,
            "level_progress": _r((points_all - floor_pts) / (nxt - floor_pts)),
        },
        "season_totals": {
            "active_days": len(season_days),
            "points": len(season_days),
            "classified": _r(classified),
            "classified_days": classified_days,
            "unclassified": _r(unclassified),
            "unclassified_share": _r(unclassified / len(season_days)) if season_days else 0.0,
            "first_day": season_days[0].isoformat() if season_days else None,
            "last_day": season_days[-1].isoformat() if season_days else None,
        },
        "stats": stat_rows,
        "chart": "radar" if lit >= 3 else "bars",
        "class": cls,
        "multiclass": multiclass(shares, profile.set, cls),
        "projects": projects,
        "party": party,
        "achievements": achievements,
        "milestones": ms,
        "chronicle": chronicle(day_points, profile.set),
        "unassigned": {"sessions": len(un_sessions), "folders": len(un_folders), "edits": len(unassigned_edits)},
        "inputs": {"commits": counted["commits"], "agent_edits": counted["edits"],
                   "sessions": len(mine)},
    }
    local = {"shares": shares, "latest_day": latest,
             "unassigned_folders": sorted(((f, len(v)) for f, v in out_sessions.items()), key=lambda kv: (-kv[1], kv[0])),
             "unassigned_edit_folders": sorted(edit_folders)}
    core["card"] = card_fields(core, profile, shares)
    return core, local


def _class_why(cls: dict | None, shares: dict) -> str:
    if not cls:
        return "No classified points yet."
    pct = lambda s: f"{round(shares.get(s, 0) * 100)}%"
    if cls["kind"] == "generalist":
        return "No stat holds more than 20%."
    if cls["kind"] == "specialist":
        why = f"{cls['stats'][0]} holds {pct(cls['stats'][0])}."
        if cls.get("close"):
            other = cls["close"]["stats"][0]
            why += f" {other} {pct(other)} is within 2 points."
        return why
    a, b = cls["stats"]
    why = f"{a} {pct(a)} and {b} {pct(b)}."
    close = cls.get("close")
    if close:
        other = [s for s in close["stats"] if s not in cls["stats"]]
        if other:
            why += f" {other[0]} {pct(other[0])} is within 2 points."
    return why


# What a saved sheet's scope digests cover, in the words "what changed" uses.
SCOPE_PARTS = {"projects": "projects", "roots": "roots", "identity": "identity", "harnesses": "harnesses",
               "days": "time zone or rollover"}


def compare(sheet: dict, prev: dict | None, prev_as_of: str | None, scope: dict | None = None) -> dict:
    """What changed since an earlier sheet of the same profile and season. Never part of sheet.json.

    Points, level, party and achievements always compare. Class and share drift compare only
    within one set. Unclassed to classed is a new class. A sheet made by another method version
    is named but not compared. scope: this build's scope_digests. When the earlier saved sheet
    holds different ones, scope_changed names what changed, since the differences then include
    history newly added or removed and not only new activity.
    """
    if not prev:
        return {"against": None}
    if prev.get("method") != sheet.get("method"):
        return {"against": prev_as_of, "method_changed": True, "method_from": prev.get("method"),
                "method_to": sheet.get("method")}
    before = prev.get("_scope") if isinstance(prev.get("_scope"), dict) else None
    scope_changed = ([SCOPE_PARTS[k] for k in SCOPE_PARTS if before.get(k) != scope.get(k)]
                     if before and scope else [])
    set_changed = prev.get("profile", {}).get("set") != sheet["profile"]["set"]
    ph, h = prev.get("history", {}), sheet["history"]
    drift = []
    if not set_changed:
        pshares = {r["key"]: r.get("share", 0.0) for r in prev.get("stats", [])}
        for r in sheet["stats"]:
            delta = _r(r["share"] - pshares.get(r["key"], 0.0))
            if abs(delta) >= 0.01:
                drift.append({"stat": r["key"], "from": _r(pshares.get(r["key"], 0.0)), "to": r["share"],
                              "delta": delta})
        drift.sort(key=lambda x: -abs(x["delta"]))
    pp = {m["harness"]: m for m in prev.get("party", [])}
    cp = {m["harness"]: m for m in sheet["party"]}
    pa = {a["id"] for a in prev.get("achievements", [])}
    pc, cc = prev.get("class"), sheet.get("class")
    return {
        "against": prev_as_of,
        "method_changed": False,
        "scope_changed": scope_changed,
        "set_changed": set_changed,
        "set_from": prev.get("profile", {}).get("set"),
        "points_since": h["points"] - int(ph.get("points", 0)),
        "level_from": ph.get("level"),
        "level_to": h["level"],
        "class_from": (pc or {}).get("name") or "Unclassed",
        "class_to": (cc or {}).get("name") or "Unclassed",
        "new_class": not set_changed and class_key(pc) != class_key(cc),
        "drift": drift,
        "party_joined": [HARNESS_NAMES[k] for k in sorted(set(cp) - set(pp))],
        "party_left": [HARNESS_NAMES[k] for k in sorted(set(pp) - set(cp)) if k in HARNESS_NAMES],
        "party_sessions": [{"name": cp[k]["name"], "sessions_since": cp[k]["sessions"] - pp[k]["sessions"]}
                           for k in sorted(set(cp) & set(pp)) if cp[k]["sessions"] != pp[k]["sessions"]],
        "achievements_new": [a["title"] for a in sheet["achievements"] if a["id"] not in pa],
    }


def card_fields(sheet: dict, profile, shares: dict | None = None) -> dict:
    """The share card's allowlist. Nothing else ever reaches card.svg, card.png or audit's listing.
    Fields the profile hides under [card] hide are left out here, so no renderer can draw them."""
    if not profile.card_enabled:
        reason = ("Work profile. Set [card] enabled = true to make a card." if profile.work
                  else "The profile sets [card] enabled = false.")
        return {"enabled": False, "reason": reason}
    cls = sheet.get("class") or {}
    multi = sheet.get("multiclass") or {}
    hide = set(getattr(profile, "card_hide", ()))
    stats = []
    for r in sheet["stats"]:
        full = shares.get(r["key"], r["share"]) if shares else r["share"]
        # Under 5% at full precision stays off the card. The rest round to the nearest 5%.
        pct = card_pct(full)
        stats.append({"stat": r["key"], "pct": pct})
    # The card's chart follows the rounded public shares, so it never reveals stats under 5%.
    public_chart = "radar" if sum(1 for x in stats if x["pct"] > 0) >= 3 else "bars"
    exact = "dates" in profile.card_show
    season = sheet["season"]
    card = {
        "enabled": True,
        # The name as the card shows it, clipped: the portrait's seed, so nothing hidden seeds the art.
        "name": public_name(getattr(profile, "card_label", profile.name)),
        "set": profile.set.capitalize(),
        "class": cls.get("display") or "Unclassed",
        "multiclass": multi.get("display") or "",
        # The stats the class and multiclass are named for. A tie in rounded shares never hides them.
        "named": list(cls.get("stats") or []) + list(multi.get("stats") or []),
        # The look tokens the portrait is drawn from, with the name above as its seed.
        "look": {k: (sheet.get("look") or portrait_look(profile))[k] for k in LOOK_TOKENS},
        "stats": stats,
        "chart": public_chart,
        "method": sheet["method"],
        "season": _card_season(season.get("from"), season.get("to"), exact),
    }
    if "level" not in hide:
        # The level and the day counts give the same band away, so they hide together.
        tot = sheet["season_totals"]
        card["level"] = sheet["history"]["level"]
        card["days"] = {"active": tot["active_days"], "classified": tot.get("classified_days", tot["active_days"])}
    if "achievements" not in hide:
        card["achievements"] = [{"title": a["title"], "when": day_label(a["date"]) if exact else month_label(a["date"])}
                                for a in sheet["achievements"]]
    if "party" not in hide:
        card["party"] = [m["name"] for m in sheet["party"]]
    if "projects" in profile.card_show:
        card["projects"] = [p["name"] for p in sheet["projects"][:3]]
    return card


def portrait_look(profile) -> dict:
    """The look in use: the profile's [look] choices, and the rest picked from the card's name."""
    seed = public_name(getattr(profile, "card_label", profile.name))
    return dict(resolve_look(getattr(profile, "look", {}) or {}, seed), seed=seed)


def _card_season(frm: str | None, to: str | None, exact: bool = False) -> str:
    """The season in a few words for the card, or "" for all history. Months, unless the profile
    shows dates."""
    label = day_label if exact else month_label
    if frm and to:
        return f"{label(frm)} to {label(to)}"
    if frm:
        return f"from {label(frm)}"
    if to:
        return f"up to {label(to)}"
    return ""


def ranked_stats(sheet: dict, set_name: str) -> list:
    shares = {r["key"]: r["share"] for r in sheet["stats"]}
    return ranked(shares, set_name)
