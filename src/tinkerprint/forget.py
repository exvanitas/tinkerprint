"""forget: delete what tinkerprint keeps in its data folder, for one profile or for all.

It works only in a data folder that a build has marked as its own, or in the default data folder,
and deletes only files it recognizes as its own: the harness cache, saved sheets, last-build
pointers, the profile list (profiles.json, or one profile's entry in it) and, with --all, the
sheets folders of builds made without --out. Files go one by one, each checked just before it
goes, and then the emptied folders. Nothing is deleted through a link: a folder or file that is a
symlink or junction is left alone. A folder holding anything else is left alone and named. Repos,
agent logs, profiles and --out folders are never touched.
"""
from __future__ import annotations

import json
import os
import re
import stat

from .datadir import MARKER, MARKER_HEAD, SHEETS_MARK, data_home
from .keys import REGISTRY, forget_key, read_registry
from .profile import is_key

# A temporary file of datadir._write for a file named NAME: ".NAME." + 8 random characters + ".tmp".
_TMP = re.compile(r"^\.(.+)\.[a-z0-9_]{8}\.tmp$")
CACHE = ("claude.json", "codex.json")
_SEASON = re.compile(r"^(start|\d{4}-\d{2}-\d{2})_(now|\d{4}-\d{2}-\d{2})$")
_DAY = re.compile(r"^\d{4}-\d{2}-\d{2}\.json$")
OUTPUTS = {"sheet.json", "changes.json", "sheet.html", "card.svg", "card.png", "portrait.png", "portrait.gif"}


class _Unknown(Exception):
    """Something tinkerprint did not write, or a link."""


