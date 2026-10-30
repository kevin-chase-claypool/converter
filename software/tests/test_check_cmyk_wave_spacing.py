"""Regression checks for the final CMYK Wave row-spacing verifier."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_checker():
    path = ROOT / "tools" / "check_cmyk_wave_spacing.py"
    spec = importlib.util.spec_from_file_location(
        "check_cmyk_wave_spacing", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class CheckCmykWaveSpacingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checker = load_checker()

    def test_audit_reads_final_machine_coordinates(self):
        folder = Path(tempfile.mkdtemp(prefix="cmyk-wave-audit-"))
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        path = folder / "rows.gcode"
        path.write_text(
            "\n".join(
                (
                    "M5",
                    "M3",
                    "G1 X0 Y0 F700",
                    "G1 X10 Y0 F700",
                    "M5",
                    "M3",
                    "G1 X0 Y2 F700",
                    "G1 X10 Y2 F700",
                    "M5",
                )
            ),
            encoding="utf-8",
        )

        result = self.checker.audit_program(path, 0.0, 2.0)

        self.assertEqual(result["samples"], 199)
        self.assertEqual(result["measurements"], 199)
        self.assertAlmostEqual(result["minimum_mm"], 2.0)
        self.assertAlmostEqual(result["maximum_mm"], 2.0)
        self.assertAlmostEqual(result["spread_mm"], 0.0)

    def test_manifest_requires_the_wave_spacing_guard(self):
        folder = Path(tempfile.mkdtemp(prefix="cmyk-wave-manifest-"))
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        path = folder / "set.json"
        data = {
            "kind": "cmyk-print-set",
            "bed_motion": "XY only (bed parked, precise)",
            "bed_compensation_path": "",
            "screen": {
                "style": "waves_even",
                "preserve_exact_row_pitch": False,
            },
        }
        path.write_text(json.dumps(data), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "row-spacing guard"):
            self.checker.load_manifest(path)


if __name__ == "__main__":
    unittest.main()
