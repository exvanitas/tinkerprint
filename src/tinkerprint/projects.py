"""Project roots, parts, globs and manifest priors."""
from __future__ import annotations

import json
import os
import re
import tomllib
from functools import lru_cache

TRAINING_DEPS = {"torch", "transformers", "peft", "jax"}
DATA_DEPS = {"dbt", "pandas", "polars", "duckdb", "alembic"}


def canonical(path: str) -> str:
    """The real path, symlinks resolved. A path that does not exist (yet) is normalized as far as it goes."""
    return os.path.realpath(os.path.expanduser(path))


class Resolver:
    """Maps an absolute path to (project, path relative to its root) by the longest matching root."""

    def __init__(self, projects):
        roots = []
        for p in projects:
            for r in p.roots:
                roots.append((canonical(r).rstrip("/") or "/", p))
        self._roots = sorted(roots, key=lambda x: (-len(x[0]), x[0], x[1].index))
        self.projects = list(projects)
        self._real = lru_cache(maxsize=None)(canonical)

    def resolve(self, path: str):
        hit = self.resolve_root(path)
        return (hit[0], hit[2]) if hit else None

    def resolve_root(self, path: str):
        """(project, matched root, path relative to it), or None."""
        if not path or not os.path.isabs(path):
            return None  # relative paths have no known folder: unassigned
        path = self._real(path)  # roots and paths compare as real paths, symlinks resolved
        for root, proj in self._roots:
            if path == root:
                return proj, root, ""
            if path.startswith(root + "/") or root == "/":
                return proj, root, path[len(root):].lstrip("/")
        return None


@lru_cache(maxsize=4096)
def compile_glob(pattern: str):
    """Glob to regex. '**' crosses folders, '*' and '?' do not."""
    out = []
    i, n = 0, len(pattern)
    while i < n:
        c = pattern[i]
        if c == "*":
            if pattern[i:i + 3] == "**/":
                out.append("(?:.*/)?")
                i += 3
                continue
            if pattern[i:i + 2] == "**":
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
        elif c == "?":
            out.append("[^/]")
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("^" + "".join(out) + "(?:/.*)?$")


def glob_match(pattern: str, rel: str) -> bool:
    return bool(compile_glob(pattern).match(rel))


def _dep_name(s: str) -> str:
    m = re.match(r"\s*([A-Za-z0-9_.\-]+)", s)
    return m.group(1).lower().replace("_", "-") if m else ""


def _dep_kind(names) -> str | None:
    names = set(names)
    if names & TRAINING_DEPS:
        return "Models"
    if any(n in DATA_DEPS or n.startswith("dbt-") for n in names):
        return "Data"
    return None


class WorkTree:
    """Manifests read from the folder as it is on disk. Used for roots that are not in git."""

    def __init__(self, base: str):
        self.base = base

    def read(self, rel: str):
        try:
            with open(os.path.join(self.base, rel), "rb") as f:
                return f.read()
        except OSError:
            return None

    def names(self, rel: str) -> list:
        try:
            return sorted(os.listdir(os.path.join(self.base, rel) if rel else self.base))
        except OSError:
            return []


class GitTree:
    """Manifests read from one commit's tree with `git show`, whatever is checked out."""

    def __init__(self, top: str, rev: str, prefix: str):
        self.top, self.rev, self.prefix = top, rev, prefix

    def _path(self, rel: str) -> str:
        return "/".join(x for x in (self.prefix, rel) if x and x != ".")

    def read(self, rel: str):
        from .readers.git import git_bytes
        return git_bytes(["show", f"{self.rev}:{self._path(rel)}"], self.top)

    def names(self, rel: str) -> list:
        from .readers.git import git_bytes
        folder = self._path(rel)
        out = git_bytes(["ls-tree", "-z", "--name-only", self.rev, "--", (folder + "/") if folder else "."], self.top)
        if not out:
            return []
        return sorted(os.path.basename(n.decode("utf-8", "replace")) for n in out.split(b"\0") if n)


def _decode(data: bytes):
    """Manifest text: UTF-8, UTF-8 with BOM, or UTF-16 with BOM. Anything else is None."""
    try:
        if data.startswith((b"\xff\xfe", b"\xfe\xff")):
            return data.decode("utf-16")
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        return None


