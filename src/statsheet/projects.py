"""Project roots, parts, globs and manifest priors."""
from __future__ import annotations

import json
import os
import re
import tomllib
from functools import lru_cache

TRAINING_DEPS = {"torch", "transformers", "peft", "jax"}
DATA_DEPS = {"dbt", "pandas", "polars", "duckdb", "alembic"}


class Resolver:
    """Maps an absolute path to (project, path relative to its root) by the longest matching root."""

    def __init__(self, projects):
        roots = []
        for p in projects:
            for r in p.roots:
                roots.append((r.rstrip("/") or "/", p))
        self._roots = sorted(roots, key=lambda x: (-len(x[0]), x[0], x[1].index))
        self.projects = list(projects)

    def resolve(self, path: str):
        if not path:
            return None
        path = os.path.normpath(path)
        for root, proj in self._roots:
            if path == root:
                return proj, ""
            if path.startswith(root + "/") or root == "/":
                return proj, path[len(root):].lstrip("/")
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


def manifest_prior(folder: str) -> str | None:
    """The prior a folder's manifests give its code: Tools, Models, Data or None.

    An extension manifest or a bin entry gives Tools. Training dependencies give Models.
    Data dependencies give Data. Tools wins over Models, Models over Data.
    """
    tools = False
    deps: set = set()

    pkg = os.path.join(folder, "package.json")
    if os.path.isfile(pkg):
        try:
            with open(pkg, encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict):
                if d.get("bin"):
                    tools = True
                eng = d.get("engines")
                if (isinstance(eng, dict) and "vscode" in eng) or d.get("contributes"):
                    tools = True
        except (OSError, ValueError):
            pass

    man = os.path.join(folder, "manifest.json")
    if os.path.isfile(man):
        try:
            with open(man, encoding="utf-8") as f:
                d = json.load(f)
            if isinstance(d, dict) and "manifest_version" in d:
                tools = True
        except (OSError, ValueError):
            pass

    py = os.path.join(folder, "pyproject.toml")
    if os.path.isfile(py):
        try:
            with open(py, "rb") as f:
                d = tomllib.load(f)
            proj = d.get("project", {})
            poetry = d.get("tool", {}).get("poetry", {})
            if proj.get("scripts") or proj.get("gui-scripts") or poetry.get("scripts"):
                tools = True
            for s in proj.get("dependencies", []) or []:
                deps.add(_dep_name(s))
            for group in (proj.get("optional-dependencies") or {}).values():
                for s in group:
                    deps.add(_dep_name(s))
            for k in (poetry.get("dependencies") or {}):
                deps.add(_dep_name(k))
        except (OSError, tomllib.TOMLDecodeError, AttributeError, TypeError):
            pass

    try:
        names = sorted(os.listdir(folder))
    except OSError:
        names = []
    for name in names:
        if name.startswith("requirements") and name.endswith(".txt"):
            try:
                with open(os.path.join(folder, name), encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith(("#", "-")):
                            deps.add(_dep_name(line))
            except OSError:
                pass

    cargo = os.path.join(folder, "Cargo.toml")
    if os.path.isfile(cargo):
        try:
            with open(cargo, "rb") as f:
                if tomllib.load(f).get("bin"):
                    tools = True
        except (OSError, tomllib.TOMLDecodeError):
            pass

    if tools:
        return "Tools"
    kind = _dep_kind(deps)
    if kind:
        return kind
    if os.path.isfile(os.path.join(folder, "dbt_project.yml")) or os.path.isfile(os.path.join(folder, "alembic.ini")):
        return "Data"
    return None


def scan_priors(projects) -> dict:
    """Priors per project: {project name: {part path or '': prior}}. Reads manifests at each root and part."""
    out = {}
    for p in projects:
        found = {}
        for folder_rel in [""] + [part.path for part in p.parts]:
            prior = None
            for root in p.roots:
                prior = manifest_prior(os.path.join(root, folder_rel) if folder_rel else root)
                if prior:
                    break
            if prior:
                found[folder_rel] = prior
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


def prior_for(priors: dict, project, rel: str) -> str | None:
    """A file takes the prior of its part when the part has one, else the project root's."""
    found = priors.get(project.name, {})
    part = part_of(project, rel)
    if part is not None and part.path in found:
        return found[part.path]
    return found.get("")
