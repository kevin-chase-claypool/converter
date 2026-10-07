"""CMYK calibration sheet layout, screening, and the scan tool's fit."""

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

SOFTWARE = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SOFTWARE))
sys.path.insert(0, str(ROOT / "tools"))

import numpy as np
from PIL import Image, ImageDraw

import converter_core as converter
from generator_tabs import cmyk_sheet

import cmyk_calibrate


def build(**overrides):
    options = dict(
        page_width_mm=200.0,
        page_height_mm=200.0,
        margin_mm=6.0,
        pitch_mm=2.0,
        dot_scale=0.75,
        pen_width_mm=0.3,
        solid=True,
        gcr_pct=100.0,
        weights=(1.0, 1.0, 1.0, 1.0),
        gamma=1.0,
        overdraw=1,
    )
    options.update(overrides)
    return cmyk_sheet.build_sheet(**options)


class SheetBuilderTests(unittest.TestCase):
    def test_sheet_blocks_and_layers(self):
        layers, manifest = build()
        blocks = {}
        for patch in manifest["patches"]:
            blocks.setdefault(patch["block"], []).append(patch)
        self.assertEqual(len(manifest["fiducials_mm"]), 4)
        self.assertEqual(len(blocks["coverage"]), 40)
        self.assertEqual(len(blocks["steps"]), 28)
        self.assertEqual(len(blocks["overdraw"]), 12)
        self.assertEqual(len(blocks["gcr"]), 5)
        self.assertEqual(len(blocks["mix"]), 5)
        self.assertEqual(len(blocks["spot"]), 4)
        self.assertEqual(len(blocks["paper"]), 1)
        for channel in converter.CHANNELS:
            self.assertTrue(layers[channel], channel)
        ids = [patch["id"] for patch in manifest["patches"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_patch_rects_stay_inside_the_content_box(self):
        _, manifest = build()
        inset = 6.0 + cmyk_sheet.CONTENT_INSET_MM
        for patch in manifest["patches"]:
            x, y, width, height = patch["rect_mm"]
            self.assertGreaterEqual(x, inset - 0.1)
            self.assertGreaterEqual(y, inset - 0.1)
            self.assertLessEqual(x + width, 200.0 - inset + 0.1)
            self.assertLessEqual(y + height, 200.0 - inset + 0.1)

    def test_gcr_ramp_moves_the_gray_into_k(self):
        _, manifest = build(weights=(1.0, 1.0, 1.0, 1.0))
        gcr = {
            patch["label"]: patch
            for patch in manifest["patches"]
            if patch["block"] == "gcr"
        }
        self.assertEqual(gcr["0"]["channels"], ["c", "m", "y"])
        self.assertAlmostEqual(gcr["0"]["tones"]["k"], 0.0, places=5)
        self.assertAlmostEqual(gcr["0"]["tones"]["c"], 0.5, places=5)
        self.assertEqual(gcr["100"]["channels"], ["k"])
        self.assertAlmostEqual(gcr["100"]["tones"]["k"], 0.5, places=5)

    def test_small_page_is_rejected(self):
        with self.assertRaises(ValueError):
            build(page_width_mm=100.0, page_height_mm=100.0)

    def test_line_sheet_swaps_the_dot_ladder_for_pitch(self):
        layers, manifest = build(screen="lines", pitch_mm=1.2)
        self.assertEqual(manifest["sheet_settings"]["style"], "lines")
        steps = [
            patch
            for patch in manifest["patches"]
            if patch["block"] == "steps" and patch["channels"] == ["c"]
        ]
        self.assertEqual(
            [patch["label"] for patch in steps],
            ["0.6", "0.8", "1", "1.4", "1.8", "2.4", "3"],
        )
        self.assertEqual(
            [patch["pitch_mm"] for patch in steps],
            [0.6, 0.8, 1.0, 1.4, 1.8, 2.4, 3.0],
        )
        for channel in converter.CHANNELS:
            self.assertTrue(layers[channel])
        dot_layers, _ = build()
        line_marks = sum(len(layers[channel]) for channel in converter.CHANNELS)
        dot_marks = sum(
            len(dot_layers[channel]) for channel in converter.CHANNELS
        )
        self.assertLess(line_marks, dot_marks)

    def test_crosshatch_sheet_sweeps_hatch_levels(self):
        _, manifest = build(screen="crosshatch")
        self.assertEqual(manifest["sheet_settings"]["style"], "crosshatch")
        steps = [
            patch
            for patch in manifest["patches"]
            if patch["block"] == "steps" and patch["channels"] == ["m"]
        ]
        self.assertEqual(
            [patch["label"] for patch in steps],
            ["2", "3", "4", "5", "6", "7", "8"],
        )
        self.assertEqual(
            [patch["levels"] for patch in steps], [2, 3, 4, 5, 6, 7, 8]
        )

    def test_mix_cells_match_the_dense_spot_spacing(self):
        for screen in ("lines", "crosshatch", "halftone"):
            _, manifest = build(screen=screen)
            spots = {
                patch["channels"][0]: patch
                for patch in manifest["patches"]
                if patch["block"] == "spot"
            }
            for patch in manifest["patches"]:
                if patch["block"] != "mix":
                    continue
                for channel in patch["channels"]:
                    spot = spots[channel]
                    self.assertEqual(
                        patch.get("pitch_mm"), spot.get("pitch_mm"), screen
                    )
                    self.assertEqual(
                        patch.get("levels"), spot.get("levels"), screen
                    )
                    self.assertEqual(
                        patch["dot_scale"], spot["dot_scale"], screen
                    )

    def test_unknown_screen_is_rejected(self):
        with self.assertRaises(ValueError):
            build(screen="spirals")

    def test_manifest_only_build_matches_the_marked_sheet(self):
        _, marked = build()
        layers, plain = build(marks=False)
        self.assertEqual(
            [patch["rect_mm"] for patch in plain["patches"]],
            [patch["rect_mm"] for patch in marked["patches"]],
        )
        self.assertEqual(
            [patch["label"] for patch in plain["patches"]],
            [patch["label"] for patch in marked["patches"]],
        )
        self.assertEqual(plain["fiducials_mm"], marked["fiducials_mm"])
        for channel in converter.CHANNELS:
            self.assertEqual(layers[channel], [])

    def test_sheet_marks_stay_inside_the_page(self):
        for screen in ("lines", "crosshatch", "halftone"):
            layers, _ = build(screen=screen)
            for channel in converter.CHANNELS:
                for line in layers[channel]:
                    for x, y in line:
                        self.assertGreaterEqual(x, -1e-6, screen)
                        self.assertGreaterEqual(y, -1e-6, screen)
                        self.assertLessEqual(x, 200.0 + 1e-6, screen)
                        self.assertLessEqual(y, 200.0 + 1e-6, screen)

    def test_sheet_is_deterministic(self):
        first, manifest_a = build()
        second, manifest_b = build()
        for channel in converter.CHANNELS:
            self.assertEqual(len(first[channel]), len(second[channel]))
        self.assertEqual(
            [patch["rect_mm"] for patch in manifest_a["patches"]],
            [patch["rect_mm"] for patch in manifest_b["patches"]],
        )


class ScanToolTests(unittest.TestCase):
    def _render(self, manifest, transmittance):
        """Draw a synthetic scan with a known scale, offset, and rotation."""
        width_px = 1000
        height_px = 1000
        scale = 4.2
        angle = np.deg2rad(1.5)

        def transform(point):
            x = 60.0 + point[0] * scale
            y = 55.0 + point[1] * scale
            centre_x = width_px / 2.0
            centre_y = height_px / 2.0
            dx = x - centre_x
            dy = y - centre_y
            return (
                centre_x + dx * np.cos(angle) - dy * np.sin(angle),
                centre_y + dx * np.sin(angle) + dy * np.cos(angle),
            )

        image = Image.new("RGB", (width_px, height_px), (255, 255, 255))
        draw = ImageDraw.Draw(image)
        for patch in manifest["patches"]:
            colour = np.ones(3)
            for channel in patch.get("channels", []):
                tone = float(patch.get("tones", {}).get(channel, 0.0))
                ink = np.asarray(transmittance[channel])
                colour = colour * (1.0 - tone * (1.0 - ink))
            x, y, w, h = patch["rect_mm"]
            corners = [(x, y), (x + w, y), (x + w, y + h), (x, y + h)]
            draw.polygon(
                [transform(point) for point in corners],
                fill=tuple(int(round(value * 255.0)) for value in colour),
            )
        half = cmyk_sheet.FIDUCIAL_SIZE_MM / 2.0
        for fiducial in manifest["fiducials_mm"]:
            x, y = fiducial["x"], fiducial["y"]
            corners = [
                (x - half, y - half),
                (x + half, y - half),
                (x + half, y + half),
                (x - half, y + half),
            ]
            draw.polygon(
                [transform(point) for point in corners], fill=(25, 25, 25)
            )
        return np.asarray(image, dtype=np.float32) / 255.0, transform

    def _transmittance(self):
        return {
            "c": (0.72, 0.93, 0.97),
            "m": (0.94, 0.70, 0.91),
            "y": (0.96, 0.90, 0.42),
            "k": (0.34, 0.34, 0.36),
        }

    def test_tool_recovers_ink_numbers(self):
        _, manifest = build()
        transmittance = self._transmittance()
        image, transform = self._render(manifest, transmittance)
        corners = cmyk_calibrate.detect_fiducials(image)
        self.assertEqual(len(corners), 4)
        for fiducial, corner in zip(manifest["fiducials_mm"], corners):
            expected = transform((fiducial["x"], fiducial["y"]))
            self.assertAlmostEqual(corner[0], expected[0], delta=5.0)
            self.assertAlmostEqual(corner[1], expected[1], delta=5.0)
        samples = cmyk_calibrate.sample_sheet(image, manifest, corners)
        profile = cmyk_calibrate.fit_profile(manifest, samples)
        for channel, expected in transmittance.items():
            actual = profile["inks"][channel]
            for want, got in zip(expected, actual):
                self.assertAlmostEqual(got, want, delta=0.06)
        errors = [
            abs(value)
            for row in profile["validation"]
            for value in row["error"]
        ]
        self.assertEqual(len(profile["validation"]), 5)
        self.assertLess(max(errors), 0.10)

    def test_cli_writes_the_profile(self):
        folder = Path(tempfile.mkdtemp(prefix="cmyk-scan-"))
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        _, manifest = build()
        manifest_path = folder / "sheet-calibration.json"
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
        image, transform = self._render(manifest, self._transmittance())
        scan_path = folder / "scan.png"
        Image.fromarray((image * 255.0).astype("uint8")).save(scan_path)
        corners = [
            transform((fiducial["x"], fiducial["y"]))
            for fiducial in manifest["fiducials_mm"]
        ]
        args = [
            str(scan_path),
            "--manifest",
            str(manifest_path),
            "--corners",
            ",".join(f"{value:.1f}" for point in corners for value in point),
        ]
        with redirect_stdout(io.StringIO()):
            code = cmyk_calibrate.main(args)
        self.assertEqual(code, 0)
        profile_path = folder / "scan-profile.json"
        self.assertTrue(profile_path.exists())
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        self.assertEqual(profile["kind"], "cmyk-ink-profile")
        self.assertIn("c", profile["inks"])

    def test_cli_rebuilds_the_layout_without_a_manifest(self):
        folder = Path(tempfile.mkdtemp(prefix="cmyk-rebuild-"))
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        _, manifest = build()
        image, _transform = self._render(manifest, self._transmittance())
        scan_path = folder / "scan.png"
        Image.fromarray((image * 255.0).astype("uint8")).save(scan_path)
        args = [
            str(scan_path),
            "--layout",
            "200x200",
            "--margin",
            "6",
            "--screen",
            "halftone",
        ]
        with redirect_stdout(io.StringIO()):
            code = cmyk_calibrate.main(args)
        self.assertEqual(code, 0)
        profile_path = folder / "scan-profile.json"
        self.assertTrue(profile_path.exists())
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        for channel, expected in self._transmittance().items():
            actual = profile["inks"][channel]
            for want, got in zip(expected, actual):
                self.assertAlmostEqual(got, want, delta=0.06)

    def test_cli_needs_a_manifest_or_a_layout(self):
        folder = Path(tempfile.mkdtemp(prefix="cmyk-args-"))
        self.addCleanup(
            lambda: __import__("shutil").rmtree(folder, ignore_errors=True)
        )
        scan_path = folder / "scan.png"
        Image.new("RGB", (64, 64), (255, 255, 255)).save(scan_path)
        with redirect_stdout(io.StringIO()), self.assertRaises(SystemExit):
            cmyk_calibrate.main([str(scan_path)])


if __name__ == "__main__":
    unittest.main()
