"""Profile loading and validation. A profile is a TOML file the person writes."""
from __future__ import annotations

import difflib
import hashlib
import json
import math
import os
import posixpath
import re
import tomllib
from dataclasses import dataclass, field

from .art.keepsake import EXPRESSIONS, EYES, HAIRSTYLES, SKINS
from .sets import BUILDER_STATS, SETS, TINKERER_FROM_BUILDER
from .timeutil import load_tz

CARD_EXTRAS = ("dates", "projects")
CARD_HIDE = ("party", "level", "achievements")


class ProfileError(ValueError):
    pass


# Every key a profile may hold, per table. Anything else is a ProfileError that names the key.
KEYS = {
    "top": ("name", "set", "timezone", "rollover_hour", "work", "milestones", "identity", "harnesses", "card",
            "look", "project"),
    "identity": ("emails", "names", "bots"),
    "harnesses": ("claude", "codex", "agy", "claude_dir", "codex_dir", "agy_db"),
    "card": ("enabled", "allow", "name", "show", "hide"),
    "look": ("presentation", "skin", "hair", "eyes", "expression"),
    "project": ("name", "root", "roots", "stats", "part", "override"),
    "part": ("path", "stats"),
    "override": ("glob", "stats"),
}
_TABLE_LABEL = {"top": "the top level", "identity": "[identity]", "harnesses": "[harnesses]", "card": "[card]",
                "look": "[look]", "project": "[[project]]", "part": "[[project.part]]", "override": "[[project.override]]"}


def toml_string(s: str) -> str:
    """s as a TOML basic string. JSON escapes are TOML escapes, apart from DEL, which TOML wants
    escaped too. Backslashes in Windows paths come out doubled, so C:\\Users parses."""
    return json.dumps(s, ensure_ascii=False).replace("\x7f", "\\u007f")


def _suggest(key: str, allowed) -> str:
    hit = difflib.get_close_matches(key.lower(), list(allowed), n=1, cutoff=0.6)
    return f" Did you mean {hit[0]!r}?" if hit else ""


def _check_keys(table: dict, kind: str, where: str) -> None:
    allowed = KEYS[kind]
    for key in table:
        if key in allowed:
            continue
        hint = _suggest(key, allowed)
        if not hint:
            home = next((k for k, keys in KEYS.items() if k != kind and key in keys and k in _TABLE_LABEL), None)
            if home:
                hint = f" It belongs in {_TABLE_LABEL[home]}."
        raise ProfileError(f"{where}: unknown key {key!r}.{hint}")


def _table(raw, kind: str, where: str) -> dict:
    """An optional table: absent is empty, anything but a table is an error."""
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ProfileError(f"{where} must be a table, like {_TABLE_LABEL[kind]} on its own line")
    _check_keys(raw, kind, where)
    return raw


def _tables(raw, kind: str, where: str, allow_str: bool = False) -> list:
    """An optional array of tables, like [[project]]."""
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ProfileError(f"{where} must be written as {_TABLE_LABEL[kind]} tables")
    out = []
    for i, item in enumerate(raw):
        if allow_str and isinstance(item, str):
            out.append(item)
            continue
        if not isinstance(item, dict):
            raise ProfileError(f"{where} {i + 1} must be a {_TABLE_LABEL[kind]} table")
        out.append(item)
    return out


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
    card_allow: bool          # the card is on: [card] enabled, else allow, else on unless work = true
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
    source: str = ""          # the profile file's real path, when it came from a file
    card_name: str = ""       # a handle the card shows instead of the profile name
    card_hide: tuple = ()     # fields left off the card: any of CARD_HIDE
    look: dict = field(default_factory=dict)  # the [look] choices the person made. The rest come from the name.

    @property
    def card_label(self) -> str:
        """The name the card and its alt text use. The sheet keeps the profile name."""
        return self.card_name or self.name

    @property
    def tz(self):
        return load_tz(self.timezone)

    @property
    def card_enabled(self) -> bool:
        return self.card_allow


