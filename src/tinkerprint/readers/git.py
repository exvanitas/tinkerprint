"""git reader: commits in the repos a profile lists, matched to the person by identity patterns.

Keeps hash, author identity match, author time, changed paths with status and added lines,
and Co-Authored-By matches. Never reads commit subjects or bodies (the trailer format
returns trailer values only).
"""
from __future__ import annotations

import fnmatch
import os
import re
import shutil
import subprocess
from collections import Counter

from ..events import Commit, Event, Inputs, Tag
from ..timeutil import iso, parse_ts

DEFAULT_BOTS = ("dependabot*", "renovate*", "github-actions*", "*[[]bot]*")

_FMT = "%x1e%H%x1f%P%x1f%an%x1f%ae%x1f%aI%x1f%(trailers:key=Co-authored-by,valueonly,separator=%x1d)"
_COAUTHOR = re.compile(r"^\s*(.*?)\s*<([^>]*)>\s*$")


def clean_env() -> dict:
    """The parent's environment without any GIT_* variable, so nothing set outside picks the repo,
    the work tree, the config, a pager, an external diff or a transport for a git call made here."""
    return {k: v for k, v in os.environ.items() if not k.upper().startswith("GIT_")}


def _env() -> dict:
    env = clean_env()
    # Local only: no prompts, no transport at all (an empty allow list beats any protocol.*.allow
    # setting), and no lazy fetch of missing objects in partial clones.
    env.update({"LC_ALL": "C", "GIT_TERMINAL_PROMPT": "0", "GIT_OPTIONAL_LOCKS": "0", "GIT_PAGER": "cat",
                "GIT_NO_LAZY_FETCH": "1", "GIT_ALLOW_PROTOCOL": ""})
    return env


# Settings no repo or user config can override for a call made here: no transport, no pager, no
# signature check (which runs gpg), no external diff, no file-system monitor.
SAFE = ["--no-pager", "-c", "protocol.allow=never", "-c", "log.showSignature=false", "-c", "diff.external=",
        "-c", "core.fsmonitor=false", "-c", "core.pager=cat"]
# For log and show: no signature check, no text conversion filter, no external diff program.
NO_PROGRAMS = ["--no-show-signature", "--no-textconv", "--no-ext-diff"]


def _git(args, cwd) -> str | None:
    try:
        r = subprocess.run(["git", *SAFE, "-C", cwd, *args], capture_output=True, env=_env(), check=False)
    except OSError:
        return None
    if r.returncode != 0:
        return None
    # surrogateescape keeps every distinct byte path distinct, whatever its encoding.
    return r.stdout.decode("utf-8", "surrogateescape")


def git_bytes(args, cwd) -> bytes | None:
    """Raw stdout of a local git command, or None on failure."""
    try:
        r = subprocess.run(["git", *SAFE, "-C", cwd, *args], capture_output=True, env=_env(), check=False)
    except OSError:
        return None
    return r.stdout if r.returncode == 0 else None


def git_text(args, cwd) -> str | None:
    return _git(args, cwd)


def global_config(key: str) -> str:
    """One value from the user's global git config, read-only, through the same local-only call.
    '' when it is unset, git is missing, or the value is not plain one-line text."""
    home = os.path.expanduser("~")
    # GIT_CONFIG_GLOBAL names the global config when it is set. Every git call here runs without
    # GIT_* variables, so that file is named outright.
    named = os.environ.get("GIT_CONFIG_GLOBAL")
    where = ["--file", os.path.abspath(named), "--includes"] if named else ["--global"]
    out = _git(["config", *where, "--get", key], home if os.path.isdir(home) else os.sep)
    value = (out or "").strip()
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return ""
    return "" if re.search(r"[\x00-\x1f\x7f]", value) else value


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


def toplevel(root: str) -> str | None:
    if not os.path.isdir(root):
        return None
    out = _git(["rev-parse", "--show-toplevel"], root)
    return os.path.normpath(out.strip()) if out else None


def _log(top: str, numstat: bool) -> str | None:
    # Merges count the files whose result differs from every parent (dense combined diff):
    # conflict resolutions and hand edits made during the merge. A clean merge counts nothing.
    # -z gives raw paths, NUL-terminated, with no quoting.
    args = ["log", "--all", "--no-renames", "--raw", "-z", "--diff-merges=dense-combined",
            "--no-abbrev", *NO_PROGRAMS, "--format=" + _FMT]
    if numstat:
        args.insert(3, "--numstat")
    return _git(args, top)


_NUMSTAT = re.compile(r"^(\d+|-)\t(\d+|-)\t(.*)$", re.S)
_RAW = re.compile(r"^:+[0-7]{6}")
_HEAD = re.compile(r"^\n?\x1e([0-9a-f]{40,64})\x1f")


