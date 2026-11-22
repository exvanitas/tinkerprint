"""The party: one member per harness. Presence only, never a share of the work."""
from __future__ import annotations

from collections import Counter

HARNESS_NAMES = {"claude": "Claude Code", "codex": "Codex", "agy": "Antigravity"}
HARNESS_ORDER = ("claude", "codex", "agy")


# Readers that see when and where a harness ran, but never which files it changed.
PRESENCE_ONLY = ("agy",)


def role_of(harness: str, edit_sessions: int, sessions: int) -> str:
    """What the logs show, never more. A session with no recorded edit may still have done work
    the log does not record, so it says "No edits recorded", never "review"."""
    if harness in PRESENCE_ONLY:
        return "Presence only"
    if edit_sessions * 2 > sessions:
        return "Mostly edits"
    if edit_sessions:
        return "Some edits recorded"
    return "No edits recorded"


def build_party(sessions: dict, in_season) -> list:
    """sessions: {(harness, session id): {"obs": [(day, model, edited)], "origin": str}}.

    Observations are already limited to the profile's roots. in_season(day) filters each one,
    so days and models from outside the season never reach the party.
    """
    members = {}
    for (harness, sid), s in sorted(sessions.items()):
        obs = [o for o in s["obs"] if in_season(o[0])]
        if not obs:
            continue
        m = members.setdefault(harness, {"days": set(), "sessions": 0, "edit": 0, "models": Counter()})
        m["days"] |= {d for d, _, _ in obs}
        m["sessions"] += 1
        if any(edited for _, _, edited in obs):
            m["edit"] += 1
        for _, model, _ in obs:
            if model:
                m["models"][model] += 1
    out = []
    for h in HARNESS_ORDER:
        if h not in members:
            continue
        m = members[h]
        days = sorted(m["days"])
        out.append({
            "harness": h,
            "name": HARNESS_NAMES[h],
            "days_together": len(days),
            "first_day": days[0].isoformat(),
            "last_day": days[-1].isoformat(),
            "sessions": m["sessions"],
            "edit_sessions": m["edit"],
            "role": role_of(h, m["edit"], m["sessions"]),
            "models": [k for k, _ in sorted(m["models"].items(), key=lambda kv: (-kv[1], kv[0]))],
        })
    return out
