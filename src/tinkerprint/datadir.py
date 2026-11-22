"""Data-folder helpers: location, the outside-every-repo guard, and atomic writes."""
from __future__ import annotations

import json
import os
import re
import stat
import sys
import tempfile
import threading
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


# tinkerprint writes this file into a data folder it creates, or adopts while empty, or finds at
# the default location from 0.1. forget --all deletes only a folder that has it, or the default one.
MARKER = "tinkerprint-data.txt"
MARKER_HEAD = "tinkerprint data folder"
MARKER_TEXT = (MARKER_HEAD + "\n\nThis folder holds what tinkerprint keeps: its cache, saved sheets and profile "
               "list.\n'tinkerprint forget' shows what is here.\n")
REGISTRY = "profiles.json"
LOCK = "tinkerprint.lock"
# What tinkerprint keeps at the top of its data folder. Anything else there is someone else's.
OWN_TOP = ("cache", "history", "last-build", "sheets", REGISTRY, MARKER, LOCK)
# A temporary file of _write for a file named NAME: ".NAME." + 8 random characters + ".tmp".
_TMP = re.compile(r"\.(.+)\.[a-z0-9_]{8}\.tmp")


def own_top(name: str) -> bool:
    """name is one tinkerprint keeps at the top of its data folder, or the temporary file of one."""
    if name in OWN_TOP:
        return True
    m = _TMP.fullmatch(name)
    return bool(m) and m.group(1) in (REGISTRY, MARKER)


def linked(path: str) -> bool:
    """A symlink, or on Windows a junction or any other reparse point."""
    try:
        st = os.lstat(path)
    except OSError:
        return False
    if stat.S_ISLNK(st.st_mode):
        return True
    return bool(getattr(st, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))


def marked(home: str) -> bool:
    """home carries tinkerprint's marker: a plain file whose first line is MARKER_HEAD."""
    path = os.path.join(home, MARKER)
    if linked(path) or not os.path.isfile(path):
        return False
    try:
        with open(path, encoding="utf-8") as f:
            return f.readline().rstrip("\r\n") == MARKER_HEAD
    except (OSError, ValueError):
        return False


def is_default_home(home: str) -> bool:
    return os.path.normcase(os.path.abspath(home)) == os.path.normcase(data_home())


def adopt_hint() -> str:
    return (f"If it is your tinkerprint 0.1 data folder, adopt it: create {MARKER} in it with the first line "
            f"'{MARKER_HEAD}'")


def claim_home(home: str) -> None:
    """Make the data folder, or adopt it, and mark it as tinkerprint's.

    A new folder, or an empty one, is marked. So is the default location, which tinkerprint 0.1
    used without a marker. Any other folder that is not empty and has no marker is refused, so a
    build never moves into someone else's folder. A 0.1 data folder chosen with --data-dir is
    adopted once its owner writes the marker.
    """
    try:
        names = os.listdir(home)
    except FileNotFoundError:
        os.makedirs(home, exist_ok=True)
        names = []
    if marked(home):
        return
    if names and not is_default_home(home):
        raise ValueError(f"{home} is not empty and is not a tinkerprint data folder. For --data-dir, choose a new "
                         f"or empty folder, or leave it out. {adopt_hint()}")
    _write(os.path.join(home, MARKER), MARKER_TEXT)


def _umask() -> int:
    mask = os.umask(0o077)
    os.umask(mask)
    return mask


def _write(path: str, text: str | bytes, share: bool = False) -> None:
    """Write through a unique temporary file in the same folder, then rename into place.

    The temporary file is private (0600). Private data (cache, history, pointers, the sheet) stays
    that way. share=True is for the card files people pass on: 0644 less what the umask takes away,
    so never writable by anyone else. Text is written as UTF-8 bytes exactly as given, with '\n'
    newlines on every platform, so what audit redraws matches it byte for byte.
    """
    folder = os.path.dirname(path) or "."
    data = text if isinstance(text, bytes) else text.encode("utf-8")
    fd, tmp = tempfile.mkstemp(prefix="." + os.path.basename(path) + ".", suffix=".tmp", dir=folder)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(data)
        if share:
            os.chmod(tmp, 0o644 & ~_umask())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


