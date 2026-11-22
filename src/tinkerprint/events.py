"""The common event record every reader emits, and git-only side records."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

SOURCES = ("git", "claude", "codex", "agy")
KINDS = ("commit", "edit", "session")
HARNESSES = ("claude", "codex", "agy")


@dataclass(frozen=True, order=True)
class Event:
    ts: str            # ISO time with offset
    source: str        # git | claude | codex | agy
    kind: str          # commit | edit | session
    path: str          # absolute file path (commit, edit) or the session folder
    session: str = ""  # harness session id
    harness: str = ""  # claude | codex | agy
    model: str = ""
    actor: str = "human"  # human | agent | bot
    origin: str = ""   # harness originator, when the log has one
    commit: str = ""   # commit hash (git)
    status: str = ""   # A, M or D for commit files
    added: int = 0     # lines added (git numstat)
    op: str = ""       # operation id (tool call, change record or commit), so distinct changes stay distinct

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Event":
        return Event(**{k: d[k] for k in Event.__dataclass_fields__ if k in d})


@dataclass(frozen=True, order=True)
class Commit:
    """One deduplicated commit, for achievements. No subject is kept."""
    ts: str
    hash: str
    repo: str          # repo id: the earliest root commit hash reachable in that clone
    top: str           # repo folder (local only, never output)
    mine: bool
    bot: bool
    root: bool         # has no parents
    files: int = 0
    scoped: bool = True  # touches a file inside the profile's roots (an empty commit: a root holds its repo)


@dataclass(frozen=True, order=True)
class Tag:
    ts: str
    name: str
    repo: str
    top: str
    mine: bool
    scoped: bool = True  # its commit is scoped (see Commit)


@dataclass
class Inputs:
    events: list = field(default_factory=list)
    commits: list = field(default_factory=list)
    tags: list = field(default_factory=list)
    warnings: list = field(default_factory=list)  # local only: printed by the CLI, never on a sheet
    root_ids: dict = field(default_factory=dict)   # profile root -> identity shared by its clones
    # Local only, for the setup warnings a build prints: whether git ran, each root's repo folder,
    # per repo the commit totals (and, where none matched, the author identities seen), and
    # per harness whether its folder was there and how many sessions were read.
    setup: dict = field(default_factory=dict)
