#!/usr/bin/env python3
"""Recover ink numbers from a plotted CMYK calibration sheet.

The CMYK tab's calibration sheet (``software/generator_tabs/cmyk_sheet.py``)
is saved next to a ``<name>-calibration.json`` manifest that records every
patch rectangle in page millimetres. Plot the four G-code files, then scan
or photograph the sheet flat and run::

    python tools\\cmyk_calibrate.py scan.png --manifest art-calibration.json

The tool finds the four dense corner fiducials, maps the manifest rectangles
onto the image, samples each patch, and reports the paper-relative
transmittance of each ink at full coverage plus a measured-vs-predicted check
of the multiply model on the two- and three-ink mix patches. Those numbers
are what a print-matching preview needs: multiply the four ink transmittances
in C, M, Y, K plot order over white paper.

When no saved manifest is available, the layout can be rebuilt from the
numbers printed in the sheet header (the geometry is deterministic)::

    python tools\\cmyk_calibrate.py scan.png --layout 216x279 --margin 6 --screen crosshatch

Scans work best; for photos keep the sheet flat and filling the frame. Pass
``--corners`` (x1,y1,...,x4,y4 in pixels: top-left, top-right, bottom-left,
bottom-right fiducial centres) when automatic detection fails.
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image


DARK_LUMINANCE = 0.45
NEUTRAL_SPREAD = 0.22
CHANNEL_LABELS = {"c": "C", "m": "M", "y": "Y", "k": "K"}


def load_manifest(path):
    """Read and validate a calibration-sheet manifest."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("kind") != "cmyk-calibration-sheet":
        raise ValueError(f"{path} is not a CMYK calibration-sheet manifest.")
    if len(data.get("fiducials_mm") or []) != 4:
        raise ValueError("The manifest needs exactly four fiducial centres.")
    if not data.get("patches"):
        raise ValueError("The manifest contains no patches.")
    return data


def parse_layout(text):
    """Return ``(page_width_mm, page_height_mm)`` from e.g. ``216x279``."""
    cleaned = str(text).lower().replace(" ", "").replace(",", "x")
    parts = cleaned.split("x")
    if len(parts) != 2:
        raise ValueError("layout must look like 216x279 (mm)")
    return float(parts[0]), float(parts[1])


def rebuild_manifest(layout, margin_mm, screen, pitch_mm=None, levels=None):
    """Rebuild the sheet manifest without a saved file (no screening)."""
    page_w, page_h = parse_layout(layout)
    software = Path(__file__).resolve().parents[1] / "software"
    if str(software) not in sys.path:
        sys.path.insert(0, str(software))
    from generator_tabs.cmyk_sheet import build_sheet

    options = {}
    if pitch_mm:
        options["pitch_mm"] = float(pitch_mm)
    if levels:
        options["levels"] = int(levels)
    _, manifest = build_sheet(
        page_w,
        page_h,
        margin_mm=margin_mm,
        screen=screen,
        marks=False,
        **options,
    )
    return manifest


def load_image(path):
    """Return the image as an ``(h, w, 3)`` float array in 0..1."""
    image = Image.open(path).convert("RGB")
    return np.asarray(image, dtype=np.float32) / 255.0


def luminance(rgb):
    values = np.asarray(rgb, dtype=np.float64)
    return 0.299 * values[..., 0] + 0.587 * values[..., 1] + 0.114 * values[..., 2]


def _components(mask):
    """4-connected components of a boolean mask (lists of (y, x) members)."""
    ys, xs = np.nonzero(mask)
    pixels = set(zip(ys.tolist(), xs.tolist()))
    seen = set()
    components = []
    for start in pixels:
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        members = []
        while stack:
            y, x = stack.pop()
            members.append((y, x))
            for neighbour in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                if neighbour in pixels and neighbour not in seen:
                    seen.add(neighbour)
                    stack.append(neighbour)
        components.append(members)
    return components


