"""Command line: build, audit, init, demo."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

from . import __version__
from .audit import audit_lines
from .build import build, compute, parse_season
from .profile import ProfileError, load_profile
from .snapshot import data_home
from .timeutil import parse_day

STARTER = '''# statsheet profile. Everything here stays on this machine.
# One person can keep several profiles, for example a day job and personal projects.

name = "Your Name"            # shown on the sheet and the card
set = "builder"               # builder or tinkerer
timezone = "{tz}"             # IANA name like "Europe/Berlin", or an offset like "+02:00"
rollover_hour = 4             # a day runs from this hour to the next. 1am counts toward the day before.
work = false                  # a work profile never makes a card unless [card] allow = true
# milestones = "milestones.txt"   # optional: one "YYYY-MM-DD what happened" per line

[identity]
# Commits match you by email or name. Globs work. Co-authored commits count.
emails = ["you@example.test"]
names = ["Your Name"]
# bots = ["release-robot*"]   # extra bot authors to drop. [bot] authors always drop.

[harnesses]
claude = true                 # ~/.claude/projects
codex = true                  # ~/.codex/sessions
agy = false                   # experimental, presence only

[card]
# allow = true                # needed only when work = true
# show = ["dates", "projects"]  # exact dates and project names stay off the card unless listed

# One [[project]] per project. A path belongs to the longest matching root.
# The name is what the sheet shows. Roots never leave this machine.
[[project]]
name = "My Project"
roots = ["~/code/my-project"]
# stats = {{ Tools = 1 }}       # treat the whole project as one stat (weights split it)

# Parts are subfolders of one repo. They keep their own manifests and weights,
# and the project still counts as one project on a day.
# [[project.part]]
# path = "web"
# stats = {{ Interface = 1 }}

# Overrides win over every other rule. Globs are relative to the project root.
# In the tinkerer set, Art, Worlds, Lore and Community come only from these hand tags.
# [[project.override]]
# glob = "art/**"
# stats = {{ Art = 1 }}
'''


def _local_tz() -> str:
    try:
        with open("/etc/timezone", encoding="utf-8") as f:
            name = f.read().strip()
            if name:
                return name
    except OSError:
        pass
    try:
        link = os.readlink("/etc/localtime")
        if "zoneinfo/" in link:
            return link.split("zoneinfo/", 1)[1]
    except OSError:
        pass
    return "UTC"


def _now() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z").strip()


def cmd_build(args) -> int:
    profile = load_profile(args.profile)
    season = parse_season(args.season)
    as_of = parse_day(args.as_of) if args.as_of else None
    home = data_home(args.data_dir)
    out = args.out or os.path.join(home, "sheets", profile.id)
    res = build(profile, out, season, as_of, home, built_at=_now())
    s = res["sheet"]
    cls = (s.get("class") or {}).get("name", "Unclassed")
    print(f"{profile.name}: level {s['history']['level']}, {cls}, {s['season_totals']['active_days']} active days "
          f"in {s['season']['label'].lower()}.")
    for k in ("html", "card", "json"):
        if k in res["paths"]:
            print(f"  {k:<5} {res['paths'][k]}")
    if not s["card"].get("enabled"):
        print("  card  off: " + s["card"].get("reason", ""))
    un = res["local"]["unassigned_folders"]
    if un:
        print(f"Unassigned: {sum(n for _, n in un)} sessions in {len(un)} folders outside every root. Not scored.")
        for folder, n in un[: args.list_unassigned]:
            print(f"  {n:>4}  {folder}")
        if len(un) > args.list_unassigned:
            print(f"  ... {len(un) - args.list_unassigned} more. Use --list-unassigned N to see them.")
    return 0


def cmd_audit(args) -> int:
    profile = load_profile(args.profile)
    sheet, _, _, _ = compute(profile, parse_season(args.season), None, data_home(args.data_dir))
    print("\n".join(audit_lines(sheet, profile.id)))
    return 0


def cmd_init(args) -> int:
    path = args.out
    if os.path.exists(path):
        print(f"{path} already exists. Not overwriting it.", file=sys.stderr)
        return 1
    with open(path, "w", encoding="utf-8") as f:
        f.write(STARTER.format(tz=_local_tz()))
    print(f"Wrote {path}. Edit it, then run: statsheet build --profile {path}")
    return 0


def cmd_demo(args) -> int:
    from .demo import run_demo
    out = os.path.abspath(args.out)
    results = run_demo(out)
    for name, res in results:
        s = res["sheet"]
        cls = (s.get("class") or {}).get("name", "Unclassed")
        lit = sum(1 for r in s["stats"] if r["points"] > 0)
        print(f"{name}: level {s['history']['level']}, {cls}, {lit} stats with points.")
        for k in ("html", "card", "json"):
            if k in res["paths"]:
                print(f"  {k:<5} {res['paths'][k]}")
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="statsheet", description="An RPG stat sheet from your git history and coding-agent logs. Local only.")
    p.add_argument("--version", action="version", version=f"statsheet {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="build sheet.html, card.svg and sheet.json for a profile")
    b.add_argument("--profile", required=True)
    b.add_argument("--season", help="FROM:TO dates, for example 2025-01-01:2025-06-30. Default: all history")
    b.add_argument("--as-of", help="ignore everything after this date (YYYY-MM-DD)")
    b.add_argument("--out", help="output folder. Default: the data folder")
    b.add_argument("--data-dir", help="cache and snapshot folder. Default: $XDG_DATA_HOME/statsheet")
    b.add_argument("--list-unassigned", type=int, default=10, metavar="N", help="unassigned folders to list")
    b.set_defaults(func=cmd_build)

    a = sub.add_parser("audit", help="print every string the share card would hold")
    a.add_argument("--profile", required=True)
    a.add_argument("--season")
    a.add_argument("--data-dir")
    a.set_defaults(func=cmd_audit)

    i = sub.add_parser("init", help="write a commented starter profile")
    i.add_argument("--out", default="statsheet.toml")
    i.set_defaults(func=cmd_init)

    d = sub.add_parser("demo", help="build sheets for two invented people")
    d.add_argument("--out", default="statsheet-demo")
    d.set_defaults(func=cmd_demo)
    return p


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.func(args)
    except (ProfileError, ValueError, OSError) as e:
        print(f"statsheet: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
