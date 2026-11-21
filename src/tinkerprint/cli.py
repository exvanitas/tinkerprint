"""Command line: build, audit, init, demo."""
from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime

from . import __version__
from .art import export_pack, load_pack
from .audit import audit_card
from .build import build, check_dirs, default_out, last_out, parse_season
from .profile import ProfileError, load_profile
from .datadir import data_home
from .timeutil import parse_day

STARTER = '''# tinkerprint profile. Everything here stays on this machine.
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
    out = args.out or default_out(home, profile)
    if not args.out:
        check_dirs(profile, [out])
    pack = load_pack(args.art_pack) if args.art_pack else None
    res = build(profile, out, season, as_of, home, built_at=_now(), pack=pack)
    s = res["sheet"]
    cls = (s.get("class") or {}).get("name", "Unclassed")
    print(f"{profile.name}: level {s['history']['level']}, {cls}, {s['season_totals']['active_days']} active days "
          f"in {s['season']['label'].lower()}.")
    for k in ("html", "card", "portrait", "json"):
        if k in res["paths"]:
            print(f"  {k:<5} {res['paths'][k]}")
    if not s["card"].get("enabled"):
        print("  card  off: " + s["card"].get("reason", ""))
    for line in unassigned_lines(res["sheet"], res["local"], args.list_unassigned):
        print(line)
    for w in res.get("warnings", []):
        print("Warning: " + w)
    return 0


def _n(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def unassigned_lines(sheet: dict, local: dict, limit: int) -> list:
    """Terminal-only listing of folders outside every root. The totals are the sheet's own."""
    un = sheet["unassigned"]
    if not (un["sessions"] or un["folders"] or un["edits"]):
        return []
    out = [f"Unassigned: {_n(un['sessions'], 'session')} in {_n(un['folders'], 'folder')}, "
           f"{_n(un['edits'], 'changed file')}, outside every root. Not scored."]
    sessions = local.get("unassigned_folders", [])
    out += [f"  {n:>4}  {folder}" for folder, n in sessions[:limit]]
    edits = [f for f in local.get("unassigned_edit_folders", []) if f not in dict(sessions)]
    out += [f"        {folder}" for folder in edits[:limit]]
    hidden = max(0, len(sessions) - limit) + max(0, len(edits) - limit)
    if hidden:
        out.append(f"  ... {hidden} more. Use --list-unassigned N to see them.")
    return out


def cmd_audit(args) -> int:
    try:
        profile = load_profile(args.profile)
    except (ProfileError, OSError) as e:
        if not args.out:
            raise
        # An explicit card folder can be audited without its profile.
        print(f"Profile not readable ({e}). Auditing {args.out} alone.")
        profile = None
    if args.out:
        out = args.out
    else:
        home = data_home(args.data_dir)
        out = last_out(home, profile) or default_out(home, profile)
    print("\n".join(audit_card(out, profile)))
    return 0


def cmd_init(args) -> int:
    path = args.out
    if os.path.exists(path):
        print(f"{path} already exists. Not overwriting it.", file=sys.stderr)
        return 1
    with open(path, "w", encoding="utf-8") as f:
        f.write(STARTER.format(tz=_local_tz()))
    print(f"Wrote {path}. Edit it, then run: tinkerprint build --profile {path}")
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


def cmd_gallery(args) -> int:
    from .gallery import write_gallery
    if args.export_pack:
        export_pack(args.export_pack)
        print(f"  pack  {args.export_pack}")
        return 0
    pack = load_pack(args.art_pack) if args.art_pack else None
    paths = write_gallery(args.out, pack, png=args.png)
    for p in paths:
        print(f"  {p}")
    return 0


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="tinkerprint", description="An RPG stat sheet from your git history and coding-agent logs. Local only.")
    p.add_argument("--version", action="version", version=f"tinkerprint {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="build sheet.html, card.svg and sheet.json for a profile")
    b.add_argument("--profile", required=True)
    b.add_argument("--season", help="FROM:TO dates, for example 2025-01-01:2025-06-30. Default: all history")
    b.add_argument("--as-of", help="ignore everything after this date (YYYY-MM-DD)")
    b.add_argument("--out", help="output folder. Default: the data folder")
    b.add_argument("--data-dir", help="cache and history folder. Default: $XDG_DATA_HOME/tinkerprint")
    b.add_argument("--list-unassigned", type=int, default=10, metavar="N", help="unassigned folders to list")
    b.add_argument("--art-pack", metavar="PACK.json", help="draw with this art pack. Default: the built-in pack")
    b.set_defaults(func=cmd_build)

    a = sub.add_parser("audit", help="print every text string in the built card.svg")
    a.add_argument("--profile", required=True)
    a.add_argument("--out", help="the build folder to audit. Default: this profile's last build")
    a.add_argument("--data-dir")
    a.set_defaults(func=cmd_audit)

    i = sub.add_parser("init", help="write a commented starter profile")
    i.add_argument("--out", default="tinkerprint.toml")
    i.set_defaults(func=cmd_init)

    d = sub.add_parser("demo", help="build sheets for two invented people")
    d.add_argument("--out", default="tinkerprint-demo")
    d.set_defaults(func=cmd_demo)

    g = sub.add_parser("gallery", help="write one page with every portrait, familiar, icon and a few banners")
    g.add_argument("--out", default="tinkerprint-gallery")
    g.add_argument("--art-pack", metavar="PACK.json", help="show this art pack instead of the built-in one")
    g.add_argument("--png", action="store_true", help="also write every picture as a PNG")
    g.add_argument("--export-pack", metavar="PACK.json", help="write the built-in pack as JSON to start your own")
    g.set_defaults(func=cmd_gallery)
    return p


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.func(args)
    except (ProfileError, ValueError, OSError) as e:
        print(f"tinkerprint: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