def _component_stats(members):
    ys = [member[0] for member in members]
    xs = [member[1] for member in members]
    height = max(ys) - min(ys) + 1
    width = max(xs) - min(xs) + 1
    return {
        "cx": sum(xs) / len(xs),
        "cy": sum(ys) / len(ys),
        "area": len(members),
        "width": width,
        "height": height,
        "aspect": width / max(1, height),
        "fill": len(members) / max(1, width * height),
    }


def detect_fiducials(image):
    """Return the four dense corner fiducials, TL, TR, BL, BR order."""
    height, width = image.shape[:2]
    factor = max(1.0, max(height, width) / 900.0)
    if factor > 1.0:
        small_pil = Image.fromarray(
            (np.clip(image, 0.0, 1.0) * 255.0).astype("uint8")
        )
        small_pil = small_pil.resize(
            (max(1, int(width / factor)), max(1, int(height / factor))),
            Image.BILINEAR,
        )
        small = np.asarray(small_pil, dtype=np.float32) / 255.0
    else:
        small = image
    lum = luminance(small)
    spread = small.max(axis=2) - small.min(axis=2)
    mask = (lum < DARK_LUMINANCE) & (spread < NEUTRAL_SPREAD)
    max_side = 0.20 * min(small.shape[0], small.shape[1])
    candidates = []
    for members in _components(mask):
        stats = _component_stats(members)
        if stats["area"] < 24 or stats["fill"] < 0.5:
            continue
        if not 0.55 <= stats["aspect"] <= 1.8:
            continue
        if max(stats["width"], stats["height"]) > max_side:
            continue
        stats["score"] = stats["area"] * stats["fill"]
        candidates.append(stats)
    small_h, small_w = small.shape[:2]
    corner_order = ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0), (1.0, 1.0))
    picked_indexes = []
    for corner_x, corner_y in corner_order:
        best_index = None
        best_distance = None
        for index, stats in enumerate(candidates):
            if index in picked_indexes:
                continue
            x = stats["cx"] / small_w
            y = stats["cy"] / small_h
            distance = math.hypot(x - corner_x, y - corner_y)
            if distance > 0.6:
                continue
            if (
                best_distance is None
                or distance < best_distance - 1e-9
                or (
                    abs(distance - best_distance) <= 1e-9
                    and stats["score"]
                    > candidates[best_index]["score"]
                )
            ):
                best_index = index
                best_distance = distance
        if best_index is None:
            raise ValueError(
                "Could not find a dense corner fiducial; pass --corners with "
                "the four fiducial centres in pixels."
            )
        picked_indexes.append(best_index)
    picked = [candidates[index] for index in picked_indexes]
    areas = [mark["area"] for mark in picked]
    if max(areas) > 3.0 * min(areas):
        raise ValueError(
            "The four corner marks differ in size; the wrong marks were "
            "picked. Pass --corners with the four fiducial centres."
        )
    corners = []
    for best in picked:
        corners.append(
            (
                best["cx"] * width / small_w,
                best["cy"] * height / small_h,
            )
        )
    return corners


def solve_homography(source_points, target_points):
    """Least-squares homography mapping source (mm) to target (px)."""
    rows = []
    values = []
    for (x, y), (u, v) in zip(source_points, target_points):
        rows.append([x, y, 1.0, 0.0, 0.0, 0.0, -u * x, -u * y])
        values.append(u)
        rows.append([0.0, 0.0, 0.0, x, y, 1.0, -v * x, -v * y])
        values.append(v)
    solution, *_ = np.linalg.lstsq(
        np.asarray(rows, dtype=np.float64),
        np.asarray(values, dtype=np.float64),
        rcond=None,
    )
    return np.asarray(
        [
            [solution[0], solution[1], solution[2]],
            [solution[3], solution[4], solution[5]],
            [solution[6], solution[7], 1.0],
        ],
        dtype=np.float64,
    )


