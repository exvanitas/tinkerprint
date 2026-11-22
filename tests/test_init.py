"""init prefills from git config, and build and audit find ./tinkerprint.toml.
Every name, path and email here is invented."""
import io
import os
import subprocess
import tempfile
import tomllib
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

import helpers  # noqa: F401
from tinkerprint.cli import main, starter
from tinkerprint.demo import git_env
from tinkerprint.profile import load_profile, parse_profile


class InCwd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.t = os.path.realpath(self.tmp.name)
        self.old = os.getcwd()
        os.chdir(self.t)
        self.gitconfig = os.path.join(self.t, "gitconfig")
        open(self.gitconfig, "w").close()
        self.env = mock.patch.dict(os.environ, {"GIT_CONFIG_GLOBAL": self.gitconfig, "GIT_CONFIG_NOSYSTEM": "1"})
        self.env.start()

    def tearDown(self):
        self.env.stop()
        os.chdir(self.old)
        self.tmp.cleanup()

    def git_config(self, key, value):
        subprocess.run(["git", "config", "--file", self.gitconfig, key, value], check=True, env=git_env())

    def cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()


class Init(InCwd):
    def test_prefills_name_and_email_from_git(self):
        self.git_config("user.name", 'Odile "Dee" Marchetti')
        self.git_config("user.email", "odile@marchetti.example.test")
        code, out, _ = self.cli("init")
        self.assertEqual(code, 0)
        with open("tinkerprint.toml", "rb") as f:
            data = tomllib.load(f)
        self.assertEqual(data["name"], 'Odile "Dee" Marchetti')
        self.assertEqual(data["identity"]["emails"], ["odile@marchetti.example.test"])
        self.assertEqual(data["identity"]["names"], ['Odile "Dee" Marchetti'])
        self.assertIn("git config", out)
        self.assertIn("Then run: tinkerprint build\n", out)
        load_profile("tinkerprint.toml")

    def test_placeholders_without_git_config(self):
        code, out, _ = self.cli("init", "--out", "me.toml")
        self.assertEqual(code, 0)
        with open("me.toml", "rb") as f:
            data = tomllib.load(f)
        self.assertEqual(data["name"], "Your Name")
        self.assertEqual(data["identity"]["emails"], ["you@example.test"])
        self.assertIn("--profile me.toml", out)

    def test_only_email_set(self):
        self.git_config("user.email", "solo@example.test")
        self.cli("init")
        with open("tinkerprint.toml", "rb") as f:
            data = tomllib.load(f)
        self.assertEqual(data["name"], "Your Name")
        self.assertEqual(data["identity"]["emails"], ["solo@example.test"])

    def test_starter_mentions_noreply_and_repos(self):
        text = starter()
        self.assertIn("users.noreply.github.com", text)
        self.assertIn("outside your repos", text)

    def test_starter_parses_with_odd_values(self):
        text = starter("Back\\slash Ünïcode", "a\\b@example.test", "+05:30", True)
        data = tomllib.loads(text)
        self.assertEqual(data["name"], "Back\\slash Ünïcode")
        self.assertEqual(data["timezone"], "+05:30")
        parse_profile(data, self.t)

    def test_warns_inside_a_repo(self):
        repo = os.path.join(self.t, "repo")
        subprocess.run(["git", "init", "-q", repo], check=True, env=git_env())
        code, out, _ = self.cli("init", "--out", os.path.join(repo, "me.toml"))
        self.assertEqual(code, 0)
        self.assertIn("inside a git repository", out)
        code, out, _ = self.cli("init", "--out", os.path.join(self.t, "outside.toml"))
        self.assertNotIn("inside a git repository", out)

    def test_never_overwrites(self):
        with open("tinkerprint.toml", "w") as f:
            f.write("# mine\n")
        code, _, err = self.cli("init")
        self.assertEqual(code, 1)
        with open("tinkerprint.toml") as f:
            self.assertEqual(f.read(), "# mine\n")


class DefaultProfile(InCwd):
    PROFILE = ('name = "Odile"\n[identity]\nemails = ["odile@marchetti.example.test"]\n'
               '[harnesses]\nclaude = false\ncodex = false\n')

    def test_build_and_audit_use_the_file_here(self):
        with open("tinkerprint.toml", "w") as f:
            f.write(self.PROFILE)
        data = os.path.join(self.t, "data")
        code, out, err = self.cli("build", "--data-dir", data)
        self.assertEqual(code, 0, err)
        self.assertIn("Profile: ./tinkerprint.toml", out)
        self.assertIn("Odile: level 0", out)
        code, out, err = self.cli("audit", "--data-dir", data)
        self.assertEqual(code, 0, err)
        self.assertIn("card.svg", out)

    def test_without_a_file_the_error_says_how(self):
        for cmd in ("build", "audit"):
            with self.subTest(cmd=cmd):
                code, _, err = self.cli(cmd, "--data-dir", os.path.join(self.t, "data"))
                self.assertEqual(code, 2)
                self.assertIn("--profile PATH", err)
                self.assertIn("tinkerprint init", err)

    def test_audit_with_out_needs_no_profile(self):
        out = os.path.join(self.t, "card")
        os.makedirs(out)
        code, text, _ = self.cli("audit", "--out", out)
        self.assertEqual(code, 1)
        self.assertIn("No card.svg", text)


if __name__ == "__main__":
    unittest.main()
