"""The party: one member per harness. Presence only, never a share of the work."""
from __future__ import annotations

from collections import Counter

HARNESS_NAMES = {"claude": "Claude Code", "codex": "Codex", "agy": "Antigravity"}
HARNESS_ORDER = ("claude", "codex", "agy")


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
        m = members.setdefault(harness, {"days": set(), "sessions": 0, "edit": 0, "review": 0, "other": 0,
                                         "models": Counter()})
        m["days"] |= {d for d, _, _ in obs}
        m["sessions"] += 1
        if any(edited for _, _, edited in obs):
            m["edit"] += 1
        elif "exec" in (s.get("origin") or ""):
            m["review"] += 1
        else:
            m["other"] += 1
        for _, model, _ in obs:
            if model:
                m["models"][model] += 1
    out = []
    for h in HARNESS_ORDER:
        if h not in members:
            continue
        m = members[h]
        if m["edit"] and m["edit"] >= m["review"]:
            role = "Mostly edits"
        elif m["review"] > m["edit"]:
            role = "Mostly reviews"
        else:
            role = "Present, no edits"
        days = sorted(m["days"])
        out.append({
            "harness": h,
            "name": HARNESS_NAMES[h],
            "days_together": len(days),
            "first_day": days[0].isoformat(),
            "last_day": days[-1].isoformat(),
            "sessions": m["sessions"],
            "edit_sessions": m["edit"],
            "review_sessions": m["review"],
            "other_sessions": m["other"],
            "role": role,
            "models": [k for k, _ in sorted(m["models"].items(), key=lambda kv: (-kv[1], kv[0]))],
        })
    return out
