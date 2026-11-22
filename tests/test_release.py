"""The release's numbers agree: package version, changelog heading and method version."""
import os
import re
import tomllib
import unittest

import helpers  # noqa: F401
import tinkerprint

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(name: str) -> str:
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return f.read()


class Release(unittest.TestCase):
    def test_versions_agree(self):
        with open(os.path.join(ROOT, "pyproject.toml"), "rb") as f:
            project = tomllib.load(f)["project"]["version"]
        self.assertEqual(project, tinkerprint.__version__)
        # The newest versioned heading in the changelog is this version. No "Unreleased" above it.
        headings = re.findall(r"^## (.+)$", read("CHANGELOG.md"), re.M)
        self.assertRegex(headings[0], r"^\d+\.\d+\.\d+ \(\d{4}-\d{2}-\d{2}\)$")
        self.assertEqual(headings[0].split()[0], tinkerprint.__version__)

    def test_method_doc_states_the_method_version(self):
        stated = re.match(r"# Method\n\nMethod version (\d+)\.", read("METHOD.md"))
        self.assertIsNotNone(stated)
        self.assertEqual(int(stated.group(1)), tinkerprint.METHOD_VERSION)

    def test_tools_stay_out_of_the_package(self):
        with open(os.path.join(ROOT, "pyproject.toml"), "rb") as f:
            find = tomllib.load(f)["tool"]["setuptools"]["packages"]["find"]
        self.assertEqual(find["where"], ["src"])
        self.assertFalse(os.path.exists(os.path.join(ROOT, "MANIFEST.in")))
        self.assertFalse(os.path.exists(os.path.join(ROOT, "src", "tools")))