def _split_commits(out: str):
    """Yield (header text, body tokens) per commit from NUL-delimited log output.

    A raw entry's path token is taken as a path whatever bytes it holds, so a file name with a
    record separator or anything else can never start a new commit.
    """
    head = None
    body: list = []
    expect_path = False
    for tok in out.split("\0"):
        if expect_path:
            body.append(tok)
            expect_path = False
            continue
        m = _HEAD.match(tok)
        if m:
            if head is not None:
                yield head, body
            head, body = tok.lstrip("\n")[1:], []
            continue
        if head is None:
            continue
        body.append(tok)
        if _RAW.match(tok.lstrip("\n")):
            expect_path = True
    if head is not None:
        yield head, body


def _parse_files(tokens: list):
    """(status by path, added lines by path) from the NUL-split body of one commit."""
    status, added = {}, {}
    i = 0
    while i < len(tokens):
        tok = tokens[i].lstrip("\n")
        i += 1
        if not tok:
            continue
        if _RAW.match(tok):
            if i < len(tokens):
                letters = tok.split()[-1] if tok.split() else "M"
                status[tokens[i]] = letters[:1] or "M"
                i += 1
            continue
        m = _NUMSTAT.match(tok)
        if m:
            added[m.group(3)] = int(m.group(1)) if m.group(1).isdigit() else 0
    return status, added


def shallow_commits(top: str) -> set:
    """Commits whose parents a shallow clone cut off. They are boundaries, not first commits."""
    path = _git(["rev-parse", "--git-path", "shallow"], top)
    if not path:
        return set()
    path = path.strip()
    if not os.path.isabs(path):
        path = os.path.join(top, path)
    try:
        with open(path, encoding="ascii", errors="replace") as f:
            return {line.strip() for line in f if line.strip()}
    except OSError:
        return set()


def read_repo(top: str, ident: Identity, warnings: list | None = None):
    """Parse one repo into commit dicts. Rows hold no text but paths.

    When line counts need objects the clone does not have (a partial clone), it reads the
    history without them and adds a warning instead of fetching anything. Warnings carry the
    repo folder separately, so callers can name it by its profile alias.
    """
    out = _log(top, numstat=True)
    if out is None:
        out = _log(top, numstat=False)
        if warnings is not None:
            warnings.append((top, "incomplete local history. Line counts skipped." if out is not None
                             else "could not read git history."))
    commits = []
    if not out:
        return commits
    cut = shallow_commits(top)
    if cut and warnings is not None:
        warnings.append((top, "history is shallow, so its oldest commits show their whole tree as changed. They "
                              "count for days but not for achievements, and this clone earns no Founder. Run "
                              "'git fetch --unshallow' in it to read its full history."))
    for head_text, body in _split_commits(out):
        head = head_text.split("\x1f")
        if len(head) < 6:
            continue
        h, parents, an, ae, at, trailers = head[:6]
        parents = parents.split()
        status, added = _parse_files(body)
        if len(parents) > 1:
            # A merge's numstat is against its first parent. Keep only the combined-diff files.
            files = sorted((p, status[p], 0) for p in status)
        else:
            files = sorted((p, status.get(p, "M"), added.get(p, 0)) for p in set(status) | set(added))
        bot = ident.is_bot(an, ae)
        mine = (not bot) and (ident.is_me(an, ae) or ident.coauthor_is_me(trailers))
        commits.append({"hash": h, "parents": parents, "ts": at, "mine": mine, "bot": bot, "files": files,
                        "boundary": h in cut, "shallow": bool(cut), "author": (an, ae)})
    return commits


def read_tags(top: str, ident: Identity):
    """Every tag with its target commit. An annotated tag says who made it and when. A lightweight
    tag says neither, so it carries its commit's committer date and is judged by its commit."""
    fmt = ("%(refname:strip=2)%1f%(objecttype)%1f%(taggername)%1f%(taggeremail:trim)%1f%(taggerdate:iso-strict)"
           "%1f%(*objectname)%1f%(objectname)%1f%(creatordate:iso-strict)")
    out = _git(["for-each-ref", "refs/tags", "--format=" + fmt], top)
    rows = []
    for line in (out or "").splitlines():
        bits = line.split("\x1f")
        if len(bits) != 8:
            continue
        name, otype, tn, te, td, deref, obj, cd = bits
        annotated = otype == "tag"
        if not annotated and otype != "commit":
            continue  # a lightweight tag of a tree or blob names no commit
        rows.append({"name": name, "annotated": annotated, "tagger_me": annotated and ident.is_me(tn, te),
                     "ts": td if annotated else cd, "target": deref if annotated else obj})
    return rows


