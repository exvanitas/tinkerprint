"""Data-folder helpers: location, the outside-every-repo guard, and atomic writes."""
from __future__ import annotations

import json
import os
import tempfile
import time
from contextlib import contextmanager


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


# One tinkerprint run at a time reads, merges and replaces the shared harness cache and the
# profile list, and forget waits for it. The lock is this file in the data folder: fcntl.flock on
# POSIX, msvcrt.locking on Windows. Either goes when the process ends, so a crash leaves no lock.
LOCK = "tinkerprint.lock"
LOCK_WAIT = 120.0  # seconds to wait for another run before giving up


class Busy(ValueError):
    """Another tinkerprint run held the data folder's lock for longer than LOCK_WAIT."""


_held: dict = {}  # lock path -> the open lock, while this process holds it


class _Lock:
    def __init__(self, fd: int):
        self.fd = fd
        self.drop = False  # remove the lock file on release: forget --all empties the folder


def _try_lock(fd: int) -> bool:
    try:
        if os.name == "nt":
            import msvcrt
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (BlockingIOError, PermissionError):
        return False
    except OSError as e:
        import errno
        if e.errno in (errno.EACCES, errno.EAGAIN, getattr(errno, "EDEADLOCK", errno.EDEADLK)):
            return False
        raise
    return True


def _unlock(fd: int) -> None:
    try:
        if os.name == "nt":
            import msvcrt
            os.lseek(fd, 0, os.SEEK_SET)
            msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(fd, fcntl.LOCK_UN)
    except OSError:
        pass


def _still_there(fd: int, path: str) -> bool:
    """The locked file is still the one at path, not one a forget --all removed meanwhile."""
    try:
        return os.path.samestat(os.fstat(fd), os.lstat(path))
    except (OSError, AttributeError):
        return os.name == "nt"


@contextmanager
def data_lock(home: str, wait: float | None = None):
    """Hold the data folder's lock for a read, merge and replace of shared state. Waits up to
    wait seconds (LOCK_WAIT by default), then raises Busy. Holding it again in the same process
    nests, so no caller can wait on itself."""
    path = os.path.join(os.path.abspath(home), LOCK)
    key = os.path.normcase(path)
    if key in _held:
        yield _held[key]
        return
    os.makedirs(home, exist_ok=True)
    deadline = time.monotonic() + (LOCK_WAIT if wait is None else wait)
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    while True:
        fd = os.open(path, flags, 0o600)
        if _try_lock(fd):
            if _still_there(fd, path):
                break
            _unlock(fd)
        os.close(fd)
        if time.monotonic() >= deadline:
            raise Busy(f"another tinkerprint run is using {home}. Wait for it to finish, then try again")
        time.sleep(0.05)
    lock = _held[key] = _Lock(fd)
    try:
        yield lock
    finally:
        del _held[key]
        if lock.drop and os.name != "nt":
            try:
                os.unlink(path)  # while still held, so a waiting run sees it go and starts afresh
            except OSError:
                pass
        _unlock(fd)
        os.close(fd)
        if lock.drop and os.name == "nt":
            try:
                os.unlink(path)  # Windows removes no open file: after closing, if no one else opened it
            except OSError:
                pass
