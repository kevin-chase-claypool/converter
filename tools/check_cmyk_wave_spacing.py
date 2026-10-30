"""Verify a saved CMYK Wave set in final machine coordinates.

The Wave screen is generated as a uniform lattice in paper space. Bed
compensation can change that lattice before the coordinates reach grblHAL.
This checker follows the emitted pen-down ``X/Y`` commands, rotates them into
each ink's effective screen frame, and measures adjacent row gaps at many
columns.

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
from pathlib import Path


MOVE = re.compile(
    r"^G[01]\s+[^;]*?X(-?[\d.]+)\s+Y(-?[\d.]+)",
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
    if "XY only" not in str(data.get("bed_motion", "")):
        raise ValueError("manifest is not an XY-only Wave set")
    screen = data.get("screen", {})
    if screen.get("style") != "waves_even":
        raise ValueError("manifest screen style is not waves_even")
    if data.get("bed_compensation_path"):
        raise ValueError(
            "manifest applies bed compensation; final row pitch is not "
            "guaranteed"
        )
    if screen.get("preserve_exact_row_pitch") is not True:
        raise ValueError("manifest does not record an active row-spacing guard")
    return data


def drawing_contours(path: Path) -> list[list[tuple[float, float]]]:
    """Return pen-down polylines from the emitted G-code."""
    contours: list[list[tuple[float, float]]] = []
    current = None
    for raw_line in path.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines():
        line = raw_line.strip()
        if line.startswith("M3"):
            current = []
            contours.append(current)
        elif line.startswith("M5"):
            current = None
        elif current is not None:
            match = MOVE.match(line)
            if match:
                current.append(
                    (float(match.group(1)), float(match.group(2)))
                )
    return [contour for contour in contours if len(contour) > 1]


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


def audit_program(
    path: Path,
    angle_deg: float,
    nominal_pitch_mm: float,
    sample_columns: int = 199,
) -> dict[str, float | int]:
    """Measure adjacent machine-space row gaps in the effective screen frame."""
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
        for contour in drawing_contours(path)
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
    pitch = float(data["screen"]["effective_pitch_mm"])
    angles = data["screen"]["screen_angles_deg"]
    files = data["files"]
    hashes = data["file_sha256"]
    failed = False

    for channel, label in LABELS.items():
        path = base / files[channel]
        try:
            actual_hash = sha256_file(path)
            if actual_hash != hashes[channel]:
                raise ValueError(f"manifest hash mismatch for {path.name}")
            result = audit_program(
                path,
                float(angles[channel]),
                pitch,
                sample_columns=args.sample_columns,
            )
        except (OSError, ValueError, KeyError) as error:
            print("FAIL: %s" % error)
            return 2
        passed = float(result["spread_mm"]) <= args.tolerance_mm
        failed |= not passed
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
            "FAIL: adjacent-gap spread exceeds %.6f mm"
            % args.tolerance_mm
        )
        return 1
    print(
        "PASS: all four inks remain within %.6f mm row-spacing spread"
        % args.tolerance_mm
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
