import json
import os
import tempfile
import unittest

import helpers  # noqa: F401
from helpers import profile
from statsheet.classify import builder_stat, classify, is_skipped
from statsheet.profile import ProfileError, parse_profile
from statsheet.projects import glob_match, manifest_prior, scan_priors


class Rules(unittest.TestCase):
    def test_paths_before_extensions(self):
        cases = {
            "pkg/tests/test_a.py": "Tests", "src/__tests__/a.js": "Tests", "src/a.test.ts": "Tests",
            "src/a.spec.tsx": "Tests", ".github/workflows/ci.yml": "Infra", "Dockerfile": "Infra",
            "deploy/run.py": "Infra", "db/migrations/0001.py": "Data", "docs/guide.html": "Docs",
            "web/components/Button.ts": "Interface", "scripts/sync.sh": "Tools", "bin/run": "Tools",
        }
        for rel, want in cases.items():
            self.assertEqual(builder_stat(rel, None), want, rel)

    def test_extensions(self):
        cases = {"a.tsx": "Interface", "a.css": "Interface", "q.sql": "Data", "n.ipynb": "Data",
                 "README.md": "Docs", "up.sh": "Infra", "main.tf": "Infra", "core.rs": "Logic", "app.py": "Logic",
                 "logo.png": None, "data.csv": None, "config.yaml": None, "CLAUDE.md": None, "AGENTS.md": None,
                 ".claude/settings.json": None}
        for rel, want in cases.items():
            self.assertEqual(builder_stat(rel, None), want, rel)

    def test_skipped(self):
        for rel in ("node_modules/a/b.js", "dist/app.js", "build/x.o", "vendor/lib.go", "target/debug/a",
                    "yarn.lock", "Cargo.lock", "app.min.js", "app.js.map"):
            self.assertTrue(is_skipped(rel), rel)
        self.assertFalse(is_skipped("src/builder.py"))

    def test_priors_relabel_logic_only(self):
        self.assertEqual(builder_stat("src/cli.ts", "Tools"), "Tools")
        self.assertEqual(builder_stat("src/train.py", "Models"), "Models")
        self.assertEqual(builder_stat("src/train.rs", "Models"), "Logic")
        self.assertEqual(builder_stat("tests/test_train.py", "Models"), "Tests")
        self.assertEqual(builder_stat("etl/load.py", "Data"), "Data")

    def test_overrides_win(self):
        prof = profile([("A", "/w/a", {"override": [{"glob": "**/*.png", "stats": {"Docs": 1}}],
                                       "part": [{"path": "web", "stats": {"Interface": 1}}]})])
        p = prof.projects[0]
        self.assertEqual(classify("img/x.png", p, "builder", {}), {"Docs": 1.0})
        self.assertEqual(classify("web/server.py", p, "builder", {}), {"Interface": 1.0})
        self.assertEqual(classify("other.py", p, "builder", {}), {"Logic": 1.0})
        self.assertEqual(classify("other.bin", p, "builder", {}), {"": 1.0})
        self.assertIsNone(classify("node_modules/x.png", p, "builder", {}))

    def test_glob(self):
        self.assertTrue(glob_match("art/**", "art/a/b.png"))
        self.assertTrue(glob_match("**/*.png", "a/b/c.png"))
        self.assertTrue(glob_match("**/*.png", "c.png"))
        self.assertFalse(glob_match("*.png", "a/c.png"))

    def test_manifest_priors(self):
        with tempfile.TemporaryDirectory() as d:
            os.makedirs(os.path.join(d, "cli"))
            with open(os.path.join(d, "cli", "package.json"), "w") as f:
                json.dump({"name": "x", "bin": {"x": "main.js"}}, f)
            with open(os.path.join(d, "pyproject.toml"), "w") as f:
                f.write('[project]\nname = "y"\ndependencies = ["torch>=2", "pandas"]\n')
            self.assertEqual(manifest_prior(os.path.join(d, "cli")), "Tools")
            self.assertEqual(manifest_prior(d), "Models")
            prof = profile([("A", d, {"part": ["cli", "web"]})])
            priors = scan_priors(prof.projects)
            p = prof.projects[0]
            self.assertEqual(classify("cli/src/main.ts", p, "builder", priors), {"Tools": 1.0})
            self.assertEqual(classify("web/src/app.py", p, "builder", priors), {"Models": 1.0})
            with open(os.path.join(d, "pyproject.toml"), "w") as f:
                f.write('[project]\nname = "y"\ndependencies = ["polars", "duckdb"]\n')
            self.assertEqual(manifest_prior(d), "Data")


class ProfileValidation(unittest.TestCase):
    base = {"identity": {"emails": ["a@example.test"]}, "project": [{"name": "A", "root": "/w/a"}]}

    def test_unknown_stat_is_an_error(self):
        data = dict(self.base, project=[{"name": "A", "root": "/w/a", "stats": {"Art": 1}}])
        with self.assertRaises(ProfileError):
            parse_profile(data, "/")

    def test_tinkerer_accepts_builder_names(self):
        data = dict(self.base, set="tinkerer", project=[{"name": "A", "root": "/w/a", "stats": {"Logic": 1}}])
        self.assertEqual(parse_profile(data, "/").projects[0].stats, {"Logic": 1.0})

    def test_needs_identity(self):
        with self.assertRaises(ProfileError):
            parse_profile({"project": []}, "/")

    def test_example_profile_loads(self):
        from statsheet.profile import load_profile
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prof = load_profile(os.path.join(here, "examples", "profile.example.toml"))
        self.assertGreaterEqual(len(prof.projects), 2)


if __name__ == "__main__":
    unittest.main()
