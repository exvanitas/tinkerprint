"""Achievements: generic rules over events and git, the same for everyone. Each is dated."""
from __future__ import annotations

import re
from collections import defaultdict
from datetime import date, timedelta

from .timeutil import parse_ts

RULES = {
    "first-light": ("First light", "Your first active day."),
    "founder": ("Founder", "You made the first commit of a repo."),
    "thousandfold": ("Thousandfold", "A repo reached its 1,000th commit by you."),
    "shipwright": ("Shipwright", "A version tag of 1.0 or higher (v1.0.0, cli/v1.2.0): annotated by you, "
                                 "or lightweight on your commit."),
    "long-road": ("Long road", "A streak of 30 active days."),
    "swarm-day": ("Swarm day", "100 or more of your commits in one day."),
    "necromancer": ("Necromancer", "You returned to a repo after 180 quiet days."),
    "polyglot": ("Polyglot", "Five or more languages past 1,000 added lines each."),
    "full-party": ("Full party", "Any three harnesses on the same day."),
    "seasons-turn": ("Season's turn", "Four calendar quarters with 10 or more active days each."),
}
ORDER = list(RULES)

_VERSION = re.compile(r"^v?(\d+)\.(\d+)(?:\.(\d+))?$")


def make(key: str, day: date | str, detail: str = "", count: int = 1) -> dict:
    title, rule = RULES[key]
    return {"id": key, "title": title, "rule": rule, "date": str(day), "detail": detail, "count": count}


def _quarter(d: date) -> tuple:
    return (d.year, (d.month - 1) // 3)


# Achievements that judge commits and tags. They count only commits that touch a file inside the
# profile's roots (see Commit.scoped), so a profile limited to one folder of a monorepo never earns
# them from elsewhere in that repo. The sheet's achievements lede says so.
SCOPED = ("founder", "thousandfold", "shipwright", "swarm-day", "necromancer")


def version_of(tag: str):
    """The version match of a tag's last path part: cli/v1.2.0 reads as v1.2.0."""
    return _VERSION.match(tag.rsplit("/", 1)[-1])


def evaluate(active_days: list, commits: list, tags: list, harness_days: dict, dayof, repo_name,
             lines_by_day: list) -> list:
    """active_days: sorted dates. commits: Commit records (deduped). tags: Tag records.
    Only your commits and tags in the profile's scope count.

    harness_days: {harness: set of dates}. dayof(ts) -> date. repo_name(top) -> display name.
    lines_by_day: sorted (date, language, added lines) for your commits.
    """
    out = []
    if active_days:
        out.append(make("first-light", active_days[0]))

    mine = [c for c in commits if c.mine and c.scoped]

    roots = sorted((c for c in mine if c.root), key=lambda c: (parse_ts(c.ts), c.hash))
    if roots:
        out.append(make("founder", dayof(roots[0].ts), repo_name(roots[0].top), count=len({c.repo for c in roots})))

    per_repo = defaultdict(list)
    for c in mine:
        per_repo[c.repo].append(c)
    firsts = []
    for repo, cs in per_repo.items():
        cs.sort(key=lambda c: (parse_ts(c.ts), c.hash))
        if len(cs) >= 1000:
            firsts.append((dayof(cs[999].ts), repo_name(cs[999].top)))
    if firsts:
        firsts.sort()
        out.append(make("thousandfold", firsts[0][0], firsts[0][1], count=len(firsts)))

    ships = []
    for t in tags:
        m = version_of(t.name)
        if t.mine and t.scoped and m and int(m.group(1)) >= 1:
            ships.append((dayof(t.ts), t.name, repo_name(t.top)))
    if ships:
        ships.sort()
        d, name, repo = ships[0]
        out.append(make("shipwright", d, f"{name} in {repo}", count=len(ships)))

    run = 0
    prev = None
    for d in active_days:
        run = run + 1 if prev is not None and d - prev == timedelta(days=1) else 1
        prev = d
        if run == 30:
            out.append(make("long-road", d))
            break

    per_day = defaultdict(int)
    for c in mine:
        per_day[dayof(c.ts)] += 1
    swarm = sorted(d for d, n in per_day.items() if n >= 100)
    if swarm:
        out.append(make("swarm-day", swarm[0], f"{per_day[swarm[0]]} commits", count=len(swarm)))

    returns = []
    for repo, cs in per_repo.items():
        days = sorted({dayof(c.ts) for c in cs})
        for a, b in zip(days, days[1:]):
            if (b - a).days - 1 >= 180:  # 180 quiet days between the two
                returns.append((b, repo_name(cs[0].top)))
    if returns:
        returns.sort()
        out.append(make("necromancer", returns[0][0], returns[0][1], count=len(returns)))

    totals = defaultdict(int)
    crossed = []
    for d, lang, n in lines_by_day:
        before = totals[lang]
        totals[lang] += n
        if before <= 1000 < totals[lang]:  # past 1,000
            crossed.append(lang)
            if len(crossed) == 5:
                out.append(make("polyglot", d, ", ".join(sorted(crossed))))
                break

    # Any three harnesses on one day. A harness seen on other days never takes the badge away.
    present = defaultdict(set)
    for h, ds in harness_days.items():
        for d in ds:
            present[d].add(h)
    full = sorted(d for d, hs in present.items() if len(hs) >= 3)
    if full:
        out.append(make("full-party", full[0], count=len(full)))

    q = defaultdict(list)
    for d in active_days:
        q[_quarter(d)].append(d)
    # The day each quarter reached 10 active days. The fourth such day, in date order, earns it.
    reached = sorted(sorted(v)[9] for v in q.values() if len(v) >= 10)
    if len(reached) >= 4:
        out.append(make("seasons-turn", reached[3]))

    out.sort(key=lambda a: (a["date"], ORDER.index(a["id"])))
    return out
