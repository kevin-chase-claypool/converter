"""Controller macro syntax validation."""

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_checker():
    path = ROOT / "tools" / "check_macros.py"
    spec = importlib.util.spec_from_file_location("check_macros", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MacroSyntaxTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checker = load_checker()

    def test_nested_comment_parentheses_are_rejected(self):
        with tempfile.TemporaryDirectory(prefix="macro-check-") as folder:
            path = Path(folder) / "P999.macro"
            path.write_text(
                "(outer comment (inner token) then more comment)\n"
                "o999 return [1]\n",
                encoding="utf-8",
            )
            problems = self.checker.check_file(path)
        self.assertTrue(
            any("nested parentheses" in problem for problem in problems),
            problems,
        )

    def test_all_controller_macros_pass(self):
        for path in sorted(self.checker.DEFAULT_DIR.glob("*.macro")):
            with self.subTest(path=path.name):
                self.assertEqual(self.checker.check_file(path), [])


if __name__ == "__main__":
    unittest.main()
