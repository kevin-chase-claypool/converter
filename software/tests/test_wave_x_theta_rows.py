"""Exact row pitch must survive the rotating-bed Wave planner."""

import math
import re
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "software"))

import converter_core as converter


WORD = re.compile(r"([XYA])(-?\d+(?:\.\d+)?)", re.IGNORECASE)
CONTOUR = re.compile(r"^\(contour (\d+)")


def drawing_contours(gcode):
    x = y = a = 0.0
    drawing = False
    contours = []
    for raw_line in gcode.splitlines():
        line = raw_line.strip()
        if line == "M3":
            drawing = True
            contours.append([])
            continue
        if line == "M5":
            drawing = False
            continue
        if not line.startswith("G1 "):
            continue
        words = {
            key.upper(): float(value)
            for key, value in WORD.findall(line)
        }
        next_x = words.get("X", x)
        next_y = words.get("Y", y)
        next_a = words.get("A", a)
        if drawing and any(key in words for key in ("X", "Y", "A")):
            contours[-1].append((x, y, a, next_x, next_y, next_a))
        x, y, a = next_x, next_y, next_a
    return [contour for contour in contours if contour]


def decoded_rows(gcode, ratio):
    rows = []
    for contour in drawing_contours(gcode):
        points = []
        for start_x, start_y, start_a, end_x, end_y, end_a in contour:
            for index in range(9):
                fraction = index / 8.0
                machine_x = start_x + fraction * (end_x - start_x)
                machine_y = start_y + fraction * (end_y - start_y)
                motor_angle = start_a + fraction * (end_a - start_a)
                theta = math.radians(-motor_angle / ratio)
                cosine = math.cos(theta)
                sine = math.sin(theta)
                points.append(
                    (
                        machine_x * cosine - machine_y * sine,
                        machine_x * sine + machine_y * cosine,
                    )
                )
        rows.append(points)
    return rows


def value_at_x(points, x_value):
    for first, second in zip(points, points[1:]):
        lower, upper = sorted((first[0], second[0]))
        if not lower - 1e-9 <= x_value <= upper + 1e-9:
            continue
        delta = second[0] - first[0]
        if abs(delta) <= 1e-12:
            continue
        fraction = (x_value - first[0]) / delta
        return first[1] + fraction * (second[1] - first[1])
    return None


def row_gap_spread(rows, angle_deg):
    angle = math.radians(-angle_deg)
    cosine = math.cos(angle)
    sine = math.sin(angle)
    screen_rows = [
        [
            (
                x_value * cosine + y_value * sine,
                -x_value * sine + y_value * cosine,
            )
            for x_value, y_value in row
        ]
        for row in rows
    ]
    xs = [point[0] for row in screen_rows for point in row]
    low, high = min(xs), max(xs)
    gaps = []
    for fraction in np.linspace(0.1, 0.9, 81):
        x_value = low + fraction * (high - low)
        values = sorted(
            value
            for row in screen_rows
            if (value := value_at_x(row, x_value)) is not None
        )
        gaps.extend(
            second - first
            for first, second in zip(values, values[1:])
            if 3.0 < second - first < 5.0
        )
    return max(gaps) - min(gaps)


class WaveXThetaRowsTests(unittest.TestCase):
    def test_x_theta_wave_rows_keep_the_same_pitch_at_every_angle(self):
        page_mm = 64.0
        _yy, xx = np.mgrid[0:128, 0:128]
        tone = (0.35 + 0.45 * xx / 127.0).astype("float32")
        for order in ("rows_ascending", "rows_descending"):
            for angle_deg in converter.SCREEN_ANGLES_DEG.values():
                with self.subTest(order=order, angle_deg=angle_deg):
                    marks = converter.screen_channel(
                        tone,
                        {
                            "off_x": 0.0,
                            "off_y": 0.0,
                            "width_mm": page_mm,
                            "height_mm": page_mm,
                            "pixels_w": 128,
                            "pixels_h": 128,
                        },
                        style="waves_even",
                        spacing_mm=4.0,
                        angle_deg=angle_deg,
                        pen_diameter_mm=0.8,
                        row_clearance_mm=1.05,
                    )
                    document = converter.svg_document(
                        {"y": marks},
                        page_mm,
                        page_mm,
                        0.8,
                        order=["y"],
                    )
                    settings = converter.Settings(
                        theta_mode="optimized",
                        theta_center_hold_diameter_mm=0.0,
                        bed_compensation_path="",
                        row_locked_compensation=True,
                        row_lock_screen_angle_deg=angle_deg,
                        contour_order=order,
                        frame_center_mm=(
                            page_mm / 2.0,
                            page_mm / 2.0,
                        ),
                        flip_y=True,
                        tolerance=0.05,
                        pen_diameter_mm=0.8,
                    )

                    with tempfile.TemporaryDirectory() as folder:
                        path = Path(folder) / "waves.svg"
                        path.write_text(document, encoding="utf-8")
                        contours = converter.read_svg(str(path), settings)
                        program_plan = converter.plan_program(
                            contours,
                            settings,
                        )
                        schedule = program_plan["wave_row_schedule"]
                        self.assertIsNotNone(schedule)
                        self.assertGreater(
                            max(schedule["thetas"])
                            - min(schedule["thetas"]),
                            1.0,
                            "the shared schedule should still use the bed",
                        )
                        for _planned, _points, thetas, _labels in (
                            program_plan["planned_jobs"]
                        ):
                            self.assertLessEqual(
                                max(
                                    abs(second - first)
                                    for first, second in zip(
                                        thetas,
                                        thetas[1:],
                                    )
                                ),
                                settings.theta_max_step_deg + 1e-6,
                            )
                        gcode = converter.contours_to_gcode(
                            contours,
                            settings,
                            program_plan,
                        )

                    contour_ids = [
                        int(match.group(1))
                        for line in gcode.splitlines()
                        if (match := CONTOUR.match(line))
                    ]
                    self.assertEqual(
                        contour_ids,
                        sorted(
                            contour_ids,
                            reverse=order == "rows_descending",
                        ),
                    )
                    self.assertIn("shared Wave row angles", gcode)
                    spread = row_gap_spread(
                        decoded_rows(
                            gcode,
                            settings.theta_drive_ratio,
                        ),
                        angle_deg,
                    )
                    self.assertLessEqual(
                        spread,
                        0.005,
                        "rotating-bed interpolation must not change "
                        "Wave row pitch",
                    )


if __name__ == "__main__":
    unittest.main()
