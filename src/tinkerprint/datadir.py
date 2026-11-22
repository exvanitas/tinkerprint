"""Data-folder helpers: location, the outside-every-repo guard, and atomic writes."""
from __future__ import annotations

import json
import os
import tempfile


def data_home(override: str | None = None) -> str:
    if override:
        return os.path.abspath(os.path.expanduser(override))
    base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "tinkerprint")


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def pretty(obj) -> str:
    return json.dumps(obj, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def season_key(season) -> str:
    frm, to = season
    return f"{frm.isoformat() if frm else 'start'}_{to.isoformat() if to else 'now'}"


def path_within(path: str, root: str, pathmod=os.path) -> bool:
    """path is root or inside it, by the platform's path rules: either separator on Windows,
    case folded where the platform folds it. Paths on different drives are never within."""
    pm = pathmod
    a, b = pm.normcase(pm.normpath(path)), pm.normcase(pm.normpath(root))
    try:
        return pm.commonpath([a, b]) == b
    except ValueError:
        return False


def _is_git_dir(d: str) -> bool:
    """A worktree (.git inside) or a bare repository (HEAD, objects and refs inside)."""
    if os.path.exists(os.path.join(d, ".git")):
        return True
    return (os.path.isfile(os.path.join(d, "HEAD")) and os.path.isdir(os.path.join(d, "objects"))
            and os.path.isdir(os.path.join(d, "refs")))


def inside_repo_or_root(path: str, roots=()) -> str | None:
    """Why a data destination may not live at path, or None when it may.

    The cache and history hold raw paths and session metadata, so every destination, after
    resolving symlinks, stays outside every git repository and every profile root.
    """
    real = os.path.realpath(path)
    for root in roots:
        if path_within(real, os.path.realpath(root)):
            return "it is inside a profile root"
    probe = real
    while True:
        if _is_git_dir(probe):
            return "it is inside a git repository"
        parent = os.path.dirname(probe)
        if parent == probe:
            return None
        probe = parent


# Every build writes this file into its data folder. forget deletes only in a folder that has it,
# or in the default data folder.
MARKER = "tinkerprint-data.txt"
MARKER_HEAD = "tinkerprint data folder"
MARKER_TEXT = (MARKER_HEAD + "\n\nThis folder holds what tinkerprint keeps: its cache, saved sheets and profile "
               "list.\n'tinkerprint forget' lists and deletes them.\n")
# Every build without --out writes this file into its sheets folder. forget --all deletes only
# sheets folders that have it, so an --out folder is never touched, even one inside sheets/.
SHEETS_MARK = ".tinkerprint-sheets"
SHEETS_TEXT = "Built by tinkerprint without --out.\n"


def _mark(path: str, text: str) -> None:
    try:
        with open(path, encoding="utf-8") as f:
            if f.read() == text:
                return
    except (OSError, ValueError):
        pass
    _write(path, text)


def mark_home(home: str) -> None:
    """Say that tinkerprint keeps its data in home."""
    os.makedirs(home, exist_ok=True)
    _mark(os.path.join(home, MARKER), MARKER_TEXT)


def mark_sheets(folder: str) -> None:
    """Say that folder is a sheets folder built without --out."""
    _mark(os.path.join(folder, SHEETS_MARK), SHEETS_TEXT)


def _umask() -> int:
    mask = os.umask(0o077)
    os.umask(mask)
    return mask


def _write(path: str, text: str | bytes, share: bool = False) -> None:
    """Write through a unique temporary file in the same folder, then rename into place.

    The temporary file is private (0600). Private data (cache, history, pointers) stays that way.
    share=True is for outputs people open or pass on: they get the usual mode for a new file under
    the user's umask, 0644 under the common 022.
    """
    folder = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(prefix="." + os.path.basename(path) + ".", suffix=".tmp", dir=folder)
    try:
        with (os.fdopen(fd, "wb") if isinstance(text, bytes) else os.fdopen(fd, "w", encoding="utf-8")) as f:
            f.write(text)
        if share:
            os.chmod(tmp, 0o666 & ~_umask())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
