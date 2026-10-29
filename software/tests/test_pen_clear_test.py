"""Generate the T-01H no-drag diagnostic program."""

import importlib.util
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter


class PenClearTestGeneratorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = ROOT / "tools" / "make_pen_clear_test.py"
        spec = importlib.util.spec_from_file_location("make_pen_clear_test", path)
        cls.module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = cls.module
        spec.loader.exec_module(cls.module)

    def test_program_has_thirty_single_start_witness_cycles(self):
        program, points = self.module.build_program(converter.Settings())
        self.assertEqual(len(points), 30)
        self.assertEqual(program.count("M3"), 30)
        self.assertEqual(program.count("M5"), 31)
        self.assertNotIn("M0 (", program)
        self.assertEqual(program.count("(witness)"), 30)
        self.assertEqual(program.count("(travel)"), 30)

    def test_travel_groups_exercise_three_speeds(self):
        program, _points = self.module.build_program(converter.Settings())
        self.assertEqual(program.count("F300 (travel)"), 10)
        self.assertEqual(program.count("F1000 (travel)"), 10)
        self.assertEqual(program.count("F3000 (travel)"), 10)

    def test_committed_pen_clear_sample_matches_generator(self):
        program, _points = self.module.build_program(converter.Settings())
        sample = ROOT / "samples" / "gcode" / "pen-clear-no-drag-30.gcode"
        self.assertEqual(sample.read_text(encoding="utf-8"), program)


if __name__ == "__main__":
    unittest.main()