def manifest_prior(folder, rel: str = "", warn=None) -> str | None:
    """The prior a folder's manifests give its code: Tools, Models, Data or None.

    folder is a WorkTree, a GitTree or a plain path. An extension manifest or a bin entry gives
    Tools. Training dependencies give Models. Data dependencies give Data. Tools wins over
    Models, Models over Data. A manifest that cannot be decoded is skipped and reported to warn.
    """
    tree = WorkTree(folder) if isinstance(folder, str) else folder
    tools = False
    deps: set = set()

    def text(name):
        data = tree.read("/".join(x for x in (rel, name) if x))
        if data is None:
            return None
        decoded = _decode(data)
        if decoded is None and warn:
            warn(f"skipped {name}: it is not UTF-8 or UTF-16 text.")
        return decoded

    d = _json(text("package.json"))
    if isinstance(d, dict):
        eng = d.get("engines")
        if d.get("bin") or (isinstance(eng, dict) and "vscode" in eng) or d.get("contributes"):
            tools = True
    d = _json(text("manifest.json"))
    if isinstance(d, dict) and "manifest_version" in d:
        tools = True

    d = _toml(text("pyproject.toml"))
    if d:
        try:
            proj = d.get("project", {})
            poetry = d.get("tool", {}).get("poetry", {})
            if proj.get("scripts") or proj.get("gui-scripts") or poetry.get("scripts"):
                tools = True
            for x in proj.get("dependencies", []) or []:
                deps.add(_dep_name(x))
            for group in (proj.get("optional-dependencies") or {}).values():
                for x in group:
                    deps.add(_dep_name(x))
            for k in (poetry.get("dependencies") or {}):
                deps.add(_dep_name(k))
        except (AttributeError, TypeError):
            pass

    names = tree.names(rel)
    for name in names:
        if name.startswith("requirements") and name.endswith(".txt"):
            body = text(name) or ""
            for line in body.splitlines():
                line = line.strip()
                if line and not line.startswith(("#", "-")):
                    deps.add(_dep_name(line))

    d = _toml(text("Cargo.toml"))
    if d and d.get("bin"):
        tools = True

    if tools:
        return "Tools"
    kind = _dep_kind(deps)
    if kind:
        return kind
    if "dbt_project.yml" in names or "alembic.ini" in names:
        return "Data"
    return None


def _json(t):
    if t is None:
        return None
    try:
        return json.loads(t)
    except ValueError:
        return None


def _toml(t):
    if t is None:
        return None
    try:
        return tomllib.loads(t)
    except tomllib.TOMLDecodeError:
        return None


def root_tree(root: str, before: str | None):
    """The tree a root's manifests come from: the newest commit on or before `before` (an ISO
    instant) when the root is in git, else the working tree. Returns (tree or None, source)."""
    from .readers.git import git_text, toplevel
    real = canonical(root)
    top = toplevel(real)
    if not top:
        return WorkTree(real), "working tree"
    args = ["rev-list", "-1", "--all", "--date-order"]
    if before:
        args.append(f"--before={before}")
    rev = (git_text(args, top) or "").strip()
    if not rev:
        return None, "git"
    prefix = os.path.relpath(real, canonical(top))
    return GitTree(top, rev, "" if prefix == "." else prefix.replace(os.sep, "/")), "git"


def scan_priors(projects, before: str | None = None, warnings: list | None = None) -> dict:
    """Priors per project: {project name: {(real root, part path or ''): prior}}.

    Each root reads its own manifests, so two roots of one project never lend each other a prior.
    A git root reads them from its newest commit on or before `before`, so the same history and
    profile give the same priors whatever is checked out. Other roots read the working tree.
    """
    out = {}
    for p in projects:
        found = {}
        for root in p.roots:
            real = canonical(root)
            tree, _ = root_tree(root, before)
            if tree is None:
                continue
            for folder_rel in [""] + [part.path for part in p.parts]:
                warn = (lambda msg, r=real: warnings.append((r, msg))) if warnings is not None else None
                prior = manifest_prior(tree, folder_rel, warn)
                if prior:
                    found[(real, folder_rel)] = prior
        out[p.name] = found
    return out


def part_of(project, rel: str):
    """The deepest part that holds rel, or None."""
    best = None
    for part in project.parts:
        if rel == part.path or rel.startswith(part.path + "/"):
            if best is None or len(part.path) > len(best.path):
                best = part
    return best


def prior_for(priors: dict, project, rel: str, root: str | None = None) -> str | None:
    """A file takes the prior of its part in its own root, else of that root. Without a root
    given, the first root of the project decides."""
    found = priors.get(project.name, {})
    real = canonical(root) if root else (canonical(project.roots[0]) if project.roots else "")
    part = part_of(project, rel)
    if part is not None and (real, part.path) in found:
        return found[(real, part.path)]
    return found.get((real, ""))