def _repo_groups(per_top: dict) -> dict:
    """Clones that share any commit are one repository. Returns {top: repo id}.

    The id is the earliest genuine first commit in the group (a shallow clone's cut-off
    boundary does not count), else the smallest commit hash in the group.
    """
    parent = {t: t for t in per_top}

    def find(t):
        while parent[t] != t:
            parent[t] = parent[parent[t]]
            t = parent[t]
        return t

    owner = {}
    for top in sorted(per_top):
        for c in per_top[top]:
            o = owner.setdefault(c["hash"], top)
            if o != top:
                a, b = find(o), find(top)
                if a != b:
                    parent[max(a, b)] = min(a, b)
    groups = {}
    for top in per_top:
        groups.setdefault(find(top), []).append(top)
    ids = {}
    for members in groups.values():
        firsts = sorted(c["hash"] for t in members for c in per_top[t] if not c["parents"] and not c["boundary"])
        every = sorted(c["hash"] for t in members for c in per_top[t])
        gid = firsts[0] if firsts else (every[0] if every else min(members))
        for t in members:
            ids[t] = gid
    return ids


def read_git(roots, ident: Identity, in_roots=None) -> Inputs:
    """Read every repo that holds a profile root. Commits dedupe by hash across clones and refs.

    in_roots(path) tells whether a path belongs to the profile. Each file of a commit seen in
    several clones takes the first clone where it lands inside a root.
    Root ids: a root inside a repo maps to (repository id, its path inside the repo), so a file is
    keyed by repository and repository-relative path whatever the root depth. Keys are real paths.
    """
    in_roots = in_roots or (lambda p: True)
    top_of = {os.path.realpath(r): toplevel(r) for r in roots}
    tops = sorted({t for t in top_of.values() if t})
    res = Inputs()
    per_top = {top: read_repo(top, ident, res.warnings) for top in tops}
    repo_ids = _repo_groups(per_top)
    res.setup = {"git": shutil.which("git") is not None, "roots": dict(top_of), "repos": {}}
    for top, rows in per_top.items():
        mine = sum(1 for c in rows if c["mine"])
        seen = Counter(c["author"] for c in rows if not c["bot"]) if not mine else Counter()
        ranked = sorted(seen.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
        res.setup["repos"][top] = {"commits": len(rows), "mine": mine,
                                   "authors": [(n, e, k) for (n, e), k in ranked]}
    for r, top in top_of.items():
        if top:
            rel = os.path.relpath(r, os.path.realpath(top))
            res.root_ids[r] = (f"git:{repo_ids[top]}", "" if rel == "." else rel.replace(os.sep, "/"))

    seen = {}
    for top in tops:
        for c in per_top[top]:
            seen.setdefault(c["hash"], []).append((top, c))

    def scoped(copies, c) -> bool:
        # In scope when a changed file lands inside a root in any clone. A commit that changed no
        # file (an empty or clean merge commit) is in scope when a root holds its whole repo.
        if not c["files"]:
            return any(in_roots(t) for t, _ in copies)
        return any(in_roots(os.path.join(t, path)) for path, _, _ in c["files"] for t, _ in copies)

    chosen = {}
    for h, copies in seen.items():
        # A shallow clone's boundary copy lacks its parents, so its diff shows its whole tree. Prefer a
        # complete copy for parents, files and line counts. With none, the commit's scope is unknown,
        # so it counts for no achievement. Only a copy in a clone that is not shallow proves a first
        # commit: a shallow one cannot show what came before.
        complete = [(t, cc) for t, cc in copies if not cc["boundary"]]
        top, c = (complete or copies)[0]
        dt = parse_ts(c["ts"])
        if dt is None:
            continue
        ts = iso(dt)
        genuine_first = any(not cc["parents"] and not cc["shallow"] for _, cc in complete)
        in_scope = bool(complete) and scoped(copies, c)
        chosen[h] = (copies, c, in_scope)
        # Scope is worked out for your own commits only: no achievement looks at anyone else's.
        res.commits.append(Commit(ts=ts, hash=h, repo=repo_ids[top], top=top, mine=c["mine"],
                                  bot=c["bot"], root=genuine_first, files=len(c["files"]),
                                  scoped=c["mine"] and in_scope))
        if not c["mine"]:
            continue
        for path, st, add in c["files"]:
            where = next((t for t, _ in copies if in_roots(os.path.join(t, path))), top)
            # A boundary-only copy counts its whole tree as added: its line counts are unknown.
            res.events.append(Event(ts=ts, source="git", kind="commit", path=os.path.join(where, path),
                                    actor="human", commit=h, status=st, added=add if complete else 0, op=h))
    tags = {}
    for top in tops:
        for t in read_tags(top, ident):
            # An annotated tag is yours when you made it. A lightweight tag names no one, so it is
            # yours when it points at your commit.
            target = chosen.get(t["target"])
            if not (t["tagger_me"] if t["annotated"] else (target is not None and target[1]["mine"])):
                continue
            dt = parse_ts(t["ts"])
            if dt is None:
                continue
            key = (t["name"], t["target"])  # one tag, however many clones hold it
            # The tag is in scope when its commit is.
            in_scope = target is not None and target[2]
            tags.setdefault(key, Tag(ts=iso(dt), name=t["name"], repo=repo_ids[top], top=top, mine=True,
                                     scoped=in_scope))
    res.commits.sort()
    res.events.sort()
    res.tags = sorted(tags.values())
    return res
