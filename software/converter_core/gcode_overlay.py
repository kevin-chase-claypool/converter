"""Post-save overlay audit for a multi-ink G-code set."""

from __future__ import annotations

import datetime
import json
import math
import os
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageFont

from .cmyk import CHANNEL_COLORS, CHANNEL_LABELS, CHANNELS, SCREEN_ANGLES_DEG
from .motion_check import (
    MOVE,
    analyse_gcode,
)
from .gcode_registration import audit_cmyk_gcode_set


OVERLAY_SIZE_PX = 1400
MAX_RENDER_SEGMENTS_PER_INK = 120_000


def _overlay_font(size):
    for name in ("arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def pen_down_segments(text):
    """Return ``(start, end, line_number)`` pen-down XY segments."""
    previous = None
    pen_down = False
    saw_pen_command = False
    drawn = []
    all_g1 = []
    for number, line in enumerate(str(text).splitlines(), 1):
        stripped = line.strip()
        if stripped.startswith("M3"):
            pen_down = True
            saw_pen_command = True
            continue
        if stripped.startswith("M5"):
            pen_down = False
            saw_pen_command = True
            continue
        match = MOVE.match(line)
        if not match:
            continue
        kind, x_text, y_text, _a_text, _feed_text = match.groups()
        point = (float(x_text), float(y_text))
        if previous is not None:
            segment = (previous, point, number)
            if kind == "1":
                all_g1.append(segment)
                if pen_down:
                    drawn.append(segment)
        previous = point
    # Use Z-mode programs, or old files without pen commands, as drawn paths.
    return drawn if saw_pen_command else all_g1


def _segment_metrics(segments):
    if not segments:
        return {
            "segments": 0,
            "points": 0,
            "bounds_mm": None,
            "center_mm": None,
            "max_radius_mm": 0.0,
        }
    points = [
        point
        for start, end, _line in segments
        for point in (start, end)
    ]
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    bounds = (min(xs), min(ys), max(xs), max(ys))
    center = (
        (bounds[0] + bounds[2]) / 2.0,
        (bounds[1] + bounds[3]) / 2.0,
    )
    return {
        "segments": len(segments),
        "points": len(points),
        "bounds_mm": tuple(round(value, 6) for value in bounds),
        "center_mm": tuple(round(value, 6) for value in center),
        "max_radius_mm": round(
            max(math.hypot(x, y) for x, y in points),
            6,
        ),
    }


def _expected_overlay_identity(settings):
    profile = None
    if getattr(settings, "bed_compensation_path", ""):
        from .bed_compensation import load_bed_compensation

        profile = load_bed_compensation(settings.bed_compensation_path)
    row_angles = None
    if (
        profile is not None
        and not profile.identity
        and getattr(settings, "row_locked_compensation", False)
    ):
        row_angles = {
            channel: SCREEN_ANGLES_DEG[channel]
            for channel in CHANNELS
        }
    return {
        "frame_center_mm": getattr(settings, "frame_center_mm", None),
        "profile_fingerprint": (
            profile.fingerprint if profile is not None else None
        ),
        "machine_reach_radius_mm": float(
            getattr(settings, "machine_reach_radius_mm", 0.0)
        ),
        "row_angles": row_angles,
    }


def _render_overlay(
    ink_metrics,
    identity,
    registration,
    reach_mm,
    planning_radius_mm,
    passed,
    errors,
    path,
):
    size = OVERLAY_SIZE_PX
    margin = 80
    plot_radius = max(
        [
            float(reach_mm or 0.0),
            float(planning_radius_mm or 0.0),
            *[
                float(metrics["max_radius_mm"])
                for metrics in ink_metrics.values()
            ],
            1.0,
        ]
    ) * 1.05
    scale = (size - 2 * margin) / (2.0 * plot_radius)
    center_px = (size / 2.0, size / 2.0)

    def screen_point(point):
        return (
            center_px[0] + float(point[0]) * scale,
            center_px[1] - float(point[1]) * scale,
        )

    base = Image.new("RGBA", (size, size), (255, 255, 255, 255))
    draw = ImageDraw.Draw(base)
    if reach_mm:
        radius_px = float(reach_mm) * scale
        draw.ellipse(
            (
                center_px[0] - radius_px,
                center_px[1] - radius_px,
                center_px[0] + radius_px,
                center_px[1] + radius_px,
            ),
            outline=(148, 163, 184, 255),
            width=3,
        )
    if planning_radius_mm:
        radius_px = float(planning_radius_mm) * scale
        draw.ellipse(
            (
                center_px[0] - radius_px,
                center_px[1] - radius_px,
                center_px[0] + radius_px,
                center_px[1] + radius_px,
            ),
            outline=(220, 38, 38, 255) if not passed else (21, 128, 61, 255),
            width=3,
        )
    draw.line(
        [
            (margin, center_px[1]),
            (size - margin, center_px[1]),
        ],
        fill=(210, 214, 220, 255),
        width=1,
    )
    draw.line(
        [
            (center_px[0], margin),
            (center_px[0], size - margin),
        ],
        fill=(210, 214, 220, 255),
        width=1,
    )

    for channel in CHANNELS:
        if channel not in ink_metrics:
            continue
        metrics = ink_metrics[channel]
        segments = metrics.pop("_segments", [])
        rgb = ImageColor.getrgb(CHANNEL_COLORS[channel])
        layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        layer_draw = ImageDraw.Draw(layer)
        stride = max(
            1,
            int(
                math.ceil(
                    len(segments) / MAX_RENDER_SEGMENTS_PER_INK
                )
            ),
        )
        for start, end, _line in segments[::stride]:
            layer_draw.line(
                [screen_point(start), screen_point(end)],
                fill=(*rgb, 118),
                width=2,
            )
        base = Image.alpha_composite(base, layer)
        bounds = metrics.get("bounds_mm")
        if bounds:
            x0, y0 = screen_point((bounds[0], bounds[3]))
            x1, y1 = screen_point((bounds[2], bounds[1]))
            draw = ImageDraw.Draw(base)
            draw.rectangle(
                (x0, y0, x1, y1),
                outline=(*rgb, 135),
                width=2,
            )

    draw = ImageDraw.Draw(base)
    font = _overlay_font(15)
    title_font = _overlay_font(20)
    title = "CMYK software registration audit - " + (
        "PASS" if passed else "BLOCKED"
    )
    draw.text(
        (20, 18),
        title,
        fill=(21, 128, 61, 255) if passed else (185, 28, 28, 255),
        font=title_font,
    )
    frame_center = identity.get("frame_center_mm")
    profile = identity.get("profile_fingerprint") or "none"
    draw.text(
        (20, 36),
        "frame %s mm | profile %s | reach %s mm | planning %s mm | "
        "physical overlay pending"
        % (
            "%.3f,%.3f" % frame_center
            if frame_center is not None
            else "missing",
            profile,
            "%.3f" % float(reach_mm) if reach_mm is not None else "?",
            (
                "%.3f" % float(planning_radius_mm)
                if planning_radius_mm is not None
                else "?"
            ),
        ),
        fill=(51, 65, 85, 255),
        font=font,
    )
    legend_y = 62
    for channel in CHANNELS:
        if channel not in ink_metrics:
            continue
        rgb = ImageColor.getrgb(CHANNEL_COLORS[channel])
        draw.line(
            [(20, legend_y + 5), (52, legend_y + 5)],
            fill=(*rgb, 255),
            width=3,
        )
        metrics = ink_metrics[channel]
        draw.text(
            (60, legend_y),
            "%s: %d seg, radius %.3f mm"
            % (
                CHANNEL_LABELS[channel],
                metrics["segments"],
                metrics["max_radius_mm"],
            ),
            fill=(30, 41, 59, 255),
            font=font,
        )
        legend_y += 18
    mark_points = {}
    if registration.get("passed") or registration.get("inks"):
        reference_channel = registration.get("reference_channel")
        for mark_id in registration.get("mark_ids", []):
            reference = (
                registration.get("inks", {})
                .get(reference_channel, {})
                .get("marks", {})
                .get(mark_id, {})
                .get("normalized_center_mm")
            )
            if reference is None:
                continue
            reference_screen = screen_point(reference)
            for channel in CHANNELS:
                point = (
                    registration.get("inks", {})
                    .get(channel, {})
                    .get("marks", {})
                    .get(mark_id, {})
                    .get("normalized_center_mm")
                )
                if point is None:
                    continue
                point_screen = screen_point(point)
                rgb = ImageColor.getrgb(CHANNEL_COLORS[channel])
                draw.line(
                    [reference_screen, point_screen],
                    fill=(*rgb, 230),
                    width=3,
                )
                draw.ellipse(
                    (
                        point_screen[0] - 5,
                        point_screen[1] - 5,
                        point_screen[0] + 5,
                        point_screen[1] + 5,
                    ),
                    outline=(*rgb, 255),
                    width=2,
                )
                mark_points.setdefault(mark_id, []).append(point_screen)
    for mark_id, points in mark_points.items():
        if not points:
            continue
        x = min(point[0] for point in points)
        y = min(point[1] for point in points)
        draw.text(
            (x + 7, y + 5),
            mark_id,
            fill=(30, 41, 59, 255),
            font=font,
        )
    summary_y = size - 76 if errors else size - 55
    draw.text(
        (20, summary_y),
        "software registration %s | marks %d | max %.3f mm | "
        "physical test pending"
        % (
            "PASS" if registration.get("passed") else "BLOCKED",
            int(registration.get("mark_count", 0)),
            max(
                (
                    float(ink.get("max_residual_mm", 0.0))
                    for ink in registration.get("inks", {}).values()
                ),
                default=0.0,
            ),
        ),
        fill=(21, 128, 61, 255)
        if registration.get("passed")
        else (185, 28, 28, 255),
        font=font,
    )
    if errors:
        draw.multiline_text(
            (20, size - 55),
            "\n".join(errors[:2]),
            fill=(185, 28, 28, 255),
            font=font,
            spacing=2,
        )
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".tmp")
    base.convert("RGB").save(temporary, format="PNG")
    os.replace(temporary, path)


