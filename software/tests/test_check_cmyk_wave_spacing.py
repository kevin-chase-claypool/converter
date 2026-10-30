"""Regression checks for the final CMYK Wave row-spacing verifier."""

import contextlib
import importlib.util
import io
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

    def test_manifest_accepts_a_row_locked_profile(self):
        folder = Path(tempfile.mkdtemp(prefix="cmyk-wave-manifest-"))
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        path = folder / "set.json"
        data = {
            "kind": "cmyk-print-set",
            "bed_motion": "XY only (bed parked, precise)",
            "bed_compensation_path": "bed.json",
            "bed_compensation": {
                "mode": "row_locked_projection",
                "profile_fingerprint": "18bfb4ed1c33",
                "per_channel_max_correction_mm": {
                    "c": 0.5,
                    "m": 0.5,
                    "y": 0.5,
                    "k": 0.5,
                },
            },
            "screen": {
                "style": "waves_even",
                "preserve_exact_row_pitch": True,
            },
        }
        path.write_text(json.dumps(data), encoding="utf-8")

        loaded = self.checker.load_manifest(path)

        self.assertEqual(
            loaded["bed_compensation"]["mode"],
            "row_locked_projection",
        )

    def test_manifest_rejects_raw_bed_compensation(self):
        folder = Path(tempfile.mkdtemp(prefix="cmyk-wave-manifest-"))
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        path = folder / "set.json"
        data = {
            "kind": "cmyk-print-set",
            "bed_motion": "XY only (bed parked, precise)",
            "bed_compensation_path": "bed.json",
            "bed_compensation": {
                "mode": "raw_unconstrained",
                "profile_fingerprint": "18bfb4ed1c33",
            },
            "screen": {
                "style": "waves_even",
                "preserve_exact_row_pitch": True,
            },
        }
        path.write_text(json.dumps(data), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "raw bed compensation"):
            self.checker.load_manifest(path)

    def test_audit_requires_the_row_locked_header_for_an_active_profile(self):
        folder = Path(tempfile.mkdtemp(prefix="cmyk-wave-manifest-"))
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        gcode = "\n".join(
            (
                "(bed compensation 18bfb4ed1c33, row-locked projection)",
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
        ) + "\n"
        files = {}
        hashes = {}
        for channel in ("c", "m", "y", "k"):
            path = folder / f"{channel}.gcode"
            path.write_text(gcode, encoding="utf-8")
            files[channel] = path.name
            hashes[channel] = self.checker.sha256_file(path)
        manifest = folder / "set.json"
        data = {
            "kind": "cmyk-print-set",
            "bed_motion": "XY only (bed parked, precise)",
            "bed_compensation_path": "bed.json",
            "bed_compensation": {
                "mode": "row_locked_projection",
                "profile_fingerprint": "18bfb4ed1c33",
                "per_channel_max_correction_mm": {
                    "c": 0.5,
                    "m": 0.5,
                    "y": 0.5,
                    "k": 0.5,
                },
            },
            "screen": {
                "style": "waves_even",
                "preserve_exact_row_pitch": True,
                "effective_pitch_mm": 2.0,
                "screen_angles_deg": {
                    "c": 0.0,
                    "m": 0.0,
                    "y": 0.0,
                    "k": 0.0,
                },
            },
            "files": files,
            "file_sha256": hashes,
        }
        manifest.write_text(json.dumps(data), encoding="utf-8")

        with contextlib.redirect_stdout(io.StringIO()):
            result = self.checker.main(
                [str(manifest), "--sample-columns", "3"]
            )

        self.assertEqual(result, 0)
        cyan = folder / files["c"]
        cyan.write_text(
            cyan.read_text(encoding="utf-8").replace(
                "(bed compensation 18bfb4ed1c33, row-locked projection)\n",
                "",
            ),
            encoding="utf-8",
        )
        data["file_sha256"]["c"] = self.checker.sha256_file(cyan)
        manifest.write_text(json.dumps(data), encoding="utf-8")

        with contextlib.redirect_stdout(io.StringIO()):
            result = self.checker.main(
                [str(manifest), "--sample-columns", "3"]
            )

        self.assertEqual(result, 2)


if __name__ == "__main__":
    unittest.main()
