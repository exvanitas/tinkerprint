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
        r = os.path.realpath(root)
        if real == r or real.startswith(r.rstrip("/") + "/"):
            return "it is inside a profile root"
    probe = real
    while True:
        if _is_git_dir(probe):
            return "it is inside a git repository"
        parent = os.path.dirname(probe)
        if parent == probe:
            return None
        probe = parent


def _write(path: str, text: str | bytes) -> None:
    """Write through a unique temporary file in the same folder, then rename into place."""
    folder = os.path.dirname(path) or "."
    fd, tmp = tempfile.mkstemp(prefix="." + os.path.basename(path) + ".", suffix=".tmp", dir=folder)
    try:
        with (os.fdopen(fd, "wb") if isinstance(text, bytes) else os.fdopen(fd, "w", encoding="utf-8")) as f:
            f.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
