"""0.2.0 review, part 2: the cache upgrade, locks, git, paths from logs and malformed records.
Every name, path and email here is invented."""
import json
import os
import tempfile
import unittest

import helpers  # noqa: F401
from tinkerprint.build import CACHE_VERSION, _cached, new_report
from tinkerprint.readers import claude


def write_lines(path, records):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write((r if isinstance(r, str) else json.dumps(r)) + "\n")
    return path


def claude_record(sid, day="2026-03-02", cwd="/w/a"):
    return {"type": "user", "sessionId": sid, "timestamp": f"{day}T10:00:00Z", "cwd": cwd, "version": "2.1.4",
            "message": {"role": "user", "content": "invented"}}


class Tmp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = os.path.realpath(self.tmp.name)
        self.base = os.path.join(self.t, "logs")
        self.cache = os.path.join(self.t, "data", "cache", "claude.json")

    def tearDown(self):
        self.tmp.cleanup()

    def read(self, files):
        rep = new_report()
        return _cached(files, claude.read_file, self.cache, self.base, rep), rep

    def entries(self):
        with open(self.cache, encoding="utf-8") as f:
            return json.load(f)


class CacheFrom01(Tmp):
    """A 0.1 cache (version 4) never marked an entry gone. Its events are still valid."""

    def v4_cache(self, files):
        os.makedirs(os.path.dirname(self.cache), exist_ok=True)
        with open(self.cache, "w", encoding="utf-8") as f:
            json.dump({"v": 4, "files": files}, f)

    def event(self, session):
        return {"ts": "2025-11-05T10:00:00+00:00", "source": "claude", "kind": "session", "path": "/w/a",
                "session": session, "harness": "claude", "model": "", "actor": "agent", "origin": "",
                "commit": "", "status": "", "added": 0, "op": ""}

    def test_a_log_gone_since_01_keeps_its_events(self):
        live = write_lines(os.path.join(self.base, "p", "live.jsonl"), [claude_record("now")])
        gone = os.path.join(self.base, "p", "gone.jsonl")
        with open(live, "rb") as f:
            raw = f.read()
        import hashlib
        st = os.stat(live)
        self.v4_cache({
            gone: {"stat": None, "sha256": "1" * 64, "size": 10, "events": [self.event("rotated")]},
            # The 0.1 entry of a live log matches it exactly, yet it is read again.
            live: {"stat": [st.st_size, st.st_mtime_ns, st.st_ctime_ns, st.st_ino],
                   "sha256": hashlib.sha256(raw).hexdigest(), "size": len(raw), "events": [self.event("stale")]},
        })
        evs, rep = self.read([live])
        self.assertEqual({e.session for e in evs}, {"now", "rotated"})
        self.assertEqual((rep["kept_files"], rep["kept_sessions"]), (1, 1))
        saved = self.entries()
        self.assertEqual(saved["v"], CACHE_VERSION)
        self.assertTrue(saved["files"][gone]["gone"])
        self.assertNotIn("gone", saved["files"][live])
        # And the next build still counts it.
        evs, rep = self.read([live])
        self.assertEqual({e.session for e in evs}, {"now", "rotated"})

    def test_an_unknown_version_keeps_only_what_it_marked_gone(self):
        gone = os.path.join(self.base, "p", "gone.jsonl")
        os.makedirs(os.path.dirname(self.cache), exist_ok=True)
        with open(self.cache, "w", encoding="utf-8") as f:
            json.dump({"v": 99, "files": {gone: {"events": [self.event("x")]}}}, f)
        evs, _ = self.read([])
        self.assertEqual(evs, [])


if __name__ == "__main__":
    unittest.main()
