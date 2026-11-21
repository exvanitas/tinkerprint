"""Profile loading and validation. A profile is a TOML file the person writes."""
from __future__ import annotations

import hashlib
import os
import re
import tomllib
from dataclasses import dataclass, field

from .sets import BUILDER_STATS, SETS, TINKERER_FROM_BUILDER
from .timeutil import load_tz

CARD_EXTRAS = ("dates", "projects")


class ProfileError(ValueError):
    pass


@dataclass
class Override:
    glob: str                 # relative to the project root
    stats: dict


@dataclass
class Part:
    path: str                 # relative to the project root
    stats: dict | None = None


@dataclass
class Project:
    index: int
    name: str                 # what outputs show. Roots never leave the cache.
    roots: list
    parts: list = field(default_factory=list)
    stats: dict | None = None  # whole-project override weights
    overrides: list = field(default_factory=list)


@dataclass
class Profile:
    id: str
    name: str
    set: str
    timezone: str
    rollover_hour: int
    work: bool
    card_allow: bool
    card_show: tuple
    emails: tuple
    names: tuple
    bots: tuple
    projects: list
    claude: bool
    codex: bool
    agy: bool
    claude_dir: str
    codex_dir: str
    agy_db: str
    milestones: str | None
    base_dir: str

    @property
    def tz(self):
        return load_tz(self.timezone)

    @property
    def card_enabled(self) -> bool:
        return self.card_allow if self.work else True


def _slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "profile"


def _path(p: str, base: str) -> str:
    p = os.path.expanduser(p)
    if not os.path.isabs(p):
        p = os.path.join(base, p)
    return os.path.normpath(p)


def _weights(raw, set_name: str, where: str) -> dict:
    if not isinstance(raw, dict) or not raw:
        raise ProfileError(f"{where}: stats must be a table like {{ Logic = 1 }}")
    allowed = set(SETS[set_name])
    if set_name == "tinkerer":
        allowed |= set(BUILDER_STATS)
    out = {}
    for k, v in raw.items():
        if k not in allowed:
            raise ProfileError(f"{where}: unknown stat {k!r} for the {set_name} set")
        if isinstance(v, bool) or not isinstance(v, (int, float)) or v <= 0:
            raise ProfileError(f"{where}: weight for {k} must be a positive number")
        out[k] = float(v)
    return out


def _bool(raw, default: bool, where: str) -> bool:
    """TOML booleans only. A string like "false" is an error, never a truthy value."""
    if raw is None:
        return default
    if not isinstance(raw, bool):
        raise ProfileError(f"{where} must be true or false, without quotes")
    return raw


def _strs(raw, where: str) -> tuple:
    if raw is None:
        return ()
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list) or not all(isinstance(x, str) for x in raw):
        raise ProfileError(f"{where} must be a list of strings")
    return tuple(raw)


