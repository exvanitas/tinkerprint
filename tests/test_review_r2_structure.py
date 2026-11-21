"""Review round 2, structural changes A (pure sheet, explicit comparison), B (close classes), C (audit the SVG)."""
import io
import json
import os
import shutil
import tempfile
import threading
import unittest
from contextlib import redirect_stdout
from datetime import date, datetime
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
from helpers import commit, profile, run
from tinkerprint.build import build
from tinkerprint.demo import RepoWriter
from tinkerprint.profile import load_profile

UTC = ZoneInfo("UTC")
ME = ("Ida Fenwick", "ida@fenwick.example.test")
TS = "2026-03-02T10:00:00+00:00"


def write_profile(path, root, extra=""):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f'{extra}\nname = "Ida"\n[identity]\nemails = ["{ME[1]}"]\n[harnesses]\nclaude = false\ncodex = false\n'
                f'[[project]]\nname = "P"\nroot = "{root}"\n')
    return path


class World(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = self.tmp.name
        self.root = os.path.join(self.t, "repo")
        r = RepoWriter(self.root)
        r.touch(datetime(2026, 3, 1, 10, tzinfo=UTC), ME, {"a.py": 2})
        r.touch(datetime(2026, 6, 1, 10, tzinfo=UTC), ME, {"README.md": 2})
        r.touch(datetime(2026, 6, 2, 10, tzinfo=UTC), ME, {"docs/x.md": 2})
        r.write()
        self.prof = load_profile(write_profile(os.path.join(self.t, "p.toml"), self.root))

    def tearDown(self):
        self.tmp.cleanup()

    def go(self, as_of, home="data", out=None, prof=None):
        out = out or f"out-{as_of}-{home}"
        return build(prof or self.prof, os.path.join(self.t, out), as_of=as_of, home=os.path.join(self.t, home))

    def read(self, res, name):
        with open(os.path.join(os.path.dirname(res["paths"]["json"]), name), "rb") as f:
            return f.read()


class A_SheetIsPure(World):
    def test_sheet_json_does_not_depend_on_history(self):
        direct = self.go(date(2026, 6, 2), home="store1")
        self.go(date(2026, 3, 1), home="store2")
        after = self.go(date(2026, 6, 2), home="store2")
        self.assertEqual(self.read(direct, "sheet.json"), self.read(after, "sheet.json"))
        sheet = json.loads(self.read(direct, "sheet.json"))
        self.assertNotIn("changes", sheet)

    def test_comparison_is_explicit_and_never_uses_the_future(self):
        self.go(date(2026, 6, 2))
        march = self.go(date(2026, 3, 1))
        changes = json.loads(self.read(march, "changes.json"))
        self.assertIsNone(changes["against"])
        june = self.go(date(2026, 6, 2))
        changes = json.loads(self.read(june, "changes.json"))
        self.assertEqual(changes["against"], "2026-03-01")
        self.assertEqual(changes["points_since"], 2)
        self.assertIn("Mar 1, 2026", self.read(june, "sheet.html").decode())

    def test_failed_build_never_becomes_the_comparison(self):
        self.go(date(2026, 3, 1))
        blocker = os.path.join(self.t, "blocker")
        open(blocker, "w").close()
        with self.assertRaises(OSError):
            build(self.prof, blocker, as_of=date(2026, 6, 1), home=os.path.join(self.t, "data"))
        res = self.go(date(2026, 6, 2))
        self.assertEqual(json.loads(self.read(res, "changes.json"))["against"], "2026-03-01")

    def test_profiles_with_the_same_id_keep_separate_folders(self):
        from tinkerprint.cli import default_out
        a = load_profile(write_profile(os.path.join(self.t, "work", "p.toml"), self.root, 'id = "same"'))
        b = load_profile(write_profile(os.path.join(self.t, "home", "p.toml"), self.root, 'id = "same"'))
        home = os.path.join(self.t, "data")
        self.assertNotEqual(default_out(home, a), default_out(home, b))
        self.go(date(2026, 3, 1), prof=a, out="oa")
        res = self.go(date(2026, 6, 2), prof=b, out="ob")
        self.assertIsNone(json.loads(self.read(res, "changes.json"))["against"])

    def test_concurrent_writes_to_one_file(self):
        from tinkerprint.datadir import _write
        path = os.path.join(self.t, "same.json")
        errors = []

        def worker(n):
            try:
                for i in range(30):
                    _write(path, f"{n}-{i}\n" * 50)
            except OSError as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(n,)) for n in range(8)]
        for th in threads:
            th.start()
        for th in threads:
            th.join()
        self.assertEqual(errors, [])


