"""git reader: commits in the repos a profile lists, matched to the person by identity patterns.

Keeps hash, author identity match, author time, changed paths with status and added lines,
and Co-Authored-By matches. Never reads commit subjects or bodies (the trailer format
returns trailer values only).
"""
from __future__ import annotations

import fnmatch
import os
import re
import subprocess

from ..events import Commit, Event, Inputs, Tag
from ..timeutil import iso, parse_ts

DEFAULT_BOTS = ("dependabot*", "renovate*", "github-actions*", "*[[]bot]*")

_FMT = "%x1e%H%x1f%P%x1f%an%x1f%ae%x1f%aI%x1f%(trailers:key=Co-authored-by,valueonly,separator=%x1d)"
_COAUTHOR = re.compile(r"^\s*(.*?)\s*<([^>]*)>\s*$")


def _env() -> dict:
    env = dict(os.environ)
    # Local only: no prompts, no lazy fetch of missing objects in partial clones.
    env.update({"LC_ALL": "C", "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0", "GIT_PAGER": "cat",
                "GIT_NO_LAZY_FETCH": "1"})
    return env


# Every transport is off, so no git call made here can reach a remote.
_NO_NET = ["-c", "protocol.allow=never"]


def _git(args, cwd) -> str | None:
    try:
        r = subprocess.run(["git", *_NO_NET, "-C", cwd, *args], capture_output=True, env=_env(), check=False)
    except OSError:
        return None
    if r.returncode != 0:
        return None
    return r.stdout.decode("utf-8", "replace")


def _match(patterns, value: str) -> bool:
    v = value.lower()
    return any(fnmatch.fnmatchcase(v, p.lower()) for p in patterns)


class Identity:
    def __init__(self, emails, names, bots=()):
        self.emails = tuple(emails)
        self.names = tuple(names)
        self.bots = tuple(DEFAULT_BOTS) + tuple(bots)

    def is_me(self, name: str, email: str) -> bool:
        return (bool(email) and _match(self.emails, email)) or (bool(name) and _match(self.names, name))

    def is_bot(self, name: str, email: str) -> bool:
        return _match(self.bots, name) or _match(self.bots, email)

    def coauthor_is_me(self, trailer_values: str) -> bool:
        for v in trailer_values.split("\x1d"):
            m = _COAUTHOR.match(v)
            if m and self.is_me(m.group(1), m.group(2)):
                return True
        return False


def _unquote(p: str) -> str:
    if len(p) >= 2 and p[0] == '"' and p[-1] == '"':
        p = p[1:-1].encode("latin-1", "backslashreplace").decode("unicode_escape").encode("latin-1", "replace").decode("utf-8", "replace")
    return p


def toplevel(root: str) -> str | None:
    if not os.path.isdir(root):
        return None
    out = _git(["rev-parse", "--show-toplevel"], root)
    return os.path.normpath(out.strip()) if out else None


def _log(top: str, numstat: bool) -> str | None:
    # Merges count the files whose result differs from every parent (dense combined diff):
    # conflict resolutions and hand edits made during the merge. A clean merge counts nothing.
    args = ["-c", "core.quotePath=false", "log", "--all", "--no-renames", "--raw", "--diff-merges=dense-combined",
            "--no-abbrev", "--format=" + _FMT]
    if numstat:
        args.insert(5, "--numstat")
    return _git(args, top)


