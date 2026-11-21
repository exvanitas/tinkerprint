"""Classify one changed file into stat weights, by METHOD.md's rules in order."""
from __future__ import annotations

import os

from .profile import map_weights
from .projects import glob_match, part_of, prior_for
from .sets import TINKERER_FROM_BUILDER

SKIP_DIRS = {"node_modules", "dist", "build", "vendor", "target", ".git"}
LOCKFILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "cargo.lock", "gemfile.lock",
    "composer.lock", "uv.lock", "go.sum", "bun.lockb", "bun.lock", "pipfile.lock", "flake.lock",
    "npm-shrinkwrap.json", "mix.lock", "pubspec.lock", "packages.lock.json",
}
AGENT_NOTES = {"claude.md", "agents.md", "gemini.md", "brief.md", "plan.md", "todo.md", "handoff.md"}
AGENT_DIRS = {".claude", ".codex", ".gemini", ".cursor", ".aider"}

TEST_DIRS = {"test", "tests", "__tests__"}
INFRA_DIRS = {".github", "deploy", "infra", "k8s"}
DATA_DIRS = {"migrations", "schema"}
DOCS_DIRS = {"docs"}
INTERFACE_DIRS = {"components", "views", "pages", "styles"}
TOOLS_DIRS = {"bin", "cli", "scripts", "tools"}

INTERFACE_EXT = {".tsx", ".jsx", ".vue", ".svelte", ".css", ".scss", ".html"}
DATA_EXT = {".sql", ".ipynb"}
DOCS_EXT = {".md", ".mdx", ".rst"}
INFRA_EXT = {".sh", ".ps1", ".tf"}
LOGIC_EXT = {
    ".py", ".pyi", ".js", ".mjs", ".cjs", ".ts", ".mts", ".cts", ".go", ".rs", ".java", ".kt", ".kts",
    ".scala", ".rb", ".php", ".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".hh", ".cs", ".fs", ".swift",
    ".m", ".mm", ".lua", ".dart", ".ex", ".exs", ".erl", ".hrl", ".hs", ".ml", ".mli", ".clj", ".cljs",
    ".elm", ".r", ".jl", ".zig", ".nim", ".gd", ".glsl", ".hlsl", ".wgsl", ".shader", ".pl", ".pm",
    ".groovy", ".sol", ".v", ".asm", ".odin", ".cr", ".d", ".vala", ".purs", ".rkt", ".scm", ".lisp", ".el",
}
CODE_EXT = INTERFACE_EXT | DATA_EXT | INFRA_EXT | LOGIC_EXT

LANGUAGE = {
    ".py": "Python", ".pyi": "Python", ".js": "JavaScript", ".mjs": "JavaScript", ".cjs": "JavaScript",
    ".jsx": "JavaScript", ".ts": "TypeScript", ".mts": "TypeScript", ".cts": "TypeScript", ".tsx": "TypeScript",
    ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin", ".scala": "Scala",
    ".rb": "Ruby", ".php": "PHP", ".c": "C", ".h": "C", ".cc": "C++", ".cpp": "C++", ".cxx": "C++",
    ".hpp": "C++", ".hh": "C++", ".cs": "C#", ".fs": "F#", ".swift": "Swift", ".m": "Objective-C",
    ".mm": "Objective-C", ".lua": "Lua", ".dart": "Dart", ".ex": "Elixir", ".exs": "Elixir", ".erl": "Erlang",
    ".hs": "Haskell", ".ml": "OCaml", ".clj": "Clojure", ".cljs": "Clojure", ".elm": "Elm", ".r": "R",
    ".jl": "Julia", ".zig": "Zig", ".nim": "Nim", ".gd": "GDScript", ".glsl": "GLSL", ".hlsl": "HLSL",
    ".wgsl": "WGSL", ".pl": "Perl", ".sol": "Solidity", ".vue": "Vue", ".svelte": "Svelte", ".css": "CSS",
    ".scss": "CSS", ".html": "HTML", ".sql": "SQL", ".sh": "Shell", ".ps1": "PowerShell", ".tf": "Terraform",
}

def ext_of(rel: str) -> str:
    return os.path.splitext(rel)[1].lower()


def is_code(rel: str) -> bool:
    return ext_of(rel) in CODE_EXT


def language_of(rel: str) -> str | None:
    return LANGUAGE.get(ext_of(rel))


def is_skipped(rel: str) -> bool:
    parts = rel.split("/")
    if any(p in SKIP_DIRS for p in parts[:-1]):
        return True
    base = parts[-1].lower()
    if base in LOCKFILES or base.endswith(".lock"):
        return True
    if ".min." in base or base.endswith(".map"):
        return True
    return False


def _is_agent_note(rel: str) -> bool:
    parts = rel.split("/")
    if any(p in AGENT_DIRS for p in parts[:-1]):
        return True
    base = parts[-1].lower()
    return base in AGENT_NOTES or base.endswith((".brief.md", ".plan.md"))


def path_stat(rel: str) -> str | None:
    """Rule 3: folder and file-name patterns."""
    parts = rel.split("/")
    dirs = set(parts[:-1])
    base = parts[-1]
    if dirs & TEST_DIRS or ".test." in base or ".spec." in base:
        return "Tests"
    if dirs & INFRA_DIRS or base == "Dockerfile" or base.startswith("Dockerfile."):
        return "Infra"
    if dirs & DATA_DIRS:
        return "Data"
    if dirs & DOCS_DIRS:
        return "Docs"
    if dirs & INTERFACE_DIRS:
        return "Interface"
    if dirs & TOOLS_DIRS:
        return "Tools"
    return None


def ext_stat(rel: str) -> str | None:
    """Rule 4: extensions. Other source code is Logic. Anything else is unclassified (None)."""
    e = ext_of(rel)
    if e in INTERFACE_EXT:
        return "Interface"
    if e in DATA_EXT:
        return "Data"
    if e in DOCS_EXT:
        return "Docs"
    if e in INFRA_EXT:
        return "Infra"
    if e in LOGIC_EXT:
        return "Logic"
    return None


def builder_stat(rel: str, prior: str | None) -> str | None:
    """Rules 2 to 5 for one file, as a builder stat or None for unclassified.

    Rule 2, manifest priors, comes before paths and extensions: a Tools prior takes all of the
    project's code, a Models or Data prior takes its Python. Other files fall through.
    """
    if _is_agent_note(rel):
        return None
    if prior == "Tools" and is_code(rel):
        return "Tools"
    if prior in ("Models", "Data") and ext_of(rel) in (".py", ".pyi"):
        return prior
    return path_stat(rel) or ext_stat(rel)


def classify(rel: str, project, set_name: str, priors: dict, root: str | None = None):
    """Weights for one file: None when skipped, else {stat: weight} summing to 1.

    The key "" is the unclassified share. In a tinkerer profile the key None stands for
    the project's main code stat.
    """
    if is_skipped(rel):
        return None
    weights = None
    for ov in project.overrides:
        if glob_match(ov.glob, rel):
            weights = ov.stats
            break
    if weights is None:
        part = part_of(project, rel)
        if part is not None and part.stats:
            weights = part.stats
    if weights is None and project.stats:
        weights = project.stats
    if weights is not None:
        mapped = map_weights(weights, set_name)
    else:
        stat = builder_stat(rel, prior_for(priors, project, rel, root))
        if stat is None:
            return {"": 1.0}
        mapped = {stat: 1.0} if set_name == "builder" else {TINKERER_FROM_BUILDER[stat]: 1.0}
    total = sum(mapped.values())
    return {k: v / total for k, v in mapped.items()}