def map_points(matrix, points):
    """Map page-millimetre points through a homography to pixels."""
    mapped = []
    for x, y in points:
        vector = matrix @ np.asarray([x, y, 1.0], dtype=np.float64)
        scale = vector[2] if abs(vector[2]) > 1e-12 else 1e-12
        mapped.append((float(vector[0] / scale), float(vector[1] / scale)))
    return mapped


def sample_rect(image, matrix, rect_mm, inset=0.2):
    """Trimmed mean colour of a manifest rectangle, in image RGB."""
    x, y, width, height = (float(value) for value in rect_mm)
    corners_mm = (
        (x + inset * width, y + inset * height),
        (x + (1.0 - inset) * width, y + inset * height),
        (x + (1.0 - inset) * width, y + (1.0 - inset) * height),
        (x + inset * width, y + (1.0 - inset) * height),
    )
    corners_px = map_points(matrix, corners_mm)
    height_px, width_px = image.shape[:2]
    x0 = max(0, int(np.floor(min(point[0] for point in corners_px))))
    x1 = min(width_px, int(np.ceil(max(point[0] for point in corners_px))) + 1)
    y0 = max(0, int(np.floor(min(point[1] for point in corners_px))))
    y1 = min(height_px, int(np.ceil(max(point[1] for point in corners_px))) + 1)
    region = image[y0:y1, x0:x1].reshape(-1, 3)
    if region.size == 0:
        return None
    low = np.percentile(region, 10.0, axis=0)
    high = np.percentile(region, 90.0, axis=0)
    return np.clip(region, low, high).mean(axis=0)


def sample_sheet(image, manifest, corners):
    """Return ``{patch id: sampled RGB}`` for the mapped sheet."""
    sources = [
        (float(fiducial["x"]), float(fiducial["y"]))
        for fiducial in manifest["fiducials_mm"]
    ]
    matrix = solve_homography(sources, corners)
    samples = {}
    for patch in manifest["patches"]:
        sample = sample_rect(image, matrix, patch["rect_mm"])
        if sample is not None:
            samples[patch["id"]] = sample
    return samples


def fit_profile(manifest, samples):
    """Paper-relative ink transmittances plus multiply-model validation."""
    paper_id = next(
        (
            patch["id"]
            for patch in manifest["patches"]
            if patch.get("block") == "paper"
        ),
        None,
    )
    if paper_id is None or paper_id not in samples:
        raise ValueError("The sheet has no sampled paper patch.")
    paper = np.clip(samples[paper_id], 1e-3, None)
    reflectance = {
        patch_id: np.clip(sample / paper, 0.0, 1.5)
        for patch_id, sample in samples.items()
    }
    inks = {}
    for channel in ("c", "m", "y", "k"):
        spot = next(
            (
                patch
                for patch in manifest["patches"]
                if patch.get("block") == "spot"
                and patch.get("channels") == [channel]
            ),
            None,
        )
        if spot and spot["id"] in reflectance:
            inks[channel] = reflectance[spot["id"]]
    validation = []
    for patch in manifest["patches"]:
        if patch.get("block") != "mix":
            continue
        channels = list(patch.get("channels") or [])
        if not channels or any(channel not in inks for channel in channels):
            continue
        if patch["id"] not in reflectance:
            continue
        predicted = np.ones(3, dtype=np.float64)
        for channel in channels:
            predicted = predicted * inks[channel]
        actual = reflectance[patch["id"]]
        validation.append(
            {
                "id": patch["id"],
                "label": patch.get("label", ""),
                "channels": channels,
                "measured": [round(float(v), 4) for v in actual],
                "predicted": [round(float(v), 4) for v in predicted],
                "error": [round(float(v), 4) for v in (actual - predicted)],
            }
        )
    blocks = {}
    for patch in manifest["patches"]:
        if patch["id"] not in reflectance:
            continue
        blocks.setdefault(patch.get("block", "?"), []).append(
            {
                "label": patch.get("label", ""),
                "channels": patch.get("channels", []),
                "reflectance": [
                    round(float(v), 4) for v in reflectance[patch["id"]]
                ],
            }
        )
    return {
        "kind": "cmyk-ink-profile",
        "version": 1,
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
        "paper_rgb": [round(float(v), 4) for v in paper],
        "inks": {
            channel: [round(float(v), 4) for v in values]
            for channel, values in inks.items()
        },
        "validation": validation,
        "blocks": blocks,
    }