def _slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s or "profile"


def _path(p: str, base: str) -> str:
    """A profile path: user-expanded and joined to the profile's folder, not normalized, so '..'
    resolves after symlinks. NUL and control characters are refused."""
    if not isinstance(p, str) or not p or re.search(r"[\x00-\x1f\x7f]", p):
        raise ProfileError("paths must be non-empty text without control characters")
    p = os.path.expanduser(p)
    if not os.path.isabs(p):
        p = os.path.join(base, p)
    return p


def _weights(raw, set_name: str, where: str) -> dict:
    if not isinstance(raw, dict) or not raw:
        raise ProfileError(f"{where}: stats must be a table like {{ Logic = 1 }}")
    allowed = set(SETS[set_name])
    if set_name == "tinkerer":
        allowed |= set(BUILDER_STATS)
    out = {}
    for k, v in raw.items():
        if k not in allowed:
            raise ProfileError(f"{where}: unknown stat {k!r} for the {set_name} set.{_suggest_stat(k, allowed)}")
        if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 < v <= 1e9:
            raise ProfileError(f"{where}: weight for {k} must be a positive number up to 1e9")
        out[k] = float(v)
    return out


def _suggest_stat(key: str, allowed) -> str:
    by_lower = {a.lower(): a for a in allowed}
    hit = difflib.get_close_matches(str(key).lower(), list(by_lower), n=1, cutoff=0.6)
    return f" Did you mean {by_lower[hit[0]]!r}?" if hit else ""


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


def _choices(raw, allowed, where: str) -> tuple:
    """A list of words from a fixed set. An unknown word names the closest one."""
    out = _strs(raw, where)
    for s in out:
        if s not in allowed:
            raise ProfileError(f"{where}: {s!r} is not supported.{_suggest(s, allowed)} Use any of {', '.join(allowed)}")
    return out


def _str(raw, default: str, where: str) -> str:
    if raw is None:
        return default
    if not isinstance(raw, str):
        raise ProfileError(f"{where} must be text in quotes")
    return raw


def _one_of(raw, allowed, where: str):
    """One word from a fixed set, or None when unset. An unknown word names the closest one."""
    if raw is None:
        return None
    word = _str(raw, "", where)
    if word not in allowed:
        raise ProfileError(f"{where}: {word!r} is not supported.{_suggest(word, allowed)} Use any of {', '.join(allowed)}")
    return word


def _look(raw) -> dict:
    """[look]: presentation and skin are the person's to choose, never random. Hair, eyes and
    expression left out are picked from the card's name at build time."""
    table = _table(raw, "look", "look")
    out = {}
    presentation = _one_of(table.get("presentation"), tuple(HAIRSTYLES), "look.presentation")
    if presentation:
        out["presentation"] = presentation
    for key, allowed in (("skin", tuple(SKINS)), ("eyes", EYES), ("expression", EXPRESSIONS)):
        word = _one_of(table.get(key), allowed, f"look.{key}")
        if word:
            out[key] = word
    if "hair" in table:
        pool = HAIRSTYLES[presentation or "neutral"]
        hair = _str(table["hair"], "", "look.hair")
        if hair not in pool:
            home = next((p for p, cuts in HAIRSTYLES.items() if hair in cuts), None)
            why = f' It is a cut for presentation "{home}".' if home else _suggest(hair, pool)
            raise ProfileError(f"look.hair: {hair!r} is not a {presentation or 'neutral'} cut.{why} "
                               f"Use any of {', '.join(pool)}, or set look.presentation to match")
        out["hair"] = hair
    return out


