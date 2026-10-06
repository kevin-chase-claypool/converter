"""Wobble post-process tab.

Parameters ported from the Unlicense-licensed cadin/line-wobbler
(https://github.com/cadin/line-wobbler): a line is subdivided every
``frequency`` millimetres; each subpoint is offset perpendicular by up to
``amplitude`` and parallel by up to ``frequencyJitter`` percent of the
frequency. This tab wobbles the contours of the current preview, so it is a
post-process: preview artwork in any tool first, then wobble it here.
"""

from __future__ import annotations

import math
import random

from PySide6.QtWidgets import QCheckBox

from ._tab_common import GeneratorTab, double_spin, int_spin, scale_polylines


TITLE = "Wobble"
ORDER = 120


def wobble_polylines(
    polylines,
    frequency_mm=3.0,
    amplitude_mm=0.5,
    jitter_pct=20.0,
    seed=7,
    wobble_end_amplitude=True,
    wobble_end_position=True,
):
    """Return hand-drawn wobbled copies of the input polylines."""
    rng = random.Random(int(seed))
    frequency = max(0.1, float(frequency_mm))
    amplitude = max(0.0, float(amplitude_mm))
    jitter = max(0.001, frequency * max(0.0, float(jitter_pct)) / 100.0)
    result = []
    for contour in polylines:
        points = [(float(point[0]), float(point[1])) for point in contour]
        if len(points) < 2:
            continue
        wobbled = [points[0]]
        for (x1, y1), (x2, y2) in zip(points, points[1:]):
            length = math.hypot(x2 - x1, y2 - y1)
            count = max(int(length / frequency), 1)
            angle = math.atan2(y2 - y1, x2 - x1)
            for index in range(1, count):
                t = index / count
                px = x1 + (x2 - x1) * t
                py = y1 + (y2 - y1) * t
                perpendicular = rng.uniform(-amplitude, amplitude)
                parallel = rng.uniform(-jitter, jitter)
                px += (
                    math.cos(angle + math.pi / 2.0) * perpendicular
                    + math.cos(angle) * parallel
                )
                py += (
                    math.sin(angle + math.pi / 2.0) * perpendicular
                    + math.sin(angle) * parallel
                )
                wobbled.append((px, py))
            wobbled.append((x2, y2))
        if wobble_end_amplitude or wobble_end_position:
            for index in (0, len(wobbled) - 1):
                x, y = wobbled[index]
                angle = math.atan2(
                    wobbled[min(index + 1, len(wobbled) - 1)][1] - y,
                    wobbled[min(index + 1, len(wobbled) - 1)][0] - x,
                )
                dx = dy = 0.0
                if wobble_end_amplitude:
                    perpendicular = rng.uniform(-amplitude, amplitude)
                    dx += math.cos(angle + math.pi / 2.0) * perpendicular
                    dy += math.sin(angle + math.pi / 2.0) * perpendicular
                if wobble_end_position:
                    parallel = rng.uniform(-jitter, jitter)
                    dx += math.cos(angle) * parallel
                    dy += math.sin(angle) * parallel
                wobbled[index] = (x + dx, y + dy)
        if len(wobbled) >= 2:
            result.append(wobbled)
    return result


class WobbleTab(GeneratorTab):
    NAME = "wobble"
    GROUP = "Algorithm only"
    DESCRIPTION = "Hand-drawn wobble for the current preview contours."

    def __init__(self, host):
        super().__init__(host)
        wobble = self.add_group("Wobble")
        self.frequency = double_spin(3.0, 0.5, 20.0, 0.5, 1, " mm")
        wobble.addRow("Frequency", self.frequency)
        self.amplitude = double_spin(0.5, 0.0, 5.0, 0.1, 2, " mm")
        wobble.addRow("Amplitude", self.amplitude)
        self.jitter = double_spin(20, 0, 100, 5, 0, " %")
        wobble.addRow("Frequency jitter", self.jitter)
        self.seed = int_spin(7, 0, 999_999)
        wobble.addRow("Seed", self.seed)
        self.end_amplitude = QCheckBox("Wobble end amplitude")
        self.end_amplitude.setChecked(True)
        wobble.addRow("", self.end_amplitude)
        self.end_position = QCheckBox("Wobble end position")
        self.end_position.setChecked(True)
        wobble.addRow("", self.end_position)

        page = self.add_group("Page")
        self.margin = double_spin(6, 0, 60, 1, 0, " mm")
        page.addRow("Margin", self.margin)
        self.line_width = double_spin(0.3, 0.1, 1.2, 0.05, 2, " mm")
        page.addRow("Line width", self.line_width)
        self.scale_pct = double_spin(100, 10, 1000, 5, 0, " %")
        page.addRow("Artwork scale", self.scale_pct)

        self.finish_controls()

    def _source_contours(self):
        if self.host is None or not hasattr(self.host, "current_contours"):
            raise ValueError("No preview contours are available.")
        contours = self.host.current_contours()
        if not contours:
            raise ValueError(
                "Press Preview in a tool first; Wobble processes the current "
                "preview contours."
            )
        return contours

    def build_svg(self):
        contours = self._source_contours()
        polylines = wobble_polylines(
            contours,
            frequency_mm=self.frequency.value(),
            amplitude_mm=self.amplitude.value(),
            jitter_pct=self.jitter.value(),
            seed=self.seed.value(),
            wobble_end_amplitude=self.end_amplitude.isChecked(),
            wobble_end_position=self.end_position.isChecked(),
        )
        xs = [x for line in polylines for x, _y in line]
        ys = [y for line in polylines for _x, y in line]
        margin = self.margin.value()
        width = max(10.0, max(xs) - min(xs) + 2 * margin)
        height = max(10.0, max(ys) - min(ys) + 2 * margin)
        offset_x = margin - min(xs)
        offset_y = margin - min(ys)
        polylines = [
            [(x + offset_x, y + offset_y) for x, y in line]
            for line in polylines
        ]
        polylines = scale_polylines(
            polylines, self.scale_pct.value() / 100.0, width, height
        )
        return self.write_result(
            polylines,
            width,
            height,
            self.line_width.value(),
            f"{len(polylines)} wobbled contours.",
        )


def create_tab(host):
    return WobbleTab(host)
