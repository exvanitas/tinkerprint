"""Build pipeline: read sources, score, render, then save the sheet to history."""
from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import date, datetime, time, timedelta

from . import art
from .events import Event, Inputs
from .profile import Profile
from .projects import Resolver, canonical, scan_priors
from .readers import agy, claude, codex
from .readers._common import HashingStream, new_health, version_text
from .readers.git import Identity, read_git
from .render_card import portrait_gif, portrait_png, render_card
from .render_card_png import render_card_png
from .render_html import render_html
from .history import History, scope_digests
from .keys import adopt
from .score import compare, score_core
from .datadir import (_is_git_dir, _write, data_home, data_lock, inside_repo_or_root, mark_home, mark_sheets,
                      path_within, pretty)
from .timeutil import month_label, parse_day, parse_ts

# A version change re-reads every log that is still there, and keeps what earlier builds read
# from logs that are gone, since those can never be read again.
CACHE_VERSION = 5
# Cache versions whose events this version still reads as they are. 4 is tinkerprint 0.1's, which
# kept the same events but never marked an entry gone. A log such a cache read that is gone now
# keeps its events. Any other version keeps only entries it marked gone itself.
EVENTS_VALID = (4, 5)


def _digest(path: str) -> str | None:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(1 << 20), b""):
                h.update(block)
    except OSError:
        return None
    return h.hexdigest()


HEALTH_COUNTS = ("lines", "records", "tool_calls", "edit_calls", "rejected")


def _health_of(entry: dict) -> dict:
    h = entry.get("health") if isinstance(entry.get("health"), dict) else {}
    out = new_health()
    for k in HEALTH_COUNTS:
        v = h.get(k)
        out[k] = v if isinstance(v, int) and not isinstance(v, bool) else 0
    out["versions"] = {v for v in h.get("versions", []) if isinstance(v, str) and version_text(v)}
    return out


def new_report() -> dict:
    """Reader health for one harness. Counts and version numbers only, never any log text."""
    return dict(new_health(), seen=0, read=0, sessions=0, edits=0, newest=None, kept_files=0, kept_sessions=0)


def _cached(files: list, reader, cache_path: str, base: str | None = None, report: dict | None = None) -> list:
    """Read harness files through a cache keyed on content. The cache stays in the data folder.

    Each entry holds the SHA-256 and size of exactly the bytes the reader parsed. It is reused
    when the file still has that size and either its stat (size, mtime, ctime, inode) is
    unchanged or its SHA-256 matches. Any other file is parsed again, so bytes that arrived
    after the reader stopped are never skipped.

    Kept history: an entry under base (every entry when base is None) whose file is no longer
    listed, or can no longer be read, is kept and marked gone, and its events still count. A
    gone file that comes back is read as it is now. Entries outside base belong to another
    harness folder: they stay in the cache and are not counted here.
    report: a dict from new_report(), filled with this listing's reader health.
    """
    rep = report if report is not None else new_report()
    try:
        with open(cache_path, encoding="utf-8") as f:
            cache = json.load(f)
        if not isinstance(cache, dict) or not isinstance(cache.get("files"), dict):
            cache = {}
    except (OSError, ValueError):
        cache = {}
    old = cache.get("files", {})
    # Two questions: whether an entry's events still count (its log is gone), and whether it may
    # stand in for a log that is still there. Only this version's entries may stand in.
    reuse = cache.get("v") == CACHE_VERSION
    if cache.get("v") not in EVENTS_VALID:
        old = {p: c for p, c in old.items() if isinstance(c, dict) and c.get("gone")}
    new = {}
    events = []
    live_sessions = set()
    for path in files:
        rep["seen"] += 1
        try:
            st = os.stat(path)
        except OSError:
            continue
        stamp = [st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_ino]
        c = (old.get(path) if reuse else None) or {}
        if not isinstance(c, dict):
            c = {}
        same_size = c.get("size") == st.st_size and isinstance(c.get("sha256"), str) and "health" in c
        if same_size and (c.get("stat") == stamp or _digest(path) == c["sha256"]):
            evs = [Event.from_dict(x) for x in c.get("events", [])]
            entry = dict(c, stat=stamp)
            entry.pop("gone", None)
        else:
            hc = new_health()
            try:
                with open(path, "rb") as f:
                    hs = HashingStream(f)
                    evs = reader(path, stream=hs, health=hc)
            except OSError:
                continue
            # The stat counts as proof only when it describes exactly the parsed bytes.
            entry = {"stat": stamp if hs.size == st.st_size else None, "sha256": hs.digest(), "size": hs.size,
                     "events": [e.to_dict() for e in evs],
                     "health": dict(hc, versions=sorted(hc["versions"]))}
        new[path] = entry
        events.extend(evs)
        rep["read"] += 1
        h = _health_of(entry)
        for k in HEALTH_COUNTS:
            rep[k] += h[k]
        rep["versions"] |= h["versions"]
        live_sessions |= {e.session for e in evs if e.session}
        rep["edits"] += sum(1 for e in evs if e.kind == "edit")
        for e in evs:
            if rep["newest"] is None or parse_ts(e.ts) > parse_ts(rep["newest"]):
                rep["newest"] = e.ts
    gone_sessions = set()
    for path, c in old.items():
        if path in new or not isinstance(c, dict):
            continue
        if base is not None and not path_within(path, base):
            new[path] = c  # another harness folder's entry: kept, not counted
            continue
        try:
            evs = [Event.from_dict(x) for x in c.get("events", [])]
        except (TypeError, AttributeError):
            continue
        new[path] = dict(c, gone=True, stat=None)
        events.extend(evs)
        rep["kept_files"] += 1
        gone_sessions |= {e.session for e in evs if e.session}
    rep["sessions"] += len(live_sessions)
    rep["kept_sessions"] += len(gone_sessions - live_sessions)
    try:
        os.makedirs(os.path.dirname(cache_path), exist_ok=True)
        _write(cache_path, json.dumps({"v": CACHE_VERSION, "files": new}, sort_keys=True))
    except OSError:
        pass
    return events


