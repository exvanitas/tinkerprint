"""Command line: build, audit, init, forget, demo, gallery."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfoNotFoundError

from . import __version__
from .art import export_pack, load_pack
from .audit import audit
from .build import build, check_dirs, default_out, last_out, parse_season
from .profile import ProfileError, load_profile
from .datadir import data_home
from .keys import adopt
from .timeutil import parse_day

STARTER = '''# tinkerprint profile. Everything here stays on this machine.
# Keep this file outside your repos and never commit it: it lists your folders and emails.
# One person can keep several profiles, for example a day job and personal projects.

{name_line}# shown on the sheet, and on the card unless [card] name is set
set = "builder"               # builder or tinkerer
{tz_line}# IANA name like "Europe/Berlin", or an offset like "+02:00"
{tz_note}rollover_hour = 4             # a day runs from this hour to the next. 1am counts toward the day before.
work = false                  # a work profile makes no card unless [card] enabled = true
# milestones = "milestones.txt"   # optional: one "YYYY-MM-DD what happened" per line

[identity]
# Commits match you by email or name. Globs work. Co-authored commits count.
# Commits made on GitHub's website (merges, edits, suggestions) use your noreply address,
# like 12345+you@users.noreply.github.com. Add it here if you work that way.
# A build lists the authors it saw in a root where none of these matched.
{ident_note}emails = [{emails}]
names = [{names}]
# bots = ["release-robot*"]   # extra bot authors to drop. [bot] authors always drop.

[harnesses]
claude = true                 # ~/.claude/projects
codex = true                  # ~/.codex/sessions
agy = false                   # experimental, presence only

[card]
# enabled = false             # on by default, off by default when work = true
# name = "your-handle"        # the card shows this instead of name. The sheet keeps name.
# hide = ["party", "level", "achievements"]  # any of these stay off the card
# show = ["dates", "projects"]  # exact dates and project names stay off the card unless listed

[look]
# The portrait. Hair, eyes and expression left unset are picked from the name the card shows.
# presentation = "neutral"    # neutral, man or woman
# skin = "light"              # light, medium or deep. Unset is the art pack's own.
# hair = "bob"                # neutral: bob, curtains, shag. man: crop, curls, side part. woman: braid, waves, chignon
# eyes = "honey"              # honey, moss, slate, chestnut, plum or lagoon
# expression = "smile"        # smile, grin, calm, determined, joy or curious

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

PLACEHOLDER_NAME = "Your Name"
PLACEHOLDER_EMAIL = "you@example.test"
DEFAULT_PROFILE = "tinkerprint.toml"


def _setting(key: str, value: str) -> str:
    """'key = value' padded so the comment after it lines up with the rest of the starter."""
    line = f"{key} = {value}"
    return line.ljust(30) if len(line) < 30 else line + " "


def starter(name: str = "", email: str = "", tz: str = "UTC", tz_guessed: bool = False) -> str:
    """The commented starter profile. name and email come from git config when set."""
    from .profile import toml_string
    filled = [w for w, v in (("name", name), ("email", email)) if v]
    note = f"# {' and '.join(filled).capitalize()} filled in from your git config.\n" if filled else ""
    tz_note = ("# This is your clock's current UTC offset, so it ignores daylight saving.\n"
               "# Replace it with your IANA name, like \"Europe/Berlin\".\n") if tz_guessed else ""
    return STARTER.format(
        name_line=_setting("name", toml_string(name or PLACEHOLDER_NAME)),
        tz_line=_setting("timezone", toml_string(tz)),
        tz_note=tz_note,
        ident_note=note,
        emails=toml_string(email or PLACEHOLDER_EMAIL),
        names=toml_string(name or PLACEHOLDER_NAME),
    )


def _profile_path(args, quiet: bool = False) -> str | None:
    """--profile, else ./tinkerprint.toml when it exists, else None."""
    if args.profile:
        return args.profile
    if os.path.isfile(DEFAULT_PROFILE):
        if not quiet:
            print(f"Profile: ./{DEFAULT_PROFILE}")
        return DEFAULT_PROFILE
    return None


def _no_profile() -> ProfileError:
    return ProfileError(f"no profile given and no {DEFAULT_PROFILE} in this folder. Pass --profile PATH, "
                        f"or run 'tinkerprint init' to write {DEFAULT_PROFILE} here")


def local_tz(etc: str = "/etc", now: datetime | None = None) -> tuple:
    """(time zone for the starter, guessed). An IANA name from /etc when there is one. Elsewhere,
    as on Windows, the clock's current UTC offset in quarter hours, which the profile accepts but
    which ignores daylight saving, so the starter says to replace it."""
    try:
        with open(os.path.join(etc, "timezone"), encoding="utf-8") as f:
            name = f.read().strip()
            if name:
                return name, False
    except OSError:
        pass
    try:
        link = os.readlink(os.path.join(etc, "localtime"))
        if "zoneinfo/" in link:
            return link.split("zoneinfo/", 1)[1], False
    except OSError:
        pass
    off = (now or datetime.now().astimezone()).utcoffset()
    minutes = round((off.total_seconds() if off else 0) / 900) * 15
    if not minutes:
        return "UTC", True
    sign = "-" if minutes < 0 else "+"
    h, m = divmod(abs(minutes), 60)
    return f"{sign}{h:02d}:{m:02d}", True


def _now() -> str:
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %Z").strip()


def cmd_build(args) -> int:
    path = _profile_path(args)
    if path is None:
        raise _no_profile()
    profile = load_profile(path)
    season = parse_season(args.season)
    as_of = parse_day(args.as_of) if args.as_of else None
    home = data_home(args.data_dir)
    check_dirs(profile, [home])
    note = adopt(home, profile)
    if note:
        print(note)
    out = args.out or default_out(home, profile)
    if not args.out:
        check_dirs(profile, [out])
    pack = load_pack(args.art_pack) if args.art_pack else None
    res = build(profile, out, season, as_of, home, built_at=_now(), pack=pack)
    s = res["sheet"]
    cls = (s.get("class") or {}).get("name", "Unclassed")
    print(f"{profile.name}: level {s['history']['level']}, {cls}, {s['season_totals']['active_days']} active days "
          f"in {s['season']['label'].lower()}.")
    for line in output_lines(res):
        print(line)
    print(look_line(res["sheet"], profile, pack))
    for line in unassigned_lines(res["sheet"], res["local"], args.list_unassigned):
        print(line)
    health = res["local"].get("health") or []
    if health:
        print("Readers, over every log in each harness folder:")
        for line in health:
            print("  " + line)
    for w in res.get("warnings", []):
        print("Warning: " + w)
    return 0


# What build prints for each output, in this order. card.png is the file to post.
OUTPUTS = (("html", "sheet", ""), ("card_png", "card", "  (share this one)"), ("card", "card", ""),
           ("portrait", "portrait", ""), ("portrait_gif", "portrait", ""), ("json", "json", ""))


def output_lines(res: dict) -> list:
    """The written files, then what the card shows and its alt text, or why there is no card."""
    from .render_card import shows, visible
    paths, card = res["paths"], res["sheet"]["card"]
    out = [f"  {label:<8} {paths[k]}{note}" for k, label, note in OUTPUTS if k in paths]
    if not card.get("enabled"):
        out.append("  card     off: " + card.get("reason", ""))
        return out
    out.append("  shows    " + shows(card))
    out.append("  alt      " + visible(card)["alt"])
    return out


def look_line(sheet: dict, profile, pack: dict | None = None) -> str:
    """The look in use, and which parts came from the name."""
    from .art import default_pack
    from .look import describe
    return describe(sheet["look"], pack or default_pack(), from_card_name=bool(profile.card_name))


def demo_look_line(sheet: dict) -> str:
    """The Look line for a demo person, who has no profile file: a handle shows as a card name unlike their own."""
    from .art import default_pack
    from .look import describe
    from .look import public_name
    own = public_name(sheet["profile"]["name"])
    handle = (sheet.get("card") or {}).get("name", own) != own
    return describe(sheet["look"], default_pack(), from_card_name=handle)


def _n(n: int, word: str) -> str:
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def unassigned_lines(sheet: dict, local: dict, limit: int = 0) -> list:
    """Terminal-only note on folders outside every root. The totals are the sheet's own.
    Folder names are listed only when asked for, so a build on a shared screen shows none."""
    un = sheet["unassigned"]
    if not (un["sessions"] or un["folders"] or un["edits"]):
        return []
    limit = max(0, limit)
    out = [f"Unassigned: {_n(un['sessions'], 'session')} in {_n(un['folders'], 'folder')}, "
           f"{_n(un['edits'], 'changed file')}, outside every root. Not scored."]
    sessions = local.get("unassigned_folders", [])
    out += [f"  {n:>4}  {folder}" for folder, n in sessions[:limit]]
    edits = [f for f in local.get("unassigned_edit_folders", []) if f not in dict(sessions)]
    out += [f"        {folder}" for folder in edits[:limit]]
    hidden = max(0, len(sessions) - limit) + max(0, len(edits) - limit)
    if hidden and not limit:
        out[0] += " Use --list-unassigned N to list the folders."
    elif hidden:
        out.append(f"  ... {hidden} more. Use --list-unassigned N to see them.")
    return out


def cmd_audit(args) -> int:
    path = _profile_path(args)
    if path is None and not args.out:
        raise _no_profile()
    profile = None
    if path is not None:
        try:
            profile = load_profile(path)
        except (ProfileError, OSError) as e:
            if not args.out:
                raise
            # An explicit card folder can be audited without its profile.
            print(f"Profile not readable ({e}). Auditing {args.out} alone.")
    if args.out:
        out = args.out
    else:
        home = data_home(args.data_dir)
        adopt(home, profile, write=False)
        out = last_out(home, profile) or default_out(home, profile)
    pack = load_pack(args.art_pack) if args.art_pack else None
    lines, clean = audit(out, profile, pack)
    print("\n".join(lines))
    # Non-zero when any card file is missing, malformed or not certified, so a script can stop a share.
    return 0 if clean else 1


def cmd_init(args) -> int:
    from .datadir import inside_repo_or_root
    from .readers.git import global_config
    path = args.out
    if os.path.exists(path):
        print(f"{path} already exists. Not overwriting it.", file=sys.stderr)
        return 1
    name, email = global_config("user.name"), global_config("user.email")
    tz, guessed = local_tz()
    text = starter(name, email, tz, guessed)
    with open(path, "x", encoding="utf-8") as f:
        f.write(text)
    print(f"Wrote {path}.")
    filled = [w for w, v in (("name", name), ("email", email)) if v]
    if filled:
        print(f"  {' and '.join(filled).capitalize()} came from your git config. Add any other emails you commit with.")
    else:
        print("  Put your name and the emails you commit with under [identity].")
    print("  Set the [[project]] roots to your own folders.")
    if guessed:
        print(f"  The time zone is your clock's offset ({tz}). Replace it with an IANA name like \"Europe/Berlin\".")
    if inside_repo_or_root(os.path.dirname(os.path.abspath(path))) == "it is inside a git repository":
        print(f"  {path} is inside a git repository. Move it out so it is never committed: it lists your folders "
              "and emails.")
    same = os.path.abspath(path) == os.path.abspath(DEFAULT_PROFILE)
    print("Then run: tinkerprint build" + ("" if same else f" --profile {path}"))
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
        for line in output_lines(res):
            print(line)
        print(demo_look_line(s))
    return 0


def cmd_forget(args) -> int:
    from .forget import forget
    from .keys import lookup, owner
    home = data_home(args.data_dir)
    if args.all:
        key = None
    else:
        path = _profile_path(args, quiet=True)
        if path is None:
            raise ProfileError(f"forget needs --profile PATH or --all, or a {DEFAULT_PROFILE} in this folder")
        key = lookup(home, path)
        print(f"Profile: {path}")
        if key is None:
            print(f"Nothing to forget for it: its saved sheets went with the profile file now at {owner(home, path)}. "
                  "Forget that one to delete them.")
            return 0
    for line in forget(home, key, args.yes):
        print(line)
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

    b = sub.add_parser("build", help="build sheet.html, sheet.json and the card files for a profile")
    b.add_argument("--profile", help=f"the profile to build. Default: ./{DEFAULT_PROFILE} when it exists")
    b.add_argument("--season", help="FROM:TO dates, for example 2025-01-01:2025-06-30. Default: all history")
    b.add_argument("--as-of", help="ignore everything after this date (YYYY-MM-DD)")
    b.add_argument("--out", help="output folder. Default: the data folder")
    b.add_argument("--data-dir", help="cache and history folder. Default: $XDG_DATA_HOME/tinkerprint")
    b.add_argument("--list-unassigned", type=int, default=0, metavar="N",
                   help="list up to N folders outside every root. Default: totals only")
    b.add_argument("--art-pack", metavar="PACK.json", help="draw with this art pack. Default: the built-in pack")
    b.set_defaults(func=cmd_build)

    a = sub.add_parser("audit", help="print every text string in the built card.svg, and check card.png and the portraits. Exits 1 unless every card file is certified")
    a.add_argument("--profile", help=f"Default: ./{DEFAULT_PROFILE} when it exists")
    a.add_argument("--out", help="the build folder to audit. Default: this profile's last build")
    a.add_argument("--data-dir")
    a.add_argument("--art-pack", metavar="PACK.json", help="the art pack the card was built with, if not the built-in one")
    a.set_defaults(func=cmd_audit)

    f = sub.add_parser("forget", help="delete the cache and saved sheets for a profile, or everything")
    which = f.add_mutually_exclusive_group()
    which.add_argument("--profile", help=f"the profile to forget. Default: ./{DEFAULT_PROFILE} when it exists. "
                                          "It need not exist any more")
    which.add_argument("--all", action="store_true", help="everything tinkerprint keeps in the data folder")
    f.add_argument("--data-dir")
    f.add_argument("--yes", action="store_true", help="delete. Without it, forget only lists what it would delete")
    f.set_defaults(func=cmd_forget)

    i = sub.add_parser("init", help="write a commented starter profile")
    i.add_argument("--out", default=DEFAULT_PROFILE)
    i.set_defaults(func=cmd_init)

    d = sub.add_parser("demo", help="build sheets for two invented people")
    d.add_argument("--out", default="tinkerprint-demo")
    d.set_defaults(func=cmd_demo)

    g = sub.add_parser("gallery", help="write one page with every class, face, room, pin, trinket and party instrument")
    g.add_argument("--out", default="tinkerprint-gallery")
    g.add_argument("--art-pack", metavar="PACK.json", help="show this art pack instead of the built-in one")
    g.add_argument("--png", action="store_true", help="also write every picture as a PNG")
    g.add_argument("--export-pack", metavar="PACK.json", help="write the built-in pack as JSON to start your own")
    g.set_defaults(func=cmd_gallery)
    return p


def _os_message(e: OSError) -> str:
    """An OSError in plain words: what failed and where, never a bare errno."""
    what = e.strerror or str(e)
    where = e.filename if e.filename is not None else ""
    return f"{what}: {where}" if where else what


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        return args.func(args)
    except ProfileError as e:
        print(f"tinkerprint: {e}", file=sys.stderr)
        return 2
    except ZoneInfoNotFoundError as e:  # a KeyError, so it comes before the general cases
        print(f"tinkerprint: a time zone is missing from this Python's time-zone data ({e}). "
              "Install the tzdata package, or use an offset like \"+02:00\".", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as e:
        tool = os.path.basename(str(e.cmd[0])) if isinstance(e.cmd, (list, tuple)) and e.cmd else "a command"
        print(f"tinkerprint: {tool} failed with exit code {e.returncode}.", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"tinkerprint: {_os_message(e)}", file=sys.stderr)
        return 2
    except ValueError as e:
        print(f"tinkerprint: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("tinkerprint: stopped.", file=sys.stderr)
        return 130
    except Exception as e:  # anything else is a bug: say so in one line, the traceback only on request
        if os.environ.get("TINKERPRINT_DEBUG"):
            raise
        print(f"tinkerprint: unexpected error ({type(e).__name__}: {e}). This is a bug. "
              "Set TINKERPRINT_DEBUG=1 to see the traceback.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
