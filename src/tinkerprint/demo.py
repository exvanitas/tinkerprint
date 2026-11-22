"""Synthetic people for `tinkerprint demo` and the tests.

Everything here is invented: names, emails (example.test), projects, prompts and model ids.
Repos are real git repos made with `git fast-import`. Harness logs follow the real formats.
"""
from __future__ import annotations

import json
import os
import random
import re
import shutil
import sqlite3
import subprocess
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from .profile import toml_string


def git_env(home: str | None = None) -> dict:
    env = dict(os.environ)
    env.update({"GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1", "LC_ALL": "C",
                "GIT_TERMINAL_PROMPT": "0"})
    if home:
        env["HOME"] = home
    return env


# ---------------------------------------------------------------- git

@dataclass
class FakeCommit:
    when: datetime
    author: tuple
    files: dict                      # path -> content, or None to delete
    coauthors: list = field(default_factory=list)
    tag: str = ""


class RepoWriter:
    """Builds a repo through fast-import. Author and committer dates are exact, so hashes are stable."""

    def __init__(self, path: str):
        self.path = path
        self.commits: list = []
        self.content: dict = {}

    def commit(self, when: datetime, author: tuple, files: dict, coauthors=(), tag: str = "") -> None:
        self.commits.append(FakeCommit(when, author, dict(files), list(coauthors), tag))

    def touch(self, when: datetime, author: tuple, changes: dict, coauthors=(), tag: str = "") -> None:
        """changes: path -> lines to append."""
        files = {}
        for path, n in changes.items():
            old = self.content.get(path, "")
            k = old.count("\n")
            new = old + "".join(f"{os.path.basename(path)} line {k + i}\n" for i in range(n))
            self.content[path] = new
            files[path] = new
        self.commit(when, author, files, coauthors, tag)

    def write(self) -> None:
        os.makedirs(self.path, exist_ok=True)
        env = git_env()
        subprocess.run(["git", "init", "-q", "-b", "main", self.path], check=True, env=env)
        buf = bytearray()

        def data(b: bytes) -> None:
            buf.extend(f"data {len(b)}\n".encode())
            buf.extend(b)
            buf.extend(b"\n")

        for i, c in enumerate(sorted(self.commits, key=lambda c: c.when), 1):
            ts = int(c.when.timestamp())
            off = c.when.strftime("%z")
            who = f"{c.author[0]} <{c.author[1]}> {ts} {off}"
            buf.extend(f"commit refs/heads/main\nmark :{i}\nauthor {who}\ncommitter {who}\n".encode())
            msg = "Work in progress\n"
            if c.coauthors:
                msg += "\n" + "".join(f"Co-authored-by: {n} <{e}>\n" for n, e in c.coauthors)
            data(msg.encode())
            if i > 1:
                buf.extend(f"from :{i - 1}\n".encode())
            for path in sorted(c.files):
                body = c.files[path]
                if body is None:
                    buf.extend(f"D {path}\n".encode())
                else:
                    buf.extend(f"M 100644 inline {path}\n".encode())
                    data(body.encode() if isinstance(body, str) else body)
            buf.extend(b"\n")
            if c.tag:
                buf.extend(f"tag {c.tag}\nfrom :{i}\ntagger {who}\n".encode())
                data(b"Release\n")
        subprocess.run(["git", "-C", self.path, "fast-import", "--quiet"], input=bytes(buf), check=True, env=env)
        subprocess.run(["git", "-C", self.path, "reset", "-q", "--hard", "main"], check=True, env=env)


# ---------------------------------------------------------------- harness logs

