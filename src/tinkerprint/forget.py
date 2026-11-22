"""forget: say what tinkerprint keeps and where, and with --all --yes delete its data folder.

Without --all it deletes nothing. It shows the data folder and its size, and for a profile that
profile's history folder, last-build pointer and default sheets folder, so a person can delete
what they choose themselves.

forget --all --yes deletes the whole data folder, and only when it is not a link, carries
tinkerprint's marker, and holds at its top nothing but what tinkerprint keeps there. It takes the
data folder's lock first, so no build is writing, then checks, then deletes. shutil.rmtree never
follows a link inside. Repos, agent logs, profiles and --out folders are outside the data folder,
so they are never touched.
"""
from __future__ import annotations

import os
import shutil

from .datadir import LOCK, MARKER, data_lock, linked, marked, own_top
from .profile import is_key


def size(path: str) -> int:
    """Bytes under path, never following a link."""
    try:
        st = os.lstat(path)
    except OSError:
        return 0
    if linked(path) or not os.path.isdir(path):
        return st.st_size
    total = 0
    for top, dirs, files in os.walk(path, followlinks=False):
        # A linked folder is listed with the folders but never walked: count the link alone.
        paths = [os.path.join(top, n) for n in files] + [os.path.join(top, n) for n in dirs
                                                          if linked(os.path.join(top, n))]
        for p in paths:
            try:
                total += os.lstat(p).st_size
            except OSError:
                pass
    return total


def human(n: int) -> str:
    if n < 1024:
        return f"{n} byte{'s' if n != 1 else ''}"
    for unit in ("KB", "MB", "GB"):
        n /= 1024
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}"
    return f"{n:.1f} GB"


def _arg(path: str) -> str:
    """A path as one shell word, quoted when it needs it."""
    return f'"{path}"' if any(c.isspace() or c in "\"'$`&|;<>()*?[]#~!" for c in path) else path


def all_command(home: str, data_dir: str | None) -> str:
    return "tinkerprint forget --all --yes" + (f" --data-dir {_arg(home)}" if data_dir else "")


def _where(path: str) -> str:
    if not os.path.lexists(path):
        return f"{path} (none yet)"
    return f"{path} ({human(size(path))})"


def show(home: str, data_dir: str | None, key: str | None = None, moved_to: str | None = None,
         profile: str | None = None) -> list:
    """What tinkerprint keeps and where, for forget without --all. Deletes nothing.
    key: the profile's storage key, when a profile was named and still owns one."""
    if key is not None and not is_key(key):
        raise ValueError(f"not a storage key: {key!r}")
    if not os.path.lexists(home):
        return [f"tinkerprint keeps nothing here yet: {home} does not exist."]
    out = [f"tinkerprint keeps its data in {_where(home)}:",
           "  cache/         what the readers kept from agent logs, shared by every profile, and the only copy",
           "                 of sessions from logs that are gone",
           "  history/       each profile's saved sheets, for \"what changed\"",
           "  last-build/    where each profile's last build went",
           "  sheets/        builds made without --out",
           "  profiles.json  which profile file each saved history belongs to"]
    if profile is not None:
        out.append(f"Profile {profile}:")
        if key is None:
            out.append(f"  its saved sheets went with the profile file now at {moved_to}. Run forget with that "
                       "path to see them.")
        else:
            out += [f"  history      {_where(os.path.join(home, 'history', key))}",
                    f"  last build   {_where(os.path.join(home, 'last-build', key + '.json'))}",
                    f"  sheets       {_where(os.path.join(home, 'sheets', key))}"]
    out.append(f"To delete everything tinkerprint keeps: {all_command(home, data_dir)}")
    out.append("To remove one profile's data, delete the folders 'tinkerprint forget --profile PATH' shows. The "
               "cache is shared, so it goes only with everything.")
    out.append("Never touched: your repos, agent logs, profiles and --out folders.")
    return out


def _refusal(home: str) -> tuple:
    """(why forget --all leaves home alone, or None when it may delete it; the names at its top)."""
    if linked(home):
        return f"{home} is a link. forget deletes only the folder itself, so it leaves this alone.", []
    if not os.path.isdir(home):
        return f"{home} is not a folder.", []
    if not marked(home):
        return (f"{home} has no {MARKER}, so it is not a data folder tinkerprint marked. A build marks a data "
                "folder from tinkerprint 0.1."), []
    try:
        names = sorted(os.listdir(home))
    except OSError as e:
        return f"{home} cannot be listed ({e.strerror or e}).", []
    others = [n for n in names if not own_top(n)]
    if others:
        return (f"{home} also holds {', '.join(others)}, which tinkerprint did not write. Move "
                f"{'it' if len(others) == 1 else 'them'} out, then run forget again."), names
    return None, names


def forget_all(home: str, yes: bool) -> list:
    """The lines to print. Deletes the data folder only when yes is true and nothing refuses it."""
    if not os.path.lexists(home):
        return [f"Nothing to forget: {home} does not exist."]
    why, names = _refusal(home)  # before the lock, so a folder that is not ours never gains a lock file
    if why:
        return ["Nothing was deleted. " + why]
    if not yes:
        names = [n for n in names if n != LOCK]
        rows = [(n + (os.sep if os.path.isdir(os.path.join(home, n)) and not linked(os.path.join(home, n)) else ""),
                 human(size(os.path.join(home, n)))) for n in names]
        width = max([len(r) for r, _ in rows] or [0])
        return ([f"This deletes {home} ({human(size(home))}):"] + [f"  {r:<{width}}  {s}" for r, s in rows]
                + ["Deleting the cache loses the sessions kept from agent logs that are gone.",
                   "Never touched: your repos, agent logs, profiles and --out folders.",
                   "Run it again with --yes to delete it."])
    with data_lock(home) as lock:  # a build that is writing here finishes first
        why, names = _refusal(home)
        if why:
            return ["Nothing was deleted. " + why]
        total = size(home)
        for n in names:  # exactly what was checked
            path = os.path.join(home, n)
            if n == LOCK:
                continue
            if os.path.isdir(path) and not linked(path):
                shutil.rmtree(path)
            else:
                os.unlink(path)
        lock.drop = True
    try:
        os.rmdir(home)
    except OSError:
        # A run that was waiting for the lock may hold a new lock file for a moment: it removes it.
        left = sorted(n for n in os.listdir(home) if n != LOCK) if os.path.isdir(home) else []
        if left:
            return [f"Deleted what tinkerprint kept in {home} ({human(total)}). Left: {', '.join(left)}, which "
                    "appeared while forget ran."]
    return [f"Deleted {home} ({human(total)})."]