def _linked(path: str) -> bool:
    """A symlink, or on Windows a junction or any other reparse point."""
    try:
        st = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(st.st_mode):
        return True
    return bool(getattr(st, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def _plain_file(path: str) -> bool:
    return not _linked(path) and os.path.isfile(path)


def _plain_dir(path: str) -> bool:
    return not _linked(path) and os.path.isdir(path)


def _names(path: str) -> list:
    if not _plain_dir(path):
        raise _Unknown(path)
    try:
        return sorted(os.listdir(path))
    except OSError:
        raise _Unknown(path) from None


def _own_name(name: str, ok) -> bool:
    """name is one ok() accepts, or the temporary file of one."""
    if ok(name):
        return True
    m = _TMP.match(name)
    return bool(m) and ok(m.group(1))


def _files(folder: str, ok) -> list:
    """Every file in folder, when each is a plain file with a name ok() accepts (or its temporary
    file). Raises _Unknown otherwise."""
    out = []
    for n in _names(folder):
        path = os.path.join(folder, n)
        if not _own_name(n, ok) or not _plain_file(path):
            raise _Unknown(path)
        out.append(path)
    return out


def _profile_history(path: str) -> tuple:
    """(files, folders) of history/KEY: season folders of dated sheets."""
    files, dirs = [], []
    for n in _names(path):
        if not _SEASON.match(n):
            raise _Unknown(os.path.join(path, n))
        files += _files(os.path.join(path, n), _DAY.match)
        dirs.append(os.path.join(path, n))
    return files, dirs + [path]


def _registry_file(path: str) -> bool:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return False
    return (isinstance(data, dict) and isinstance(data.get("profiles"), dict) and set(data) <= {"v", "profiles"}
            and all(is_key(k) for k in data["profiles"]))


def _pointer(name: str) -> bool:
    return name.endswith(".json") and is_key(name[:-5])


def _tree(path: str, kind: str) -> tuple:
    """(files, folders) that make up path, folders deepest first. Raises _Unknown when path holds
    anything tinkerprint does not write there."""
    if kind == "pointer":
        if not _plain_file(path):
            raise _Unknown(path)
        return [path], []
    if kind == "registry":
        if not _plain_file(path) or not _registry_file(path):
            raise _Unknown(path)
        return [path], []
    if kind == "cache":
        return _files(path, lambda n: n in CACHE), [path]
    if kind == "pointers":
        return _files(path, _pointer), [path]
    if kind == "profile-history":
        return _profile_history(path)
    if kind == "history":
        files, dirs = [], []
        for n in _names(path):
            if not is_key(n):
                raise _Unknown(os.path.join(path, n))
            f, d = _profile_history(os.path.join(path, n))
            files, dirs = files + f, dirs + d
        return files, dirs + [path]
    if kind == "sheets-folder":
        if not _plain_file(os.path.join(path, SHEETS_MARK)):
            raise _Unknown(path)
        return _files(path, lambda n: n in OUTPUTS or n == SHEETS_MARK), [path]
    raise ValueError(kind)


def owns(home: str) -> bool:
    """Whether forget may delete in home: a build marked it, or it is the default data folder."""
    path = os.path.join(home, MARKER)
    if _plain_file(path):
        try:
            with open(path, encoding="utf-8") as f:
                if f.readline().rstrip("\r\n") == MARKER_HEAD:
                    return True
        except (OSError, ValueError):
            pass
    return os.path.normcase(os.path.abspath(home)) == os.path.normcase(data_home())


def plan(home: str, profile_key: str | None):
    """(to delete, left alone). To delete: (path, what it is, files, folders). Left alone: (path,
    why). profile_key None means everything."""
    items = [(os.path.join(home, "cache"), "cache", "the harness cache, shared by all profiles. Rebuilt from "
                                                     "the logs, but sessions kept from deleted logs are lost")]
    if profile_key is None:
        items += [(os.path.join(home, "history"), "history", "saved sheets for every profile"),
                  (os.path.join(home, "last-build"), "pointers", "where each profile's last build went")]
        sheets = os.path.join(home, "sheets")
        try:
            items += [(os.path.join(sheets, n), "sheets-folder" if is_key(n) else "unknown",
                       "sheets built without --out") for n in _names(sheets)]
        except _Unknown:
            if os.path.lexists(sheets):
                items.append((sheets, "unknown", ""))
        items.append((os.path.join(home, REGISTRY), "registry", "which profile file each saved history belongs to"))
    else:
        items += [(os.path.join(home, "history", profile_key), "profile-history",
                   "this profile's saved sheets, for \"what changed\""),
                  (os.path.join(home, "last-build", profile_key + ".json"), "pointer",
                   "where this profile's last build went")]
    delete, keep = [], []
    for path, kind, what in items:
        if not os.path.lexists(path):
            continue
        try:
            if not _unlinked_below(home, path):
                raise _Unknown(path)
            if kind == "unknown":
                raise _Unknown(path)
            files, dirs = _tree(path, kind)
        except _Unknown:
            if not _unlinked_below(home, path):
                why = "link"
            elif kind == "unknown" or (kind == "sheets-folder" and not _plain_file(os.path.join(path, SHEETS_MARK))):
                why = "sheets"
            else:
                why = "files"
            keep.append((path, why))
            continue
        delete.append((path, what, files, dirs))
    # The profile keeps its entry while anything of its own is left, so its next build still finds it.
    if (profile_key is not None and not keep and profile_key in read_registry(home)
            and _plain_file(os.path.join(home, REGISTRY))):
        delete.append((os.path.join(home, REGISTRY) + "#" + profile_key, "this profile's entry in the profile list",
                       [], []))
    return delete, keep


def _entry(path: str):
    """(registry file, key) for an entry row, else None."""
    head, sep, key = path.rpartition("#")
    return (head, key) if sep and os.path.basename(head) == REGISTRY else None


def _unlinked_below(home: str, path: str) -> bool:
    """No folder between home and path, nor path itself, is a link."""
    rel = os.path.relpath(path, home)
    if rel.startswith(os.pardir) or os.path.isabs(rel):
        return False
    probe = home
    for part in rel.split(os.sep):
        probe = os.path.join(probe, part)
        if _linked(probe):
            return False
    return True


def remove(home: str, items) -> list:
    """Delete the planned files one by one, then their folders. Returns the folders that could
    not go: something appeared in them, or became a link, after forget looked."""
    left = []
    for path, _, files, dirs in items:
        entry = _entry(path)
        if entry:
            forget_key(os.path.dirname(entry[0]), entry[1])
            continue
        for f in files:
            if not os.path.lexists(f):
                continue
            if not (_unlinked_below(home, f) and os.path.isfile(f)):
                left.append(os.path.dirname(f))
                continue
            os.unlink(f)
        for d in dirs:
            if not os.path.lexists(d):
                continue
            try:
                if not _unlinked_below(home, d):
                    raise OSError
                os.rmdir(d)
            except OSError:
                left.append(d)
    out = []
    for d in left:  # a folder that kept something names it, not every folder above it
        if d not in out and not any(o != d and o.startswith(d.rstrip(os.sep) + os.sep) for o in left):
            out.append(d)
    return out


def _finish_all(home: str) -> None:
    """After --all: the marker and the temporary files at the top go when nothing else is left,
    then the folder itself."""
    try:
        names = os.listdir(home)
    except OSError:
        return
    ours = [n for n in names if _own_name(n, lambda x: x in (MARKER, REGISTRY))]
    if len(ours) != len(names):
        return
    for n in ours:
        path = os.path.join(home, n)
        if _plain_file(path):
            os.unlink(path)
    try:
        os.rmdir(home)
    except OSError:
        pass


def forget(home: str, profile_key: str | None, yes: bool) -> list:
    """The lines to print. Deletes only when yes is true."""
    if profile_key is not None and not is_key(profile_key):
        raise ValueError(f"not a storage key: {profile_key!r}")
    if not os.path.lexists(home):
        return [f"Nothing to forget in {home}."]
    if not owns(home):
        return [f"Left alone: {home} has no {MARKER}, so it is not a data folder tinkerprint made. "
                "Nothing was deleted."]
    delete, keep = plan(home, profile_key)
    lines = []
    if delete:
        head = "Deleted" if yes else "This deletes"
        lines.append(f"{head}, in {home}:")
        rows = []
        for path, what, files, dirs in delete:
            if _entry(path):
                rows.append((REGISTRY, what))
                continue
            n = len(files)
            suffix = os.sep if dirs else ""
            rows.append((os.path.relpath(path, home) + suffix, f"{what} ({n} file{'s' if n != 1 else ''})"))
        width = max(len(r) for r, _ in rows)
        lines += [f"  {r:<{width}}  {w}" for r, w in rows]
    else:
        lines.append(f"Nothing to forget in {home}.")
    for path, why in keep:
        if why == "link":
            lines.append(f"Left alone: {path} is a link, or inside one. forget never deletes through a link.")
        elif why == "sheets":
            lines.append(f"Left alone: {path}, not a folder of builds made without --out.")
        else:
            lines.append(f"Left alone: {path} holds files tinkerprint did not write.")
    if profile_key is not None:
        sheets = os.path.join(home, "sheets", profile_key)
        if os.path.lexists(sheets):
            lines.append(f"Kept: {sheets}, this profile's sheets. Delete them yourself, or use --all.")
    lines.append("Never touched: your repos, agent logs, profiles and --out folders.")
    if delete and not yes:
        lines.append("Run it again with --yes to delete them.")
    if delete and yes:
        for d in remove(home, delete):
            lines.append(f"Left alone: {d} gained files tinkerprint did not write while forget ran.")
        if profile_key is None:
            sheets = os.path.join(home, "sheets")
            try:
                if _plain_dir(sheets):
                    os.rmdir(sheets)
            except OSError:
                pass
            _finish_all(home)
    return lines