def read_repo(top: str, ident: Identity, warnings: list | None = None):
    """Parse one repo into commit dicts. Rows hold no text but paths.

    When line counts need objects the clone does not have (a partial clone), it reads the
    history without them and adds a warning instead of fetching anything.
    """
    out = _log(top, numstat=True)
    if out is None:
        out = _log(top, numstat=False)
        if warnings is not None:
            warnings.append(f"{top}: incomplete local history. Line counts skipped." if out is not None
                            else f"{top}: could not read git history.")
    commits = []
    if not out:
        return commits
    for chunk in out.split("\x1e")[1:]:
        lines = chunk.split("\n")
        head = lines[0].split("\x1f")
        if len(head) < 6:
            continue
        h, parents, an, ae, at, trailers = head[:6]
        parents = parents.split()
        status = {}
        added = {}
        for line in lines[1:]:
            if not line:
                continue
            if line.startswith(":"):
                meta, _, path = line.partition("\t")
                path = path.split("\t")[-1]
                st = meta.split()[-1][:1] if meta.split() else "M"
                status[_unquote(path)] = st
            else:
                bits = line.split("\t", 2)
                if len(bits) == 3:
                    a = int(bits[0]) if bits[0].isdigit() else 0
                    added[_unquote(bits[2])] = a
        if len(parents) > 1:
            # A merge's numstat is against its first parent. Keep only the combined-diff files.
            files = sorted((p, status[p], 0) for p in status)
        else:
            files = sorted((p, status.get(p, "M"), added.get(p, 0)) for p in set(status) | set(added))
        bot = ident.is_bot(an, ae)
        mine = (not bot) and (ident.is_me(an, ae) or ident.coauthor_is_me(trailers))
        commits.append({"hash": h, "parents": parents, "ts": at, "mine": mine, "bot": bot, "files": files})
    return commits


def read_tags(top: str, ident: Identity):
    fmt = "%(refname:strip=2)%1f%(objecttype)%1f%(taggername)%1f%(taggeremail:trim)%1f%(taggerdate:iso-strict)%1f%(*objectname)%1f%(objectname)"
    out = _git(["for-each-ref", "refs/tags", "--format=" + fmt], top)
    rows = []
    for line in (out or "").splitlines():
        bits = line.split("\x1f")
        if len(bits) != 7:
            continue
        name, otype, tn, te, td, deref, obj = bits
        target = deref if otype == "tag" else obj
        rows.append({"name": name, "annotated": otype == "tag", "tagger_me": otype == "tag" and ident.is_me(tn, te),
                     "ts": td, "target": target})
    return rows


def read_git(roots, ident: Identity, in_roots=None) -> Inputs:
    """Read every repo that holds a profile root. Commits dedupe by hash across clones and refs.

    in_roots(path) tells whether a path belongs to the profile. Each file of a commit seen in
    several clones takes the first clone where it lands inside a root.
    roots ids: a root inside a repo is named by the repo's first commit and the root's place in it,
    so clones of one repo share file keys and unrelated roots never do.
    """
    in_roots = in_roots or (lambda p: True)
    top_of = {r: toplevel(r) for r in roots}
    tops = sorted({t for t in top_of.values() if t})
    res = Inputs()
    per_top = {}
    repo_ids = {}
    for top in tops:
        commits = read_repo(top, ident, res.warnings)
        per_top[top] = commits
        roots_of = sorted(c["hash"] for c in commits if not c["parents"])
        repo_ids[top] = roots_of[0] if roots_of else top
    for r, top in top_of.items():
        if top:
            rel = os.path.relpath(os.path.realpath(r), os.path.realpath(top))
            res.root_ids[r] = f"git:{repo_ids[top]}:{'' if rel == '.' else rel}"

    seen = {}
    for top in tops:
        for c in per_top[top]:
            seen.setdefault(c["hash"], []).append((top, c))
    for h, copies in seen.items():
        top, c = copies[0]
        dt = parse_ts(c["ts"])
        if dt is None:
            continue
        ts = iso(dt)
        res.commits.append(Commit(ts=ts, hash=h, repo=repo_ids[top], top=top, mine=c["mine"],
                                  bot=c["bot"], root=not c["parents"], files=len(c["files"])))
        if not c["mine"]:
            continue
        for path, st, add in c["files"]:
            where = next((t for t, _ in copies if in_roots(os.path.join(t, path))), top)
            res.events.append(Event(ts=ts, source="git", kind="commit", path=os.path.join(where, path),
                                    actor="human", commit=h, status=st, added=add))
    for top in tops:
        by_hash = {c["hash"]: c for c in per_top[top]}
        for t in read_tags(top, ident):
            target = by_hash.get(t["target"])
            mine = t["tagger_me"] or (not t["annotated"] and bool(target and target["mine"]))
            dt = parse_ts(t["ts"]) or (parse_ts(target["ts"]) if target else None)
            if dt is None:
                continue
            res.tags.append(Tag(ts=iso(dt), name=t["name"], repo=repo_ids[top], top=top, mine=mine))
    res.commits.sort()
    res.events.sort()
    res.tags = sorted(set(res.tags))
    return res
