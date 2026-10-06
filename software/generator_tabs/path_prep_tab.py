"""Path preparation tab, vpype-style.

Implements the four operations from the MIT-licensed vpype ecosystem that
matter for plotter artwork: linemerge (collapse collinear points),
deduplicate (drop repeated segments), reloop (join ends within a gap
tolerance), and linesort (nearest-neighbour ordering). It runs on the current
preview contours, like Wobble. The full vpype CLI remains the external tool of
record; this tab is the documented in-app subset.
"""

from __future__ import annotations

import math

from PySide6.QtWidgets import QCheckBox

from ._tab_common import GeneratorTab, double_spin, scale_polylines


TITLE = "Path Prep"
ORDER = 150


def _segment_key(first, second, tolerance):
    if tolerance <= 0:
        pair = ((round(first[0], 6), round(first[1], 6)),
                (round(second[0], 6), round(second[1], 6)))
        return tuple(sorted(pair))
    cells = tolerance
    def cell(point):
        return (round(point[0] / cells), round(point[1] / cells))
    return tuple(sorted((cell(first), cell(second))))


def _merge_collinear(lines, angle_deg, distance_mm):
    if angle_deg <= 0 and distance_mm <= 0:
        return lines
    limit = math.radians(max(0.0, angle_deg))
    merged = []
    for line in lines:
        if len(line) < 3:
            merged.append(list(line))
            continue
        output = [line[0]]
        for index in range(1, len(line) - 1):
            first = output[-1]
            middle = line[index]
            following = line[index + 1]
            v1 = (middle[0] - first[0], middle[1] - first[1])
            v2 = (following[0] - middle[0], following[1] - middle[1])
            norm1 = math.hypot(*v1) or 1.0
            norm2 = math.hypot(*v2) or 1.0
            dot = (v1[0] * v2[0] + v1[1] * v2[1]) / (norm1 * norm2)
            turn = math.acos(max(-1.0, min(1.0, dot)))
            chord = math.hypot(
                following[0] - first[0], following[1] - first[1]
            ) or 1.0
            cross = abs(v1[0] * v2[1] - v1[1] * v2[0]) / (norm1 * norm2)
            deviation = cross * norm1
            if turn <= limit and deviation <= distance_mm:
                continue
            output.append(middle)
        output.append(line[-1])
        merged.append(output)
    return merged


def _deduplicate(lines, tolerance_mm):
    seen = set()
    result = []
    for line in lines:
        run = [line[0]]
        for first, second in zip(line, line[1:]):
            key = _segment_key(first, second, tolerance_mm)
            if key in seen:
                if len(run) >= 2:
                    result.append(run)
                run = [second]
                continue
            seen.add(key)
            run.append(second)
        if len(run) >= 2:
            result.append(run)
    return result


def _close_gaps(lines, gap_mm, limit=10_000):
    remaining = [list(line) for line in lines if len(line) >= 2]
    chains = []
    while remaining:
        chain = remaining.pop(0)
        joined = True
        steps = 0
        while joined and remaining and steps < limit:
            joined = False
            steps += 1
            for index, candidate in enumerate(remaining):
                if math.hypot(
                    chain[-1][0] - candidate[0][0],
                    chain[-1][1] - candidate[0][1],
                ) <= gap_mm:
                    chain.extend(candidate[1:])
                elif math.hypot(
                    chain[-1][0] - candidate[-1][0],
                    chain[-1][1] - candidate[-1][1],
                ) <= gap_mm:
                    chain.extend(reversed(candidate[:-1]))
                else:
                    continue
                remaining.pop(index)
                joined = True
                break
        chains.append(chain)
    return chains


def _sort_lines(lines, reverse=False):
    if not lines:
        return lines
    remaining = [list(line) for line in lines]
    ordered = []
    current = remaining.pop(0)
    ordered.append(current)
    while remaining:
        end = current[-1]
        best_index = 0
        best_reverse = False
        best_distance = float("inf")
        for index, candidate in enumerate(remaining):
            for flip, point in ((False, candidate[0]), (True, candidate[-1])):
                distance = math.hypot(end[0] - point[0], end[1] - point[1])
                if distance < best_distance:
                    best_distance = distance
                    best_index = index
                    best_reverse = flip
        current = remaining.pop(best_index)
        if best_reverse:
            current = list(reversed(current))
        ordered.append(current)
    if reverse:
        ordered = [list(reversed(line)) for line in reversed(ordered)]
    return ordered


def path_prep_polylines(
    polylines,
    merge_angle_deg=5.0,
    merge_distance_mm=0.05,
    duplicate_mm=0.05,
    gap_mm=0.2,
    sort=True,
    reverse=False,
):
    """Return the cleaned polylines (page placement is the tab's job)."""
    lines = [
        [(float(point[0]), float(point[1])) for point in line]
        for line in polylines
        if len(line) >= 2
    ]
    lines = _merge_collinear(lines, merge_angle_deg, merge_distance_mm)
    lines = _deduplicate(lines, duplicate_mm)
    if gap_mm > 0:
        lines = _close_gaps(lines, gap_mm)
    if sort:
        lines = _sort_lines(lines, reverse=reverse)
    return lines


class PathPrepTab(GeneratorTab):
    NAME = "path-prep"
    GROUP = "Algorithm only"
    DESCRIPTION = "vpype-style merge, dedupe, reloop, and sort on the preview."

    def __init__(self, host):
        super().__init__(host)
        prep = self.add_group("Cleanup")
        self.merge_angle = double_spin(5.0, 0.0, 45.0, 1.0, 1, " deg")
        prep.addRow("Merge angle", self.merge_angle)
        self.merge_distance = double_spin(0.05, 0.0, 2.0, 0.05, 2, " mm")
        prep.addRow("Merge tolerance", self.merge_distance)
        self.duplicate = double_spin(0.05, 0.0, 2.0, 0.05, 2, " mm")
        prep.addRow("Duplicate tolerance", self.duplicate)
        self.gap = double_spin(0.2, 0.0, 5.0, 0.1, 2, " mm")
        prep.addRow("Close gaps under", self.gap)

        order = self.add_group("Order")
        self.sort = QCheckBox("Sort by nearest neighbour")
        self.sort.setChecked(True)
        order.addRow("", self.sort)
        self.reverse = QCheckBox("Reverse the sorted order")
        order.addRow("", self.reverse)

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
                "Press Preview in a tool first; Path Prep cleans the current "
                "preview contours."
            )
        return contours

    def build_svg(self):
        contours = self._source_contours()
        polylines = path_prep_polylines(
            contours,
            merge_angle_deg=self.merge_angle.value(),
            merge_distance_mm=self.merge_distance.value(),
            duplicate_mm=self.duplicate.value(),
            gap_mm=self.gap.value(),
            sort=self.sort.isChecked(),
            reverse=self.reverse.isChecked(),
        )
        xs = [x for line in polylines for x, _y in line]
        ys = [y for line in polylines for _x, y in line]
        margin = self.margin.value()
        width = max(10.0, max(xs) - min(xs) + 2 * margin)
        height = max(10.0, max(ys) - min(ys) + 2 * margin)
        polylines = [
            [(x - min(xs) + margin, y - min(ys) + margin) for x, y in line]
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
            f"{len(polylines)} prepared paths.",
        )


def create_tab(host):
    return PathPrepTab(host)