def _tz_error(tz) -> ProfileError:
    try:
        import zoneinfo
        no_data = not zoneinfo.available_timezones()
    except Exception:  # an unusual zoneinfo install: give the usual advice
        no_data = False
    if no_data and isinstance(tz, str) and "/" in tz:
        return ProfileError(f"timezone {tz!r} needs time-zone data, and this Python has none. Install the tzdata "
                            "package, or use an offset in quarter hours like \"+05:30\"")
    return ProfileError(f"timezone {tz!r} is not usable. Use an IANA name like \"Europe/Berlin\", "
                        "or an offset in quarter hours like \"+05:30\"")


def parse_profile(data: dict, base_dir: str, default_id: str = "profile") -> Profile:
    _check_keys(data, "top", "profile")
    set_name = _str(data.get("set"), "builder", "set")
    if set_name not in SETS:
        raise ProfileError(f"set must be one of {', '.join(SETS)}")
    tz = _str(data.get("timezone"), "UTC", "timezone")
    try:
        load_tz(tz)
    except Exception as e:  # zoneinfo raises several types
        raise _tz_error(tz) from e
    rollover = data.get("rollover_hour", 4)
    if isinstance(rollover, bool) or not isinstance(rollover, int) or not 0 <= rollover <= 23:
        raise ProfileError("rollover_hour must be a whole hour from 0 to 23")

    ident = _table(data.get("identity"), "identity", "identity")
    emails = _strs(ident.get("emails"), "identity.emails")
    names = _strs(ident.get("names"), "identity.names")
    if not emails and not names:
        raise ProfileError("identity needs at least one email or name pattern")
    bots = _strs(ident.get("bots"), "identity.bots")

    harn = _table(data.get("harnesses"), "harnesses", "harnesses")
    look = _look(data.get("look"))
    card = _table(data.get("card"), "card", "card")
    show = _choices(card.get("show"), CARD_EXTRAS, "card.show")
    hide = _choices(card.get("hide"), CARD_HIDE, "card.hide")
    # enabled works on every profile. allow is its older name, kept for work profiles.
    enabled = _bool(card.get("enabled"), None, "card.enabled")
    allow = _bool(card.get("allow"), None, "card.allow")
    if enabled is not None and allow is not None and enabled != allow:
        raise ProfileError("card.enabled and card.allow disagree. Keep enabled and remove allow")
    work = _bool(data.get("work"), False, "work")
    card_on = enabled if enabled is not None else allow if allow is not None else not work
    card_name = _str(card.get("name"), "", "card.name").strip()
    if "name" in card and (not card_name or re.search(r"[\x00-\x1f\x7f]", card_name)):
        raise ProfileError("card.name must be a handle in quotes, not empty and without control characters")

    projects = []
    for i, rp in enumerate(_tables(data.get("project"), "project", "project")):
        where = f"project {i + 1}"
        _check_keys(rp, "project", where)
        roots = rp.get("roots") or ([rp["root"]] if "root" in rp else [])
        roots = [_path(r, base_dir) for r in _strs(roots, f"{where}.roots")]
        if not roots:
            raise ProfileError(f"{where}: needs root or roots")
        # The default is for a missing name only. A name that is given must be text.
        name = rp["name"] if "name" in rp else f"Project {i + 1}"
        if not isinstance(name, str) or not name:
            raise ProfileError(f"{where}: name must be text in quotes, not empty")
        where = f"project {name!r}"
        parts = []
        for j, raw in enumerate(_tables(rp.get("part"), "part", f"{where} part", allow_str=True)):
            if isinstance(raw, str):
                raw = {"path": raw}
            _check_keys(raw, "part", f"{where} part {j + 1}")
            p = raw.get("path", "")
            if not isinstance(p, str):
                raise ProfileError(f"{where} part {j + 1}: path must be text in quotes")
            # Part paths compare with '/' separators, as the resolver hands them back, on every platform.
            p = p.replace(os.sep, "/").strip("/")
            if not p:
                raise ProfileError(f"{where} part {j + 1}: needs a path")
            norm = posixpath.normpath(p)
            if norm == "." or norm == ".." or norm.startswith("../") or re.match(r"^[A-Za-z]:", norm):
                raise ProfileError(f"{where} part {j + 1}: path must be a folder inside the project's root, "
                                   f"like \"web\", not {p!r}")
            st = _weights(raw["stats"], set_name, f"{where} part {p}") if "stats" in raw else None
            parts.append(Part(path=norm, stats=st))
        overrides = []
        for j, raw in enumerate(_tables(rp.get("override"), "override", f"{where} override")):
            _check_keys(raw, "override", f"{where} override {j + 1}")
            g = raw.get("glob")
            if not isinstance(g, str) or not g:
                raise ProfileError(f"{where} override {j + 1}: needs a glob")
            overrides.append(Override(glob=g.strip("/"), stats=_weights(raw.get("stats"), set_name, f"{where} override {g}")))
        stats = _weights(rp["stats"], set_name, where) if "stats" in rp else None
        projects.append(Project(index=i, name=name, roots=roots, parts=parts, stats=stats, overrides=overrides))
    names_seen = [p.name for p in projects]
    if len(set(names_seen)) != len(names_seen):
        raise ProfileError("project names must be unique")

    milestones = _str(data.get("milestones"), "", "milestones")
    return Profile(
        id=_slug(default_id),  # storage key: from the profile file path, never from the file content
        name=_str(data.get("name"), "Unnamed", "name"),
        set=set_name,
        timezone=tz,
        rollover_hour=rollover,
        work=work,
        card_allow=card_on,
        card_show=tuple(sorted(set(show))),
        card_name=card_name,
        card_hide=tuple(sorted(set(hide))),
        look=look,
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


# A storage key, as profile_id makes it: the file's stem as a slug, then "-" and eight hex digits.
# A stem with no Latin letters or digits leaves the hex digits alone. Every key that names a path in
# the data folder, from a profile file or from profiles.json, is checked with is_key.
_KEY = re.compile(r"(?:[a-z0-9]+(?:-[a-z0-9]+)*-)?[0-9a-f]{8}")


def is_key(s) -> bool:
    """Whether s is a storage key profile_id could have made."""
    return isinstance(s, str) and bool(_KEY.fullmatch(s))


def profile_id(path: str, salt: int = 0) -> str:
    """A storage key for a profile file: its stem and a hash of its real path. This is the key a
    profile file gets when it is first built. keys.py then keeps it with the file when the file
    moves. salt picks another key when this one is taken. The file need not exist."""
    path = os.path.realpath(os.path.expanduser(path))
    stem = os.path.splitext(os.path.basename(path))[0]
    tag = hashlib.sha256((path + (f"\0{salt}" if salt else "")).encode("utf-8")).hexdigest()[:8]
    key = _slug(f"{stem}-{tag}")
    if not is_key(key):
        raise ValueError(f"not a storage key: {key!r}")
    return key


def read_toml(path: str) -> dict:
    """The parsed profile file. Every failure is a ProfileError with a plain message."""
    shown = path
    try:
        with open(path, "rb") as f:
            raw = f.read()
    except FileNotFoundError:
        raise ProfileError(f"no profile at {shown}. Run 'tinkerprint init' to write one, "
                           "or pass --profile PATH") from None
    except IsADirectoryError:
        raise ProfileError(f"{shown} is a folder. Pass the profile file itself with --profile PATH") from None
    except PermissionError:
        raise ProfileError(f"cannot read {shown}: permission denied") from None
    except OSError as e:
        raise ProfileError(f"cannot read {shown}: {e.strerror or e}") from None
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ProfileError(f"{shown} is not UTF-8 text") from None
    try:
        return tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        raise ProfileError(f"{os.path.basename(path)}: {e}") from None


def load_profile(path: str) -> Profile:
    real = os.path.realpath(os.path.expanduser(path))
    data = read_toml(real)
    prof = parse_profile(data, os.path.dirname(real), default_id=profile_id(real))
    prof.source = real
    return prof


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