class B_CloseClasses(unittest.TestCase):
    def sheet(self, weights):
        prof = profile([("A", "/w/a", {"stats": weights})])
        return run(prof, [commit(TS, "/w/a/x.py")])[0]

    def test_pair_close_to_runner_up_pair(self):
        # One file: shares are log(1 + weight) normalized, so these land a point apart.
        s = self.sheet({"Logic": 30, "Tests": 20.5, "Interface": 20, "Docs": 15, "Infra": 14.5})
        self.assertEqual(s["class"]["name"], "Templar")
        self.assertEqual(s["class"]["close"]["name"], "Spellblade")
        self.assertEqual(s["class"]["display"], "Templar, close to Spellblade")
        far = self.sheet({"Logic": 30, "Tests": 26, "Interface": 20, "Docs": 13, "Infra": 11})
        self.assertIsNone(far["class"]["close"])

    def test_specialist_close_to_second_specialist(self):
        s = self.sheet({"Logic": 1.02, "Interface": 1})
        self.assertEqual(s["class"]["display"], "Sage, close to Illusionist")

    def test_ties_break_by_set_order(self):
        s = self.sheet({"Logic": 2, "Tests": 1, "Interface": 1})
        self.assertEqual(s["class"]["display"], "Spellblade, close to Templar")

    def test_multiclass_names_both_when_close(self):
        s = self.sheet({"Logic": 35, "Interface": 25, "Data": 16, "Tests": 12.5, "Docs": 11.5})
        self.assertEqual(s["multiclass"]["display"], "Assayer, close to Chronicler")

    def test_no_history_fields_and_method_two(self):
        s = self.sheet({"Logic": 1})
        self.assertEqual(s["method"], 2)
        self.assertNotIn("held", s["class"])
        self.assertNotIn("new-class", [a["id"] for a in s["achievements"]])


class C_AuditReadsTheSvg(World):
    def test_audit_lists_the_card_on_disk(self):
        from tinkerprint.cli import main
        prof_path = os.path.join(self.t, "p.toml")
        data = os.path.join(self.t, "data")
        out = os.path.join(self.t, "out")
        with redirect_stdout(io.StringIO()):
            main(["build", "--profile", prof_path, "--data-dir", data, "--out", out])
        shutil.copy(os.path.join(out, "card.svg"), os.path.join(self.t, "old.svg"))
        write_profile(prof_path, self.root)
        with open(prof_path, "a") as f:
            f.write("")
        text = open(prof_path).read().replace('name = "Ida"', 'name = "Later Name"', 1)
        open(prof_path, "w").write(text)
        with redirect_stdout(io.StringIO()):
            main(["build", "--profile", prof_path, "--data-dir", data, "--out", out])
        shutil.copy(os.path.join(self.t, "old.svg"), os.path.join(out, "card.svg"))
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(["audit", "--profile", prof_path, "--out", out])
        self.assertIn("Ida", buf.getvalue())
        self.assertNotIn("Later Name", buf.getvalue())

    def test_audit_without_a_card(self):
        from tinkerprint.cli import main
        out = os.path.join(self.t, "empty")
        os.makedirs(out)
        buf = io.StringIO()
        with redirect_stdout(buf):
            main(["audit", "--profile", os.path.join(self.t, "p.toml"), "--out", out])
        self.assertIn("No card", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
