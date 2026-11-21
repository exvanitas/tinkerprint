"""Test helpers. Every name, path and email here is invented."""
import os
import sys

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")
if SRC not in sys.path:
    sys.path.insert(0, SRC)

from tinkerprint.events import Event, Inputs  # noqa: E402
from tinkerprint.profile import parse_profile  # noqa: E402
from tinkerprint.score import finish, score_core  # noqa: E402


def profile(projects, set="builder", tz="UTC", rollover=4, **extra):
    """projects: [(name, root, extra table)]."""
    data = {"name": "Test Person", "set": set, "timezone": tz, "rollover_hour": rollover,
            "identity": {"emails": ["tester@example.test"]},
            "project": [dict({"name": n, "root": r}, **(x or {})) for n, r, x in projects]}
    data.update(extra)
    return parse_profile(data, "/nonexistent-base")


def commit(ts, path, h="c1", status="M", added=0):
    return Event(ts=ts, source="git", kind="commit", path=path, actor="human", commit=h, status=status, added=added)


def edit(ts, path, session="s1", harness="claude", model="model-x"):
    return Event(ts=ts, source=harness, kind="edit", path=path, session=session, harness=harness, model=model,
                 actor="agent")


def session(ts, folder, sid="s1", harness="claude", origin="", model="model-x"):
    return Event(ts=ts, source=harness, kind="session", path=folder, session=sid, harness=harness, model=model,
                 actor="agent", origin=origin)


def run(prof, events, commits=(), tags=(), priors=None, season=(None, None), prev=None, as_of=None, milestones=()):
    core, local = score_core(Inputs(events=list(events), commits=list(commits), tags=list(tags)), prof,
                             priors or {}, season, as_of, milestones)
    return finish(core, prev, prof, local["shares"]), local


def stat(sheet, key):
    return next(r for r in sheet["stats"] if r["key"] == key)


def project(sheet, name):
    return next(p for p in sheet["projects"] if p["name"] == name)
