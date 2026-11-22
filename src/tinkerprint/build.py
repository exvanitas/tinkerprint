"""Build pipeline: read sources, score, render, then save the sheet to history."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import date, datetime, time, timedelta

from . import art
from .events import Event, Inputs
from .profile import Profile
from .projects import Resolver, canonical, scan_priors
from .readers import agy, claude, codex
from .readers._common import HashingStream
from .readers.git import Identity, read_git
from .render_card import render_card
from .render_html import render_html
from .history import History
from .score import compare, score_core
from .datadir import _is_git_dir, _write, data_home, inside_repo_or_root, path_within, pretty
from .timeutil import parse_day

CACHE_VERSION = 4


def _digest(path: str) -> str | None:
    h = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(1 << 20), b""):
                h.update(block)
    except OSError:
        return None
    return h.hexdigest()


def _cached(files: list, reader, cache_path: str) -> list:
    """Read harness files through a cache keyed on content. The cache stays in the data folder.

    Each entry holds the SHA-256 and size of exactly the bytes the reader parsed. It is reused
    when the file still has that size and either its stat (size, mtime, ctime, inode) is
    unchanged or its SHA-256 matches. Any other file is parsed again, so bytes that arrived
    after the reader stopped are never skipped.
    """
    try:
        with open(cache_path, encoding="utf-8") as f:
            cache = json.load(f)
        if cache.get("v") != CACHE_VERSION:
            cache = {}
    except (OSError, ValueError):
        cache = {}
    old = cache.get("files", {})
    new = {}
    events = []
    for path in files:
        try:
            st = os.stat(path)
        except OSError:
            continue
        stamp = [st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_ino]
        c = old.get(path) or {}
        same_size = c.get("size") == st.st_size and isinstance(c.get("sha256"), str)
        if same_size and (c.get("stat") == stamp or _digest(path) == c["sha256"]):
            evs = [Event.from_dict(x) for x in c.get("events", [])]
            entry = dict(c, stat=stamp)
        else:
            try:
                with open(path, "rb") as f:
                    hs = HashingStream(f)
                    evs = reader(path, stream=hs)
            except OSError:
                continue
            # The stat counts as proof only when it describes exactly the parsed bytes.
            entry = {"stat": stamp if hs.size == st.st_size else None, "sha256": hs.digest(), "size": hs.size,
                     "events": [e.to_dict() for e in evs]}
        new[path] = entry
        events.extend(evs)
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

    def note(name, where, found, evs):
        harnesses[name] = {"path": where, "found": found, "sessions": len({e.session for e in evs if e.session})}
        return evs

    if profile.claude:
        found = os.path.isdir(profile.claude_dir)
        events += note("claude", profile.claude_dir, found, _cached(
            claude.transcript_files(profile.claude_dir), claude.read_file,
            os.path.join(cache, "claude.json")) if found else [])
    if profile.codex:
        found = os.path.isdir(profile.codex_dir)
        events += note("codex", profile.codex_dir, found, _cached(
            codex.rollout_files(profile.codex_dir), codex.read_file,
            os.path.join(cache, "codex.json")) if found else [])
    if profile.agy:
        found = os.path.isfile(profile.agy_db)
        events += note("agy", profile.agy_db, found, agy.read_db(profile.agy_db) if found else [])
    return Inputs(events=sorted(set(events)), commits=g.commits, tags=g.tags, warnings=g.warnings,
                  root_ids=g.root_ids, setup=dict(g.setup, harnesses=harnesses))


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
            out.append(f"{label} is on, but {where} does not exist. Set {flag} = false under [harnesses], "
                       f"or set {setting} to where its logs are.")
        elif not h["sessions"]:
            out.append(f"{label} is on, but no sessions were read from {where}.")
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
    inputs = inputs if inputs is not None else gather(profile, home)
    warnings = list(inputs.warnings)
    priors = scan_priors(profile.projects, cutoff(profile, as_of), warnings)
    sheet, local = score_core(inputs, profile, priors, season, as_of, read_milestones(profile.milestones))
    local["warnings"] = ([f"{alias_of(top, profile)}: {msg}" for top, msg in warnings]
                         + setup_warnings(profile, inputs))
    return sheet, local


def build(profile: Profile, out_dir: str, season=(None, None), as_of: date | None = None,
          home: str | None = None, built_at: str = "", inputs: Inputs | None = None,
          today: date | None = None, pack: dict | None = None) -> dict:
    """Score, compare with the newest earlier saved sheet, write the outputs, then save to history.

    Nothing reaches history unless every output was written.
    """
    home = data_home(home)
    hist = History(home, profile.id, season)
    pointer = os.path.join(home, "last-build", profile.id + ".json")
    # The guard checks the folders that actually receive writes, after symlinks.
    check_dirs(profile, [hist.dir, os.path.dirname(pointer)])
    sheet, local = compute(profile, season, as_of, home, inputs)
    # A sheet saved without --as-of is dated so that it holds nothing after its date.
    stamp = as_of or max(today or date.today(), local.get("latest_day") or date.min)
    prev_day, prev = hist.previous(stamp)
    changes = compare(sheet, prev, prev_day)
    os.makedirs(out_dir, exist_ok=True)
    # Everything in the output folder is for opening or sharing, so it gets the umask's usual mode.
    # The pointer and history below stay private.
    paths = {"json": os.path.join(out_dir, "sheet.json"), "changes": os.path.join(out_dir, "changes.json"),
             "html": os.path.join(out_dir, "sheet.html")}
    _write(paths["json"], pretty(sheet), share=True)
    _write(paths["changes"], pretty(changes), share=True)
    pack = pack or art.default_pack()
    _write(paths["html"], render_html(sheet, built_at, changes, pack), share=True)
    card_path = os.path.join(out_dir, "card.svg")
    png_path = os.path.join(out_dir, "portrait.png")
    if sheet["card"].get("enabled"):
        _write(card_path, render_card(sheet["card"], pack), share=True)
        paths["card"] = card_path
        # The portrait as a PNG, from the card's allowlisted fields only.
        _write(png_path, art.portrait(pack, art.card_look(sheet["card"])).png(8), share=True)
        paths["portrait"] = png_path
    else:
        for path in (card_path, png_path):
            if os.path.exists(path):
                os.remove(path)
    os.makedirs(os.path.dirname(pointer), exist_ok=True)
    _write(pointer, pretty({"out": os.path.abspath(out_dir)}))
    # History is published last: a build that failed anywhere earlier never becomes a comparison.
    hist.save(stamp, sheet)
    return {"sheet": sheet, "changes": changes, "local": local, "paths": paths,
            "warnings": local.get("warnings", [])}