# One tinkerprint run at a time reads, merges and replaces the shared harness cache and the
# profile list, and publishes into the data folder, and forget --all waits for it. The lock is
# LOCK in the data folder: fcntl.flock on POSIX, msvcrt.locking on Windows. Either goes when the
# process ends, so a crash leaves no lock, and a run waits for another as long as it takes.
NOTICE_AFTER = 5.0  # seconds of waiting before saying so


class _Lock:
    def __init__(self, fd: int | None):
        self.fd = fd  # None when the file system cannot lock
        self.drop = False  # remove the lock file on release: forget --all empties the folder


class Gone(ValueError):
    """The data folder was deleted, by forget --all, while this run waited for it."""


_held: dict = {}  # lock path -> the open lock, while a thread of this process holds it
_mutexes: dict = {}  # lock path -> RLock: other threads of this process wait on it, its owner nests
_guard = threading.Lock()
_warned = []


def _mutex(key: str):
    with _guard:
        return _mutexes.setdefault(key, threading.RLock())


class _NoLocking(OSError):
    pass


def _try_lock(fd: int) -> bool:
    """True when locked, False when another run holds it. Raises _NoLocking when the file system
    cannot lock at all, and OSError for anything else."""
    import errno
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
        if e.errno in (errno.EACCES, errno.EAGAIN, getattr(errno, "EDEADLOCK", errno.EDEADLK)):
            return False
        if e.errno in (errno.ENOLCK, errno.EINVAL, errno.ENOSYS, getattr(errno, "ENOTSUP", -1),
                       getattr(errno, "EOPNOTSUPP", -1)):
            raise _NoLocking(e.errno, e.strerror) from None
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


def _gone(home: str) -> Gone:
    return Gone(f"the data folder {home} was deleted while this run waited for it. Nothing more was written. "
                "Run it again")


def _acquire(home: str, path: str) -> int | None:
    """Open and lock the lock file, waiting as long as another run holds it. None when the file
    system cannot lock: a warning, once, and the run goes on."""
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    notice = time.monotonic() + NOTICE_AFTER
    while True:
        try:
            fd = os.open(path, flags, 0o600)
        except FileNotFoundError:
            if not os.path.isdir(home):
                raise _gone(home) from None
            raise
        try:
            if _try_lock(fd):
                if _still_there(fd, path):
                    return fd
                _unlock(fd)
        except _NoLocking:
            os.close(fd)
            if not _warned:
                _warned.append(path)
                print(f"tinkerprint: warning: the file system of {home} cannot lock files, so this run goes on "
                      "without its lock. Run one tinkerprint at a time there.", file=sys.stderr)
            return None
        except BaseException:
            os.close(fd)
            raise
        os.close(fd)
        if notice is not None and time.monotonic() >= notice:
            print("tinkerprint: waiting for another tinkerprint run...", file=sys.stderr)
            notice = None
        time.sleep(0.05)


@contextmanager
def data_lock(home: str, claimed: bool = False):
    """Hold the data folder's lock for a read, merge and replace of shared state, waiting for any
    other run. A thread that holds it already nests, so no caller waits on itself. Other threads
    of this process wait for it like other processes do.

    claimed: the folder must still carry its marker once locked, else Gone. A build passes it, so
    a run that waited while forget --all deleted the folder writes nothing more into it."""
    home = os.path.abspath(home)
    path = os.path.join(home, LOCK)
    key = os.path.normcase(path)
    with _mutex(key):
        if key in _held:  # only the thread inside the mutex can find its own lock here
            yield _held[key]
            return
        fd = _acquire(home, path)
        lock = _held[key] = _Lock(fd)
        gone = False
        try:
            if claimed and not marked(home):
                # The lock file this run just made is all that is left: it goes, and the folder with it.
                gone = lock.drop = True
                raise _gone(home)
            yield lock
        finally:
            del _held[key]
            if fd is not None:
                if lock.drop and os.name != "nt":
                    try:
                        os.unlink(path)  # while still held, so a waiting run sees it go
                    except OSError:
                        pass
                _unlock(fd)
                os.close(fd)
            if lock.drop and (os.name == "nt" or fd is None):
                try:
                    os.unlink(path)  # Windows removes no open file: after closing, if no one else opened it
                except OSError:
                    pass
            if gone:
                try:
                    os.rmdir(home)  # only when empty
                except OSError:
                    pass
