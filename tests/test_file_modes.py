"""Outputs people open or share follow the umask (0644 under 022). The cache, history and pointer stay 0600.
Every name, path and email here is invented."""
import os
import stat
import tempfile
import unittest
from datetime import date, datetime
from zoneinfo import ZoneInfo

import helpers  # noqa: F401
from tinkerprint.build import build
from tinkerprint.demo import PEOPLE, RepoWriter, run_demo
from tinkerprint.profile import load_profile

UTC = ZoneInfo("UTC")
ME = ("Ida Fenwick", "ida@fenwick.example.test")


def mode(path):
    return stat.S_IMODE(os.stat(path).st_mode)


@unittest.skipUnless(os.name == "posix", "POSIX file modes")
class FileModes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = os.path.realpath(self.tmp.name)
        self.old_mask = os.umask(0o022)

    def tearDown(self):
        os.umask(self.old_mask)
        self.tmp.cleanup()

    def build(self):
        root = os.path.join(self.t, "repo")
        r = RepoWriter(root)
        r.touch(datetime(2026, 3, 2, 10, tzinfo=UTC), ME, {"a.py": 2})
        r.write()
        logs = os.path.join(self.t, "logs")
        os.makedirs(logs)
        path = os.path.join(self.t, "p.toml")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f'name = "Ida"\n[identity]\nemails = ["{ME[1]}"]\n[harnesses]\nclaude = true\ncodex = false\n'
                    f'claude_dir = "{logs}"\n[[project]]\nname = "P"\nroot = "{root}"\n')
        out, home = os.path.join(self.t, "out"), os.path.join(self.t, "data")
        build(load_profile(path), out, home=home, today=date(2026, 11, 1))
        return out, home

    def private_files(self, home):
        for folder, _, files in os.walk(home):
            for name in files:
                yield os.path.join(folder, name)

    def test_outputs_shared_data_private(self):
        out, home = self.build()
        for name in ("sheet.html", "card.svg", "portrait.png", "sheet.json", "changes.json"):
            self.assertEqual(mode(os.path.join(out, name)), 0o644, name)
        private = list(self.private_files(home))
        self.assertTrue(any(os.sep + "cache" + os.sep in p for p in private))
        self.assertTrue(any(os.sep + "history" + os.sep in p for p in private))
        self.assertTrue(any(os.sep + "last-build" + os.sep in p for p in private))
        self.assertTrue(any(p.endswith(os.sep + "profiles.json") for p in private))
        for p in private:
            self.assertEqual(mode(p), 0o600, p)

    def test_strict_umask_is_respected(self):
        os.umask(0o077)
        out, _ = self.build()
        self.assertEqual(mode(os.path.join(out, "sheet.html")), 0o600)

    def test_gallery(self):
        from tinkerprint.gallery import write_gallery
        out = os.path.join(self.t, "gallery")
        os.makedirs(out)
        write_gallery(out, None, png=True)
        self.assertEqual(mode(os.path.join(out, "gallery.html")), 0o644)
        pngs = os.listdir(os.path.join(out, "png"))
        self.assertTrue(pngs)
        self.assertEqual({mode(os.path.join(out, "png", n)) for n in pngs}, {0o644})

    def test_demo(self):
        out = os.path.join(self.t, "demo")
        run_demo(out, people=PEOPLE[1:])
        files = [os.path.join(f, n) for f, _, ns in os.walk(out) for n in ns]
        self.assertTrue(any(p.endswith("sheet.html") for p in files))
        self.assertEqual({mode(p) for p in files}, {0o644})


if __name__ == "__main__":
    unittest.main()
