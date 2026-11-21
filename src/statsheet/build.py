"""Build pipeline: read sources, score, snapshot, render."""
from __future__ import annotations

import json
import os
from datetime import date

from .events import Event, Inputs
from .profile import Profile
from .projects import scan_priors
from .readers import agy, claude, codex
from .readers.git import Identity, read_git
from .render_card import render_card
from .render_html import render_html
from .score import finish, score_core
from .snapshot import SnapshotStore, _write, core_key, data_home, pretty
from .timeutil import parse_day

CACHE_VERSION = 1


def _cached(files: list, reader, cache_path: str) -> list:
    """Read harness files through a cache keyed by path, size and mtime. The cache stays in the data folder."""
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
        c = old.get(path)
        if c and c.get("size") == st.st_size and c.get("mtime") == st.st_mtime_ns:
            evs = [Event.from_dict(x) for x in c.get("events", [])]
        else:
            evs = reader(path)
        new[path] = {"size": st.st_size, "mtime": st.st_mtime_ns, "events": [e.to_dict() for e in evs]}
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
    g = read_git(roots, ident)
    events = list(g.events)
    cache = os.path.join(home, "cache")
    if profile.claude and os.path.isdir(profile.claude_dir):
        events += _cached(claude.transcript_files(profile.claude_dir), claude.read_file,
                          os.path.join(cache, "claude.json"))
    if profile.codex and os.path.isdir(profile.codex_dir):
        events += _cached(codex.rollout_files(profile.codex_dir), codex.read_file, os.path.join(cache, "codex.json"))
    if profile.agy:
        events += agy.read_db(profile.agy_db)
    return Inputs(events=sorted(set(events)), commits=g.commits, tags=g.tags, warnings=g.warnings)


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


def compute(profile: Profile, season=(None, None), as_of: date | None = None, home: str | None = None,
            inputs: Inputs | None = None):
    """Score without writing anything. Returns (sheet, local, key, store)."""
    home = data_home(home)
    inputs = inputs if inputs is not None else gather(profile, home)
    priors = scan_priors(profile.projects)
    core, local = score_core(inputs, profile, priors, season, as_of, read_milestones(profile.milestones))
    store = SnapshotStore(home, profile.id, season)
    key = core_key(core)
    sheet = finish(core, store.previous(key), profile)
    return sheet, local, key, store


def build(profile: Profile, out_dir: str, season=(None, None), as_of: date | None = None,
          home: str | None = None, built_at: str = "", inputs: Inputs | None = None) -> dict:
    sheet, local, key, store = compute(profile, season, as_of, home, inputs)
    store.save(key, sheet)
    os.makedirs(out_dir, exist_ok=True)
    paths = {"json": os.path.join(out_dir, "sheet.json"), "html": os.path.join(out_dir, "sheet.html")}
    _write(paths["json"], pretty(sheet))
    _write(paths["html"], render_html(sheet, built_at))
    card_path = os.path.join(out_dir, "card.svg")
    if sheet["card"].get("enabled"):
        _write(card_path, render_card(sheet["card"]))
        paths["card"] = card_path
    elif os.path.exists(card_path):
        os.remove(card_path)
    return {"sheet": sheet, "local": local, "paths": paths}
