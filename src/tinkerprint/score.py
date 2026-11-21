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
from .classes import class_key, multiclass, pick_class, ranked
from .classify import classify, is_code, is_skipped, language_of
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
        # Clones of one repo share an identity, so their copies of a file are one file.
        return (root_ids.get(root, root), rel)

    # 1. Resolve every event once. Sessions keep dated observations for the party.
    resolved = []
    sessions: dict = {}   # (harness, session) -> {"obs": [(day, model, edited)], "out": [(day, folder)], "origin"}
    unassigned_edits = set()
    lines = []
    for ev in sorted(inp.events):
        dt = parse_ts(ev.ts)
        if dt is None:
            continue
        d = day_of(dt, tz, ro)
        if not in_bounds(d):
            continue
        hit = resolver.resolve_root(ev.path)
        if ev.kind in ("session", "edit"):
            s = sessions.setdefault((ev.harness, ev.session), {"obs": [], "out": [], "origin": ev.origin})
            if hit is None or (ev.kind == "edit" and not hit[2]):
                s["out"].append((d, ev.path if ev.kind == "session" else os.path.dirname(ev.path)))
                if ev.kind == "edit" and in_season(d):
                    unassigned_edits.add(ev.path)
                continue
            s["obs"].append((d, ev.model, ev.kind == "edit"))
            if ev.kind == "session":
                continue
        elif hit is None:
            continue
        proj, root, rel = hit
        if not rel:
            continue
        resolved.append((ev, d, proj, root, rel))

    # 2. Bulk imports: a commit adding more than 200 non-code files counts them once, as one file
    # spread over its projects with the average weights of those files, unclassified share kept.
    bulk_rows = defaultdict(list)
    for ev, d, proj, root, rel in resolved:
        if ev.kind == "commit" and ev.status == "A" and not is_code(rel) and not is_skipped(rel):
            bulk_rows[ev.commit].append((d, proj, root, rel))
    bulk = {h: rows for h, rows in bulk_rows.items() if len(rows) > BULK_LIMIT}
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
        w = classify(rel, proj, profile.set, priors)
        if w is None:
            continue
        touches[(d, proj.name)][file_key(root, rel)] = (w, 1.0)
    for h, rows in sorted(bulk.items()):
        per_proj = defaultdict(list)
        for d, proj, root, rel in rows:
            w = classify(rel, proj, profile.set, priors)
            if w is not None:
                per_proj[(d, proj.name)].append(w)
        total = sum(len(v) for v in per_proj.values())
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
        pw = {p: math.log1p(sum(m for _, m in f.values())) for p, f in projs.items()}
        total = sum(pw.values())
        out = {}
        for pname in sorted(projs):
            share = pw[pname] / total
            per = defaultdict(float)
            for w, mass in projs[pname].values():
                for s, x in w.items():
                    per[main_stat.get(pname, "Systems") if s is None else s] += x * mass
            sw = {s: math.log1p(n) for s, n in per.items() if n > 0}
            st = sum(sw.values())
            out[pname] = {s: share * v / st for s, v in sorted(sw.items(), key=lambda kv: str(kv[0]))}
        day_points[d] = out

    active = sorted(day_points)
    points_all = len(active)
    level = math.isqrt(points_all)
    nxt = (level + 1) ** 2
    floor_pts = level ** 2

    # 5. Season totals.
    season_days = [d for d in active if in_season(d)]
    stat_pts = {s: 0.0 for s in stats}
    stat_proj = {s: defaultdict(float) for s in stats}
    proj_pts = defaultdict(float)
    proj_days = defaultdict(int)
    unclassified = 0.0
    for d in season_days:
        for pname, per in day_points[d].items():
            proj_days[pname] += 1
            for s, v in per.items():
                proj_pts[pname] += v
                if s == "":
                    unclassified += v
                else:
                    stat_pts[s] += v
                    stat_proj[s][pname] += v
    classified = sum(stat_pts.values())
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
    un_folders = Counter()
    for key, s in sessions.items():
        if key in mine:
            continue
        seen = sorted({f for d, f in s["out"] if in_season(d)})
        if seen:
            un_folders[seen[0] or "(no folder)"] += 1

    # 7. Achievements over all history up to as_of.
    def repo_name(top: str) -> str:
        hit = resolver.resolve(top)
        if hit:
            return hit[0].name
        for p in profile.projects:
            if any(r.startswith(top.rstrip("/") + "/") for r in p.roots):
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
        "unassigned": {"sessions": sum(un_folders.values()), "folders": len(un_folders),
                       "edits": len(unassigned_edits)},
        "inputs": {"commits": counted["commits"], "agent_edits": counted["edits"],
                   "sessions": len(mine)},
    }
    local = {"shares": shares,
             "unassigned_folders": sorted(un_folders.items(), key=lambda kv: (-kv[1], kv[0])),
             "unassigned_edit_folders": sorted({os.path.dirname(p) for p in unassigned_edits})}
    core["card"] = card_fields(core, profile)
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


