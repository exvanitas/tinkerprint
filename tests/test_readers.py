import os
import random
import tempfile
import unittest
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
from statsheet.demo import RepoWriter, write_agy_db, write_claude_session, write_codex_session
from statsheet.readers import agy, claude, codex
from statsheet.readers.git import Identity, read_git

UTC = ZoneInfo("UTC")
ME = ("Ida Fenwick", "ida@fenwick.example.test")
MATE = ("Oren Pell", "oren@fenwick.example.test")
BOT = ("tidy-robot[bot]", "robot@example.test")


class GitReader(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = os.path.join(self.tmp.name, "repo-one")
        r = RepoWriter(self.root)
        t = datetime(2026, 3, 2, 10, tzinfo=UTC)
        r.touch(t, ME, {"a.py": 3})
        r.touch(t + timedelta(hours=1), BOT, {"b.py": 2}, coauthors=[ME])
        r.touch(t + timedelta(hours=2), MATE, {"c.py": 4}, coauthors=[ME])
        r.touch(t + timedelta(hours=3), MATE, {"d.py": 1})
        r.touch(t + timedelta(hours=4), ME, {"a.py": 2}, tag="v1.0.0")
        r.write()

    def tearDown(self):
        self.tmp.cleanup()

    def test_bots_dropped_and_coauthored_commits_count(self):
        res = read_git([self.root], Identity([ME[1]], []))
        paths = sorted({os.path.basename(e.path) for e in res.events})
        self.assertEqual(paths, ["a.py", "c.py"])
        self.assertEqual(sum(1 for c in res.commits if c.mine), 3)
        self.assertEqual(sum(1 for c in res.commits if c.bot), 1)
        self.assertTrue(any(c.root and c.mine for c in res.commits))
        self.assertEqual([(t.name, t.mine) for t in res.tags], [("v1.0.0", True)])
        added = {os.path.basename(e.path): e.added for e in res.events if e.status == "A"}
        self.assertEqual(added, {"a.py": 3, "c.py": 4})

    def test_clones_dedupe_by_hash(self):
        import subprocess
        from statsheet.demo import git_env
        clone = os.path.join(self.tmp.name, "repo-two")
        subprocess.run(["git", "clone", "-q", self.root, clone], check=True, env=git_env())
        res = read_git([self.root, clone], Identity([ME[1]], []))
        self.assertEqual(len(res.commits), 5)

    def test_name_patterns_match(self):
        res = read_git([self.root], Identity([], ["ida *"]))
        self.assertEqual(sum(1 for c in res.commits if c.mine), 3)


class HarnessReaders(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.rng = random.Random(5)
        self.cwd = os.path.join(self.tmp.name, "work", "proj")

    def tearDown(self):
        self.tmp.cleanup()

    def test_claude_edits_subagents_and_failed_calls(self):
        base = os.path.join(self.tmp.name, "claude")
        t = datetime(2026, 3, 2, 10, tzinfo=UTC)
        write_claude_session(base, self.cwd, t, "model-q", [(t, self.cwd + "/a.py", "Edit"),
                                                             (t, self.cwd + "/n.ipynb", "NotebookEdit")],
                             self.rng, subagent_edits=[(t + timedelta(hours=2), self.cwd + "/b.py")],
                             errored=[(t, self.cwd + "/bad.py")])
        files = claude.transcript_files(base)
        self.assertEqual(len(files), 2)
        evs = [e for f in files for e in claude.read_file(f)]
        edits = sorted(os.path.basename(e.path) for e in evs if e.kind == "edit")
        self.assertEqual(edits, ["a.py", "b.py", "n.ipynb"])
        self.assertEqual(len({e.session for e in evs}), 1)
        self.assertTrue(all(e.model == "model-q" for e in evs if e.kind == "edit"))
        sessions = [e for e in evs if e.kind == "session"]
        self.assertTrue(sessions and all(e.path == self.cwd for e in sessions))
        self.assertNotIn("Invented", repr(evs))

    def test_codex_patches_and_presence(self):
        base = os.path.join(self.tmp.name, "codex")
        t = datetime(2026, 3, 2, 10, tzinfo=UTC)
        write_codex_session(base, self.cwd, t, "model-r", [(t, self.cwd + "/x.py"), (t, self.cwd + "/y.py")], self.rng)
        write_codex_session(base, self.cwd, t, "model-r", [], self.rng, originator="codex_exec")
        files = codex.rollout_files(base)
        self.assertEqual(len(files), 2)
        evs = [e for f in files for e in codex.read_file(f)]
        edits = sorted(e.path for e in evs if e.kind == "edit")
        self.assertEqual(edits, [self.cwd + "/x.py", self.cwd + "/y.py"])
        self.assertEqual({e.origin for e in evs}, {"codex_exec"})
        self.assertEqual({e.model for e in evs}, {"model-r"})
        self.assertNotIn("Invented", repr(evs))

    def test_agy_presence(self):
        db = os.path.join(self.tmp.name, "agy", "conversation_summaries.db")
        write_agy_db(db, [("conv-1", [self.cwd + " two"], datetime(2026, 3, 2, 10, tzinfo=UTC))])
        evs = agy.read_db(db)
        self.assertEqual([(e.kind, e.path, e.session) for e in evs], [("session", self.cwd + " two", "conv-1")])
        self.assertTrue(evs[0].ts.startswith("2026-03-02T10:00:00"))
        self.assertNotIn("Invented", repr(evs))


if __name__ == "__main__":
    unittest.main()