def _ts(dt: datetime) -> str:
    return dt.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _uuid(rng: random.Random) -> str:
    return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def write_claude_session(base: str, cwd: str, start: datetime, model: str, edits: list, rng: random.Random,
                         subagent_edits: list = (), errored: list = ()) -> str:
    """edits: [(datetime, absolute path, tool name)]. errored: paths whose tool call fails."""
    sid = _uuid(rng)
    slug = re.sub(r"[^A-Za-z0-9-]", "-", cwd)  # like Claude Code's folder names, and valid on Windows
    folder = os.path.join(base, slug)
    os.makedirs(folder, exist_ok=True)
    lines = [
        {"type": "permission-mode", "permissionMode": "default", "sessionId": sid},
        {"type": "user", "sessionId": sid, "timestamp": _ts(start), "cwd": cwd, "uuid": _uuid(rng),
         "parentUuid": None, "isSidechain": False, "userType": "external", "version": "0.0.0", "gitBranch": "main",
         "message": {"role": "user", "content": "Invented prompt text that the reader must never keep."}},
        {"type": "ai-title", "aiTitle": "Invented title", "sessionId": sid},
    ]
    t = start + timedelta(minutes=1)
    lines.append({"type": "assistant", "sessionId": sid, "timestamp": _ts(t), "cwd": cwd, "uuid": _uuid(rng),
                  "message": {"id": "msg_" + _uuid(rng)[:8], "role": "assistant", "model": model,
                              "content": [{"type": "text", "text": "Invented reply text."}]}})
    for when, path, tool in list(edits) + [(w, p, "Write") for w, p in errored]:
        tid = "toolu_" + _uuid(rng).replace("-", "")[:16]
        key = "notebook_path" if tool == "NotebookEdit" else "file_path"
        inp = {key: path, "old_string": "invented old", "new_string": "invented new"}
        lines.append({"type": "assistant", "sessionId": sid, "timestamp": _ts(when), "cwd": cwd, "uuid": _uuid(rng),
                      "message": {"id": "msg_" + _uuid(rng)[:8], "role": "assistant", "model": model,
                                  "content": [{"type": "tool_use", "id": tid, "name": tool, "input": inp}]}})
        failed = (when, path) in list(errored)
        lines.append({"type": "user", "sessionId": sid, "timestamp": _ts(when + timedelta(seconds=2)), "cwd": cwd,
                      "uuid": _uuid(rng), "message": {"role": "user", "content": [
                          {"type": "tool_result", "tool_use_id": tid, "content": "invented result",
                           **({"is_error": True} if failed else {})}]}})
    with open(os.path.join(folder, sid + ".jsonl"), "w", encoding="utf-8") as f:
        for ln in lines:
            f.write(json.dumps(ln) + "\n")
    if subagent_edits:
        sub = os.path.join(folder, sid, "subagents")
        os.makedirs(sub, exist_ok=True)
        with open(os.path.join(sub, "agent-" + _uuid(rng)[:8] + ".jsonl"), "w", encoding="utf-8") as f:
            for when, path in subagent_edits:
                tid = "toolu_" + _uuid(rng).replace("-", "")[:16]
                f.write(json.dumps({"type": "assistant", "sessionId": sid, "isSidechain": True, "agentId": "a1",
                                    "timestamp": _ts(when), "cwd": cwd, "message": {
                                        "role": "assistant", "model": model, "content": [
                                            {"type": "tool_use", "id": tid, "name": "Write",
                                             "input": {"file_path": path, "content": "invented"}}]}}) + "\n")
                f.write(json.dumps({"type": "user", "sessionId": sid, "isSidechain": True, "agentId": "a1",
                                    "timestamp": _ts(when + timedelta(seconds=2)), "cwd": cwd, "message": {
                                        "role": "user", "content": [
                                            {"type": "tool_result", "tool_use_id": tid, "content": "invented"}]}}) + "\n")
    return sid


def write_codex_session(base: str, cwd: str, start: datetime, model: str, edits: list, rng: random.Random,
                        originator: str = "codex_exec") -> str:
    """edits: [(datetime, absolute path)]. Each is a patch call followed by its FileChange completion."""
    sid = _uuid(rng)
    day = start.astimezone(ZoneInfo("UTC"))
    folder = os.path.join(base, f"{day:%Y}", f"{day:%m}", f"{day:%d}")
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, f"rollout-{day:%Y-%m-%dT%H-%M-%S}-{sid}.jsonl")
    lines = [
        {"timestamp": _ts(start), "type": "session_meta", "payload": {
            "id": sid, "timestamp": _ts(start), "cwd": cwd, "originator": originator, "cli_version": "0.0.0",
            "source": "exec", "model_provider": "invented"}},
        {"timestamp": _ts(start), "type": "turn_context", "payload": {"cwd": cwd, "model": model,
                                                                     "approval_policy": "never", "effort": "high"}},
        {"timestamp": _ts(start), "type": "response_item", "payload": {
            "type": "message", "role": "user", "content": [{"type": "input_text", "text": "Invented prompt."}]}},
        {"timestamp": _ts(start), "type": "event_msg", "payload": {"type": "task_started", "turn_id": "t1"}},
    ]
    for i, (when, fp) in enumerate(edits):
        # The patch call itself is never read. Only the completion record counts.
        rel = os.path.relpath(fp, cwd)
        patch = f"*** Begin Patch\n*** Update File: {rel}\n@@\n-invented\n+invented too\n*** End Patch"
        lines.append({"timestamp": _ts(when), "type": "response_item", "payload": {
            "type": "custom_tool_call", "name": "exec", "call_id": f"c{i}", "status": "completed",
            "input": "const r = await apply_patch(`" + patch + "`);"}})
        change = {"type": "update", "unified_diff": "invented"} if i % 2 == 0 else {"type": "add", "content": "invented"}
        lines.append({"timestamp": _ts(when + timedelta(seconds=3)), "type": "event_msg", "payload": {
            "type": "item_completed", "turn_id": "t1", "item": {
                "type": "FileChange", "id": f"fc{i}", "status": "completed", "changes": {fp: change}}}})
    lines.append({"timestamp": _ts(start + timedelta(minutes=20)), "type": "event_msg",
                  "payload": {"type": "task_complete", "turn_id": "t1", "last_agent_message": "Invented summary."}})
    with open(path, "w", encoding="utf-8") as f:
        for ln in lines:
            f.write(json.dumps(ln) + "\n")
    return sid


