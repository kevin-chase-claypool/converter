"""Export and verify a CMYK print set through the real converter workflow.

The driver intentionally uses the existing ``CMYK Photo`` tab, its workflow
preset application and save path, and ``MainWindow.export_program_set``. It
does not synthesize a replacement SVG or G-code document.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.machinery
import importlib.util
import json
import math
import os
import re
import sys
import tempfile
import time
from contextlib import ExitStack
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SOFTWARE_DIR = ROOT / "software"
if str(SOFTWARE_DIR) not in sys.path:
    sys.path.insert(0, str(SOFTWARE_DIR))

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import converter_core as converter
from program_set_export import program_set_paths


PRINT_LABELS = ("01-yellow", "02-magenta", "03-cyan", "04-black")
PRINT_CHANNELS = ("y", "m", "c", "k")
UNIT_COMMANDS = ("G21", "G90", "G94", "G17", "G54")
MAX_PREVIEW_BYTES = 750_000
_COORDINATE_RE = re.compile(r"\b([XY])(-?(?:\d+(?:\.\d*)?|\.\d+))")
_MOVE_RE = re.compile(r"^G(?:0|1)\b")


class HeadlessExportError(RuntimeError):
    """The application did not produce a complete verified CMYK set."""


@dataclass(frozen=True)
class ExportOptions:
    source: Path
    output_dir: Path
    base_name: str
    recipe: str = "process_area"
    page_mm: float = 250.0
    margin_mm: float = 5.0
    scale_pct: float = 100.0
    pen_width_mm: float = 0.9
    pitch_mm: float = 0.35
    path_tolerance_mm: float = 0.05
    max_marks: int = 800_000
    seed: int = 7
    theta_mode: str = "optimized"
    timeout_seconds: float = 900.0
    determinism_repeat: bool = True
    preview: bool = True
    reference_image: Path | None = None
    ink_profile: Path | None = None


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_app_module():
    path = SOFTWARE_DIR / "qt_svg_to_gcode.pyw"
    name = "converter_headless_cmyk_app"
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    spec = importlib.util.spec_from_loader(name, loader)
    if spec is None:
        raise HeadlessExportError(f"Could not load the converter app: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    loader.exec_module(module)
    return module


def _qt_application():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


def _cmyk_tab(window):
    for title, widget, _group, _description in window.generator_tools:
        if title == "CMYK Photo":
            return widget
    raise HeadlessExportError("The CMYK Photo tab is unavailable.")


def _expected_files(output_dir: Path, base_name: str) -> tuple[Path, ...]:
    base_path = output_dir / f"{base_name}.gcode"
    programs = tuple(program_set_paths(base_path, PRINT_LABELS))
    manifest = output_dir / f"{base_name}-set.json"
    return programs + (manifest,)


def _configure_tab(tab, options: ExportOptions) -> None:
    tab.pen_width.setValue(float(options.pen_width_mm))
    tab.page_w.setValue(float(options.page_mm))
    tab.page_h.setValue(float(options.page_mm))
    tab.margin.setValue(float(options.margin_mm))
    tab.scale_pct.setValue(float(options.scale_pct))
    tab.registration_marks.setChecked(True)
    tab.theta_mode.set_value(str(options.theta_mode))
    tab.calibration_mode.setChecked(False)
    for box in tab.write_boxes.values():
        box.setChecked(True)
    if not tab.apply_workflow_preset(options.recipe):
        raise HeadlessExportError(
            f"Could not apply CMYK workflow recipe {options.recipe!r}: "
            f"{tab.status.text()}"
        )
    tab.pen_width.setValue(float(options.pen_width_mm))
    tab.page_w.setValue(float(options.page_mm))
    tab.page_h.setValue(float(options.page_mm))
    tab.margin.setValue(float(options.margin_mm))
    tab.scale_pct.setValue(float(options.scale_pct))
    tab.pitch.setValue(float(options.pitch_mm))
    tab.path_tolerance.setValue(float(options.path_tolerance_mm))
    tab.max_marks.setValue(int(options.max_marks))
    tab.seed.setValue(int(options.seed))
    tab.registration_marks.setChecked(True)
    tab.theta_mode.set_value(str(options.theta_mode))
    tab.calibration_mode.setChecked(False)
    for box in tab.write_boxes.values():
        box.setChecked(True)
    tab.workflow_navigator.set_stage("review")
    tab._update_wave_spacing_guard()
    tab._refresh_pass_summary()


def _dialog_capture(messages: list[tuple[str, str]]):
    def capture(kind):
        def record(*args, **_kwargs):
            text = str(args[2]) if len(args) >= 3 else ""
            messages.append((kind, text))
            return None

        return record

    return (
        mock.patch(
            "PySide6.QtWidgets.QMessageBox.critical",
            side_effect=capture("critical"),
        ),
        mock.patch(
            "PySide6.QtWidgets.QMessageBox.warning",
            side_effect=capture("warning"),
        ),
        mock.patch(
            "PySide6.QtWidgets.QMessageBox.information",
            side_effect=capture("information"),
        ),
    )


def _wait_for_set(
    app,
    tab,
    window,
    expected: tuple[Path, ...],
    messages: list[tuple[str, str]],
    timeout_seconds: float,
) -> None:
    deadline = time.monotonic() + max(1.0, float(timeout_seconds))
    while time.monotonic() < deadline:
        app.processEvents()
        critical = [text for kind, text in messages if kind == "critical"]
        if critical:
            raise HeadlessExportError(
                "The application rejected the CMYK export: " + "; ".join(critical)
            )
        reported_saved = tab.status.text().startswith("Saved 4 G-code files")
        if reported_saved and all(path.is_file() for path in expected):
            return
        if not tab.analysis_running() and not getattr(tab, "_pending_save", False):
            file_state = ", ".join(
                f"{path.name}={path.is_file()}" for path in expected
            )
            raise HeadlessExportError(
                "The CMYK save ended without a complete set. "
                f"Status: {tab.status.text()} | "
                f"Window: {window.status.text()} | "
                f"Reported saved: {reported_saved} | "
                f"Files: {file_state}"
            )
        time.sleep(0.02)
    tab.cancel_analysis()
    raise HeadlessExportError(
        "Timed out waiting for the CMYK set: "
        + ", ".join(path.name for path in expected)
    )


def _header_lines(gcode: str) -> list[str]:
    return [
        line.strip()
        for line in gcode.splitlines()
        if line.strip().startswith("(")
    ]


def _command_lines(gcode: str) -> list[str]:
    return [
        line.strip()
        for line in gcode.splitlines()
        if line.strip() and not line.lstrip().startswith("(")
    ]


def _common_header(gcode: str) -> tuple[str, ...]:
    prefixes = (
        "(frame center",
        "(theta ratio",
        "(feed ",
        "(reach guard",
        "(bed compensation",
        "(screen chain",
    )
    return tuple(
        line for line in _header_lines(gcode) if line.startswith(prefixes)
    )


def _layer_bounds(layers, width_mm: float, height_mm: float) -> dict[str, dict]:
    result = {}
    epsilon = 1e-6
    for channel in PRINT_CHANNELS:
        points = [
            point
            for contour in layers.get(channel, ())
            for point in contour
        ]
        if not points:
            raise HeadlessExportError(
                f"{channel.upper()} contains no pen-down geometry."
            )
        min_x = min(float(x) for x, _y in points)
        max_x = max(float(x) for x, _y in points)
        min_y = min(float(y) for _x, y in points)
        max_y = max(float(y) for _x, y in points)
        if (
            min_x < -epsilon
            or min_y < -epsilon
            or max_x > width_mm + epsilon
            or max_y > height_mm + epsilon
        ):
            raise HeadlessExportError(
                f"{channel.upper()} exceeds the {width_mm:g} x {height_mm:g} "
                f"mm page: x {min_x:.6f}..{max_x:.6f}, "
                f"y {min_y:.6f}..{max_y:.6f}."
            )
        result[channel] = {
            "min_x_mm": min_x,
            "max_x_mm": max_x,
            "min_y_mm": min_y,
            "max_y_mm": max_y,
            "marks": len(layers.get(channel, ())),
        }
    return result


def _machine_bounds(gcode: str) -> dict[str, float]:
    maximum_radius = 0.0
    max_x = -math.inf
    min_x = math.inf
    max_y = -math.inf
    min_y = math.inf
    move_count = 0
    for line in _command_lines(gcode):
        if not _MOVE_RE.match(line) or line.startswith("G53 "):
            continue
        words = dict(_COORDINATE_RE.findall(line))
        if "X" not in words and "Y" not in words:
            continue
        x = float(words.get("X", "0"))
        y = float(words.get("Y", "0"))
        max_x = max(max_x, x)
        min_x = min(min_x, x)
        max_y = max(max_y, y)
        min_y = min(min_y, y)
        maximum_radius = max(maximum_radius, math.hypot(x, y))
        move_count += 1
    if not move_count:
        raise HeadlessExportError("No coordinate-bearing XY moves were found.")
    return {
        "min_x_mm": min_x,
        "max_x_mm": max_x,
        "min_y_mm": min_y,
        "max_y_mm": max_y,
        "max_radius_mm": maximum_radius,
        "xy_moves": move_count,
    }


def verify_program_set(
    output_dir: Path,
    base_name: str,
    source: Path,
    layers,
    options: ExportOptions,
) -> dict[str, Any]:
    """Verify the four programs, manifest, page bounds, and machine bounds."""
    expected = _expected_files(output_dir, base_name)
    missing = [path for path in expected if not path.is_file()]
    if missing:
        raise HeadlessExportError(
            "Incomplete CMYK set; missing " + ", ".join(path.name for path in missing)
        )
    program_paths = expected[:4]
    manifest_path = expected[4]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HeadlessExportError(f"Could not read the set manifest: {exc}") from exc

    if manifest.get("kind") != "cmyk-print-set":
        raise HeadlessExportError("The companion JSON is not a CMYK print set.")
    if int(manifest.get("version", 0)) != 8:
        raise HeadlessExportError(
            f"Expected manifest version 8, got {manifest.get('version')!r}."
        )
    if manifest.get("print_order") != list(PRINT_LABELS):
        raise HeadlessExportError(
            "Physical ink order is not Yellow, Magenta, Cyan, Black."
        )
    if manifest.get("source", {}).get("sha256") != _sha256(source):
        raise HeadlessExportError("The manifest source hash does not match.")
    if manifest.get("registration_crosses") is not True:
        raise HeadlessExportError("Registration crosses are not enabled in the set.")

    page = manifest.get("page", {})
    width_mm = float(page.get("width_mm", 0.0))
    height_mm = float(page.get("height_mm", 0.0))
    if not (
        math.isclose(width_mm, options.page_mm, abs_tol=1e-6)
        and math.isclose(height_mm, options.page_mm, abs_tol=1e-6)
    ):
        raise HeadlessExportError(
            f"Manifest page is {width_mm:g} x {height_mm:g} mm, "
            f"expected {options.page_mm:g} mm square."
        )
    expected_center = [width_mm / 2.0, height_mm / 2.0]
    if manifest.get("frame_center_mm") != expected_center:
        raise HeadlessExportError("The manifest artwork frame centre is invalid.")

    layer_bounds = _layer_bounds(layers, width_mm, height_mm)
    common_headers = {}
    program_verification = {}
    gcode_bounds = {}
    for index, (label, channel, path) in enumerate(
        zip(PRINT_LABELS, PRINT_CHANNELS, program_paths),
        start=1,
    ):
        gcode = path.read_text(encoding="utf-8")
        digest = _sha256(path)
        expected_digest = manifest.get("file_sha256", {}).get(channel)
        if digest != expected_digest:
            raise HeadlessExportError(
                f"{path.name} hash does not match the manifest."
            )
        if manifest.get("files", {}).get(channel) != path.name:
            raise HeadlessExportError(
                f"Manifest file mapping for {channel.upper()} is invalid."
            )
        commands = _command_lines(gcode)
        missing_units = [code for code in UNIT_COMMANDS if code not in commands]
        if missing_units:
            raise HeadlessExportError(
                f"{path.name} lacks required unit/frame commands "
                + ", ".join(missing_units)
            )
        if not commands or commands[-1] != "M2":
            raise HeadlessExportError(f"{path.name} does not end with M2.")
        if "M5" not in commands[-8:]:
            raise HeadlessExportError(
                f"{path.name} does not leave the pen clear before M2."
            )
        if any(re.search(r"(?:^|\s)Z[-+]?(?:\d|\.)", line) for line in commands):
            raise HeadlessExportError(f"{path.name} contains an unexpected Z command.")

        geometry = manifest.get("program_geometry", {}).get(channel, {})
        marks = int(geometry.get("marks", 0))
        if marks <= 0:
            raise HeadlessExportError(
                f"Manifest reports no {channel.upper()} marks."
            )
        if marks > options.max_marks + 5:
            raise HeadlessExportError(
                f"{channel.upper()} mark count {marks} exceeds the cap "
                f"{options.max_marks} plus registration crosses."
            )

        checks = manifest.get("preflight", {}).get(channel, {})
        problems = converter.preflight_problems(checks)
        if problems:
            raise HeadlessExportError(
                f"{path.name} motion preflight failed: " + "; ".join(problems)
            )
        machine_radius = float(checks.get("max_xy_radius_mm", math.inf))
        reach = float(checks.get("machine_reach_radius_mm", 0.0))
        if reach <= 0.0 or machine_radius > reach + 1e-6:
            raise HeadlessExportError(
                f"{path.name} exceeds the machine reach: "
                f"{machine_radius:.6f} > {reach:.6f} mm."
            )
        bounds = _machine_bounds(gcode)
        if bounds["max_radius_mm"] > reach + 1e-6:
            raise HeadlessExportError(
                f"{path.name} parsed coordinates exceed the reach guard."
            )
        gcode_bounds[channel] = bounds
        common_headers[channel] = _common_header(gcode)
        program_verification[channel] = {
            "label": label,
            "file": path.name,
            "bytes": path.stat().st_size,
            "sha256": digest,
            "lines": len(gcode.splitlines()),
            "units_and_frame": list(UNIT_COMMANDS),
            "complete": True,
            "mark_count": marks,
            "max_xy_radius_mm": machine_radius,
            "machine_reach_radius_mm": reach,
        }
    if len(set(common_headers.values())) != 1:
        raise HeadlessExportError(
            "The four programs do not share one frame, theta, feed, reach, "
            "compensation, and registration header contract."
        )

    set_verification = manifest.get("set_verification", {})
    if not set_verification.get("complete"):
        raise HeadlessExportError("The manifest does not mark the set complete.")
    if not set_verification.get("consistency_checked"):
        raise HeadlessExportError("The manifest did not check common set identity.")
    if not set_verification.get("motion_preflight_passed"):
        raise HeadlessExportError("The manifest reports failed motion preflight.")
    if not set_verification.get("whole_set_transaction"):
        raise HeadlessExportError(
            "The manifest does not report transactional whole-set publication."
        )

    return {
        "manifest": manifest,
        "layer_bounds": layer_bounds,
        "gcode_bounds": gcode_bounds,
        "programs": program_verification,
        "manifest_sha256": _sha256(manifest_path),
    }


def _run_once(
    module,
    app,
    options: ExportOptions,
    output_dir: Path,
    *,
    make_preview: bool,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    expected = _expected_files(output_dir, options.base_name)
    window = module.MainWindow()
    messages: list[tuple[str, str]] = []
    stack = ExitStack()
    completed = False
    try:
        for patcher in _dialog_capture(messages):
            stack.enter_context(patcher)
        window.svg_path.setText(str(options.source))
        window.gcode_dir = str(output_dir)
        window.show_tool("CMYK Photo")
        app.processEvents()
        tab = _cmyk_tab(window)
        if options.ink_profile is not None:
            window.load_ink_profile(str(options.ink_profile))
        _configure_tab(tab, options)
        tab.build_svg()
        app.processEvents()
        issues = {
            stage.key: tab.validate_stage(stage.key)
            for stage in tab._stage_navigator.stages
        }

        tab._next_export_base_path = str(
            output_dir / f"{options.base_name}.gcode"
        )
        tab.save_all()
        _wait_for_set(
            app,
            tab,
            window,
            expected,
            messages,
            options.timeout_seconds,
        )
        process_layers = {
            channel: list(tab._layers.get(channel, ()))
            for channel in PRINT_CHANNELS
        }
        verification = verify_program_set(
            output_dir,
            options.base_name,
            options.source,
            process_layers,
            options,
        )
        verification["workflow_validation"] = issues
        verification["application_status"] = window.status.text()
        verification["tab_status"] = tab.status.text()
        verification["dialog_messages"] = messages

        coherent_layers = None
        if make_preview:
            if not tab.apply_workflow_preset("recommended"):
                raise HeadlessExportError(
                    "Could not build the coherent-flow comparison preview."
                )
            tab.pen_width.setValue(float(options.pen_width_mm))
            tab.page_w.setValue(float(options.page_mm))
            tab.page_h.setValue(float(options.page_mm))
            tab.margin.setValue(float(options.margin_mm))
            tab.scale_pct.setValue(float(options.scale_pct))
            tab.seed.setValue(int(options.seed))
            tab.registration_marks.setChecked(True)
            tab.theta_mode.set_value(str(options.theta_mode))
            for box in tab.write_boxes.values():
                box.setChecked(True)
            tab.build_svg()
            coherent_layers = {
                channel: list(tab._layers.get(channel, ()))
                for channel in PRINT_CHANNELS
            }
        completed = True
        return {
            "verification": verification,
            "process_layers": process_layers,
            "coherent_layers": coherent_layers,
            "tab": tab,
            "window": window,
            "messages": messages,
        }
    finally:
        stack.close()
        if not completed:
            _closed_window(app, window)


def _closed_window(app, window) -> None:
    if window.save_thread is not None:
        window.cancel_save()
        deadline = time.monotonic() + 5.0
        while window.save_thread is not None and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.01)
    if window.preview_thread is not None:
        window.cancel_preview()
        deadline = time.monotonic() + 5.0
        while window.preview_thread is not None and time.monotonic() < deadline:
            app.processEvents()
            time.sleep(0.01)
    window.hide()
    window.deleteLater()
    app.processEvents()


def _render_layers(
    layers,
    width_mm: float,
    height_mm: float,
    pen_width_mm: float,
    ink_colors,
    *,
    pixels: int = 1100,
):
    import numpy as np
    from PIL import Image, ImageDraw

    supersample = 2
    width = max(100, int(pixels))
    height = max(100, int(pixels))
    work = Image.new("RGB", (width * supersample, height * supersample), "white")
    values = np.asarray(work, dtype=np.float32)
    scale_x = (width * supersample) / float(width_mm)
    scale_y = (height * supersample) / float(height_mm)
    stroke = max(1, round(float(pen_width_mm) * (scale_x + scale_y) / 2.0))
    transmittances = converter.ink_transmittance_matrix(ink_colors)
    transmittance_by_ink = dict(zip(PRINT_CHANNELS, transmittances))
    for channel in PRINT_CHANNELS:
        mask = Image.new("L", work.size, 0)
        draw = ImageDraw.Draw(mask)
        for contour in layers.get(channel, ()):
            if len(contour) < 2:
                continue
            points = [
                (round(float(x) * scale_x), round(float(y) * scale_y))
                for x, y in contour
            ]
            draw.line(
                points,
                fill=255,
                width=stroke,
                joint="curve",
            )
        alpha = np.asarray(mask, dtype=np.float32) / 255.0
        for component, transmittance in enumerate(
            transmittance_by_ink[channel]
        ):
            values[..., component] *= 1.0 - alpha * (
                1.0 - float(transmittance)
            )
    values = np.clip(values + 0.5, 0, 255).astype(np.uint8)
    return Image.fromarray(values, mode="RGB").resize(
        (width, height),
        Image.Resampling.LANCZOS,
    )


def _fit_panel(image, size: int):
    from PIL import Image, ImageOps

    image = ImageOps.exif_transpose(image).convert("RGBA")
    paper = Image.new("RGBA", image.size, (255, 255, 255, 255))
    image = Image.alpha_composite(paper, image).convert("RGB")
    fitted = image.copy()
    fitted.thumbnail((size, size), Image.Resampling.LANCZOS)
    panel = Image.new("RGB", (size, size), "white")
    panel.paste(
        fitted,
        ((size - fitted.width) // 2, (size - fitted.height) // 2),
    )
    return panel


def write_comparison_preview(
    source: Path,
    reference: Path | None,
    process_layers,
    coherent_layers,
    output_path: Path,
    *,
    width_mm: float,
    height_mm: float,
    pen_width_mm: float,
    ink_colors,
) -> Path:
    """Write one compressed source/coherent/process/reference contact sheet."""
    from PIL import Image, ImageDraw, ImageFont, ImageOps

    panel_size = 570
    gap = 26
    caption_height = 38
    columns = 2
    rows = 2
    sheet_size = (
        columns * panel_size + (columns + 1) * gap,
        rows * (panel_size + caption_height) + (rows + 1) * gap,
    )
    sheet = Image.new("RGB", sheet_size, (238, 238, 235))
    source_image = Image.open(source)
    coherent_image = _render_layers(
        coherent_layers,
        width_mm,
        height_mm,
        pen_width_mm,
        ink_colors,
        pixels=panel_size,
    )
    process_image = _render_layers(
        process_layers,
        width_mm,
        height_mm,
        pen_width_mm,
        ink_colors,
        pixels=panel_size,
    )
    panels = [
        ("Source", _fit_panel(source_image, panel_size)),
        ("Coherent color flow", _fit_panel(coherent_image, panel_size)),
        ("Precision process (final)", _fit_panel(process_image, panel_size)),
    ]
    if reference is not None and reference.is_file():
        panels.append(
            (
                "Color reference",
                _fit_panel(Image.open(reference), panel_size),
            )
        )
    else:
        panels.append(("Registration", _fit_panel(process_image, panel_size)))

    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except OSError:
        font = ImageFont.load_default()
    draw = ImageDraw.Draw(sheet)
    for index, (label, panel) in enumerate(panels):
        column = index % columns
        row = index // columns
        x = gap + column * (panel_size + gap)
        y = gap + row * (panel_size + caption_height + gap)
        sheet.paste(panel, (x, y))
        draw.text((x + 6, y + panel_size + 7), label, fill=(20, 20, 20), font=font)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    for quality in (88, 82, 76, 70, 64, 58, 52, 46):
        sheet.save(
            output_path,
            format="JPEG",
            quality=quality,
            optimize=True,
            progressive=True,
            subsampling=2,
        )
        if output_path.stat().st_size <= MAX_PREVIEW_BYTES:
            return output_path
    raise HeadlessExportError(
        f"Comparison preview remains above {MAX_PREVIEW_BYTES} bytes."
    )


def _manifest_without_timestamp(manifest: dict[str, Any]) -> dict[str, Any]:
    normalized = copy.deepcopy(manifest)
    normalized.pop("created", None)
    return normalized


def run_headless_export(options: ExportOptions) -> dict[str, Any]:
    """Run, repeat-check, verify, and describe one complete CMYK export."""
    source = options.source.expanduser().resolve()
    output_dir = options.output_dir.expanduser().resolve()
    reference = (
        options.reference_image.expanduser().resolve()
        if options.reference_image is not None
        else None
    )
    profile = (
        options.ink_profile.expanduser().resolve()
        if options.ink_profile is not None
        else None
    )
    if not source.is_file():
        raise HeadlessExportError(f"Source image does not exist: {source}")
    if reference is not None and not reference.is_file():
        raise HeadlessExportError(
            f"Reference image does not exist: {reference}"
        )
    if profile is not None and not profile.is_file():
        raise HeadlessExportError(f"Ink profile does not exist: {profile}")
    if not options.base_name.strip():
        raise HeadlessExportError("A non-empty output base name is required.")
    if options.max_marks < 1:
        raise HeadlessExportError("Max marks must be positive.")
    if not 50.0 <= float(options.page_mm) <= 1000.0:
        raise HeadlessExportError("Page size must be 50..1000 mm.")
    if not 0.0 <= float(options.margin_mm) < float(options.page_mm) / 2.0:
        raise HeadlessExportError("Page margin leaves no usable area.")
    if float(options.pen_width_mm) <= 0.0:
        raise HeadlessExportError("Pen width must be positive.")
    if float(options.pitch_mm) <= 0.0:
        raise HeadlessExportError("Pitch must be positive.")
    if float(options.path_tolerance_mm) <= 0.0:
        raise HeadlessExportError("Path tolerance must be positive.")

    normalized_options = ExportOptions(
        source=source,
        output_dir=output_dir,
        base_name=options.base_name.strip(),
        recipe=options.recipe,
        page_mm=float(options.page_mm),
        margin_mm=float(options.margin_mm),
        scale_pct=float(options.scale_pct),
        pen_width_mm=float(options.pen_width_mm),
        pitch_mm=float(options.pitch_mm),
        path_tolerance_mm=float(options.path_tolerance_mm),
        max_marks=int(options.max_marks),
        seed=int(options.seed),
        theta_mode=str(options.theta_mode),
        timeout_seconds=float(options.timeout_seconds),
        determinism_repeat=bool(options.determinism_repeat),
        preview=bool(options.preview),
        reference_image=reference,
        ink_profile=profile,
    )

    app = _qt_application()
    module = _load_app_module()
    first = _run_once(
        module,
        app,
        normalized_options,
        output_dir,
        make_preview=normalized_options.preview,
    )
    window = first["window"]
    tab = first["tab"]
    try:
        verification = first["verification"]
        preview_path = None
        if normalized_options.preview:
            preview_path = output_dir / f"{normalized_options.base_name}-comparison.jpg"
            write_comparison_preview(
                normalized_options.source,
                normalized_options.reference_image,
                first["process_layers"],
                first["coherent_layers"],
                preview_path,
                width_mm=float(normalized_options.page_mm),
                height_mm=float(normalized_options.page_mm),
                pen_width_mm=float(normalized_options.pen_width_mm),
                ink_colors=tab._active_ink_colors(),
            )
            if preview_path.stat().st_size > MAX_PREVIEW_BYTES:
                raise HeadlessExportError(
                    "Comparison preview exceeds the payload limit."
                )

        determinism = {
            "checked": bool(normalized_options.determinism_repeat),
            "program_bytes_equal": None,
            "manifest_except_created_equal": None,
        }
        if normalized_options.determinism_repeat:
            with tempfile.TemporaryDirectory(
                prefix="theta-cmyk-repeat-"
            ) as repeat_dir:
                repeat = _run_once(
                    module,
                    app,
                    normalized_options,
                    Path(repeat_dir),
                    make_preview=False,
                )
                try:
                    repeat_verification = repeat["verification"]
                    first_hashes = verification["programs"]
                    second_hashes = repeat_verification["programs"]
                    deterministic_programs = all(
                        first_hashes[channel]["sha256"]
                        == second_hashes[channel]["sha256"]
                        for channel in PRINT_CHANNELS
                    )
                    deterministic_manifest = (
                        _manifest_without_timestamp(verification["manifest"])
                        == _manifest_without_timestamp(
                            repeat_verification["manifest"]
                        )
                    )
                    determinism["program_bytes_equal"] = deterministic_programs
                    determinism[
                        "manifest_except_created_equal"
                    ] = deterministic_manifest
                    if not deterministic_programs:
                        raise HeadlessExportError(
                            "A repeat run produced different program bytes."
                        )
                    if not deterministic_manifest:
                        raise HeadlessExportError(
                            "A repeat run produced a different set manifest "
                            "after excluding its creation timestamp."
                        )
                finally:
                    _closed_window(app, repeat["window"])

        report = {
            "kind": "cmyk-headless-verification",
            "status": "passed",
            "source": {
                "file": normalized_options.source.name,
                "sha256": _sha256(normalized_options.source),
            },
            "output": {
                "directory": str(output_dir),
                "base_name": normalized_options.base_name,
                "manifest_version": 8,
                "print_order": list(PRINT_LABELS),
            },
            "recipe": {
                "name": normalized_options.recipe,
                "page_mm": normalized_options.page_mm,
                "margin_mm": normalized_options.margin_mm,
                "scale_pct": normalized_options.scale_pct,
                "pen_width_mm": normalized_options.pen_width_mm,
                "requested_pitch_mm": normalized_options.pitch_mm,
                "path_tolerance_mm": normalized_options.path_tolerance_mm,
                "max_marks": normalized_options.max_marks,
                "seed": normalized_options.seed,
                "theta_mode": normalized_options.theta_mode,
            },
            "manifest_sha256": verification["manifest_sha256"],
            "programs": verification["programs"],
            "layer_bounds": verification["layer_bounds"],
            "gcode_bounds": verification["gcode_bounds"],
            "set_verification": verification["manifest"]["set_verification"],
            "workflow_validation": verification["workflow_validation"],
            "determinism": determinism,
            "comparison_preview": (
                {
                    "file": preview_path.name,
                    "bytes": preview_path.stat().st_size,
                    "sha256": _sha256(preview_path),
                }
                if preview_path is not None
                else None
            ),
            "limitations": [
                "Digital/headless export verification only.",
                "No physical four-pass paper registration or ink-density "
                "validation was performed.",
            ],
        }
        report_path = output_dir / (
            f"{normalized_options.base_name}-verification.json"
        )
        report_path.write_text(
            json.dumps(report, indent=2) + "\n",
            encoding="utf-8",
        )
        return report
    finally:
        _closed_window(app, window)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export a four-program CMYK set through the real Qt converter "
            "workflow, with deterministic and geometric verification."
        )
    )
    parser.add_argument("source", type=Path, help="Source photo")
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory for the four programs, manifest, and evidence",
    )
    parser.add_argument(
        "--base-name",
        default="",
        help="Program set base name (default: source stem + -cmyk)",
    )
    parser.add_argument(
        "--recipe",
        default="process_area",
        choices=(
            "process_area",
            "recommended",
            "edge_flow_per_ink",
            "edge_flow_shared",
            "line_screen",
        ),
    )
    parser.add_argument("--page-mm", type=float, default=250.0)
    parser.add_argument("--margin-mm", type=float, default=5.0)
    parser.add_argument("--scale-pct", type=float, default=100.0)
    parser.add_argument("--pen-width-mm", type=float, default=0.9)
    parser.add_argument("--pitch-mm", type=float, default=0.35)
    parser.add_argument("--path-tolerance-mm", type=float, default=0.05)
    parser.add_argument("--max-marks", type=int, default=800_000)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--theta-mode",
        choices=("optimized", "fixed"),
        default="optimized",
    )
    parser.add_argument("--timeout-seconds", type=float, default=900.0)
    parser.add_argument(
        "--reference-image",
        type=Path,
        default=None,
        help="Optional colour reference included in the contact sheet",
    )
    parser.add_argument(
        "--ink-profile",
        type=Path,
        default=None,
        help="Optional measured CMYK ink profile",
    )
    parser.add_argument(
        "--no-determinism-repeat",
        action="store_true",
        help="Skip the second full export and byte-for-byte comparison",
    )
    parser.add_argument(
        "--no-preview",
        action="store_true",
        help="Skip the compressed comparison contact sheet",
    )
    parser.add_argument(
        "--full-report",
        action="store_true",
        help="Print the complete verification report instead of a summary",
    )
    return parser


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    base_name = args.base_name.strip() or f"{args.source.stem}-cmyk"
    options = ExportOptions(
        source=args.source,
        output_dir=args.output_dir,
        base_name=base_name,
        recipe=args.recipe,
        page_mm=args.page_mm,
        margin_mm=args.margin_mm,
        scale_pct=args.scale_pct,
        pen_width_mm=args.pen_width_mm,
        pitch_mm=args.pitch_mm,
        path_tolerance_mm=args.path_tolerance_mm,
        max_marks=args.max_marks,
        seed=args.seed,
        theta_mode=args.theta_mode,
        timeout_seconds=args.timeout_seconds,
        determinism_repeat=not args.no_determinism_repeat,
        preview=not args.no_preview,
        reference_image=args.reference_image,
        ink_profile=args.ink_profile,
    )
    try:
        report = run_headless_export(options)
    except Exception as exc:  # noqa: BLE001 - command-line boundary
        print(f"CMYK headless export failed: {exc}", file=sys.stderr)
        return 1
    if args.full_report:
        print(json.dumps(report, indent=2))
        return 0
    summary = {
        "status": report["status"],
        "output_directory": report["output"]["directory"],
        "manifest_sha256": report["manifest_sha256"],
        "programs": {
            channel: {
                "file": record["file"],
                "marks": record["mark_count"],
                "bytes": record["bytes"],
                "sha256": record["sha256"],
                "max_xy_radius_mm": record["max_xy_radius_mm"],
            }
            for channel, record in report["programs"].items()
        },
        "transaction_complete": report["set_verification"]["complete"],
        "transactional_publication": report["set_verification"][
            "whole_set_transaction"
        ],
        "determinism": report["determinism"],
        "comparison_preview": report["comparison_preview"],
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
