"""Measure a photographed full-field bed calibration sheet.

The current sheet uses one pen and encodes pass angle by marker lane. This tool
finds the printed L components, uses the four large fiducials to fit a
projective sheet transform, measures the shared corner of every station L, and
writes the companion measurement CSV used by
``analyze_bed_error_calibration.py``.

The defaults target a straight-down phone photo with reasonably even lighting.
The paper must fill a substantial part of the image and the four large
fiducials must all be visible. The sheet may be rotated in the photo; the
non-mirrored quarter-turn with the best station-lattice agreement is selected
automatically. A small number of ink flecks or detached label fragments is
tolerated, but every expected station mark must still be uniquely assigned.

If pen-up drag marks connect printed components, pass the previous sheet's
``*-photo.json`` as ``--seed-diagnostic``. The seed transform finds the four
fiducials and unique station markers by local expected geometry instead of
requiring an exact global component count.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import itertools
import json
import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software"))

from converter_core.bed_calibration import (  # noqa: E402
    CALIBRATION_LAYOUTS,
    STANDARD_LAYOUT,
    calibration_layout,
    calibration_stations,
    expected_marks,
)


DEFAULT_MAXIMUM_ASSIGNMENT_PX = 13.0


@dataclass(frozen=True)
class Component:
    points: tuple[tuple[int, int], ...]
    bbox: tuple[int, int, int, int]

    @property
    def maximum_dimension(self):
        x0, y0, x1, y1 = self.bbox
        return max(x1 - x0 + 1, y1 - y0 + 1)


def _fiducial_sized_components(components):
    return tuple(
        component
        for component in components
        if 80 <= len(component.points) <= 1200
        and 32 <= component.maximum_dimension <= 120
    )


def _station_sized_components(
    components,
    minimum_dimension=16,
    maximum_dimension=30,
):
    return tuple(
        component
        for component in components
        if minimum_dimension
        <= component.maximum_dimension
        <= maximum_dimension
    )


def _default_station_dimensions(layout):
    """Return the expected station-L bounding-box range at photo scale."""
    if layout.layout_id.startswith("dense-"):
        return 14, 60
    return 16, 30


def _default_station_point_bounds(layout):
    """Return the expected station-L ink-pixel range for seeded matching."""
    if layout.layout_id.startswith("dense-"):
        return 40, 500
    return 60, 200


def _quadrant_fiducials(components, center):
    fiducials_by_quadrant = {}
    for component in components:
        points = np.asarray(component.points, dtype=float)
        component_center = points.mean(axis=0)
        quadrant = (
            0 if component_center[0] > center[0] else 1,
            0 if component_center[1] < center[1] else 1,
        )
        previous = fiducials_by_quadrant.get(quadrant)
        if previous is None or len(component.points) > len(previous.points):
            fiducials_by_quadrant[quadrant] = component
    quadrants = ((0, 0), (1, 0), (1, 1), (0, 1))
    if set(fiducials_by_quadrant) != set(quadrants):
        raise ValueError("the four fiducials are not in four distinct quadrants")
    return tuple(fiducials_by_quadrant[quadrant] for quadrant in quadrants)


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


def _bbox_component_corner(component, quadrant):
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


def _convex_hull(points):
    unique = sorted({(float(x), float(y)) for x, y in points})
    if len(unique) <= 2:
        return np.asarray(unique, dtype=float)

    def cross(origin, a, b):
        return (
            (a[0] - origin[0]) * (b[1] - origin[1])
            - (a[1] - origin[1]) * (b[0] - origin[0])
        )

    lower = []
    for point in unique:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], point) <= 0:
            lower.pop()
        lower.append(point)
    upper = []
    for point in reversed(unique):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], point) <= 0:
            upper.pop()
        upper.append(point)
    return np.asarray(lower[:-1] + upper[:-1], dtype=float)


def _fiducial_corner_candidates(component):
    hull = _convex_hull(component.points)
    if len(hull) < 3:
        return tuple(hull)
    best = None
    for first, second, third in itertools.combinations(hull, 3):
        area = abs(
            (second[0] - first[0]) * (third[1] - first[1])
            - (second[1] - first[1]) * (third[0] - first[0])
        )
        if best is None or area > best[0]:
            best = (area, (first, second, third))
    return best[1]


def _component_corner(component, quadrant=None, prediction=None):
    """Return the shared vertex of a printed V-shaped fiducial."""
    candidates = _fiducial_corner_candidates(component)
    if len(candidates) >= 3:
        prediction_array = (
            None
            if prediction is None
            else np.asarray(prediction, dtype=float)
        )

        def rank(point):
            incident_lengths = sorted(
                float(np.linalg.norm(point - other))
                for other in candidates
                if not np.array_equal(point, other)
            )
            predicted_distance = (
                0.0
                if prediction_array is None
                else float(np.linalg.norm(point - prediction_array))
            )
            return (
                sum(incident_lengths),
                max(incident_lengths),
                predicted_distance,
            )

        return min(candidates, key=rank)
    if prediction is not None and candidates:
        prediction = np.asarray(prediction, dtype=float)
        return min(
            candidates,
            key=lambda point: float(np.linalg.norm(point - prediction)),
        )
    return _bbox_component_corner(component, quadrant or (0, 0))


def _fiducial_shape_error(component, expected_lengths, pixel_scale):
    corners = _fiducial_corner_candidates(component)
    if len(corners) < 3:
        return float("inf")
    observed_lengths = np.sort(
        [
            float(np.linalg.norm(first - second))
            for first_index, first in enumerate(corners)
            for second in corners[first_index + 1 :]
        ]
    )
    return float(
        np.linalg.norm(observed_lengths - expected_lengths) / pixel_scale
    )


def _components_in_box(mask, bounds):
    x0, y0, x1, y1 = bounds
    cropped = mask[max(0, y0):y1, max(0, x0):x1]
    components = _connected_components(cropped)
    output = []
    offset_x = max(0, x0)
    offset_y = max(0, y0)
    for component in components:
        points = tuple(
            (x_value + offset_x, y_value + offset_y)
            for x_value, y_value in component.points
        )
        output.append(
            Component(
                points,
                (
                    component.bbox[0] + offset_x,
                    component.bbox[1] + offset_y,
                    component.bbox[2] + offset_x,
                    component.bbox[3] + offset_y,
                ),
            )
        )
    return tuple(output)


def _scaled_seed_homography(diagnostic, image_size):
    seed = np.asarray(diagnostic["homography"], dtype=float)
    old_width, old_height = diagnostic["image_size_px"]
    new_width, new_height = image_size
    return (
        np.diag([new_width / old_width, new_height / old_height, 1.0])
        @ seed
    )


def _layout_mask(shape, homography, radius_mm=172.0, samples=180):
    height, width = shape
    points = []
    for index in range(samples):
        angle = math.tau * index / samples
        points.append(
            _forward(
                homography,
                (
                    radius_mm * math.cos(angle),
                    radius_mm * math.sin(angle),
                ),
            )
        )
    image = Image.new("1", (width, height), 0)
    ImageDraw.Draw(image).polygon([tuple(point) for point in points], fill=1)
    return np.asarray(image, dtype=bool)


def _seeded_fiducials(
    residual,
    expected_fiducials,
    seed_homography,
    threshold,
    layout=STANDARD_LAYOUT,
):
    layout = calibration_layout(layout)
    pixel_scale = float(
        np.linalg.svd(seed_homography[:2, :2], compute_uv=False).mean()
    )
    expected_lengths = np.asarray(
        (
            layout.fiducial_radial_arm_mm,
            layout.fiducial_tangent_arm_mm,
            math.hypot(
                layout.fiducial_radial_arm_mm,
                layout.fiducial_tangent_arm_mm,
            ),
        )
    ) * pixel_scale
    selected = []
    for mark in expected_fiducials:
        expected = _forward(
            seed_homography, (mark.nominal_x_mm, mark.nominal_y_mm)
        )
        x_value, y_value = expected
        candidates = _components_in_box(
            residual > threshold,
            (
                int(x_value - 280),
                int(y_value - 280),
                int(x_value + 281),
                int(y_value + 281),
            ),
        )
        candidates = _fiducial_sized_components(candidates)
        if not candidates:
            raise ValueError("no fiducial candidate near %s" % mark.station_id)

        def rank(component):
            center = np.asarray(component.points, dtype=float).mean(axis=0)
            shape_error = _fiducial_shape_error(
                component,
                expected_lengths,
                pixel_scale,
            )
            center_distance = float(np.linalg.norm(center - expected))
            score = shape_error + center_distance / (pixel_scale * 30.0)
            return (score, center_distance, -len(component.points))

        selected.append(min(candidates, key=rank))
    nominal = np.asarray(
        [
            (mark.nominal_x_mm, mark.nominal_y_mm)
            for mark in expected_fiducials
        ]
    )
    quadrants = (
        (0, 0),
        (1, 0),
        (1, 1),
        (0, 1),
    )
    image_points = np.asarray(
        [
            _component_corner(
                component,
                expected_quadrant,
                prediction=_forward(
                    seed_homography,
                    (mark.nominal_x_mm, mark.nominal_y_mm),
                ),
            )
            for component, expected_quadrant, mark in zip(
                selected,
                quadrants,
                expected_fiducials,
            )
        ]
    )
    return _fit_homography(nominal, image_points), image_points


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
    """Return the shared corner centre of one station L in sheet coordinates."""
    inverse_homography = np.linalg.inv(homography)
    points = np.asarray(
        [
            _inverse(inverse_homography, point)
            for point in component.points
        ],
        dtype=float,
    )
    nominal = np.asarray(nominal_point, dtype=float)
    near = points[
        (np.abs(points[:, 0] - nominal[0]) < 6.0)
        & (np.abs(points[:, 1] - nominal[1]) < 6.0)
    ]
    if len(near) < 6:
        return tuple(_forward(homography, nominal_point))
    horizontal = near[
        (near[:, 0] < nominal[0] - 1.0)
        & (np.abs(near[:, 1] - nominal[1]) < 3.0)
    ]
    vertical = near[
        (near[:, 1] > nominal[1] + 1.0)
        & (np.abs(near[:, 0] - nominal[0]) < 3.0)
    ]
    if len(horizontal) < 3 or len(vertical) < 3:
        corner = (
            float(np.percentile(near[:, 0], 98)),
            float(np.percentile(near[:, 1], 2)),
        )
    else:
        corner = (
            float(np.median(vertical[:, 0])),
            float(np.median(horizontal[:, 1])),
        )
    return tuple(_forward(homography, corner))


def _fit_oriented_homography(
    expected_fiducials,
    image_fiducials,
    station_marks,
    component_centroids,
    layout=STANDARD_LAYOUT,
):
    """Choose the non-mirrored sheet rotation that best matches the station grid."""
    layout = calibration_layout(layout)
    nominal_fiducials = np.asarray(
        [
            (mark.nominal_x_mm, mark.nominal_y_mm)
            for mark in expected_fiducials
        ]
    )
    best = None
    for order in itertools.permutations(range(4)):
        ordered_fiducials = image_fiducials[list(order)]
        homography = _fit_homography(
            nominal_fiducials,
            ordered_fiducials,
        )
        if np.linalg.det(homography) >= -1e-9:
            continue
        distances = []
        for mark in station_marks:
            expected_centroid = _forward(
                homography,
                (
                    mark.nominal_x_mm - layout.mark_arm_mm / 2.0,
                    mark.nominal_y_mm + layout.mark_arm_mm / 2.0,
                ),
            )
            distances.append(
                float(
                    np.min(
                        np.linalg.norm(
                            component_centroids - expected_centroid,
                            axis=1,
                        )
                    )
                )
            )
        distances = np.asarray(distances)
        score = (
            float(np.median(distances)),
            float(np.percentile(distances, 95)),
            float(distances.mean()),
        )
        if best is None or score < best[0]:
            best = (score, homography, ordered_fiducials, order)
    if best is None:
        raise ValueError("could not fit a non-mirrored sheet orientation")
    return best[1], best[2], best[3], best[0]


def _measure_dense_seeded_photo(
    image_path,
    layout,
    *,
    threshold,
    fiducial_threshold,
    blur_radius,
    minimum_station_dimension,
    maximum_station_dimension,
    seed_diagnostic,
):
    """Measure the tighter dense grid by matching whole station L groups."""
    source = Image.open(image_path).convert("L")
    residual = (
        np.asarray(
            source.filter(ImageFilter.GaussianBlur(blur_radius)),
            dtype=np.int16,
        )
        - np.asarray(source, dtype=np.int16)
    )
    expected = expected_marks(layout)
    expected_fiducials = tuple(
        mark for mark in expected if mark.section == "fiducial"
    )
    station_marks = tuple(
        mark for mark in expected if mark.section == "station"
    )
    seed_homography = _scaled_seed_homography(
        seed_diagnostic,
        (source.width, source.height),
    )
    homography, image_fiducials = _seeded_fiducials(
        residual,
        expected_fiducials,
        seed_homography,
        fiducial_threshold,
        layout,
    )
    inverse_homography = np.linalg.inv(homography)
    paper_mask = _layout_mask(residual.shape, homography)
    components = _connected_components(
        (residual > threshold) & paper_mask
    )
    minimum_points, maximum_points = _default_station_point_bounds(layout)
    candidates = tuple(
        component
        for component in _station_sized_components(
            components,
            minimum_dimension=minimum_station_dimension,
            maximum_dimension=maximum_station_dimension,
        )
        if minimum_points <= len(component.points) <= maximum_points
    )
    by_station = {}
    for mark in station_marks:
        by_station.setdefault(mark.station_id, []).append(mark)
    stations = calibration_stations(layout)
    station_groups = {}
    for station in stations:
        station_groups.setdefault(station.ring_radius_mm, []).append(station)

    neighbor_offsets = np.asarray(
        [(x, y) for x in (-1, 0, 1) for y in (-1, 0, 1)],
        dtype=float,
    )

    def sample_points(points):
        x_values = np.rint(points[:, 0]).astype(int)
        y_values = np.rint(points[:, 1]).astype(int)
        valid = (
            (x_values >= 0)
            & (y_values >= 0)
            & (x_values < residual.shape[1])
            & (y_values < residual.shape[0])
        )
        values = np.zeros(len(points), dtype=float)
        values[valid] = residual[y_values[valid], x_values[valid]]
        return values

    def group_score(base_points, mark_count, shift):
        shifted = base_points + np.asarray(shift)
        samples = shifted[:, None, :] + neighbor_offsets[None, :, :]
        values = sample_points(samples.reshape(-1, 2)).reshape(
            len(base_points),
            len(neighbor_offsets),
        )
        per_mark = values.max(axis=1).reshape(mark_count, -1).mean(axis=1)
        return float(per_mark.mean()), float(per_mark.min())

    station_results = {}
    processed = []
    for ring_radius in sorted(station_groups):
        for station in station_groups[ring_radius]:
            if processed:
                nearest = min(
                    processed,
                    key=lambda item: (
                        (item.x_mm - station.x_mm) ** 2
                        + (item.y_mm - station.y_mm) ** 2
                    ),
                )
                base_shift = station_results[nearest.station_id]["shift"]
                search_offsets = range(-10, 11, 2)
            else:
                base_shift = (0.0, 0.0)
                search_offsets = range(-60, 61, 3)
            group = by_station[station.station_id]
            base_points = []
            for mark in group:
                corner = _forward(
                    homography,
                    (mark.nominal_x_mm, mark.nominal_y_mm),
                )
                for arm_end in (
                    (
                        mark.nominal_x_mm - layout.mark_arm_mm,
                        mark.nominal_y_mm,
                    ),
                    (
                        mark.nominal_x_mm,
                        mark.nominal_y_mm + layout.mark_arm_mm,
                    ),
                ):
                    endpoint = _forward(homography, arm_end)
                    for parameter in np.linspace(0.18, 0.86, 8):
                        base_points.append(
                            corner + parameter * (endpoint - corner)
                        )
            base_points = np.asarray(base_points, dtype=float)
            best = None
            for dy in [
                base_shift[1] + offset for offset in search_offsets
            ]:
                for dx in [
                    base_shift[0] + offset for offset in search_offsets
                ]:
                    score = group_score(base_points, len(group), (dx, dy))
                    key = (score[0], score[1])
                    if best is None or key > best[0]:
                        best = (key, dx, dy, score)
            for dy in np.arange(best[2] - 3, best[2] + 3.01, 1):
                for dx in np.arange(best[1] - 3, best[1] + 3.01, 1):
                    score = group_score(base_points, len(group), (dx, dy))
                    key = (score[0], score[1])
                    if key > best[0]:
                        best = (key, dx, dy, score)
            station_results[station.station_id] = {
                "shift": [float(best[1]), float(best[2])],
                "mean_score": best[3][0],
                "min_score": best[3][1],
            }
            processed.append(station)

    mark_results = {}
    measured_by_key = {}
    for mark in station_marks:
        corner = _forward(
            homography,
            (mark.nominal_x_mm, mark.nominal_y_mm),
        )
        base_points = []
        for arm_end in (
            (
                mark.nominal_x_mm - layout.mark_arm_mm,
                mark.nominal_y_mm,
            ),
            (
                mark.nominal_x_mm,
                mark.nominal_y_mm + layout.mark_arm_mm,
            ),
        ):
            endpoint = _forward(homography, arm_end)
            for parameter in np.linspace(0.18, 0.86, 8):
                base_points.append(
                    corner + parameter * (endpoint - corner)
                )
        base_points = np.asarray(base_points, dtype=float)
        group_shift = station_results[mark.station_id]["shift"]
        best = None
        for dy in np.arange(group_shift[1] - 5, group_shift[1] + 5.01, 1):
            for dx in np.arange(group_shift[0] - 5, group_shift[0] + 5.01, 1):
                score = group_score(base_points, 1, (dx, dy))
                key = (score[0], score[1])
                if best is None or key > best[0]:
                    best = (key, float(dx), float(dy), score)
        mark_results[(mark.station_id, mark.pass_id)] = {
            "shift": [best[1], best[2]],
            "mean_score": best[3][0],
            "min_score": best[3][1],
        }
        measured_corner = (
            np.asarray(corner) + np.asarray((best[1], best[2]))
        )
        measured_by_key[(mark.station_id, mark.pass_id)] = tuple(
            _inverse(inverse_homography, measured_corner)
        )
    for mark in expected_fiducials:
        measured_by_key[(mark.station_id, mark.pass_id)] = (
            mark.nominal_x_mm,
            mark.nominal_y_mm,
        )

    shifts = list(station_results.values())
    mark_scores = [value["mean_score"] for value in mark_results.values()]
    diagnostic = {
        "layout_id": layout.layout_id,
        "layout_name": layout.display_name,
        "image": str(Path(image_path).resolve()),
        "image_sha256": hashlib.sha256(Path(image_path).read_bytes()).hexdigest(),
        "image_size_px": [source.width, source.height],
        "threshold": threshold,
        "fiducial_threshold": fiducial_threshold,
        "blur_radius": blur_radius,
        "station_dimension_px": {
            "minimum": minimum_station_dimension,
            "maximum": maximum_station_dimension,
        },
        "component_counts": {
            "total": len(components),
            "fiducials": len(image_fiducials),
            "station_L_candidates": len(candidates),
            "template_refined_station_L": len(mark_results),
        },
        "mode": "dense-seeded-local-template",
        "fiducial_points_px": image_fiducials.tolist(),
        "station_group_score": {
            "minimum": min(value["min_score"] for value in shifts),
            "median_mean": float(
                np.median([value["mean_score"] for value in shifts])
            ),
        },
        "station_mark_score": {
            "minimum": min(mark_scores),
            "median": float(np.median(mark_scores)),
            "maximum": max(mark_scores),
        },
        "station_shifts_px": station_results,
        "station_mark_shifts_px": {
            "%s/%s" % key: value for key, value in mark_results.items()
        },
        "homography": homography.tolist(),
    }
    return expected, measured_by_key, diagnostic


def measure_photo(
    image_path,
    *,
    layout=STANDARD_LAYOUT,
    threshold=20,
    fiducial_threshold=None,
    blur_radius=18.0,
    minimum_station_dimension=None,
    maximum_station_dimension=None,
    mask_center_fraction=(0.5295, 0.4869),
    mask_radius_fraction=0.4322,
    maximum_assignment_px=DEFAULT_MAXIMUM_ASSIGNMENT_PX,
    seed_diagnostic=None,
):
    layout = calibration_layout(layout)
    if fiducial_threshold is None:
        fiducial_threshold = threshold
    default_minimum, default_maximum = _default_station_dimensions(layout)
    if minimum_station_dimension is None:
        minimum_station_dimension = default_minimum
    if maximum_station_dimension is None:
        maximum_station_dimension = default_maximum
    if (
        seed_diagnostic is not None
        and layout.layout_id.startswith("dense-")
    ):
        return _measure_dense_seeded_photo(
            image_path,
            layout,
            threshold=threshold,
            fiducial_threshold=fiducial_threshold,
            blur_radius=blur_radius,
            minimum_station_dimension=minimum_station_dimension,
            maximum_station_dimension=maximum_station_dimension,
            seed_diagnostic=seed_diagnostic,
        )
    source = Image.open(image_path).convert("L")
    background = source.filter(ImageFilter.GaussianBlur(blur_radius))
    gray = np.asarray(source, dtype=np.int16)
    local_background = np.asarray(background, dtype=np.int16)
    residual = local_background - gray
    expected = expected_marks(layout)
    expected_fiducials = tuple(
        mark for mark in expected if mark.section == "fiducial"
    )
    expected_station_count = sum(
        1 for mark in expected if mark.section == "station"
    )
    station_marks = tuple(
        mark for mark in expected if mark.section == "station"
    )
    center = (
        (source.width - 1) * mask_center_fraction[0],
        (source.height - 1) * mask_center_fraction[1],
    )
    working_radius = min(source.width, source.height) * mask_radius_fraction
    components = ()
    large = ()
    medium = ()
    small = ()
    if seed_diagnostic is None:
        paper_mask, center, working_radius = _working_mask(
            gray.shape,
            center_fraction=mask_center_fraction,
            radius_fraction=mask_radius_fraction,
        )
        components = _connected_components(
            (residual > threshold) & paper_mask
        )
        large = _fiducial_sized_components(components)
        medium = _station_sized_components(
            components,
            minimum_dimension=minimum_station_dimension,
            maximum_dimension=maximum_station_dimension,
        )
        small = tuple(
            component
            for component in components
            if component.maximum_dimension < minimum_station_dimension
        )
        maximum_extra_components = 12
        if not (
            4 <= len(large) <= 16
            and expected_station_count
            <= len(medium)
            <= expected_station_count + maximum_extra_components
        ):
            raise ValueError(
                "unexpected component counts: %d fiducial, %d L-mark "
                "(expected %d plus at most %d extras), %d label"
                % (
                    len(large),
                    len(medium),
                    expected_station_count,
                    maximum_extra_components,
                    len(small),
                )
            )

        quadrants = ((0, 0), (1, 0), (1, 1), (0, 1))
        fiducials_in_quadrant_order = _quadrant_fiducials(large, center)
        image_fiducials = np.asarray(
            [
                _component_corner(component, quadrant)
                for quadrant, component in zip(
                    quadrants, fiducials_in_quadrant_order
                )
            ]
        )
        component_centroids = np.asarray(
            [
                np.asarray(component.points, dtype=float).mean(axis=0)
                for component in medium
            ],
            dtype=float,
        )
        (
            homography,
            image_fiducials,
            fiducial_order,
            orientation_score,
        ) = _fit_oriented_homography(
            expected_fiducials,
            image_fiducials,
            station_marks,
            component_centroids,
            layout,
        )
        nominal_fiducials = np.asarray(
            [
                (mark.nominal_x_mm, mark.nominal_y_mm)
                for mark in expected_fiducials
            ]
        )
        ordered_components = tuple(
            fiducials_in_quadrant_order[index] for index in fiducial_order
        )
        for _iteration in range(2):
            refined_fiducials = np.asarray(
                [
                    _component_corner(
                        component,
                        prediction=_forward(
                            homography,
                            (mark.nominal_x_mm, mark.nominal_y_mm),
                        ),
                    )
                    for component, mark in zip(
                        ordered_components,
                        expected_fiducials,
                    )
                ]
            )
            homography = _fit_homography(
                nominal_fiducials,
                refined_fiducials,
            )
            image_fiducials = refined_fiducials
    else:
        seed_homography = _scaled_seed_homography(
            seed_diagnostic, (source.width, source.height)
        )
        homography, image_fiducials = _seeded_fiducials(
            residual,
            expected_fiducials,
            seed_homography,
            fiducial_threshold,
            layout,
        )
        paper_mask = _layout_mask(gray.shape, homography)
        components = _connected_components(
            (residual > threshold) & paper_mask
        )
        mark_area_ratio = (
            layout.mark_arm_mm / STANDARD_LAYOUT.mark_arm_mm
        ) ** 2
        minimum_points, maximum_points = _default_station_point_bounds(layout)
        medium = tuple(
            component
            for component in _station_sized_components(
                components,
                minimum_dimension=minimum_station_dimension,
                maximum_dimension=maximum_station_dimension,
            )
            if (
                max(minimum_points, int(round(60 * mark_area_ratio)))
                <= len(component.points)
                <= max(maximum_points, int(round(200 * mark_area_ratio)))
            )
        )
        fiducial_order = (0, 1, 2, 3)
        orientation_score = (0.0, 0.0, 0.0)
    inverse_homography = np.linalg.inv(homography)

    approximate_vertices = np.asarray(
        [
            np.asarray(component.points, dtype=float).mean(axis=0)
            for component in medium
        ],
        dtype=float,
    )
    candidates = []
    for expected_index, mark in enumerate(station_marks):
        expected_image = _forward(
            homography,
            (
                mark.nominal_x_mm - layout.mark_arm_mm / 2.0,
                mark.nominal_y_mm + layout.mark_arm_mm / 2.0,
            ),
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
        raise ValueError(
            "could not assign every station L component "
            "(%d assigned from %d detected candidates for %d expected marks)"
            % (len(assignments), len(medium), len(station_marks))
        )
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

    component_counts = (
        {
            "total": len(components),
            "fiducials": len(large),
            "station_L": len(medium),
            "label_glyphs": len(small),
        }
        if seed_diagnostic is None
        else {
            "total": len(components),
            "fiducials": len(image_fiducials),
            "station_L_candidates": len(medium),
        }
    )
    diagnostic = {
        "layout_id": layout.layout_id,
        "layout_name": layout.display_name,
        "image": str(Path(image_path).resolve()),
        "image_sha256": hashlib.sha256(Path(image_path).read_bytes()).hexdigest(),
        "image_size_px": [source.width, source.height],
        "threshold": threshold,
        "fiducial_threshold": fiducial_threshold,
        "station_dimension_px": {
            "minimum": minimum_station_dimension,
            "maximum": maximum_station_dimension,
        },
        "mask_center_fraction": list(mask_center_fraction),
        "mask_radius_fraction": mask_radius_fraction,
        "component_counts": component_counts,
        "mode": "standard" if seed_diagnostic is None else "seed-assisted",
        "working_center_px": list(center),
        "working_radius_px": working_radius,
        "fiducial_points_px": image_fiducials.tolist(),
        "fiducial_order": list(fiducial_order),
        "orientation_score_px": {
            "median": orientation_score[0],
            "p95": orientation_score[1],
            "mean": orientation_score[2],
        },
        "assignment_distance_px": {
            "minimum": min(assignment_distances),
            "median": float(np.median(assignment_distances)),
            "maximum": max(assignment_distances),
        },
        "homography": homography.tolist(),
    }
    return expected, measured_by_key, diagnostic


def measurement_csv(
    expected,
    measured_by_key,
    layout=STANDARD_LAYOUT,
):
    layout = calibration_layout(layout)
    columns = (
        "layout_id",
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
            layout.layout_id,
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
        "--layout",
        choices=tuple(CALIBRATION_LAYOUTS),
        default=STANDARD_LAYOUT.layout_id,
        help="calibration station layout used for the printed sheet",
    )
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
    parser.add_argument(
        "--fiducial-threshold",
        type=int,
        default=None,
        help=(
            "separate threshold for seeded fiducial detection; defaults to "
            "--threshold"
        ),
    )
    parser.add_argument("--blur-radius", type=float, default=18.0)
    parser.add_argument(
        "--minimum-station-dimension",
        type=int,
        default=None,
        help=(
            "minimum component width or height treated as a station L; "
            "raise this when large station labels are misclassified"
        ),
    )
    parser.add_argument(
        "--maximum-station-dimension",
        type=int,
        default=None,
        help=(
            "maximum component width or height treated as a station L; "
            "defaults to the layout's expected marker scale"
        ),
    )
    parser.add_argument(
        "--mask-center-fraction",
        default="0.5295,0.4869",
        help="working-circle centre as x,y fractions of image width/height",
    )
    parser.add_argument("--mask-radius-fraction", type=float, default=0.4322)
    parser.add_argument(
        "--maximum-assignment-px",
        type=float,
        default=DEFAULT_MAXIMUM_ASSIGNMENT_PX,
    )
    parser.add_argument(
        "--seed-diagnostic",
        default="",
        help="optional prior photo diagnostic JSON for artefact-tolerant matching",
    )
    args = parser.parse_args()
    layout = calibration_layout(args.layout)

    mask_center_fraction = tuple(
        float(value)
        for value in args.mask_center_fraction.split(",", 1)
    )
    if len(mask_center_fraction) != 2:
        raise SystemExit("--mask-center-fraction needs X,Y")
    seed_diagnostic = None
    if args.seed_diagnostic:
        try:
            seed_diagnostic = json.loads(
                Path(args.seed_diagnostic).read_text(encoding="utf-8")
            )
        except (OSError, ValueError) as error:
            raise SystemExit("cannot read seed diagnostic: %s" % error) from error
    expected, measured_by_key, diagnostic = measure_photo(
        args.image,
        layout=layout,
        threshold=args.threshold,
        fiducial_threshold=args.fiducial_threshold,
        blur_radius=args.blur_radius,
        minimum_station_dimension=args.minimum_station_dimension,
        maximum_station_dimension=args.maximum_station_dimension,
        mask_center_fraction=mask_center_fraction,
        mask_radius_fraction=args.mask_radius_fraction,
        maximum_assignment_px=args.maximum_assignment_px,
        seed_diagnostic=seed_diagnostic,
    )
    measurement_path = Path(args.measurement_out)
    diagnostic_path = Path(args.diagnostic_out)
    overlay_path = Path(args.overlay_out)
    for path in (measurement_path, diagnostic_path, overlay_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    measurement_path.write_text(
        measurement_csv(expected, measured_by_key, layout),
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
    counts = diagnostic["component_counts"]
    if "station_L" in counts:
        print(
            "mark components: %(fiducials)d fiducial, %(station_L)d station L, "
            "%(label_glyphs)d label glyph" % counts
        )
    else:
        print(
            "seed-assisted components: %(fiducials)d fiducials, "
            "%(station_L_candidates)d L candidates" % counts
        )
    if "assignment_distance_px" in diagnostic:
        print(
            "station assignment px: min %.3f, median %.3f, max %.3f"
            % (
                diagnostic["assignment_distance_px"]["minimum"],
                diagnostic["assignment_distance_px"]["median"],
                diagnostic["assignment_distance_px"]["maximum"],
            )
        )
    else:
        print(
            "template-refined station marks: %(template_refined_station_L)d"
            % counts
        )


if __name__ == "__main__":
    main()