_URI_SAFE = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~/:")


def file_uri(path: str) -> str:
    """A file:// URI for an absolute path, as editors write them: /x/y on POSIX, /C:/x/y on Windows.
    Written by hand because urllib is a network module and the tool loads none."""
    p = path.replace(os.sep, "/")
    if not p.startswith("/"):
        p = "/" + p
    return "file://" + "".join(c if c in _URI_SAFE else "".join(f"%{b:02X}" for b in c.encode("utf-8")) for c in p)


def write_agy_db(path: str, rows: list) -> None:
    """rows: [(conversation id, [folders], datetime)]."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    con = sqlite3.connect(path)
    con.execute("""CREATE TABLE `conversation_summaries` (`conversation_id` text,`title` text NOT NULL DEFAULT "",
        `preview` text NOT NULL DEFAULT "",`step_count` integer NOT NULL DEFAULT 0,`last_modified_time` datetime NOT NULL,
        `workspace_uris` text NOT NULL,`status` text NOT NULL DEFAULT "",`last_user_input_time` datetime NOT NULL,
        PRIMARY KEY (`conversation_id`))""")
    for cid, folders, when in rows:
        stamp = when.astimezone(ZoneInfo("UTC")).strftime("%Y-%m-%d %H:%M:%S.123456789+00:00")
        uris = json.dumps([file_uri(f) for f in folders])
        con.execute("insert into conversation_summaries (conversation_id, title, preview, last_modified_time, "
                    "workspace_uris, last_user_input_time) values (?,?,?,?,?,?)",
                    (cid, "Invented title", "Invented preview", stamp, uris, stamp))
    con.commit()
    con.close()


# ---------------------------------------------------------------- people

@dataclass
class DemoProject:
    name: str
    folder: str
    files: list                    # [(path, weight)]
    start: date
    end: date
    activity: float
    manifests: dict = field(default_factory=dict)
    toml: str = ""
    quiet: tuple = ()               # (from, to) with no work
    tags: list = field(default_factory=list)  # [(date, name)]
    lines: tuple = (4, 40)


@dataclass
class DemoPerson:
    slug: str
    name: str
    email: str
    set: str
    tz: str
    projects: list
    seed: int
    work: bool = False
    weekdays_only: bool = False
    claude_rate: float = 0.5
    codex_rate: float = 0.2
    codex_review_share: float = 0.5
    agy_rate: float = 0.0
    claude_models: tuple = ("atlas-7",)
    codex_models: tuple = ("orbit-3",)
    teammate: tuple = ()
    coauthor_rate: float = 0.0
    streak: tuple = ()             # (project index, start date, days)
    party_day: date | None = None


WREN = DemoPerson(
    slug="wren", name="Wren Aldous", email="wren@aldous.example.test", set="tinkerer", tz="Europe/Lisbon", seed=11,
    claude_rate=0.55, codex_rate=0.18, agy_rate=0.08, claude_models=("atlas-7", "atlas-7-mini"),
    codex_models=("orbit-3",), streak=(0, date(2026, 3, 2), 34), party_day=date(2026, 5, 9),
    projects=[
        DemoProject(
            name="Moth Lantern", folder="moth-lantern-game", start=date(2025, 9, 1), end=date(2026, 10, 30), activity=0.34,
            files=[("src/player.gd", 5), ("src/world.gd", 4), ("src/save.gd", 2), ("src/ai.gd", 3),
                   ("ui/components/hud.gd", 2), ("ui/components/menu.gd", 1), ("art/sprites/moth.png", 3),
                   ("art/sprites/lamp.png", 2), ("art/tiles/forest.png", 2), ("levels/forest.json", 3),
                   ("levels/caves.json", 2), ("lore/moths.md", 2), ("lore/keepers.md", 1), ("tests/test_save.gd", 1),
                   ("project.godot", 1), ("README.md", 1)],
            toml='[[project.override]]\nglob = "art/**"\nstats = { Art = 1 }\n'
                 '[[project.override]]\nglob = "levels/**"\nstats = { Worlds = 1 }\n'
                 '[[project.override]]\nglob = "lore/**"\nstats = { Lore = 1 }\n',
            tags=[(date(2026, 6, 20), "v1.0.0")]),
        DemoProject(
            name="Ferry Bot", folder="ferrybot", start=date(2025, 9, 1), end=date(2026, 10, 30), activity=0.22,
            quiet=(date(2026, 1, 31), date(2026, 8, 14)),
            files=[("bot/main.py", 3), ("bot/commands.py", 4), ("bot/schedule.py", 2), ("tests/test_commands.py", 2),
                   ("docs/commands.md", 1), ("Dockerfile", 1), ("deploy/ferrybot.service", 1)],
            toml="stats = { Community = 2, Systems = 1 }\n"),
        DemoProject(
            name="Palette Press", folder="palette-press", start=date(2026, 2, 1), end=date(2026, 10, 30), activity=0.24,
            manifests={"pyproject.toml": '[project]\nname = "palette-press"\nversion = "0.3.0"\n'
                                         'dependencies = ["pillow"]\n\n[project.scripts]\npalette-press = "palette_press.cli:main"\n'},
            files=[("palette_press/cli.py", 3), ("palette_press/quantize.py", 4), ("palette_press/export.py", 2),
                   ("web/styles/site.css", 1), ("web/index.html", 1), ("tests/test_quantize.py", 2), ("README.md", 1)]),
        DemoProject(
            name="Sketchbook", folder="sketch-site", start=date(2025, 10, 1), end=date(2026, 10, 30), activity=0.1,
            files=[("index.html", 2), ("styles/main.css", 2), ("gallery/heron.png", 2), ("gallery/fen.png", 2),
                   ("posts/winter.md", 1), ("posts/kites.md", 1)],
            toml='[[project.override]]\nglob = "gallery/**"\nstats = { Art = 1 }\n'
                 '[[project.override]]\nglob = "posts/**"\nstats = { Lore = 1 }\n'),
    ],
)

TOBI = DemoPerson(
    slug="tobi", name="Tobi Marsh", email="tobi@ledgerworks.example.test", set="builder", tz="America/Chicago", seed=23,
    work=True, weekdays_only=True, claude_rate=0.5, codex_rate=0.3, codex_review_share=0.6,
    claude_models=("atlas-7",), codex_models=("orbit-3", "orbit-3-fast"),
    teammate=("Rae Quill", "rae@ledgerworks.example.test"), coauthor_rate=0.12,
    projects=[
        DemoProject(
            name="Ledger Service", folder="ledger-svc", start=date(2025, 9, 1), end=date(2026, 10, 30), activity=0.55,
            files=[("app/accounts.py", 4), ("app/transfers.py", 4), ("app/api.py", 3), ("app/auth.py", 2),
                   ("migrations/0001_init.sql", 1), ("migrations/0002_ledger.sql", 2), ("tests/test_transfers.py", 3),
                   ("tests/test_api.py", 2), ("Dockerfile", 1), (".github/workflows/ci.yml", 1), ("deploy/deploy.sh", 2),
                   ("docs/runbook.md", 1), ("docs/adr-001.md", 1), ("CHANGELOG.md", 1)],
            tags=[(date(2026, 1, 15), "v1.0.0"), (date(2026, 7, 1), "v1.2.0")], lines=(6, 60)),
        DemoProject(
            name="Ops Console", folder="ops-console", start=date(2025, 11, 3), end=date(2026, 10, 30), activity=0.4,
            manifests={"cli/package.json": '{"name": "opsctl", "version": "1.0.0", "bin": {"opsctl": "dist/main.js"}}\n',
                       "web/package.json": '{"name": "web", "version": "1.0.0"}\n'},
            files=[("web/src/components/Table.tsx", 3), ("web/src/components/Chart.tsx", 2), ("web/src/pages/index.tsx", 2),
                   ("web/src/styles/app.css", 2), ("web/src/components/Table.test.tsx", 1), ("api/src/routes.ts", 3),
                   ("api/src/db.ts", 2), ("cli/src/main.ts", 2), ("cli/src/format.ts", 1), ("shared/src/types.ts", 1)],
            toml='[[project.part]]\npath = "web"\n[[project.part]]\npath = "api"\n'
                 '[[project.part]]\npath = "cli"\n[[project.part]]\npath = "shared"\n', lines=(6, 60)),
        DemoProject(
            name="Metrics Pipeline", folder="metrics-pipeline", start=date(2026, 3, 2), end=date(2026, 10, 30), activity=0.3,
            manifests={"pyproject.toml": '[project]\nname = "metrics-pipeline"\nversion = "0.1.0"\n'
                                         'dependencies = ["pandas>=2", "duckdb"]\n'},
            files=[("pipeline/load.py", 3), ("pipeline/transform.py", 3), ("sql/daily.sql", 2), ("sql/weekly.sql", 1),
                   ("notebooks/explore.ipynb", 1), ("tests/test_transform.py", 2), ("scripts/backfill.sh", 1)],
            lines=(6, 60)),
    ],
)

PEOPLE = (WREN, TOBI)


def _pick(rng: random.Random, files: list, k: int) -> list:
    paths = [p for p, _ in files]
    weights = [w for _, w in files]
    chosen = []
    for _ in range(k * 3):
        if len(chosen) >= k:
            break
        p = rng.choices(paths, weights)[0]
        if p not in chosen:
            chosen.append(p)
    return chosen


def make_person(base: str, person: DemoPerson) -> str:
    """Write repos, harness logs and a profile for one invented person. Returns the profile path."""
    rng = random.Random(person.seed)
    tz = ZoneInfo(person.tz)
    me = (person.name, person.email)
    home = os.path.join(base, person.slug)
    code = os.path.join(home, "code")
    claude_dir = os.path.join(home, "agents", "claude", "projects")
    codex_dir = os.path.join(home, "agents", "codex", "sessions")
    agy_db = os.path.join(home, "agents", "agy", "conversation_summaries.db")
    os.makedirs(claude_dir, exist_ok=True)
    os.makedirs(codex_dir, exist_ok=True)
    agy_rows = []

    def at(d: date, hour: int, minute: int = 0) -> datetime:
        return datetime.combine(d, time(0, 0), tz) + timedelta(hours=hour, minutes=minute)

    for pi, proj in enumerate(person.projects):
        root = os.path.join(code, proj.folder)
        repo = RepoWriter(root)
        first = at(proj.start, 10)
        init_files = {"README.md": f"# {proj.folder}\n"}
        init_files.update(proj.manifests)
        repo.commit(first, me, init_files)
        repo.content.update(init_files)
        tags = dict(proj.tags)
        d = proj.start + timedelta(days=1)
        while d <= proj.end:
            streak = person.streak and person.streak[0] == pi and person.streak[1] <= d < person.streak[1] + timedelta(
                days=person.streak[2])
            quiet = proj.quiet and proj.quiet[0] <= d <= proj.quiet[1]
            weekday_ok = not person.weekdays_only or d.weekday() < 5
            forced = d == person.party_day and pi == 0
            active = forced or streak or (not quiet and weekday_ok and rng.random() < proj.activity)
            tag = tags.pop(d, "") if d in tags else ""
            if tag and not active:
                active = True
            if active:
                agent_only = (not forced) and (not tag) and rng.random() < 0.12
                n_commits = 0 if agent_only else rng.choice((1, 1, 1, 2, 2, 3))
                touched = []
                for c in range(n_commits):
                    hour = rng.choice((9, 10, 11, 14, 15, 16, 20, 22, 25))  # 25 = 1am next morning
                    when = at(d, hour, rng.randrange(60))
                    files = _pick(rng, proj.files, rng.choice((1, 1, 2, 2, 3, 4)))
                    touched += files
                    changes = {f: rng.randint(*proj.lines) for f in files}
                    author, co = me, []
                    if person.teammate and rng.random() < person.coauthor_rate:
                        author, co = person.teammate, [me]
                    repo.touch(when, author, changes, co, tag if c == n_commits - 1 else "")
                if tag and n_commits == 0:
                    repo.touch(at(d, 12), me, {proj.files[0][0]: 3}, (), tag)
                if forced or rng.random() < person.claude_rate or agent_only:
                    start = at(d, rng.choice((10, 13, 21)), rng.randrange(60))
                    pool = list(dict.fromkeys(touched[:2] + _pick(rng, proj.files, 2)))
                    edits = [(start + timedelta(minutes=3 + i * 4), os.path.join(root, f), "Edit") for i, f in enumerate(pool)]
                    sub = [(start + timedelta(minutes=30), os.path.join(root, pool[0]))] if rng.random() < 0.15 else []
                    write_claude_session(claude_dir, root, start, rng.choice(person.claude_models), edits, rng,
                                         subagent_edits=sub)
                if forced or rng.random() < person.codex_rate:
                    start = at(d, rng.choice((11, 16, 23)), rng.randrange(60))
                    review = (not forced) and rng.random() < person.codex_review_share
                    edits = [] if review else [(start + timedelta(minutes=5 + i * 3), os.path.join(root, f))
                                               for i, f in enumerate(_pick(rng, proj.files, 2))]
                    write_codex_session(codex_dir, root, start, rng.choice(person.codex_models), edits, rng,
                                        originator="codex_exec" if rng.random() < 0.8 else "codex_cli")
                if forced or (person.agy_rate and rng.random() < person.agy_rate):
                    agy_rows.append((_uuid(rng), [root], at(d, 18, rng.randrange(60))))
            d += timedelta(days=1)
        if person.slug == "tobi" and pi == 0:
            bot = ("renovate[bot]", "bot@renovate.example.test")
            for k in range(6):
                repo.touch(at(date(2026, 2, 2) + timedelta(days=7 * k), 3), bot, {"requirements.txt": 1})
        repo.write()

    scratch = os.path.join(home, "scratch", "notes")
    os.makedirs(scratch, exist_ok=True)
    for k in range(5):
        start = at(date(2026, 4, 6) + timedelta(days=9 * k), 15)
        write_claude_session(claude_dir, scratch, start, person.claude_models[0],
                             [(start + timedelta(minutes=2), os.path.join(scratch, "todo.txt"), "Write")], rng)
    if agy_rows:
        write_agy_db(agy_db, agy_rows)

    q = toml_string  # every value goes in as a TOML string, so Windows paths like C:\\Users parse
    lines = [
        f"name = {q(person.name)}", f"set = {q(person.set)}", f"timezone = {q(person.tz)}", "rollover_hour = 4",
        f"work = {'true' if person.work else 'false'}", "",
        "[identity]", f"emails = [{q(person.email)}]", f"names = [{q(person.name)}]", "",
        "[harnesses]", "claude = true", "codex = true", f"agy = {'true' if agy_rows else 'false'}",
        f"claude_dir = {q(claude_dir)}", f"codex_dir = {q(codex_dir)}", f"agy_db = {q(agy_db)}", "",
    ]
    if person.work:
        lines += ["[card]", "allow = true", ""]
    for proj in person.projects:
        lines += ["[[project]]", f"name = {q(proj.name)}", f"roots = [{q(os.path.join(code, proj.folder))}]"]
        if proj.toml:
            lines.append(proj.toml.rstrip("\n"))
        lines.append("")
    path = os.path.join(home, "profile.toml")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return path


def run_demo(out: str, people=PEOPLE, built_at: str = "demo build") -> list:
    """Build both invented people's sheets into out/<slug>/. A first build as of six weeks earlier
    gives the second one an earlier saved sheet, so the What changed panel has something to say."""
    from .build import build
    from .profile import load_profile

    work = tempfile.mkdtemp(prefix="tinkerprint-demo-")
    results = []
    try:
        for person in people:
            prof = load_profile(make_person(work, person))
            home = os.path.join(work, "data", person.slug)
            dest = os.path.join(out, person.slug)
            build(prof, dest, as_of=date(2026, 9, 15), home=home, built_at=built_at)
            results.append((person.name, build(prof, dest, home=home, built_at=built_at)))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return results