def gather(profile: Profile, home: str) -> Inputs:
    ident = Identity(profile.emails, profile.names, profile.bots)
    roots = sorted({r for p in profile.projects for r in p.roots})
    resolver = Resolver(profile.projects)
    g = read_git(roots, ident, in_roots=lambda p: resolver.resolve(p) is not None)
    events = list(g.events)
    cache = os.path.join(home, "cache")
    harnesses = {}
    health = {}

    def note(name, where, found, evs, rep):
        harnesses[name] = {"path": where, "found": found, "sessions": len({e.session for e in evs if e.session})}
        health[name] = rep
        return evs

    # Logs are read even when their folder is gone, so what earlier builds kept still counts. The
    # cache is shared: each read, merge and replace holds the data folder's lock.
    if profile.claude:
        rep = new_report()
        with data_lock(home):
            evs = _cached(claude.transcript_files(profile.claude_dir), claude.read_file,
                          os.path.join(cache, "claude.json"), profile.claude_dir, rep)
        events += note("claude", profile.claude_dir, os.path.isdir(profile.claude_dir), evs, rep)
    if profile.codex:
        rep = new_report()
        with data_lock(home):
            evs = _cached(codex.rollout_files(profile.codex_dir), codex.read_file,
                          os.path.join(cache, "codex.json"), profile.codex_dir, rep)
        events += note("codex", profile.codex_dir, os.path.isdir(profile.codex_dir), evs, rep)
    if profile.agy:
        # One database, not a file per session: what it no longer holds is gone (see METHOD.md).
        found = os.path.isfile(profile.agy_db)
        rep = new_report()
        hc = new_health()
        evs = agy.read_db(profile.agy_db, hc) if found else []
        rep.update({k: v for k, v in hc.items() if k in rep}, seen=int(found),
                   read=int(found and not hc.get("unreadable")), sessions=len({e.session for e in evs}),
                   newest=max((e.ts for e in evs), key=parse_ts, default=None))
        events += note("agy", profile.agy_db, found, evs, rep)
    return Inputs(events=sorted(set(events)), commits=g.commits, tags=g.tags, warnings=g.warnings,
                  root_ids=g.root_ids, setup=dict(g.setup, harnesses=harnesses, health=health))


HARNESS_NAMES = {"claude": ("Claude Code", "claude", "claude_dir"), "codex": ("Codex", "codex", "codex_dir"),
                 "agy": ("Antigravity", "agy", "agy_db")}


def _tilde(path: str) -> str:
    home = os.path.expanduser("~")
    if home and home != os.sep and (path == home or path.startswith(home.rstrip(os.sep) + os.sep)):
        return "~" + path[len(home):]
    return path


