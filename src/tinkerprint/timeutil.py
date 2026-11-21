"""Timestamp parsing and day bucketing."""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone, tzinfo
from zoneinfo import ZoneInfo

_FRAC = re.compile(r"^(.*?\d\d:\d\d:\d\d)(\.\d+)?(.*)$")
_OFFSET = re.compile(r"^([+-])(\d\d):?(\d\d)$")


def parse_ts(value) -> datetime | None:
    """Parse an ISO-ish timestamp or epoch number into an aware datetime.

    Accepts 'Z', a space separator and fractions longer than six digits.
    Naive values are taken as UTC.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        secs = float(value)
        if secs > 1e11:  # milliseconds
            secs /= 1000.0
        try:
            return datetime.fromtimestamp(secs, timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if not isinstance(value, str):
        return None
    s = value.strip()
    if len(s) > 10 and s[10] == " ":
        s = s[:10] + "T" + s[11:]
    if s[-1:] in ("Z", "z"):
        s = s[:-1] + "+00:00"
    m = _FRAC.match(s)
    if m and m.group(2) and len(m.group(2)) > 7:
        s = m.group(1) + m.group(2)[:7] + m.group(3)
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def iso(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def load_tz(name: str | None) -> tzinfo:
    if not name or name.upper() == "UTC":
        return timezone.utc
    m = _OFFSET.match(name.strip())
    if m:
        sign = -1 if m.group(1) == "-" else 1
        return timezone(sign * timedelta(hours=int(m.group(2)), minutes=int(m.group(3))))
    return ZoneInfo(name)


def day_of(dt: datetime, tz: tzinfo, rollover_hour: int) -> date:
    """The profile day a moment belongs to. Work before the rollover hour counts toward the day before."""
    local = dt.astimezone(tz)
    return (local - timedelta(hours=rollover_hour)).date()


def parse_day(s: str) -> date:
    return date.fromisoformat(s.strip())


MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def month_label(day: str) -> str:
    d = date.fromisoformat(day)
    return f"{MONTHS[d.month - 1]} {d.year}"


def day_label(day: str) -> str:
    d = date.fromisoformat(day)
    return f"{MONTHS[d.month - 1]} {d.day}, {d.year}"
