"""The party: one member per harness. Presence only, never a share of the work."""
from __future__ import annotations

from collections import Counter

HARNESS_NAMES = {"claude": "Claude Code", "codex": "Codex", "agy": "Antigravity"}
HARNESS_ORDER = ("claude", "codex", "agy")


def build_party(sessions: dict, in_season) -> list:
    """sessions: {(harness, session id): {"days": set, "edit_days": set, "origin": str, "models": Counter}}.

    Only sessions inside the profile reach here. in_season(day) filters days.
    """
    members = {}
    for (harness, sid), s in sorted(sessions.items()):
        days = {d for d in s["days"] if in_season(d)}
        if not days:
            continue
        m = members.setdefault(harness, {"days": set(), "sessions": 0, "edit": 0, "review": 0, "other": 0,
                                         "models": Counter()})
        m["days"] |= days
        m["sessions"] += 1
        edited = any(in_season(d) for d in s["edit_days"])
        if edited:
            m["edit"] += 1
        elif "exec" in (s.get("origin") or ""):
            m["review"] += 1
        else:
            m["other"] += 1
        for model, n in s["models"].items():
            if model:
                m["models"][model] += n
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
