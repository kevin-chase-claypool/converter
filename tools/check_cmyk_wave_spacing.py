"""Verify a saved CMYK Wave set in final paper-space coordinates.

The Wave screen is generated as a uniform lattice in paper space. Bed
compensation can change that lattice before the coordinates reach grblHAL.
This checker follows the emitted pen-down ``X/Y/A`` commands, samples each
linear interpolation interval, rotates the result back onto the bed, and
measures adjacent row gaps in each ink's effective screen frame.

Usage::

    python tools\\check_cmyk_wave_spacing.py `
      samples\\gcode\\Ben2\\PXL_20201128_211515508-cmyk-set.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "software"))

from converter_core.cmyk import (
    _polyline_pair_is_clear,
    _polyline_segments,
)


WORD = re.compile(r"([XYA])(-?\d+(?:\.\d+)?)", re.IGNORECASE)
THETA_RATIO = re.compile(r"theta ratio\s+([\d.]+)", re.IGNORECASE)
WAVE_ROW = re.compile(
    r"\(wave row\s+(\d+)\s+baseline\s+"
    r"(-?\d+(?:\.\d+)?)\s+mm\)",
    re.IGNORECASE,
)
FIXED_BASELINE_HEADER = re.compile(
    r"\(Wave fixed baselines:\s*pitch\s+([\d.]+)\s+mm,\s*"
    r"origin\s+(-?[\d.]+)\s+mm,\s*rows\s+(\d+),\s*"
    r"screen angle\s+(-?[\d.]+)\s+deg",
    re.IGNORECASE,
)
LABELS = {
    "c": "cyan",
    "m": "magenta",
    "y": "yellow",
    "k": "black",
}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("kind") != "cmyk-print-set":
        raise ValueError("not a CMYK print-set manifest")
    bed_motion = str(data.get("bed_motion", ""))
    rotating = "Xθ/Yθ" in bed_motion or "xtheta/ytheta" in bed_motion.lower()
    if not rotating and "XY only" not in bed_motion:
        raise ValueError("manifest has no supported bed-motion mode")
    if rotating and not bool(data.get("row_theta_lock")):
        raise ValueError(
            "rotating-bed manifest does not record the shared row-angle lock"
        )
    screen = data.get("screen", {})
    style = screen.get("style")
    if style not in ("waves_even", "waves_fixed"):
        raise ValueError(
            "manifest screen style is not a production Wave baseline mode"
        )
    if style == "waves_even" and screen.get("preserve_exact_row_pitch") is not True:
        raise ValueError("manifest does not record an active row-spacing guard")
    if (
        style == "waves_fixed"
        and screen.get("preserve_fixed_row_baselines") is not True
    ):
        raise ValueError(
            "manifest does not record an active fixed-baseline guard"
        )
    if style == "waves_fixed":
        grid = data.get("wave_baseline_grid")
        if not isinstance(grid, dict):
            raise ValueError(
                "fixed-baseline manifest has no machine-readable baseline grid"
            )
        if grid.get("mode") != "fixed_baselines":
            raise ValueError(
                "fixed-baseline manifest has the wrong baseline-grid mode"
            )
        if (
            grid.get("instantaneous_gap_semantics")
            != "varies_by_design"
        ):
            raise ValueError(
                "fixed-baseline manifest does not classify variable "
                "instantaneous gaps as intentional"
            )
        try:
            if float(grid["pitch_mm"]) <= 0.0:
                raise ValueError
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                "fixed-baseline manifest has no positive final pitch"
            ) from error
    compensation_path = data.get("bed_compensation_path", "")
    if compensation_path:
        compensation = data.get("bed_compensation", {})
        if compensation.get("mode") != "row_locked_projection":
            raise ValueError(
                "manifest applies raw bed compensation; final row pitch is "
                "not guaranteed"
            )
        if not compensation.get("profile_fingerprint"):
            raise ValueError(
                "row-locked manifest does not identify its compensation profile"
            )
        maxima = compensation.get("per_channel_max_correction_mm", {})
        for channel in LABELS:
            try:
                retained_max = float(maxima[channel])
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(
                    f"row-locked manifest has no projected correction for {channel}"
                ) from error
            if retained_max <= 0.0:
                raise ValueError(
                    f"row-locked projection is inactive for {channel}"
                )
        if int(data.get("version", 0)) >= 4:
            normalization = compensation.get(
                "translation_normalization", {}
            )
            if normalization.get("mode") != "shared_zero_mean":
                raise ValueError(
                    "row-locked manifest has no shared translation "
                    "normalization"
                )
            common = normalization.get("common_mean_mm")
            try:
                common_x, common_y = (float(value) for value in common)
            except (TypeError, ValueError) as error:
                raise ValueError(
                    "shared translation manifest has no common mean"
                ) from error
            if abs(common_x) > 1e-9 or abs(common_y) > 1e-9:
                raise ValueError(
                    "shared translation manifest does not use zero common mean"
                )
            raw_means = compensation.get(
                "per_channel_raw_translation_means_mm", {}
            )
            if set(raw_means) != set(LABELS):
                raise ValueError(
                    "row-locked manifest has incomplete raw translation means"
                )
    return data


def theta_ratio(path: Path) -> float:
    for line in path.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()[:20]:
        match = THETA_RATIO.search(line)
        if match:
            value = float(match.group(1))
            if value > 0.0:
                return value
    raise ValueError(f"{path.name} has no positive theta ratio header")


def drawing_contours(
    path: Path,
    sample_steps: int = 1,
) -> list[list[tuple[float, float, float]]]:
    """Return sampled pen-down paper points from the emitted G-code."""
    sample_steps = max(1, int(sample_steps))
    contours: list[list[tuple[float, float, float]]] = []
    current = None
    x = y = a = 0.0
    for raw_line in path.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines():
        line = raw_line.strip()
        if line.startswith("M3"):
            current = []
            contours.append(current)
        elif line.startswith("M5"):
            current = None
        elif line.startswith(("G0 ", "G1 ")):
            words = {
                key.upper(): float(value)
                for key, value in WORD.findall(line)
            }
            next_x = words.get("X", x)
            next_y = words.get("Y", y)
            next_a = words.get("A", a)
            if current is not None and words:
                for index in range(sample_steps + 1):
                    fraction = index / sample_steps
                    current.append(
                        (
                            x + fraction * (next_x - x),
                            y + fraction * (next_y - y),
                            a + fraction * (next_a - a),
                        )
                    )
            x, y, a = next_x, next_y, next_a
    return [contour for contour in contours if len(contour) > 1]


def annotated_drawing_contours(
    path: Path,
    sample_steps: int = 1,
) -> list[dict]:
    """Return pen-down contours with their emitted fixed-row annotations."""
    sample_steps = max(1, int(sample_steps))
    contours: list[dict] = []
    current = None
    pending_row = None
    pending_baseline = None
    x = y = a = 0.0
    for raw_line in path.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines():
        line = raw_line.strip()
        row_match = WAVE_ROW.match(line)
        if row_match:
            pending_row = int(row_match.group(1))
            pending_baseline = float(row_match.group(2))
            continue
        if line.startswith("M3"):
            current = {
                "points": [],
                "row_index": pending_row,
                "baseline_mm": pending_baseline,
            }
            contours.append(current)
            pending_row = None
            pending_baseline = None
            continue
        if line.startswith("M5"):
            current = None
            continue
        if not line.startswith(("G0 ", "G1 ")):
            continue
        words = {
            key.upper(): float(value)
            for key, value in WORD.findall(line)
        }
        next_x = words.get("X", x)
        next_y = words.get("Y", y)
        next_a = words.get("A", a)
        if current is not None and words:
            for index in range(sample_steps + 1):
                fraction = index / sample_steps
                current["points"].append(
                    (
                        x + fraction * (next_x - x),
                        y + fraction * (next_y - y),
                        a + fraction * (next_a - a),
                    )
                )
        x, y, a = next_x, next_y, next_a
    return [
        contour
        for contour in contours
        if len(contour["points"]) > 1
    ]


def _screen_points(points, angle_deg):
    theta = math.radians(-angle_deg)
    cosine = math.cos(theta)
    sine = math.sin(theta)
    return [
        (
            x_value * cosine + y_value * sine,
            -x_value * sine + y_value * cosine,
        )
        for x_value, y_value in points
    ]


def _row_grid(row_baselines):
    rows = sorted(
        (
            int(row_index),
            float(
                sorted(values)[len(values) // 2]
            ),
        )
        for row_index, values in row_baselines.items()
    )
    if len(rows) < 2:
        raise ValueError("fixed-baseline output has fewer than two rows")
    first_index, first_baseline = rows[0]
    last_index, last_baseline = rows[-1]
    if last_index <= first_index:
        raise ValueError("fixed-baseline row indices are not increasing")
    pitch = (last_baseline - first_baseline) / (
        last_index - first_index
    )
    if abs(pitch) <= 1e-9:
        raise ValueError("fixed-baseline row pitch is zero")
    origin = first_baseline - first_index * pitch
    residual = max(
        abs(baseline - (origin + row_index * pitch))
        for row_index, baseline in rows
    )
    return {
        "pitch_mm": abs(pitch),
        "origin_mm": origin,
        "rows": len(rows),
        "residual_mm": residual,
    }


def audit_fixed_baseline_program(
    path: Path,
    angle_deg: float,
    expected_pitch_mm: float,
    expected_origin_mm: float | None = None,
    sample_columns: int = 199,
    *,
    rotating_bed: bool = False,
    ratio: float = 1.0,
    minimum_clearance_mm: float = 0.0,
) -> dict[str, float | int]:
    """Validate fixed row baselines and variable per-row final waveforms."""
    text = path.read_text(encoding="utf-8", errors="replace")
    header = FIXED_BASELINE_HEADER.search(text)
    if not header:
        raise ValueError(f"{path.name} has no fixed-baseline Wave header")
    header_pitch = float(header.group(1))
    header_origin = float(header.group(2))
    header_rows = int(header.group(3))
    header_angle = float(header.group(4))
    if abs(header_pitch - float(expected_pitch_mm)) > 0.005:
        raise ValueError(
            f"{path.name} final baseline pitch does not match the manifest"
        )
    if (
        expected_origin_mm is not None
        and abs(header_origin - float(expected_origin_mm)) > 0.005
    ):
        raise ValueError(
            f"{path.name} final baseline origin does not match the manifest"
        )
    expected_header_angle = -float(angle_deg)
    angle_difference = (
        header_angle - expected_header_angle + 90.0
    ) % 180.0 - 90.0
    if abs(angle_difference) > 0.005:
        raise ValueError(
            f"{path.name} final baseline screen angle does not match "
            "the manifest"
        )

    contours = annotated_drawing_contours(
        path,
        sample_steps=9 if rotating_bed else 1,
    )
    row_baselines: dict[int, list[float]] = {}
    row_fragments: dict[int, list[list[tuple[float, float]]]] = {}
    screen_fragments = []
    ratio = max(float(ratio), 1e-12)
    for contour in contours:
        row_index = contour["row_index"]
        baseline = contour["baseline_mm"]
        if row_index is None or baseline is None:
            continue
        row_baselines.setdefault(int(row_index), []).append(float(baseline))
        bed_points = (
            [
                _machine_to_bed_point(x_value, y_value, a_value, ratio)[
                    :2
                ]
                for x_value, y_value, a_value in contour["points"]
            ]
            if rotating_bed
            else [
                (x_value, y_value)
                for x_value, y_value, _a_value in contour["points"]
            ]
        )
        screen = _screen_points(bed_points, angle_deg)
        row_fragments.setdefault(int(row_index), []).append(screen)
        screen_fragments.append(screen)
    if len(row_baselines) < 2:
        raise ValueError(
            f"{path.name} has no emitted fixed-baseline row annotations"
        )
    if len(row_baselines) != header_rows:
        raise ValueError(
            f"{path.name} baseline row count does not match its header"
        )

    grid = _row_grid(row_baselines)
    if abs(float(grid["pitch_mm"]) - float(expected_pitch_mm)) > 0.005:
        raise ValueError(
            f"{path.name} emitted baseline pitch does not match the manifest"
        )
    if float(grid["residual_mm"]) > 0.005:
        raise ValueError(
            f"{path.name} fixed row baselines are not uniformly spaced"
        )

    if minimum_clearance_mm > 0.0:
        ordered_rows = sorted(row_fragments)
        for first_row, second_row in zip(
            ordered_rows,
            ordered_rows[1:],
        ):
            for first in row_fragments[first_row]:
                for second in row_fragments[second_row]:
                    if not _polyline_pair_is_clear(
                        _polyline_segments(first),
                        _polyline_segments(second),
                        float(minimum_clearance_mm),
                    ):
                        raise ValueError(
                            f"{path.name} fixed-baseline rows touch or cross"
                        )

    ranges = sorted(
        max(value for _along, value in fragment)
        - min(value for _along, value in fragment)
        for fragment in screen_fragments
        if len(fragment) > 1
    )
    if not ranges:
        raise ValueError(f"{path.name} has no visible fixed-baseline rows")
    return {
        "samples": max(0, int(sample_columns)),
        "measurements": len(row_fragments),
        "pitch_mm": float(grid["pitch_mm"]),
        "origin_mm": float(grid["origin_mm"]),
        "rows": len(row_baselines),
        "baseline_residual_mm": float(grid["residual_mm"]),
        "minimum_wave_range_mm": ranges[0],
        "maximum_wave_range_mm": ranges[-1],
    }


def _value_at_x(
    contour: list[tuple[float, float]], x_value: float
) -> float | None:
    for first, second in zip(contour, contour[1:]):
        lower, upper = sorted((first[0], second[0]))
        if not lower - 1e-9 <= x_value <= upper + 1e-9:
            continue
        delta = second[0] - first[0]
        if abs(delta) < 1e-12:
            continue
        fraction = (x_value - first[0]) / delta
        if -1e-9 <= fraction <= 1.0 + 1e-9:
            return first[1] + fraction * (second[1] - first[1])
    return None


def _machine_to_bed_point(x_value, y_value, motor_angle, ratio):
    theta = math.radians(-motor_angle / ratio)
    cosine = math.cos(theta)
    sine = math.sin(theta)
    return (
        x_value * cosine - y_value * sine,
        x_value * sine + y_value * cosine,
    )


def audit_program(
    path: Path,
    angle_deg: float,
    nominal_pitch_mm: float,
    sample_columns: int = 199,
    *,
    rotating_bed: bool = False,
    ratio: float = 1.0,
) -> dict[str, float | int]:
    """Measure adjacent paper-space row gaps in the effective screen frame."""
    contours = drawing_contours(path, sample_steps=9 if rotating_bed else 1)
    if rotating_bed:
        ratio = max(float(ratio), 1e-12)
        bed_contours = [
            [
                _machine_to_bed_point(
                    x_value,
                    y_value,
                    a_value,
                    ratio,
                )
                for x_value, y_value, a_value in contour
            ]
            for contour in contours
        ]
    else:
        bed_contours = [
            [(x_value, y_value) for x_value, y_value, _a in contour]
            for contour in contours
        ]
    theta = math.radians(-angle_deg)
    cosine = math.cos(theta)
    sine = math.sin(theta)
    rows = [
        [
            (
                x_value * cosine + y_value * sine,
                -x_value * sine + y_value * cosine,
            )
            for x_value, y_value in contour
        ]
        for contour in bed_contours
    ]
    if not rows:
        raise ValueError(f"no pen-down contours in {path.name}")

    plane_values = [point[0] for row in rows for point in row]
    low = min(plane_values)
    high = max(plane_values)
    if high - low <= 1e-9:
        raise ValueError(f"no screen-frame width in {path.name}")

    gaps: list[float] = []
    sampled_columns = 0
    for index in range(1, sample_columns + 1):
        plane = low + (high - low) * index / (sample_columns + 1)
        values = sorted(
            value
            for row in rows
            if (value := _value_at_x(row, plane)) is not None
        )
        observed = [
            second - first
            for first, second in zip(values, values[1:])
            if 0.5 * nominal_pitch_mm
            < second - first
            < 1.5 * nominal_pitch_mm
        ]
        if observed:
            sampled_columns += 1
            gaps.extend(observed)

    if not gaps:
        raise ValueError(f"no adjacent Wave rows found in {path.name}")
    gaps.sort()
    median = gaps[len(gaps) // 2]
    return {
        "samples": sampled_columns,
        "measurements": len(gaps),
        "minimum_mm": gaps[0],
        "median_mm": median,
        "maximum_mm": gaps[-1],
        "spread_mm": gaps[-1] - gaps[0],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument(
        "--tolerance-mm",
        type=float,
        default=0.005,
        help="maximum allowed adjacent-gap spread (default: 0.005)",
    )
    parser.add_argument(
        "--sample-columns",
        type=int,
        default=199,
        help="screen-frame columns sampled per ink (default: 199)",
    )
    args = parser.parse_args(argv)
    if args.tolerance_mm <= 0 or args.sample_columns < 3:
        parser.error("tolerance must be positive and samples must be at least 3")

    try:
        data = load_manifest(args.manifest)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print("FAIL: %s" % error)
        return 2
    base = args.manifest.parent
    screen = data["screen"]
    style = screen["style"]
    pitch_value = screen.get(
        "final_baseline_pitch_mm",
        screen.get("effective_pitch_mm"),
    )
    if pitch_value is None:
        print("FAIL: manifest has no Wave baseline pitch")
        return 2
    pitch = float(pitch_value)
    angles = data["screen"]["screen_angles_deg"]
    baseline_grid = data.get("wave_baseline_grid") or {}
    per_channel_grid = baseline_grid.get("per_channel", {})
    minimum_clearance = float(
        screen.get("minimum_centerline_clearance_mm", 0.0)
    )
    rotating_bed = (
        "Xθ/Yθ" in str(data.get("bed_motion", ""))
        or "xtheta/ytheta" in str(data.get("bed_motion", "")).lower()
    )
    files = data["files"]
    hashes = data["file_sha256"]
    compensation = data.get("bed_compensation", {})
    compensation_active = bool(data.get("bed_compensation_path"))
    profile_fingerprint = str(compensation.get("profile_fingerprint", ""))
    failed = False

    for channel, label in LABELS.items():
        path = base / files[channel]
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
            actual_hash = sha256_file(path)
            if actual_hash != hashes[channel]:
                raise ValueError(f"manifest hash mismatch for {path.name}")
            if compensation_active:
                if "row-locked projection" not in text:
                    raise ValueError(
                        f"{path.name} has no row-locked projection header"
                    )
                if profile_fingerprint not in text:
                    raise ValueError(
                        f"{path.name} does not identify the active profile"
                    )
            if rotating_bed and "shared Wave row angles" not in text:
                raise ValueError(
                    f"{path.name} has no shared rotating row-angle header"
                )
            channel_pitch = float(
                per_channel_grid.get(channel, {}).get(
                    "pitch_mm",
                    pitch,
                )
            )
            if style == "waves_fixed":
                channel_grid = per_channel_grid.get(channel, {})
                result = audit_fixed_baseline_program(
                    path,
                    float(angles[channel]),
                    channel_pitch,
                    expected_origin_mm=channel_grid.get("origin_mm"),
                    sample_columns=args.sample_columns,
                    rotating_bed=rotating_bed,
                    ratio=(
                        theta_ratio(path) if rotating_bed else 1.0
                    ),
                    minimum_clearance_mm=minimum_clearance,
                )
            else:
                result = audit_program(
                    path,
                    float(angles[channel]),
                    channel_pitch,
                    sample_columns=args.sample_columns,
                    rotating_bed=rotating_bed,
                    ratio=(
                        theta_ratio(path) if rotating_bed else 1.0
                    ),
                )
        except (OSError, ValueError, KeyError) as error:
            print("FAIL: %s" % error)
            return 2
        passed = (
            float(result["baseline_residual_mm"]) <= args.tolerance_mm
            if style == "waves_fixed"
            else float(result["spread_mm"]) <= args.tolerance_mm
        )
        failed |= not passed
        if style == "waves_fixed":
            print(
                "%-8s pitch=%.6f rows=%3d residual=%.6f "
                "wave-range=%.6f..%.6f mm %s"
                % (
                    label,
                    result["pitch_mm"],
                    result["rows"],
                    result["baseline_residual_mm"],
                    result["minimum_wave_range_mm"],
                    result["maximum_wave_range_mm"],
                    "PASS" if passed else "FAIL",
                )
            )
        else:
            print(
                "%-8s samples=%3d min=%.6f median=%.6f max=%.6f "
                "spread=%.6f mm %s"
                % (
                    label,
                    result["samples"],
                    result["minimum_mm"],
                    result["median_mm"],
                    result["maximum_mm"],
                    result["spread_mm"],
                    "PASS" if passed else "FAIL",
                )
            )

    if failed:
        print(
            "FAIL: Wave baseline or adjacent-gap spread exceeds %.6f mm"
            % args.tolerance_mm
        )
        return 1
    if style == "waves_fixed":
        print(
            "PASS: all four inks keep fixed uniform baselines; "
            "row-local visible gaps may vary"
        )
    else:
        print(
            "PASS: all four inks remain within %.6f mm row-spacing spread"
            % args.tolerance_mm
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