def write_cmyk_gcode_overlay(
    program_paths,
    output_stem,
    settings,
    expected_pen_offsets_mm=None,
):
    """Audit saved CMYK programs and render them in one machine-frame overlay."""
    programs = {}
    paths = {}
    for channel in CHANNELS:
        if channel not in program_paths:
            continue
        path = Path(program_paths[channel])
        programs[channel] = path.read_text(
            encoding="utf-8",
            errors="replace",
        )
        paths[channel] = path
    expected = _expected_overlay_identity(settings)
    expected_row_angles = expected["row_angles"]
    if expected_row_angles is not None:
        expected_row_angles = {
            channel: angle
            for channel, angle in expected_row_angles.items()
            if channel in programs
        }
    audit = audit_cmyk_gcode_set(
        programs,
        settings,
        expected_pen_offsets_mm=expected_pen_offsets_mm,
        expected_row_angles=expected_row_angles,
    )
    identity = audit["identity"]
    registration = audit["registration"]
    errors = list(audit["errors"])
    reach = identity.get("machine_reach_radius_mm")
    planning_radius = identity.get("planning_radius_mm")
    ink_metrics = {}
    for channel, text in programs.items():
        segments = pen_down_segments(text)
        metrics = _segment_metrics(segments)
        analysis = analyse_gcode(text, settings)
        metrics["max_ink_radius_mm"] = round(
            float(analysis.get("max_ink_radius_mm", 0.0)),
            6,
        )
        metrics["row_angle_deg"] = SCREEN_ANGLES_DEG[channel]
        metrics["_segments"] = segments
        ink_metrics[channel] = metrics
        if reach and metrics["max_ink_radius_mm"] > reach + 0.001:
            errors.append(
                "%s ink envelope %.3f mm exceeds reach %.3f mm"
                % (
                    CHANNEL_LABELS[channel],
                    metrics["max_ink_radius_mm"],
                    reach,
                )
            )
    output_stem = Path(output_stem)
    if output_stem.suffix:
        output_stem = output_stem.with_suffix("")
    image_path = output_stem.with_suffix(".png")
    report_path = output_stem.with_suffix(".json")
    passed = not errors
    _render_overlay(
        ink_metrics,
        identity,
        registration,
        reach,
        planning_radius,
        passed,
        errors,
        image_path,
    )
    for metrics in ink_metrics.values():
        metrics.pop("_segments", None)
    report = {
        "kind": "cmyk-gcode-overlay-audit",
        "version": 2,
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
        "scope": [
            "software_registration",
            "program_identity",
            "machine_frame",
            "machine_reach",
            "emitted_machine_geometry",
            "registration_marks",
            "compensation_inversion",
            "pen_offset_single_application",
            "translation_rotation_scale",
        ],
        "passed": passed,
        "registration_passed": registration.get("passed", False),
        "physical_overlay": "pending physical four-pen test",
        "errors": errors,
        "identity": identity,
        "registration": registration,
        "programs": {
            channel: str(paths[channel])
            for channel in programs
        },
        "inks": {
            channel: ink_metrics[channel]
            for channel in programs
        },
        "overlay_png": str(image_path),
        "overlay_json": str(report_path),
    }
    temporary = report_path.with_suffix(report_path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(report, indent=2) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, report_path)
    return report
