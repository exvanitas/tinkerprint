"""Review round 1: card, radar scale, cache and audit findings."""
import io
import json
import math
import os
import re
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import date, datetime
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
from helpers import commit, profile, run
from tinkerprint.build import _cached
from tinkerprint.demo import RepoWriter
from tinkerprint.readers import codex
from tinkerprint.render_card import card_strings, render_card

UTC = ZoneInfo("UTC")
ME = ("Ida Fenwick", "ida@fenwick.example.test")


class Item17CardAndRadarScale(unittest.TestCase):
    def test_sparse_card_draws_bars(self):
        prof = profile([("A", "/w/a", None)])
        sheet, _ = run(prof, [commit("2026-03-02T10:00:00+00:00", "/w/a/x.py")])
        self.assertEqual(sheet["chart"], "bars")
        svg = render_card(sheet["card"])
        self.assertNotIn("<polygon", svg)
        self.assertIn("<rect x=\"640\"", svg)

    def test_radar_scale_is_common(self):
        from tinkerprint.render_html import _radar

        def peak_radius(share):
            stats = [{"key": k, "share": share if i == 0 else 0.0, "points": 1.0 if i == 0 else 0.0}
                     for i, k in enumerate("ABCDEFGH")]
            svg = _radar(stats)
            cx, cy = 280, 262
            x, y = map(float, re.search(r'class="pt" cx="([\d.]+)" cy="([\d.]+)"', svg).groups())
            return math.hypot(x - cx, y - cy)

        self.assertLess(peak_radius(0.4), peak_radius(0.8) - 20)


class Item19CacheFollowsContent(unittest.TestCase):
    def test_same_size_and_mtime_new_content_is_reread(self):
        with tempfile.TemporaryDirectory() as t:
            path = os.path.join(t, "sessions", "rollout-1.jsonl")
            os.makedirs(os.path.dirname(path))

            def write(name):
                lines = [{"timestamp": "2026-03-02T10:00:00Z", "type": "session_meta",
                          "payload": {"id": "s1", "cwd": "/w/a", "originator": "codex_exec"}},
                         {"timestamp": "2026-03-02T10:01:00Z", "type": "event_msg", "payload": {
                             "type": "item_completed", "item": {"type": "FileChange", "id": "f", "status": "completed",
                                                                "changes": {f"/w/a/{name}": {"type": "update"}}}}}]
                with open(path, "w") as f:
                    f.write("".join(json.dumps(x) + "\n" for x in lines))

            write("a.py")
            st = os.stat(path)
            cache = os.path.join(t, "cache", "codex.json")
            first = _cached([path], codex.read_file, cache)
            write("a.md")
            os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns))
            self.assertEqual(os.stat(path).st_size, st.st_size)
            second = _cached([path], codex.read_file, cache)
            self.assertEqual([e.path for e in first if e.kind == "edit"], ["/w/a/a.py"])
            self.assertEqual([e.path for e in second if e.kind == "edit"], ["/w/a/a.md"])


class Item22AuditDescribesTheBuiltCard(unittest.TestCase):
    def test_audit_reads_the_selected_build(self):
        from tinkerprint.cli import main
        with tempfile.TemporaryDirectory() as t:
            root = os.path.join(t, "repo")
            r = RepoWriter(root)
            for d in (2, 3, 4, 5):
                r.touch(datetime(2026, 3, d, 10, tzinfo=UTC), ME, {f"f{d}.py": 2})
            r.write()
            prof_path = os.path.join(t, "p.toml")
            with open(prof_path, "w") as f:
                f.write(f'name = "Ida"\n[identity]\nemails = ["{ME[1]}"]\n[harnesses]\nclaude = false\n'
                        f'codex = false\n[[project]]\nname = "P"\nroot = "{root}"\n')
            data = os.path.join(t, "data")
            with redirect_stdout(io.StringIO()):
                main(["build", "--profile", prof_path, "--as-of", "2026-03-04", "--data-dir", data])
            buf = io.StringIO()
            with redirect_stdout(buf):
                main(["audit", "--profile", prof_path, "--data-dir", data])
            self.assertRegex(buf.getvalue(), r"level\s+1\n")

    def test_audit_lists_only_what_the_card_draws(self):
        prof = profile([("A", "/w/a", None)])
        sheet, _ = run(prof, [commit("2026-03-02T10:00:00+00:00", "/w/a/x.py")])
        card = dict(sheet["card"], achievements=[{"title": f"Title {i}", "when": "Mar 2026"} for i in range(6)])
        rows = [v for k, v in card_strings(card) if k == "achievement"]
        self.assertEqual(len(rows), 4)
        svg = render_card(card)
        for v in rows:
            self.assertIn(v.split(" · ")[0], svg)
        self.assertNotIn("Title 0", svg)


if __name__ == "__main__":
    unittest.main()