def compare(sheet: dict, prev: dict | None, prev_as_of: str | None) -> dict:
    """What changed since an earlier sheet of the same profile and season. Never part of sheet.json."""
    if not prev or prev.get("method") != sheet.get("method") or \
            prev.get("profile", {}).get("set") != sheet["profile"]["set"]:
        return {"against": None}
    ph, h = prev.get("history", {}), sheet["history"]
    pshares = {r["key"]: r.get("share", 0.0) for r in prev.get("stats", [])}
    drift = []
    for r in sheet["stats"]:
        delta = _r(r["share"] - pshares.get(r["key"], 0.0))
        if abs(delta) >= 0.01:
            drift.append({"stat": r["key"], "from": _r(pshares.get(r["key"], 0.0)), "to": r["share"], "delta": delta})
    drift.sort(key=lambda x: -abs(x["delta"]))
    pp = {m["harness"]: m for m in prev.get("party", [])}
    cp = {m["harness"]: m for m in sheet["party"]}
    pa = {a["id"] for a in prev.get("achievements", [])}
    pc, cc = prev.get("class") or {}, sheet.get("class") or {}
    return {
        "against": prev_as_of,
        "points_since": h["points"] - int(ph.get("points", 0)),
        "level_from": ph.get("level"),
        "level_to": h["level"],
        "class_from": pc.get("name"),
        "class_to": cc.get("name"),
        "new_class": bool(pc) and bool(cc) and class_key(pc) != class_key(cc),
        "drift": drift,
        "party_joined": [HARNESS_NAMES[k] for k in sorted(set(cp) - set(pp))],
        "party_left": [HARNESS_NAMES[k] for k in sorted(set(pp) - set(cp)) if k in HARNESS_NAMES],
        "party_sessions": [{"name": cp[k]["name"], "sessions_since": cp[k]["sessions"] - pp[k]["sessions"]}
                           for k in sorted(set(cp) & set(pp)) if cp[k]["sessions"] != pp[k]["sessions"]],
        "achievements_new": [a["title"] for a in sheet["achievements"] if a["id"] not in pa],
    }


def card_fields(sheet: dict, profile) -> dict:
    """The share card's allowlist. Nothing else ever reaches card.svg or audit's card listing."""
    if not profile.card_enabled:
        return {"enabled": False, "reason": "Work profile. Set [card] allow = true to make a card."}
    cls = sheet.get("class") or {}
    multi = sheet.get("multiclass") or {}
    stats = []
    for r in sheet["stats"]:
        pct = int(round(r["share"] * 20)) * 5
        stats.append({"stat": r["key"], "pct": pct})
    exact = "dates" in profile.card_show
    card = {
        "enabled": True,
        "name": profile.name,
        "set": profile.set.capitalize(),
        "class": cls.get("display") or "Unclassed",
        "multiclass": multi.get("display") or "",
        "level": sheet["history"]["level"],
        "stats": stats,
        "achievements": [{"title": a["title"], "when": day_label(a["date"]) if exact else month_label(a["date"])}
                         for a in sheet["achievements"]],
        "party": [m["name"] for m in sheet["party"]],
        "chart": sheet["chart"],
    }
    if "projects" in profile.card_show:
        card["projects"] = [p["name"] for p in sheet["projects"][:3]]
    return card


def ranked_stats(sheet: dict, set_name: str) -> list:
    shares = {r["key"]: r["share"] for r in sheet["stats"]}
    return ranked(shares, set_name)