def _holds_repos(folder: str) -> int:
    """How many direct subfolders of a folder are git repos. Only names are read."""
    try:
        names = os.listdir(folder)
    except OSError:
        return 0
    return sum(1 for n in names if os.path.isdir(os.path.join(folder, n)) and _is_git_dir(os.path.join(folder, n)))


def setup_warnings(profile: Profile, inputs: Inputs) -> list:
    """Why a build may have found less than expected: missing roots, roots with no commits by the
    profile's identities, harnesses with no folder or no sessions. Local only, never on a sheet.
    Roots are named by project and number, never by path."""
    out = []
    setup = inputs.setup or {}
    roots_top = setup.get("roots", {})
    repos = setup.get("repos", {})
    if setup and not setup.get("git", True) and any(p.roots for p in profile.projects):
        out.append("git was not found on PATH, so no commits were read. Install git, or put it on PATH.")
    for p in profile.projects:
        told = set()
        for i, root in enumerate(p.roots, 1):
            which = "its root" if len(p.roots) == 1 else f"root {i} of {len(p.roots)}"
            if not os.path.exists(root):
                out.append(f"{p.name}: {which} does not exist. Set roots to a folder on this machine.")
                continue
            if not roots_top:
                continue
            top = roots_top.get(os.path.realpath(root))
            if top is None:
                n = _holds_repos(root)
                if n:
                    out.append(f"{p.name}: {which} is not a git repo, but {n} folder{'s' if n != 1 else ''} in it "
                               f"{'are' if n != 1 else 'is'}. Commits are read only from the repo a root is in, so "
                               "list each repo as a root.")
                continue
            info = repos.get(top)
            if not info or info["mine"] or not info["commits"] or top in told:
                continue
            told.add(top)
            seen = ", ".join(f"{n} <{e}> ({k})" for n, e, k in info["authors"])
            repo = "the repo" if len(p.roots) == 1 else f"the repo of root {i}"
            msg = (f"{p.name}: {info['commits']} commit{'s' if info['commits'] != 1 else ''} in {repo}, "
                   "none by the emails or names under [identity].")
            msg += f" Authors seen there: {seen}. Add yours to [identity]." if seen else " All are by bots."
            out.append(msg)
    for key, h in sorted((setup.get("harnesses") or {}).items()):
        label, flag, setting = HARNESS_NAMES[key]
        where = _tilde(h["path"])
        if not h["found"]:
            kept = ((setup.get("health") or {}).get(key) or {}).get("kept_sessions", 0)
            note = (f" The {kept} session{'s' if kept != 1 else ''} kept from earlier builds still count."
                    if kept else "")
            out.append(f"{label} is on, but {where} does not exist. Set {flag} = false under [harnesses], "
                       f"or set {setting} to where its logs are.{note}")
        elif not h["sessions"]:
            out.append(f"{label} is on, but no sessions were read from {where}.")
    return out


# A harness with at least this many tool calls and no edit of a kind its reader knows has
# probably changed its log format. Fewer calls can be a session that only read files.
HEALTH_MIN_CALLS = 20


def _num(n: int) -> str:
    return f"{n:,}"


def _version_key(v: str):
    return [(0, int(x), "") if x.isdigit() else (1, 0, x) for x in re.split(r"[.+-]", v)]


def health_lines(profile: Profile, inputs: Inputs) -> list:
    """One line per harness on what its reader found. Counts, dates and version numbers only.
    Local only: printed by build, never on a sheet or the card."""
    out = []
    for key, rep in sorted(((inputs.setup or {}).get("health") or {}).items(),
                           key=lambda kv: list(HARNESS_NAMES).index(kv[0])):
        label = HARNESS_NAMES[key][0]
        if key == "agy":
            bits = ["database read" if rep["read"] else ("database not readable" if rep["seen"] else "no database")]
        else:
            bits = [f"{_num(rep['read'])} of {_num(rep['seen'])} files read"]
        bits.append(f"{_num(rep['records'])} records recognised")
        if rep.get("rejected"):
            n = rep["rejected"]
            bits.append(f"{_num(n)} malformed record{'s' if n != 1 else ''} skipped")
        bits.append(f"{_num(rep['sessions'])} session{'s' if rep['sessions'] != 1 else ''}")
        bits.append("presence only" if key == "agy" else f"{_num(rep['edits'])} edits confirmed")
        if rep.get("newest"):
            bits.append("newest " + parse_ts(rep["newest"]).astimezone(profile.tz).date().isoformat())
        versions = sorted(rep.get("versions") or (), key=_version_key)
        if len(versions) == 1:
            bits.append(f"version {versions[0]}")
        elif versions:
            bits.append(f"versions {versions[0]} to {versions[-1]}")
        line = f"{label}: " + ", ".join(bits) + "."
        if rep.get("kept_sessions"):
            n = rep["kept_sessions"]
            line += f" Plus {_num(n)} session{'s' if n != 1 else ''} kept from logs that are gone."
        out.append(line)
    return out