def parse_profile(data: dict, base_dir: str, default_id: str = "profile") -> Profile:
    set_name = data.get("set", "builder")
    if set_name not in SETS:
        raise ProfileError(f"set must be one of {', '.join(SETS)}")
    tz = data.get("timezone", "UTC")
    try:
        load_tz(tz)
    except Exception as e:  # zoneinfo raises several types
        raise ProfileError(f"unknown timezone {tz!r}") from e
    rollover = data.get("rollover_hour", 4)
    if not isinstance(rollover, int) or not 0 <= rollover <= 23:
        raise ProfileError("rollover_hour must be a whole hour from 0 to 23")

    ident = data.get("identity", {})
    emails = _strs(ident.get("emails"), "identity.emails")
    names = _strs(ident.get("names"), "identity.names")
    if not emails and not names:
        raise ProfileError("identity needs at least one email or name pattern")
    bots = _strs(ident.get("bots"), "identity.bots")

    harn = data.get("harnesses", {})
    card = data.get("card", {})
    if not isinstance(harn, dict) or not isinstance(card, dict):
        raise ProfileError("[harnesses] and [card] must be tables")
    show = _strs(card.get("show"), "card.show")
    for s in show:
        if s not in CARD_EXTRAS:
            raise ProfileError(f"card.show: {s!r} is not supported. Use {', '.join(CARD_EXTRAS)}")

    projects = []
    raw_projects = data.get("project", [])
    if not isinstance(raw_projects, list):
        raise ProfileError("projects go in [[project]] tables")
    for i, rp in enumerate(raw_projects):
        where = f"project {i + 1}"
        roots = rp.get("roots") or ([rp["root"]] if "root" in rp else [])
        roots = [_path(r, base_dir) for r in _strs(roots, f"{where}.roots")]
        if not roots:
            raise ProfileError(f"{where}: needs root or roots")
        name = rp.get("name") or f"Project {i + 1}"
        if not isinstance(name, str):
            raise ProfileError(f"{where}: name must be a string")
        parts = []
        for j, raw in enumerate(rp.get("part", [])):
            if isinstance(raw, str):
                raw = {"path": raw}
            p = raw.get("path", "").strip("/")
            if not p:
                raise ProfileError(f"{where} part {j + 1}: needs a path")
            st = _weights(raw["stats"], set_name, f"{where} part {p}") if "stats" in raw else None
            parts.append(Part(path=os.path.normpath(p), stats=st))
        overrides = []
        for j, raw in enumerate(rp.get("override", [])):
            g = raw.get("glob")
            if not isinstance(g, str) or not g:
                raise ProfileError(f"{where} override {j + 1}: needs a glob")
            overrides.append(Override(glob=g.strip("/"), stats=_weights(raw.get("stats"), set_name, f"{where} override {g}")))
        stats = _weights(rp["stats"], set_name, where) if "stats" in rp else None
        projects.append(Project(index=i, name=name, roots=roots, parts=parts, stats=stats, overrides=overrides))
    names_seen = [p.name for p in projects]
    if len(set(names_seen)) != len(names_seen):
        raise ProfileError("project names must be unique")

    milestones = data.get("milestones")
    return Profile(
        id=_slug(str(data.get("id") or default_id)),
        name=str(data.get("name", "Unnamed")),
        set=set_name,
        timezone=tz,
        rollover_hour=rollover,
        work=_bool(data.get("work"), False, "work"),
        card_allow=_bool(card.get("allow"), False, "card.allow"),
        card_show=tuple(sorted(set(show))),
        emails=emails,
        names=names,
        bots=bots,
        projects=projects,
        claude=_bool(harn.get("claude"), True, "harnesses.claude"),
        codex=_bool(harn.get("codex"), True, "harnesses.codex"),
        agy=_bool(harn.get("agy"), False, "harnesses.agy"),
        claude_dir=_path(harn.get("claude_dir", "~/.claude/projects"), base_dir),
        codex_dir=_path(harn.get("codex_dir", "~/.codex/sessions"), base_dir),
        agy_db=_path(harn.get("agy_db", "~/.gemini/antigravity-cli/conversation_summaries.db"), base_dir),
        milestones=_path(milestones, base_dir) if milestones else None,
        base_dir=base_dir,
    )


def load_profile(path: str) -> Profile:
    path = os.path.abspath(os.path.expanduser(path))
    with open(path, "rb") as f:
        try:
            data = tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ProfileError(f"{os.path.basename(path)}: {e}") from e
    # Two profile files never share snapshots by accident: the default id carries a hash of the path.
    stem = os.path.splitext(os.path.basename(path))[0]
    tag = hashlib.sha256(path.encode("utf-8")).hexdigest()[:8]
    return parse_profile(data, os.path.dirname(path), default_id=f"{stem}-{tag}")


def map_weights(weights: dict, set_name: str) -> dict:
    """Map override weights into the profile's set. Tinkerer profiles may use builder names.

    Returns stat -> weight, where the key None stands for the project's main code stat.
    Docs in a tinkerer profile maps to the empty string: unclassified.
    """
    if set_name == "builder":
        return dict(weights)
    out: dict = {}
    for k, v in weights.items():
        key = k if k in SETS["tinkerer"] else TINKERER_FROM_BUILDER[k]
        out[key] = out.get(key, 0.0) + v
    return out
