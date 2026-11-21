"""Build pipeline: read sources, score, render, then save the sheet to history."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import date

from .events import Event, Inputs
from .profile import Profile
from .projects import Resolver, scan_priors
from .readers import agy, claude, codex
from .readers._common import HashingStream
from .readers.git import Identity, read_git
from .render_card import render_card
from .render_html import render_html
from .history import History
from .score import compare, score_core
from .datadir import _write, data_home, inside_repo_or_root, pretty
from .timeutil import parse_day

CACHE_VERSION = 3


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

    An entry is reused without rereading when size, mtime, ctime and inode all match. Any write
    or restore of a file changes its ctime, which no ordinary tool can set back. Otherwise the
    file's SHA-256 must match the stored one, or the file is read again.
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
        digest = c.get("sha256")
        if c.get("stat") == stamp and digest:
            evs = [Event.from_dict(x) for x in c.get("events", [])]
        else:
            now = _digest(path)
            if now is None:
                continue
            if now == digest:
                evs = [Event.from_dict(x) for x in c.get("events", [])]
            else:
                # Hash the very bytes the reader parses, so the stored digest always matches its events.
                try:
                    with open(path, "rb") as f:
                        hs = HashingStream(f)
                        evs = reader(path, stream=hs)
                        now = hs.digest()
                except OSError:
                    continue
            digest = now
        new[path] = {"stat": stamp, "sha256": digest, "events": [e.to_dict() for e in evs]}
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
    if profile.claude and os.path.isdir(profile.claude_dir):
        events += _cached(claude.transcript_files(profile.claude_dir), claude.read_file,
                          os.path.join(cache, "claude.json"))
    if profile.codex and os.path.isdir(profile.codex_dir):
        events += _cached(codex.rollout_files(profile.codex_dir), codex.read_file, os.path.join(cache, "codex.json"))
    if profile.agy:
        events += agy.read_db(profile.agy_db)
    return Inputs(events=sorted(set(events)), commits=g.commits, tags=g.tags, warnings=g.warnings,
                  root_ids=g.root_ids)


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
    roots = [r for p in profile.projects for r in p.roots]
    for sub in DESTINATIONS:
        dest = os.path.join(home, sub) if sub else home
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


def compute(profile: Profile, season=(None, None), as_of: date | None = None, home: str | None = None,
            inputs: Inputs | None = None):
    """Score. Writes only the harness cache. sheet.json depends on the events and the profile alone.
    Returns (sheet, local)."""
    home = data_home(home)
    check_data_home(home, profile)
    inputs = inputs if inputs is not None else gather(profile, home)
    priors = scan_priors(profile.projects)
    sheet, local = score_core(inputs, profile, priors, season, as_of, read_milestones(profile.milestones))
    local["warnings"] = list(inputs.warnings)
    return sheet, local


def build(profile: Profile, out_dir: str, season=(None, None), as_of: date | None = None,
          home: str | None = None, built_at: str = "", inputs: Inputs | None = None,
          today: date | None = None) -> dict:
    """Score, compare with the newest earlier saved sheet, write the outputs, then save to history.

    Nothing reaches history unless every output was written.
    """
    home = data_home(home)
    sheet, local = compute(profile, season, as_of, home, inputs)
    stamp = as_of or today or date.today()
    hist = History(home, profile.id, season)
    prev_day, prev = hist.previous(stamp)
    changes = compare(sheet, prev, prev_day)
    os.makedirs(out_dir, exist_ok=True)
    paths = {"json": os.path.join(out_dir, "sheet.json"), "changes": os.path.join(out_dir, "changes.json"),
             "html": os.path.join(out_dir, "sheet.html")}
    _write(paths["json"], pretty(sheet))
    _write(paths["changes"], pretty(changes))
    _write(paths["html"], render_html(sheet, built_at, changes))
    card_path = os.path.join(out_dir, "card.svg")
    if sheet["card"].get("enabled"):
        _write(card_path, render_card(sheet["card"]))
        paths["card"] = card_path
    elif os.path.exists(card_path):
        os.remove(card_path)
    hist.save(stamp, sheet)
    os.makedirs(os.path.join(home, "last-build"), exist_ok=True)
    _write(os.path.join(home, "last-build", profile.id + ".json"), pretty({"out": os.path.abspath(out_dir)}))
    return {"sheet": sheet, "changes": changes, "local": local, "paths": paths,
            "warnings": local.get("warnings", [])}
