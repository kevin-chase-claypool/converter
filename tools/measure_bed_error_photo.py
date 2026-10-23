"""Measure a photographed full-field bed calibration sheet.

The current sheet uses one pen and encodes pass angle by marker lane. This tool
finds the printed L components, uses the four large fiducials to fit a
projective sheet transform, measures the shared corner of every station L, and
writes the companion measurement CSV used by
``analyze_bed_error_calibration.py``.

The defaults target a straight-down phone photo with reasonably even lighting.
The paper must fill a substantial part of the image and the four large
fiducials must all be visible.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software"))

from converter_core.bed_calibration import expected_marks  # noqa: E402


@dataclass(frozen=True)
class Component:
    points: tuple[tuple[int, int], ...]
    bbox: tuple[int, int, int, int]

    @property
    def maximum_dimension(self):
        x0, y0, x1, y1 = self.bbox
        return max(x1 - x0 + 1, y1 - y0 + 1)


def _connected_components(mask):
    ys, xs = np.nonzero(mask)
    remaining = set(zip(xs.tolist(), ys.tolist()))
    components = []
    while remaining:
        seed = remaining.pop()
        stack = [seed]
        points = [seed]
        while stack:
            x_value, y_value = stack.pop()
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    neighbour = (x_value + dx, y_value + dy)
                    if neighbour in remaining:
                        remaining.remove(neighbour)
                        stack.append(neighbour)
                        points.append(neighbour)
        if len(points) >= 10:
            x0 = min(point[0] for point in points)
            y0 = min(point[1] for point in points)
            x1 = max(point[0] for point in points)
            y1 = max(point[1] for point in points)
            components.append(
                Component(tuple(points), (x0, y0, x1, y1))
            )
    return tuple(components)


def _working_mask(
    shape,
    *,
    center_fraction=(0.5295, 0.4869),
    radius_fraction=0.4322,
):
    height, width = shape
    center_x = (width - 1) * center_fraction[0]
    center_y = (height - 1) * center_fraction[1]
    radius = min(width, height) * radius_fraction
    y_values, x_values = np.ogrid[:height, :width]
    mask = (
        (x_values - center_x) ** 2 + (y_values - center_y) ** 2
        <= radius * radius
    )
    return mask, (center_x, center_y), radius


def _component_corner(component, quadrant):
    points = np.asarray(component.points, dtype=float)
    if quadrant == (0, 0):
        value = points[:, 0].max()
        return np.array(
            [value, np.median(points[points[:, 0] >= value - 1, 1])]
        )
    if quadrant == (1, 0):
        value = points[:, 1].min()
        return np.array(
            [np.median(points[points[:, 1] <= value + 1, 0]), value]
        )
    if quadrant == (1, 1):
        value = points[:, 0].min()
        return np.array(
            [value, np.median(points[points[:, 0] <= value + 1, 1])]
        )
    value = points[:, 1].max()
    return np.array(
        [np.median(points[points[:, 1] >= value - 1, 0]), value]
    )


def _fit_homography(nominal_points, image_points):
    rows = []
    values = []
    for (x_mm, y_mm), (image_x, image_y) in zip(
        nominal_points, image_points
    ):
        rows.append(
            [
                x_mm,
                y_mm,
                1.0,
                0.0,
                0.0,
                0.0,
                -image_x * x_mm,
                -image_x * y_mm,
            ]
        )
        values.append(image_x)
        rows.append(
            [
                0.0,
                0.0,
                0.0,
                x_mm,
                y_mm,
                1.0,
                -image_y * x_mm,
                -image_y * y_mm,
            ]
        )
        values.append(image_y)
    coefficients = np.linalg.solve(np.asarray(rows), np.asarray(values))
    return np.append(coefficients, 1.0).reshape(3, 3)


def _forward(homography, point):
    result = homography @ np.asarray([point[0], point[1], 1.0])
    return result[:2] / result[2]


def _inverse(inverse_homography, point):
    result = inverse_homography @ np.asarray([point[0], point[1], 1.0])
    return result[:2] / result[2]


def _station_vertex(component, homography, nominal_point):
    """Return the shared corner centre of one station L."""
    x0, y0, x1, y1 = component.bbox
    approximation = np.asarray([x1, y1], dtype=float)
    origin = _forward(homography, nominal_point)
    x_axis = _forward(
        homography, (nominal_point[0] + 1.0, nominal_point[1])
    ) - origin
    y_axis = _forward(
        homography, (nominal_point[0], nominal_point[1] + 1.0)
    ) - origin
    axes = np.column_stack((x_axis, y_axis))
    axes_inverse = np.linalg.inv(axes)
    points = np.asarray(component.points, dtype=float)
    local = (points - approximation) @ axes_inverse.T
    horizontal = local[
        (local[:, 0] < -1.5) & (np.abs(local[:, 1]) < 3.0)
    ]
    vertical = local[
        (local[:, 1] > 1.5) & (np.abs(local[:, 0]) < 3.0)
    ]
    if len(horizontal) < 5 or len(vertical) < 5:
        return approximation
    corner_local = np.asarray(
        [np.median(vertical[:, 0]), np.median(horizontal[:, 1])]
    )
    return approximation + axes @ corner_local


def measure_photo(
    image_path,
    *,
    threshold=20,
    blur_radius=18.0,
    mask_center_fraction=(0.5295, 0.4869),
    mask_radius_fraction=0.4322,
    maximum_assignment_px=8.0,
):
    source = Image.open(image_path).convert("L")
    background = source.filter(ImageFilter.GaussianBlur(blur_radius))
    gray = np.asarray(source, dtype=np.int16)
    local_background = np.asarray(background, dtype=np.int16)
    residual = local_background - gray
    paper_mask, center, working_radius = _working_mask(
        gray.shape,
        center_fraction=mask_center_fraction,
        radius_fraction=mask_radius_fraction,
    )
    components = _connected_components(
        (residual > threshold) & paper_mask
    )
    large = tuple(
        component
        for component in components
        if component.maximum_dimension > 40
    )
    medium = tuple(
        component
        for component in components
        if 16 <= component.maximum_dimension <= 30
    )
    small = tuple(
        component
        for component in components
        if component.maximum_dimension < 16
    )
    if not (len(large) == 4 and len(medium) == 185 and len(small) == 74):
        raise ValueError(
            "unexpected component counts: %d fiducial, %d L-mark, %d label"
            % (len(large), len(medium), len(small))
        )

    fiducials_by_quadrant = {}
    for component in large:
        points = np.asarray(component.points, dtype=float)
        component_center = points.mean(axis=0)
        quadrant = (
            0 if component_center[0] > center[0] else 1,
            0 if component_center[1] < center[1] else 1,
        )
        fiducials_by_quadrant[quadrant] = component
    if set(fiducials_by_quadrant) != {(0, 0), (1, 0), (1, 1), (0, 1)}:
        raise ValueError("the four fiducials are not in four distinct quadrants")
    quadrants = ((0, 0), (1, 0), (1, 1), (0, 1))
    image_fiducials = np.asarray(
        [
            _component_corner(fiducials_by_quadrant[quadrant], quadrant)
            for quadrant in quadrants
        ]
    )
    expected = expected_marks()
    expected_fiducials = tuple(
        mark for mark in expected if mark.section == "fiducial"
    )
    nominal_fiducials = np.asarray(
        [
            (mark.nominal_x_mm, mark.nominal_y_mm)
            for mark in expected_fiducials
        ]
    )
    homography = _fit_homography(nominal_fiducials, image_fiducials)
    inverse_homography = np.linalg.inv(homography)

    station_marks = tuple(mark for mark in expected if mark.section == "station")
    approximate_vertices = np.asarray(
        [(component.bbox[2], component.bbox[3]) for component in medium],
        dtype=float,
    )
    candidates = []
    for expected_index, mark in enumerate(station_marks):
        expected_image = _forward(
            homography, (mark.nominal_x_mm, mark.nominal_y_mm)
        )
        for component_index, vertex in enumerate(approximate_vertices):
            candidates.append(
                (
                    float(np.linalg.norm(vertex - expected_image)),
                    expected_index,
                    component_index,
                )
            )
    candidates.sort()
    used_expected = set()
    used_components = set()
    assignments = {}
    assignment_distances = []
    for distance, expected_index, component_index in candidates:
        if expected_index in used_expected or component_index in used_components:
            continue
        used_expected.add(expected_index)
        used_components.add(component_index)
        assignments[expected_index] = component_index
        assignment_distances.append(distance)
    if len(assignments) != len(station_marks):
        raise ValueError("could not assign every station L component")
    if max(assignment_distances) > maximum_assignment_px:
        raise ValueError(
            "station assignment exceeds %.1f px: maximum %.3f px"
            % (maximum_assignment_px, max(assignment_distances))
        )

    measured_by_key = {}
    for expected_index, mark in enumerate(station_marks):
        component = medium[assignments[expected_index]]
        image_vertex = _station_vertex(
            component,
            homography,
            (mark.nominal_x_mm, mark.nominal_y_mm),
        )
        bed_point = _inverse(inverse_homography, image_vertex)
        measured_by_key[(mark.station_id, mark.pass_id)] = tuple(bed_point)
    for mark in expected_fiducials:
        measured_by_key[(mark.station_id, mark.pass_id)] = (
            mark.nominal_x_mm,
            mark.nominal_y_mm,
        )

    diagnostic = {
        "image": str(Path(image_path).resolve()),
        "image_sha256": hashlib.sha256(Path(image_path).read_bytes()).hexdigest(),
        "image_size_px": [source.width, source.height],
        "threshold": threshold,
        "mask_center_fraction": list(mask_center_fraction),
        "mask_radius_fraction": mask_radius_fraction,
        "component_counts": {
            "total": len(components),
            "fiducials": len(large),
            "station_L": len(medium),
            "label_glyphs": len(small),
        },
        "working_center_px": list(center),
        "working_radius_px": working_radius,
        "fiducial_points_px": image_fiducials.tolist(),
        "assignment_distance_px": {
            "minimum": min(assignment_distances),
            "median": float(np.median(assignment_distances)),
            "maximum": max(assignment_distances),
        },
        "homography": homography.tolist(),
    }
    return expected, measured_by_key, diagnostic


def measurement_csv(expected, measured_by_key):
    columns = (
        "section",
        "station_id",
        "ring_radius_mm",
        "station_angle_deg",
        "pass_id",
        "pass_name",
        "mark_kind",
        "angle_deg",
        "base_x_mm",
        "base_y_mm",
        "nominal_x_mm",
        "nominal_y_mm",
        "measured_x_mm",
        "measured_y_mm",
    )
    lines = [",".join(columns)]

    def value(number):
        return ("%.6f" % float(number)).rstrip("0").rstrip(".")

    for mark in expected:
        measured_x, measured_y = measured_by_key[
            (mark.station_id, mark.pass_id)
        ]
        row = (
            mark.section,
            mark.station_id,
            value(mark.ring_radius_mm),
            value(mark.station_angle_deg),
            mark.pass_id,
            mark.pass_name,
            mark.mark_kind,
            value(mark.angle_deg),
            value(mark.base_x_mm),
            value(mark.base_y_mm),
            value(mark.nominal_x_mm),
            value(mark.nominal_y_mm),
            value(measured_x),
            value(measured_y),
        )
        lines.append(",".join(row))
    return "\n".join(lines) + "\n"


def overlay_image(image_path, expected, measured_by_key, diagnostic):
    homography = np.asarray(diagnostic["homography"])
    output = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(output)
    for mark in expected:
        if mark.section != "station":
            continue
        expected_point = _forward(
            homography, (mark.nominal_x_mm, mark.nominal_y_mm)
        )
        measured_point = _forward(
            homography,
            measured_by_key[(mark.station_id, mark.pass_id)],
        )
        draw.line(
            (
                expected_point[0] - 4,
                expected_point[1],
                expected_point[0] + 4,
                expected_point[1],
            ),
            fill=(255, 0, 0),
            width=1,
        )
        draw.line(
            (
                expected_point[0],
                expected_point[1] - 4,
                expected_point[0],
                expected_point[1] + 4,
            ),
            fill=(255, 0, 0),
            width=1,
        )
        draw.ellipse(
            (
                measured_point[0] - 2,
                measured_point[1] - 2,
                measured_point[0] + 2,
                measured_point[1] + 2,
            ),
            fill=(0, 255, 0),
        )
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image")
    parser.add_argument(
        "--measurement-out",
        default=str(
            ROOT / "samples" / "gcode" / "bed-error-map-measured.csv"
        ),
    )
    parser.add_argument(
        "--diagnostic-out",
        default=str(
            ROOT / "samples" / "gcode" / "bed-error-map-photo.json"
        ),
    )
    parser.add_argument(
        "--overlay-out",
        default=str(
            ROOT / "samples" / "gcode" / "bed-error-map-photo-overlay.png"
        ),
    )
    parser.add_argument("--threshold", type=int, default=20)
    parser.add_argument("--blur-radius", type=float, default=18.0)
    parser.add_argument(
        "--mask-center-fraction",
        default="0.5295,0.4869",
        help="working-circle centre as x,y fractions of image width/height",
    )
    parser.add_argument("--mask-radius-fraction", type=float, default=0.4322)
    parser.add_argument("--maximum-assignment-px", type=float, default=8.0)
    args = parser.parse_args()

    mask_center_fraction = tuple(
        float(value)
        for value in args.mask_center_fraction.split(",", 1)
    )
    if len(mask_center_fraction) != 2:
        raise SystemExit("--mask-center-fraction needs X,Y")
    expected, measured_by_key, diagnostic = measure_photo(
        args.image,
        threshold=args.threshold,
        blur_radius=args.blur_radius,
        mask_center_fraction=mask_center_fraction,
        mask_radius_fraction=args.mask_radius_fraction,
        maximum_assignment_px=args.maximum_assignment_px,
    )
    measurement_path = Path(args.measurement_out)
    diagnostic_path = Path(args.diagnostic_out)
    overlay_path = Path(args.overlay_out)
    for path in (measurement_path, diagnostic_path, overlay_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    measurement_path.write_text(
        measurement_csv(expected, measured_by_key),
        encoding="utf-8",
        newline="\n",
    )
    diagnostic_path.write_text(
        json.dumps(diagnostic, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    overlay_image(args.image, expected, measured_by_key, diagnostic).save(
        overlay_path
    )
    print("wrote %s" % measurement_path)
    print("wrote %s" % diagnostic_path)
    print("wrote %s" % overlay_path)
    print(
        "mark components: %(fiducials)d fiducial, %(station_L)d station L, "
        "%(label_glyphs)d label glyph" % diagnostic["component_counts"]
    )
    print(
        "station assignment px: min %.3f, median %.3f, max %.3f"
        % (
            diagnostic["assignment_distance_px"]["minimum"],
            diagnostic["assignment_distance_px"]["median"],
            diagnostic["assignment_distance_px"]["maximum"],
        )
    )


if __name__ == "__main__":
    main()