def health_warnings(inputs: Inputs) -> list:
    """Signs that a harness changed its log format. Each says what to do next."""
    out = []
    step = ("Its log format may have changed. Update tinkerprint, and if that does not help, report the "
            "versions in the reader line above.")
    for key, rep in sorted(((inputs.setup or {}).get("health") or {}).items()):
        label = HARNESS_NAMES[key][0]
        if key != "agy" and rep["seen"] and not rep["read"]:
            out.append(f"{label}: none of its {_num(rep['seen'])} log files could be read. Check that your user "
                       "can read them.")
        elif (rep.get("lines") and not rep["records"]) or (key == "agy" and rep["seen"] and not rep["read"]):
            what = "its database" if key == "agy" else f"its {_num(rep['read'])} log files"
            out.append(f"{label}: {what} held no records tinkerprint recognised. {step}")
        elif key != "agy" and rep["tool_calls"] >= HEALTH_MIN_CALLS and not rep["edit_calls"]:
            out.append(f"{label}: {_num(rep['tool_calls'])} tool calls, but none of an edit kind tinkerprint knows, "
                       f"so no agent edits were counted. {step}")
    return out


def read_milestones(path: str | None) -> list:
    """One milestone per line: 'YYYY-MM-DD text'. Lines starting with # are comments."""
    if not path or not os.path.isfile(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            head, _, text = line.partition(" ")
            try:
                out.append((parse_day(head), text.strip()))
            except ValueError:
                continue
    return sorted(out)


def parse_season(s: str | None):
    if not s:
        return (None, None)
    if ":" not in s:
        raise ValueError("season must be FROM:TO, for example 2025-01-01:2025-06-30 (either end may be empty)")
    a, b = s.split(":", 1)
    frm = parse_day(a) if a.strip() else None
    to = parse_day(b) if b.strip() else None
    if frm and to and frm > to:
        raise ValueError("season starts after it ends")
    return (frm, to)


DESTINATIONS = ("", "cache", "history", "sheets", "last-build")


def check_data_home(home: str, profile: Profile) -> None:
    check_dirs(profile, [os.path.join(home, sub) if sub else home for sub in DESTINATIONS])


def check_dirs(profile: Profile, dirs) -> None:
    roots = [r for p in profile.projects for r in p.roots]
    for dest in dirs:
        why = inside_repo_or_root(dest, roots)
        if why:
            raise ValueError(f"data folder {dest} is refused: {why}. Use --data-dir or XDG_DATA_HOME to pick "
                             "a folder outside every repo")


def default_out(home: str, profile: Profile) -> str:
    return os.path.join(home, "sheets", profile.id)


def last_out(home: str, profile: Profile) -> str | None:
    try:
        with open(os.path.join(home, "last-build", profile.id + ".json"), encoding="utf-8") as f:
            out = json.load(f).get("out")
        return out if isinstance(out, str) else None
    except (OSError, ValueError, AttributeError):
        return None


def alias_of(folder: str, profile: Profile) -> str:
    """The profile's names for the projects in a folder. Diagnostics never print an assigned path."""
    real = canonical(folder)
    names = []
    for p in profile.projects:
        for r in p.roots:
            cr = canonical(r)
            if path_within(cr, real) or path_within(real, cr):
                names.append(p.name)
                break
    return ", ".join(sorted(set(names))) if names else "A repo outside the profile"


def cutoff(profile: Profile, as_of: date | None) -> str | None:
    """The instant an as-of date ends in the profile's time zone and rollover, as ISO text."""
    if as_of is None:
        return None
    end = datetime.combine(as_of + timedelta(days=1), time(profile.rollover_hour), profile.tz)
    return end.isoformat()


def compute(profile: Profile, season=(None, None), as_of: date | None = None, home: str | None = None,
            inputs: Inputs | None = None):
    """Score. Writes only the harness cache. sheet.json depends on the events and the profile alone.
    Returns (sheet, local)."""
    home = data_home(home)
    check_data_home(home, profile)
    mark_home(home)
    inputs = inputs if inputs is not None else gather(profile, home)
    warnings = list(inputs.warnings)
    priors = scan_priors(profile.projects, cutoff(profile, as_of), warnings)
    sheet, local = score_core(inputs, profile, priors, season, as_of, read_milestones(profile.milestones))
    local["warnings"] = ([f"{alias_of(top, profile)}: {msg}" for top, msg in warnings]
                         + setup_warnings(profile, inputs) + health_warnings(inputs))
    local["health"] = health_lines(profile, inputs)
    return sheet, local


def build(profile: Profile, out_dir: str, season=(None, None), as_of: date | None = None,
          home: str | None = None, built_at: str = "", inputs: Inputs | None = None,
          today: date | None = None, pack: dict | None = None) -> dict:
    """Score, compare with the newest earlier saved sheet, write the outputs, then save to history.

    Nothing reaches history unless every output was written.
    """
    home = data_home(home)
    check_data_home(home, profile)
    mark_home(home)
    adopt(home, profile)
    hist = History(home, profile.id, season)
    pointer = os.path.join(home, "last-build", profile.id + ".json")
    # The guard checks the folders that actually receive writes, after symlinks.
    check_dirs(profile, [hist.dir, os.path.dirname(pointer)])
    sheet, local = compute(profile, season, as_of, home, inputs)
    # A sheet saved without --as-of is dated so that it holds nothing after its date.
    stamp = as_of or max(today or date.today(), local.get("latest_day") or date.min)
    if sheet["card"].get("enabled"):
        # The card says the month it was built: the as-of month, else today's. Nothing finer.
        sheet["card"]["built"] = month_label(stamp.isoformat())
    prev_day, prev = hist.previous(stamp)
    scope = scope_digests(profile)
    changes = compare(sheet, prev, prev_day, scope)
    os.makedirs(out_dir, exist_ok=True)
    if os.path.abspath(out_dir) == os.path.abspath(default_out(home, profile)):
        mark_sheets(out_dir)  # so forget --all can tell this folder from an --out folder
    # The sheet holds project names, models and exact dates, so it stays private (0600) like the
    # pointer and history below. Only the card files, made for passing on, are readable by others.
    paths = {"json": os.path.join(out_dir, "sheet.json"), "changes": os.path.join(out_dir, "changes.json"),
             "html": os.path.join(out_dir, "sheet.html")}
    _write(paths["json"], pretty(sheet))
    _write(paths["changes"], pretty(changes))
    pack = pack or art.default_pack()
    _write(paths["html"], render_html(sheet, built_at, changes, pack))
    card_path = os.path.join(out_dir, "card.svg")
    card_png = os.path.join(out_dir, "card.png")
    png_path = os.path.join(out_dir, "portrait.png")
    gif_path = os.path.join(out_dir, "portrait.gif")
    if sheet["card"].get("enabled"):
        # Both card files draw visible()'s fields and nothing else.
        _write(card_path, render_card(sheet["card"], pack), share=True)
        paths["card"] = card_path
        _write(card_png, render_card_png(sheet["card"], pack), share=True)
        paths["card_png"] = card_png
        # The portrait plate at 6x, still and idling, from the card's allowlisted fields only.
        _write(png_path, portrait_png(sheet["card"], pack), share=True)
        paths["portrait"] = png_path
        _write(gif_path, portrait_gif(sheet["card"], pack), share=True)
        paths["portrait_gif"] = gif_path
    else:
        for path in (card_path, card_png, png_path, gif_path):
            if os.path.exists(path):
                os.remove(path)
    os.makedirs(os.path.dirname(pointer), exist_ok=True)
    _write(pointer, pretty({"out": os.path.abspath(out_dir)}))
    # History is published last: a build that failed anywhere earlier never becomes a comparison.
    # The saved copy also keeps the scope digests, so the next build can say when they changed.
    hist.save(stamp, dict(sheet, _scope=scope))
    return {"sheet": sheet, "changes": changes, "local": local, "paths": paths,
            "warnings": local.get("warnings", [])}