def _rgb255(values):
    parts = []
    for value in values:
        clamped = max(0.0, min(1.0, float(value)))
        parts.append(f"{int(round(clamped * 255.0)):3d}")
    return " ".join(parts)


def _block_lookup(manifest):
    blocks = {}
    for patch in manifest["patches"]:
        blocks.setdefault(patch.get("block", "?"), []).append(patch)
    return blocks


def print_report(args, image, manifest, samples, profile, detection, source):
    blocks = _block_lookup(manifest)
    settings = manifest.get("sheet_settings", {})
    print("CMYK calibration report")
    print(
        f"  image  : {args.image} "
        f"({image.shape[1]} x {image.shape[0]} px, fiducials: {detection})"
    )
    print(f"  source : {source}")
    print(
        "  sheet  : "
        f"{manifest['page']['width_mm']:g} x "
        f"{manifest['page']['height_mm']:g} mm, "
        f"pitch {settings.get('pitch_mm', '?')} mm, "
        f"dot {int(round(100.0 * float(settings.get('dot_scale', 0.0))))}%, "
        f"pen {settings.get('pen_width_mm', '?')} mm, "
        f"overdraw {settings.get('overdraw', '?')}"
    )
    print(f"  paper  : RGB {_rgb255(profile['paper_rgb'])}")
    print()
    print("Ink transmittance at full coverage (paper = 1.0; 0-255 values):")
    missing = []
    for channel in ("c", "m", "y", "k"):
        values = profile["inks"].get(channel)
        if not values:
            missing.append(channel)
            print(f"  {CHANNEL_LABELS[channel]}   (dense spot not sampled)")
            continue
        print(
            f"  {CHANNEL_LABELS[channel]}   "
            f"({values[0]:.2f}, {values[1]:.2f}, {values[2]:.2f})"
            f"   {_rgb255(values)}"
        )
    if missing:
        print(
            "  warning: plot and scan every ink file; missing "
            + "/".join(CHANNEL_LABELS[channel] for channel in missing)
        )
    print()
    print("Multiply check on the mix patches (measured vs predicted, 0-255):")
    if profile["validation"]:
        errors = []
        for row in profile["validation"]:
            error = np.abs(np.asarray(row["error"], dtype=np.float64))
            errors.extend(error.tolist())
            print(
                f"  {row['label']:<6} "
                f"measured {_rgb255(row['measured'])}   "
                f"predicted {_rgb255(row['predicted'])}   "
                f"delta {_rgb255(error)}"
            )
        mean_error = float(np.mean(errors)) * 255.0
        max_error = float(np.max(errors)) * 255.0
        if mean_error <= 8.0:
            verdict = "the multiply model matches this pen set"
        elif mean_error <= 20.0:
            verdict = "multiply is approximate for these pens"
        else:
            verdict = "the mixes disagree with the single inks; recheck the plot"
        print(
            f"  mean |delta| {mean_error:.0f}/255, worst {max_error:.0f}/255 "
            f"- {verdict}."
        )
    else:
        print("  no mix patches could be evaluated.")
    print()
    paper = np.asarray(profile["paper_rgb"], dtype=np.float64)
    for block in ("coverage", "dots", "steps", "overdraw"):
        patches = blocks.get(block, [])
        if not patches:
            continue
        print(f"{block.upper()} cells (paper-relative luminance by label):")
        for channel in ("c", "m", "y", "k"):
            row = []
            for patch in patches:
                if patch.get("channels") != [channel]:
                    continue
                if patch["id"] not in samples:
                    continue
                value = samples[patch["id"]] / paper
                row.append(f"{patch.get('label', '?'):>4}:{luminance(value):.2f}")
            if row:
                print(f"  {CHANNEL_LABELS[channel]}   " + "  ".join(row))
        print()
    gcr_patches = blocks.get("gcr", [])
    if gcr_patches:
        print("GCR ramp on 50% gray (sampled reflectance; judge neutrality on paper):")
        for patch in gcr_patches:
            if patch["id"] not in samples:
                continue
            value = samples[patch["id"]] / paper
            channels = " ".join(
                CHANNEL_LABELS[channel].lower()
                for channel in patch.get("channels", [])
            )
            print(
                f"  {patch.get('label', '?'):>4}%  "
                f"R {value[0]:.2f} G {value[1]:.2f} B {value[2]:.2f}   "
                f"({channels or 'paper'})"
            )
        print()
    print(
        "Preview model: result = paper x C x M x Y x K (multiply, plot order)."
    )


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=(
            "Sample a plotted CMYK calibration sheet and recover the ink "
            "transmittances used by a multiply print-matching preview."
        )
    )
    parser.add_argument("image", help="scan or photo of the plotted sheet")
    parser.add_argument(
        "--manifest",
        default="",
        help="<name>-calibration.json saved with the sheet's G-code",
    )
    parser.add_argument(
        "--layout",
        default="",
        help=(
            "rebuild the layout without a manifest: PAGE_WxPAGE_H in mm, "
            "e.g. 216x279 (read it from the sheet header)"
        ),
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=6.0,
        help="page margin in mm for --layout (default 6)",
    )
    parser.add_argument(
        "--screen",
        choices=("lines", "crosshatch", "halftone"),
        default="halftone",
        help="sheet screen for --layout (default halftone)",
    )
    parser.add_argument(
        "--pitch",
        type=float,
        default=0.0,
        help="printed pitch in mm for --layout (descriptive only)",
    )
    parser.add_argument(
        "--levels",
        type=int,
        default=0,
        help="printed hatch levels for --layout (descriptive only)",
    )
    parser.add_argument(
        "--out",
        default="",
        help="profile JSON path (default: <scan stem>-profile.json)",
    )
    parser.add_argument(
        "--corners",
        default="",
        help=(
            "manual fiducial centres in pixels, TL TR BL BR: "
            "x1,y1,x2,y2,x3,y3,x4,y4"
        ),
    )
    args = parser.parse_args(argv)

    if not args.manifest and not args.layout:
        parser.error("give --manifest, or --layout with --margin and --screen")
    if args.manifest:
        manifest = load_manifest(args.manifest)
        source = f"manifest {Path(args.manifest).name}"
    else:
        try:
            manifest = rebuild_manifest(
                args.layout,
                args.margin,
                args.screen,
                args.pitch,
                args.levels,
            )
        except ValueError as exc:
            parser.error(str(exc))
        source = f"rebuilt layout {args.layout} mm ({args.screen})"
    image = load_image(args.image)
    if args.corners:
        values = [
            float(part)
            for part in args.corners.replace(" ", "").split(",")
            if part
        ]
        if len(values) != 8:
            parser.error("--corners needs eight numbers: x1,y1,...,x4,y4")
        corners = [
            (values[index], values[index + 1]) for index in range(0, 8, 2)
        ]
        detection = "manual"
    else:
        corners = detect_fiducials(image)
        detection = "auto"
    samples = sample_sheet(image, manifest, corners)
    if not samples:
        raise SystemExit("No patches could be sampled; check image and manifest.")
    profile = fit_profile(manifest, samples)
    print_report(args, image, manifest, samples, profile, detection, source)
    out_path = (
        Path(args.out)
        if args.out
        else Path(args.image).with_name(
            Path(args.image).stem + "-profile.json"
        )
    )
    out_path.write_text(
        json.dumps(profile, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Profile written to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
