"""CMYK separation tab: one screened layer per ink pen.

RGB -> CMYK separation (with gray-component replacement) and the per-channel
screening styles live in ``converter_core/cmyk.py``; the separation
math follows the MIT-licensed ohnorobo/cmyk-splitter. The tab builds four
layer SVGs, lets the shared OpenGL preview show any combination of them
through the layer checkboxes, and asks the host to analyze/save one complete
G-code program per ink.

The G-code itself is produced by the converter's normal pipeline - including
the r-theta axis-cost solver - so each file carries the same cost-efficient
motion planning as a Convert-tab program.
"""

from __future__ import annotations

import dataclasses
import datetime
import hashlib
import json
import os
import threading
from pathlib import Path

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)

import converter_core as converter

from ._tab_common import (
    ChoiceBullets,
    GeneratorTab,
    double_spin,
    int_spin,
    scale_polylines,
    write_svg_document,
)
from .cmyk_sheet import build_sheet


TITLE = "CMYK"
ORDER = 25


def format_seconds(seconds):
    """Short h/m/s form used by the cost table."""
    seconds = max(0, int(round(float(seconds))))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h{minutes:02d}m"
    if minutes:
        return f"{minutes}m{secs:02d}s"
    return f"{secs}s"


def format_cost_summary(results):
    """One-line per-ink cost: the planner's kinematics split, or XY only."""
    parts = []
    for channel in converter.CHANNELS:
        record = results.get(channel)
        if not record:
            continue
        if record["x_count"] or record["y_count"]:
            motion = f"x{record['x_count']}/y{record['y_count']}"
        else:
            motion = "XY only"
        parts.append(
            f"{converter.CHANNEL_LABELS[channel][0]} "
            f"{motion} {format_seconds(record['seconds'])}"
        )
    return "Cost: " + ", ".join(parts) if parts else "Cost: not planned yet."


class ProgramAnalysisWorker(QObject):
    """Plan one program per ink on a worker thread via the host analyzer."""

    progress = Signal(int, str)
    finished = Signal(object)
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, host, settings, scale, entries):
        super().__init__()
        self.host = host
        self.settings = settings
        self.scale = float(scale)
        self.entries = list(entries)
        self.cancel_event = threading.Event()

    def cancel(self):
        self.cancel_event.set()

    def is_cancelled(self):
        return self.cancel_event.is_set()

    def run(self):
        try:
            results = {}
            total = max(1, len(self.entries))
            for index, (channel, svg_path) in enumerate(self.entries):
                if self.is_cancelled():
                    self.cancelled.emit()
                    return
                self.progress.emit(
                    int(100 * index / total),
                    f"Planning {converter.CHANNEL_LABELS[channel]}...",
                )
                channel_settings = dataclasses.replace(
                    self.settings,
                    row_lock_screen_angle_deg=converter.SCREEN_ANGLES_DEG[
                        channel
                    ],
                )
                data = self.host.analyze_program(
                    svg_path, channel_settings, self.is_cancelled
                )
                moves = data["moves"]
                estimate = converter.estimate_program_time(moves, self.scale)
                counts = estimate["strategy_counts"]
                lengths = estimate["strategy_mm"]
                checks = converter.analyse_gcode(data["gcode"], self.settings)
                record = {
                    "marks": len(data["contours"]),
                    "moves": len(moves),
                    "gcode": data["gcode"],
                    "lines": len(data["gcode"].splitlines()),
                    "x_count": counts.get("x_theta", 0),
                    "y_count": counts.get("y_theta", 0),
                    "x_mm": lengths.get("x_theta", 0.0),
                    "y_mm": lengths.get("y_theta", 0.0),
                    "draw_mm": estimate["draw_mm"],
                    "seconds": estimate["total_seconds"],
                    "checks": checks,
                }
                compensation = data.get("bed_compensation")
                if getattr(compensation, "row_locked", False):
                    record["compensation"] = {
                        "mode": "row_locked_projection",
                        "profile_fingerprint": (
                            compensation.full_profile_fingerprint
                        ),
                        "projected_max_correction_mm": (
                            compensation.max_correction_mm
                        ),
                        "screen_angle_deg": compensation.screen_angle_deg,
                    }
                results[channel] = record
            self.finished.emit(results)
        except converter.OperationCancelled:
            self.cancelled.emit()
        except Exception as exc:  # noqa: BLE001 - surfaced to the tab status
            self.failed.emit(str(exc))


class CmykTab(GeneratorTab):
    NAME = "cmyk"
    GROUP = "Photo-based"
    DESCRIPTION = "Split an image into four ink layers, one G-code each."
    # The tab draws its own halftone marks; the Convert-tab fill must not
    # hatch every dot outline a second time.
    SELF_SCREENED = True

    def __init__(self, host):
        super().__init__(host)
        image = self.add_group("Image")
        self.image_label = QLabel()
        self.image_label.setWordWrap(True)
        image.addRow("Artwork", self.image_label)

        options = self.add_group("Image options")
        self.auto_button = QPushButton("Auto (photo)")
        self.auto_button.setToolTip(
            "Analyze the artwork and set auto levels, brightness, contrast, "
            "saturation, GCR, and a starting gamma for a faithful photo "
            "representation. Wave screens use an exposure-preserving setup; "
            "tweak gamma for print lightness afterwards."
        )
        self.auto_button.clicked.connect(self.apply_auto_settings)
        options.addRow("Auto", self.auto_button)
        self.auto_levels = QCheckBox("Stretch tonality")
        self.auto_levels.setChecked(True)
        self.auto_levels.setToolTip(
            "Stretch the image luminance between its 1st and 99th percentiles "
            "before separation, so a low-key or hazy photo uses the full tonal "
            "range instead of screening into one flat mid-tone."
        )
        options.addRow("Auto levels", self.auto_levels)
        self.saturation = double_spin(115, 0, 200, 5, 0, " %")
        options.addRow("Saturation", self.saturation)
        self.contrast = double_spin(285, 25, 300, 5, 0, " %")
        self.contrast.setToolTip(
            "Soft S-curve contrast up to 300 %: above 200 % the curve keeps "
            "steepening instead of clipping, so colour punch keeps "
            "increasing without blown highlights."
        )
        options.addRow("Contrast", self.contrast)
        self.brightness = double_spin(170, 20, 200, 5, 0, " %")
        self.brightness.setToolTip(
            "Shadow-weighted brightness lift (a gamma curve that keeps the "
            "black and white points). Raise it when the plot reads too dark, "
            "lower it toward 100 % for the untouched tone."
        )
        options.addRow("Brightness", self.brightness)
        self.sharpen = QCheckBox("Unsharp mask")
        self.sharpen.setChecked(True)
        self.sharpen.setToolTip(
            "Restore small facial and edge detail before CMYK separation. "
            "The mask is applied to luminance only, so it sharpens structure "
            "without changing the ink balance. Turn it off for soft artwork "
            "or an already-sharp source."
        )
        options.addRow("Sharpen", self.sharpen)
        self.sharpen_amount = double_spin(70, 10, 200, 5, 0, " %")
        self.sharpen_amount.setToolTip(
            "Unsharp-mask strength. 70 % is the photo default; lower it if "
            "edges show halos, and raise it for fine features that still "
            "disappear into the screen."
        )
        options.addRow("Sharpen amount", self.sharpen_amount)
        self.sharpen_radius = double_spin(1.5, 0.2, 5.0, 0.1, 1, " mm")
        self.sharpen_radius.setToolTip(
            "Radius of the luminance blur, in final on-paper millimetres. "
            "A small radius restores fine detail; a larger radius emphasizes "
            "broader local contrast and can create visible halos."
        )
        options.addRow("Sharpen radius", self.sharpen_radius)
        self.sharpen.toggled.connect(self._update_sharpen_controls)
        self._update_sharpen_controls()
        self.gamma = double_spin(1.40, 0.2, 3.0, 0.05, 2)
        options.addRow("Ink gamma", self.gamma)
        self.gcr = double_spin(95, 0, 100, 5, 0, " %")
        options.addRow("Black (GCR)", self.gcr)
        self.resolution = int_spin(10000, 200, 100000, 50)
        self.resolution.setToolTip(
            "Longest side of the sampling image in pixels. The source is "
            "only ever downsampled, never upsampled, so values at or above "
            "the source size keep full detail; memory grows with the source "
            "size you keep."
        )
        options.addRow("Resolution px", self.resolution)
        self.weight_c = double_spin(100, 0, 150, 5, 0, " %")
        self.weight_m = double_spin(100, 0, 150, 5, 0, " %")
        self.weight_y = double_spin(100, 0, 150, 5, 0, " %")
        self.weight_k = double_spin(100, 0, 150, 5, 0, " %")
        options.addRow("Cyan weight", self.weight_c)
        options.addRow("Magenta weight", self.weight_m)
        options.addRow("Yellow weight", self.weight_y)
        options.addRow("Black weight", self.weight_k)

        screen = self.add_group("Screen")
        self.style = QComboBox()
        self.style.addItem("Halftone dots", "halftone")
        self.style.addItem("Stipple dots", "stipple")
        self.style.addItem("Line screen (tone pitch)", "lines")
        self.style.addItem("Rectilinear fill (joined rows)", "rectilinear")
        self.style.addItem("Crosshatch levels", "crosshatch")
        self.style.addItem("Wave screen - equidistant rows", "waves_even")
        self.style.addItem("Interference (gyroid)", "gyroid")
        self.style.addItem("Single line (TSP)", "tsp")
        self.style.addItem("Topographic contours", "contours")
        self.style.setToolTip(
            "Dot styles use the dot pitch and dot size; line, rectilinear, "
            "wave, gyroid, TSP and contour styles use the same pitch as "
            "their local mark spacing. Rectilinear joins consecutive rows "
            "over ink so one M3/M5 cycle covers a whole connected region. "
            "Wave screen translates one common waveform to every row, so "
            "adjacent rows remain exactly one pitch apart. Legacy variable-"
            "depth wave values are promoted to this layout when regenerated."
        )
        self.style.setCurrentIndex(self.style.findData("rectilinear"))
        screen.addRow("Style", self.style)
        pitch_row = QWidget()
        pitch_layout = QHBoxLayout(pitch_row)
        pitch_layout.setContentsMargins(0, 0, 0, 0)
        pitch_layout.setSpacing(4)
        self.pitch = double_spin(0.1, 0.1, 8.0, 0.1, 2, " mm")
        pitch_layout.addWidget(self.pitch, 1)
        self.match_pen_button = QPushButton("Match pen")
        self.match_pen_button.setToolTip(
            "Set Dot pitch so full-tone rows sit about one pen width apart "
            "at the current artwork scale (effective pitch = pitch x scale)."
        )
        self.match_pen_button.clicked.connect(self.match_pen_pitch)
        pitch_layout.addWidget(self.match_pen_button)
        self.effective_pitch_label = QLabel("")
        self.effective_pitch_label.setToolTip(
            "On-paper row spacing: Dot pitch x Artwork scale. This is the "
            "number to compare with the pen width."
        )
        pitch_layout.addWidget(self.effective_pitch_label)
        screen.addRow("Dot pitch", pitch_row)
        self.preserve_wave_pitch = QCheckBox(
            "Preserve exact row pitch (row-lock bed compensation)"
        )
        self.preserve_wave_pitch.setChecked(True)
        self.preserve_wave_pitch.setToolTip(
            "Wave screen - equidistant rows projects the full measured "
            "bed-compensation mesh onto one displacement common to every "
            "parallel row. Compatible positional correction remains active "
            "while the final row pitch stays exact. Uncheck only to apply "
            "the raw two-dimensional field and accept non-uniform rows."
        )
        screen.addRow("Spacing guard", self.preserve_wave_pitch)
        self.dot_size = double_spin(100, 20, 140, 5, 0, " %")
        screen.addRow("Dot size", self.dot_size)
        self.solid_dots = QCheckBox("Solid dots")
        self.solid_dots.setChecked(False)
        self.solid_dots.setToolTip(
            "Draw each halftone dot as a two-turn spiral so it reads as a "
            "filled dot at pen width instead of an open ring."
        )
        screen.addRow("", self.solid_dots)
        self.levels = int_spin(8, 2, 9)
        self.levels.setToolTip(
            "Crosshatch levels: 2 draws one line family, each extra level adds "
            "a family at the next tone threshold. The first four families "
            "step +45 degrees; further families spread evenly across the "
            "half turn so every direction stays distinct."
        )
        screen.addRow("Hatch levels", self.levels)
        self.overdraw = int_spin(1, 1, 3)
        self.overdraw.setToolTip(
            "Draw every mark 1-3 times with a sub-pen offset so ballpoint ink "
            "reads darker without changing the geometry."
        )
        screen.addRow("Overdraw", self.overdraw)
        # Cap 1.2 -> 6.0 mm (2026-10-13): the brush end of a Tombow Dual Brush
        # water-based pen lays 1-6 mm wide strokes depending on pressure, and the
        # model already accepts up to 8 mm downstream. The fine nib (~0.8 mm)
        # still sits inside the range.
        self.pen_width = double_spin(0.3, 0.1, 6.0, 0.05, 2, " mm")
        screen.addRow("Pen width", self.pen_width)
        # Path-fidelity budget for this tab's output: each emitted move is
        # subdivided so the bed-frame path stays within this of a straight
        # line (the rotating bed bows single moves). The main tab's Geometry
        # Tolerance does the same job but resets to 0.25 every launch, which
        # was too coarse for the halftone rows near the centre.
        self.path_tolerance = double_spin(0.15, 0.05, 1.0, 0.05, 2, " mm")
        self.path_tolerance.setToolTip(
            "Path-fidelity budget: limits both rotating-bed bow and visible "
            "facets in sine-wave rows. Lower values produce smoother waves and "
            "straighter paths at the cost of more moves. Overrides the main "
            "tab's Tolerance for CMYK output only."
        )
        screen.addRow("Path tolerance", self.path_tolerance)
        self.max_marks = int_spin(40000, 200, 200000, 500)
        screen.addRow("Max marks/ink", self.max_marks)
        self.seed = int_spin(7, 0, 999_999)
        screen.addRow("Seed (stipple)", self.seed)

        # This tab's own kinematic either/or. The main tab's bullets set the
        # Convert page; a CMYK print keeps its own choice so a precision
        # (XY-only) pass does not depend on whichever page was used before.
        kinematics = self.add_group("Kinematics")
        self.theta_mode = ChoiceBullets(
            converter.THETA_MODE_CHOICES,
            "optimized",
            converter.FIELD_TOOLTIPS.get("theta_mode", ""),
        )
        kinematics.addRow("Bed motion", self.theta_mode)
        self.center_hold = double_spin(60.0, 0.0, 200.0, 1.0, 0, " mm")
        self.center_hold.setToolTip(
            converter.FIELD_TOOLTIPS.get("theta_center_hold_diameter_mm", "")
        )
        kinematics.addRow("Center hold", self.center_hold)
        kinematics_hint = QLabel(
            "Xθ/Yθ rotates the bed per segment (fast; every bed-angle error "
            "prints). XY only parks the bed and draws with the gantry "
            "(slower; the bed cannot add error) - use it for precision "
            "prints. Applies to the four ink programs and the calibration "
            "sheet. Center hold parks the bed inside that diameter, where the "
            "same paper move would otherwise demand a huge bed rotation and "
            "fine rows can wobble."
        )
        kinematics_hint.setWordWrap(True)
        kinematics_hint.setStyleSheet("color: #475569;")
        kinematics.addRow("", kinematics_hint)

        alignment = self.add_group("Pen alignment")
        self.offset_spins = {}
        for channel in converter.CHANNELS:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)
            x_spin = double_spin(0.0, -20.0, 20.0, 0.01, 2, " mm")
            y_spin = double_spin(0.0, -20.0, 20.0, 0.01, 2, " mm")
            x_spin.setToolTip(
                "X correction for this pen, in paper millimetres. Positive "
                "moves this ink toward +X; use the measured-alignment helper "
                "to convert a measured displacement."
            )
            y_spin.setToolTip(
                "Y correction for this pen, in paper millimetres. Positive "
                "moves this ink toward +Y."
            )
            row_layout.addWidget(QLabel("X"))
            row_layout.addWidget(x_spin)
            row_layout.addWidget(QLabel("Y"))
            row_layout.addWidget(y_spin)
            row_layout.addStretch(1)
            alignment.addRow(
                f"{converter.CHANNEL_LABELS[channel][0]} offset", row
            )
            self.offset_spins[channel] = (x_spin, y_spin)

        measured_hint = QLabel(
            "Measured cross positions from cmyk-pen-alignment.gcode, "
            "relative to cyan (positive = landed toward +X/+Y)."
        )
        measured_hint.setWordWrap(True)
        measured_hint.setStyleSheet("color: #475569;")
        alignment.addRow("", measured_hint)
        self.measured_spins = {}
        for channel in converter.CHANNELS:
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)
            x_spin = double_spin(0.0, -20.0, 20.0, 0.01, 2, " mm")
            y_spin = double_spin(0.0, -20.0, 20.0, 0.01, 2, " mm")
            row_layout.addWidget(QLabel("X"))
            row_layout.addWidget(x_spin)
            row_layout.addWidget(QLabel("Y"))
            row_layout.addWidget(y_spin)
            row_layout.addStretch(1)
            alignment.addRow(
                f"{converter.CHANNEL_LABELS[channel][0]} measured", row
            )
            self.measured_spins[channel] = (x_spin, y_spin)
        self.use_measured_button = QPushButton("Use measured offsets")
        self.use_measured_button.setToolTip(
            "Set each ink's correction to the opposite of its measured "
            "displacement from cyan. Cyan is the reference and stays at 0,0."
        )
        self.use_measured_button.clicked.connect(self._apply_measured_offsets)
        alignment.addRow("", self.use_measured_button)
        offset_hint = QLabel(
            "Offsets apply to the artwork programs and the preview. The "
            "calibration sheet keeps its geometric layout so the scan "
            "manifest stays valid."
        )
        offset_hint.setWordWrap(True)
        offset_hint.setStyleSheet("color: #475569;")
        alignment.addRow("", offset_hint)

        layers = self.add_group("Layers")
        self.preview_boxes = {}
        preview_row = QWidget()
        preview_layout = QHBoxLayout(preview_row)
        preview_layout.setContentsMargins(0, 0, 0, 0)
        for channel in converter.CHANNELS:
            box = QCheckBox(converter.CHANNEL_LABELS[channel][0])
            box.setChecked(True)
            box.setToolTip(f"Show {converter.CHANNEL_LABELS[channel]} in the preview")
            box.toggled.connect(self._on_preview_layer_toggled)
            self.preview_boxes[channel] = box
            preview_layout.addWidget(box)
        layers.addRow("Preview", preview_row)
        self.write_boxes = {}
        write_row = QWidget()
        write_layout = QHBoxLayout(write_row)
        write_layout.setContentsMargins(0, 0, 0, 0)
        for channel in converter.CHANNELS:
            box = QCheckBox(converter.CHANNEL_LABELS[channel][0])
            box.setChecked(True)
            box.setToolTip(f"Write {converter.CHANNEL_LABELS[channel]} G-code")
            self.write_boxes[channel] = box
            write_layout.addWidget(box)
        layers.addRow("Write files", write_row)

        calibration = self.add_group("Calibration")
        self.calibration_mode = QCheckBox(
            "Test sheet (tune against a real print)"
        )
        self.calibration_mode.setToolTip(
            "Build a calibration sheet instead of the artwork: "
            "per-ink coverage and overdraw ladders, a dot-size, line-pitch, "
            "or hatch-level ladder for the chosen sheet screen, a GCR ramp, "
            "dense full-tone mixes (pairs, triple, quad) and single-ink "
            "spots, blank paper, and four corner fiducials. The sheet prints "
            "only a two-line "
            "identification header; the cell values live in the calibration "
            "manifest, which Save writes for tools\\cmyk_calibrate.py."
        )
        calibration.addRow("Test sheet", self.calibration_mode)
        self.calibration_screen = QComboBox()
        self.calibration_screen.addItem("Match the Screen style", "match")
        self.calibration_screen.addItem(
            "Line screen (straight strokes)", "lines"
        )
        self.calibration_screen.addItem(
            "Rectilinear fill (joined rows)", "rectilinear"
        )
        self.calibration_screen.addItem("Crosshatch levels", "crosshatch")
        self.calibration_screen.addItem("Halftone dots", "halftone")
        self.calibration_screen.setToolTip(
            "Marks used by the calibration sheet. Matching your art's Screen "
            "style makes the ladders calibrate exactly what you print: dot "
            "size for halftone, line pitch for the line screen, hatch levels "
            "for crosshatch."
        )
        calibration.addRow("Sheet screen", self.calibration_screen)
        self.calibration_hint = QLabel(
            "Sheet mode uses the current pitch, dot size, pen width, "
            "overdraw, GCR, gamma, and weights; the sheet screen follows "
            "your Screen style by default. Only the page/screen header is "
            "printed; raise the pitch for a faster calibration plot."
        )
        self.calibration_hint.setWordWrap(True)
        self.calibration_hint.setStyleSheet("color: #475569;")
        calibration.addRow("", self.calibration_hint)

        page = self.add_group("Page")
        self.page_w = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Width", self.page_w)
        self.page_h = double_spin(200, 50, 1000, 10, 0, " mm")
        page.addRow("Height", self.page_h)
        self.margin = double_spin(6, 0, 50, 1, 0, " mm")
        page.addRow("Margin", self.margin)
        self.scale_pct = double_spin(280, 10, 1000, 5, 0, " %")
        self.scale_pct.setToolTip(
            "Scales the screened result about the page centre. The effective "
            "line pitch scales with it, so 200 % doubles the spacing between "
            "rows - halve Dot pitch to keep the same density."
        )
        page.addRow("Artwork scale", self.scale_pct)
        # Live effective-pitch readout: Dot pitch x Artwork scale is what lands
        # on paper, and it is the number that should sit next to the pen width.
        self.pitch.valueChanged.connect(self._update_effective_pitch)
        self.scale_pct.valueChanged.connect(self._update_effective_pitch)
        self.pen_width.valueChanged.connect(self._update_effective_pitch)
        self._update_effective_pitch()
        self.registration_marks = QCheckBox("Corner crosses (all inks)")
        self.registration_marks.setToolTip(
            "Draw four small crosses in the page margin, one set per ink "
            "layer, so the four passes can be checked for alignment. Keep "
            "the sheet still between passes."
        )
        page.addRow("Registration", self.registration_marks)

        actions = self.add_group("G-code (4 files)")
        self.save_button = QPushButton("Save 4 G-code files...")
        self.save_button.clicked.connect(self.save_all)
        actions.addRow("", self.save_button)
        self.cancel_button = QPushButton("Cancel planning")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_analysis)
        actions.addRow("", self.cancel_button)
        self.cost_label = QLabel(
            "Preview plans the four ink programs in the background using the "
            "Bed motion choice above (Xθ/Yθ or XY only)."
        )
        self.cost_label.setWordWrap(True)
        self.cost_label.setStyleSheet("color: #475569;")
        actions.addRow("", self.cost_label)
        self.pass_summary = QLabel()
        self.pass_summary.setWordWrap(True)
        self.pass_summary.setStyleSheet("color: #334155;")
        actions.addRow("Pass summary", self.pass_summary)
        self.theta_mode.changed.connect(
            lambda _value: self.cost_label.setText(
                "Bed motion changed; the next Preview or Save re-plans the "
                "four inks."
            )
        )

        self._layers = {}
        self._layer_files = {}
        self._preview_visible = []
        self._layers_key = None
        self._layers_manifest = None
        self._analysis = None
        self._analysis_key = None
        self._thread = None
        self._worker = None
        self._pending_save = False
        for channel in converter.CHANNELS:
            for spin in self.offset_spins[channel]:
                spin.valueChanged.connect(lambda *_: self._refresh_pass_summary())
        for spin in (self.center_hold, self.page_w, self.page_h, self.margin):
            spin.valueChanged.connect(lambda *_: self._refresh_pass_summary())
        self.registration_marks.toggled.connect(
            lambda *_: self._refresh_pass_summary()
        )
        self.style.currentIndexChanged.connect(
            self._update_wave_spacing_guard
        )
        self.preserve_wave_pitch.toggled.connect(
            self._update_wave_spacing_guard
        )
        self.calibration_mode.toggled.connect(
            self._update_wave_spacing_guard
        )
        self.theta_mode.changed.connect(lambda *_: self._refresh_pass_summary())
        self._update_wave_spacing_guard()
        self._refresh_pass_summary()
        self.finish_controls()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_artwork()

    def _refresh_artwork(self):
        path = ""
        if self.host is not None and hasattr(self.host, "artwork_path"):
            path = self.host.artwork_path()
        self._artwork = path
        self.image_label.setText(
            os.path.basename(path)
            if path
            else "(use Browse in the Artwork row above)"
        )

    def _weights(self):
        return {
            "c": self.weight_c.value() / 100.0,
            "m": self.weight_m.value() / 100.0,
            "y": self.weight_y.value() / 100.0,
            "k": self.weight_k.value() / 100.0,
        }

    def _pen_offsets(self):
        """Per-ink X/Y corrections in paper millimetres."""
        return {
            channel: (
                float(self.offset_spins[channel][0].value()),
                float(self.offset_spins[channel][1].value()),
            )
            for channel in converter.CHANNELS
        }

    def _measured_offsets(self):
        """Measured cross displacement relative to cyan, in millimetres."""
        return {
            channel: (
                float(self.measured_spins[channel][0].value()),
                float(self.measured_spins[channel][1].value()),
            )
            for channel in converter.CHANNELS
        }

    def _apply_measured_offsets(self):
        """Convert measured displacement into the opposite correction."""
        for channel in converter.CHANNELS:
            dx, dy = self._measured_offsets()[channel]
            if channel == converter.CHANNELS[0]:
                dx = dy = 0.0
            self.offset_spins[channel][0].setValue(-dx)
            self.offset_spins[channel][1].setValue(-dy)
        self._refresh_pass_summary()

    def _translate_marks(self, marks, dx, dy):
        if not dx and not dy:
            return marks
        return [
            [(x + dx, y + dy) for x, y in line]
            for line in marks
        ]

    def apply_auto_settings(self, _checked=False):
        """Fit the Image-options controls to the loaded photo."""
        self._refresh_artwork()
        if not self._artwork:
            self.report_error("Import an image with the Artwork row above first.")
            return
        try:
            values = converter.auto_photo_settings(
                self._artwork,
                pen_width_mm=self.pen_width.value(),
                effective_pitch_mm=(
                    self.pitch.value() * self.scale_pct.value() / 100.0
                ),
                style=self.style.currentData(),
                dot_pitch_mm=self.pitch.value(),
            )
        except Exception as exc:  # noqa: BLE001 - user-facing setup error
            self.report_error(f"Auto settings failed: {exc}")
            return
        self.auto_levels.setChecked(bool(values["auto_levels"]))
        self.saturation.setValue(values["saturation"])
        self.contrast.setValue(values["contrast"])
        self.brightness.setValue(values["brightness"])
        self.gamma.setValue(values["gamma"])
        self.gcr.setValue(values["gcr"])
        if "dot_pitch_mm" in values:
            self.pitch.setValue(values["dot_pitch_mm"])
        if "sharpen" in values:
            self.sharpen.setChecked(bool(values["sharpen"]))
            self.sharpen_amount.setValue(values["sharpen_pct"])
            self.sharpen_radius.setValue(values["sharpen_radius_mm"])
        message = (
            f"Auto: brightness {values['brightness']} %, contrast "
            f"{values['contrast']} %, saturation {values['saturation']} %, "
            f"GCR {values['gcr']} %, gamma {values['gamma']:.2f}"
            + (
                f", sharpen {values['sharpen_pct']:.0f} % at "
                f"{values['sharpen_radius_mm']:.1f} mm"
                if "sharpen_pct" in values
                else ""
            )
            + (
                f"; Dot pitch set to {self.pitch.value():.2f} mm"
                if "dot_pitch_mm" in values
                else f"; Dot pitch left at {self.pitch.value():.2f} mm"
            )
            + f" (Match pen would suggest "
            f"{self.pen_pitch_mm():.2f} mm for the {self.pen_width.value():.2f} "
            f"mm pen at {self.scale_pct.value():.0f} % scale) - tweak gamma "
            "for print lightness, then press Preview."
        )
        self.status.setText(message)
        if self.host is not None:
            self.host.generator_status(message)

    def pen_pitch_mm(self):
        """Dot pitch that puts full-tone rows one pen width apart on paper."""
        scale = max(0.01, self.scale_pct.value() / 100.0)
        return max(0.1, min(8.0, self.pen_width.value() / scale))

    def _update_effective_pitch(self, *_args):
        """Show the on-paper row spacing next to the Dot pitch field."""
        effective = self.pitch.value() * self.scale_pct.value() / 100.0
        pen = self.pen_width.value()
        if pen > 0.0:
            ratio = effective / pen
            relation = (
                "touching" if ratio < 1.05 else
                "slight gap" if ratio < 1.6 else
                "separated rows" if ratio < 2.6 else
                "wide gaps"
            )
            text = "= %.2f mm on paper (%s)" % (effective, relation)
        else:
            text = "= %.2f mm on paper" % effective
        self.effective_pitch_label.setText(text)

    def _update_sharpen_controls(self, *_args):
        """Enable the mask settings only while sharpening is selected."""
        enabled = self.sharpen.isChecked()
        self.sharpen_amount.setEnabled(enabled)
        self.sharpen_radius.setEnabled(enabled)

    def match_pen_pitch(self, _checked=False):
        """Set Dot pitch to one pen width at the current artwork scale."""
        self.pitch.setValue(self.pen_pitch_mm())
        self.status.setText(
            f"Dot pitch {self.pitch.value():.2f} mm matches the "
            f"{self.pen_width.value():.2f} mm pen at "
            f"{self.scale_pct.value():.0f} % artwork scale."
        )

    def _registration_crosses(self):
        """Four small crosses every ink draws, for four-pass alignment."""
        width = self.page_w.value()
        height = self.page_h.value()
        margin = self.margin.value()
        inset = max(2.0, min(margin, 8.0) / 2.0)
        half = max(0.5, min(2.5, inset - 0.4))
        crosses = []
        for cx, cy in (
            (inset, inset),
            (width - inset, inset),
            (inset, height - inset),
            (width - inset, height - inset),
        ):
            crosses.append([(cx - half, cy), (cx + half, cy)])
            crosses.append([(cx, cy - half), (cx, cy + half)])
        return crosses

    def apply_tab_settings(self, settings):
        """Overrides the host applies to this tab's preview and programs.

        Pen width drives the ink-simulation stroke width and the tone math;
        Path tolerance drives the polar subdivision. The shared page frame
        makes every ink layer (and the preview) recenter on the page centre
        rather than on its own ink coverage, so the four passes overlay at
        any Artwork scale. The host calls this from settings_for_source, so
        preview, analysis and saved files agree.
        """
        scale = float(settings.scale)
        settings = dataclasses.replace(
            settings,
            tolerance=self.path_tolerance.value(),
            pen_diameter_mm=self.pen_width.value(),
            theta_mode=self.theta_mode.value(),
            theta_center_hold_diameter_mm=self.center_hold.value(),
            frame_center_mm=(
                self.page_w.value() / 2.0 * scale,
                self.page_h.value() / 2.0 * scale,
            ),
        )
        settings = dataclasses.replace(
            settings,
            row_locked_compensation=self._wave_spacing_guard_active(),
        )
        return settings

    def _effective_settings(self):
        """Host settings with this tab's overrides applied."""
        settings = (
            self.host.settings_for_source(self)
            if self.host is not None and hasattr(self.host, "settings_for_source")
            else converter.Settings()
        )
        return self.apply_tab_settings(settings)

    def _control_key(self):
        settings_key = ""
        if self.host is not None and hasattr(self.host, "settings_for_source"):
            settings_key = repr(self._effective_settings())
        return (
            getattr(self, "_artwork", ""),
            self.page_w.value(),
            self.page_h.value(),
            self.margin.value(),
            self.scale_pct.value(),
            self.registration_marks.isChecked(),
            self.auto_levels.isChecked(),
            self.saturation.value(),
            self.contrast.value(),
            self.brightness.value(),
            self.sharpen.isChecked(),
            self.sharpen_amount.value(),
            self.sharpen_radius.value(),
            self.gamma.value(),
            self.gcr.value(),
            self.resolution.value(),
            tuple(self._weights().items()),
            self.style.currentData(),
            self.pitch.value(),
            self._wave_spacing_guard_active(),
            self.dot_size.value(),
            self.solid_dots.isChecked(),
            self.theta_mode.value(),
            self.center_hold.value(),
            tuple(
                (channel,) + self._pen_offsets()[channel]
                for channel in converter.CHANNELS
            ),
            self.pen_width.value(),
            self.path_tolerance.value(),
            self.levels.value(),
            self.overdraw.value(),
            self.max_marks.value(),
            self.seed.value(),
            tuple(
                channel
                for channel in converter.CHANNELS
                if self.write_boxes[channel].isChecked()
            ),
            self.calibration_mode.isChecked(),
            self.calibration_screen.currentData(),
            settings_key,
        )

    def _bed_motion_label(self):
        value = self.theta_mode.value()
        for label, choice in converter.THETA_MODE_CHOICES:
            if choice == value:
                return label
        return str(value)

    def _preflight_errors(self, results):
        problems = []
        for channel, record in results.items():
            checks = record.get("checks")
            if not checks:
                continue
            for problem in converter.preflight_problems(checks):
                problems.append(
                    f"{converter.CHANNEL_LABELS[channel][0]}: {problem}"
                )
        return problems

    def _preflight_warnings(self, results):
        warnings = []
        for channel, record in results.items():
            checks = record.get("checks")
            if not checks:
                continue
            if checks.get("over_tolerance"):
                warnings.append(
                    "%s: %d moves exceed %.3f mm tolerance"
                    % (
                        converter.CHANNEL_LABELS[channel][0],
                        checks["over_tolerance"],
                        checks["tolerance"],
                    )
                )
        return warnings

    def _wave_spacing_guard_active(self):
        """Whether to project compensation onto the Wave row lattice."""
        return (
            not self.calibration_mode.isChecked()
            and self.style.currentData() == "waves_even"
            and self.preserve_wave_pitch.isChecked()
        )

    def _update_wave_spacing_guard(self, _value=None):
        """Keep the guard meaningful for the selected screen style."""
        wave_selected = (
            not self.calibration_mode.isChecked()
            and self.style.currentData() == "waves_even"
        )
        self.preserve_wave_pitch.setEnabled(wave_selected)
        if hasattr(self, "pass_summary"):
            self._refresh_pass_summary()

    def _summary_text(self, results=None):
        offsets = self._pen_offsets()
        offset_parts = [
            "%s %+.2f/%+.2f"
            % (converter.CHANNEL_LABELS[channel][0], offsets[channel][0], offsets[channel][1])
            for channel in converter.CHANNELS
            if offsets[channel][0] or offsets[channel][1]
        ]
        parts = [
            f"page {self.page_w.value():g}x{self.page_h.value():g} mm",
            "frame %.1f,%.1f"
            % (self.page_w.value() / 2.0, self.page_h.value() / 2.0),
            "bed motion %s" % self._bed_motion_label(),
            "center hold %g mm diameter" % self.center_hold.value(),
            "row lock %s"
            % (
                "active"
                if self._wave_spacing_guard_active()
                else (
                    "OFF - raw compensation may alter pitch"
                    if (
                        not self.calibration_mode.isChecked()
                        and self.style.currentData() == "waves_even"
                    )
                    else "not applicable"
                )
            ),
            "crosses %s" % ("on" if self.registration_marks.isChecked() else "off"),
            "pen offsets %s" % (", ".join(offset_parts) if offset_parts else "none"),
        ]
        if results is not None:
            errors = self._preflight_errors(results)
            warnings = self._preflight_warnings(results)
            if errors:
                parts.append("preflight BLOCKED: " + "; ".join(errors))
            elif warnings:
                parts.append("preflight warning: " + "; ".join(warnings))
            else:
                parts.append("preflight OK")
        return " | ".join(parts)

    def _refresh_pass_summary(self):
        self.pass_summary.setText(self._summary_text())

    def _preview_channels(self):
        return [
            channel
            for channel in converter.CHANNELS
            if self.preview_boxes[channel].isChecked()
        ]

    def _write_channels(self):
        return [
            channel
            for channel in converter.CHANNELS
            if self.write_boxes[channel].isChecked()
        ]

    def _ensure_layers(self):
        self._refresh_artwork()
        key = self._control_key()
        if self._layers_key == key and self._layers:
            return
        if self.calibration_mode.isChecked():
            layers, files, manifest = self._build_calibration_layers()
        else:
            layers, files, manifest = self._build_artwork_layers()
        self._layers = layers
        self._layer_files = files
        self._layers_manifest = manifest
        self._layers_key = key

    def _build_artwork_layers(self):
        path = self._artwork
        if not path:
            raise ValueError("Import an image with the Artwork row above first.")
        factor = self.scale_pct.value() / 100.0
        tones, geometry = converter.prepare_image_tones(
            path,
            self.page_w.value(),
            self.page_h.value(),
            margin_mm=self.margin.value(),
            brightness=self.brightness.value(),
            resolution_px=self.resolution.value(),
            saturation=self.saturation.value() / 100.0,
            contrast=self.contrast.value() / 100.0,
            gcr=self.gcr.value() / 100.0,
            weights=self._weights(),
            gamma=self.gamma.value(),
            auto_levels=self.auto_levels.isChecked(),
            sharpen_pct=(
                self.sharpen_amount.value()
                if self.sharpen.isChecked()
                else 0.0
            ),
            sharpen_radius_mm=self.sharpen_radius.value() / factor,
        )
        width = self.page_w.value()
        height = self.page_h.value()
        stroke = self.pen_width.value()
        style = self.style.currentData()
        layers = {}
        files = {}
        for index, channel in enumerate(converter.CHANNELS):
            marks = converter.screen_channel(
                tones[channel],
                geometry,
                style=style,
                spacing_mm=self.pitch.value(),
                dot_scale=self.dot_size.value() / 100.0,
                angle_deg=converter.SCREEN_ANGLES_DEG[channel],
                seed=self.seed.value() + index,
                max_marks=self.max_marks.value(),
                pen_diameter_mm=self.pen_width.value(),
                levels=self.levels.value(),
                overdraw=self.overdraw.value(),
                solid=self.solid_dots.isChecked(),
                path_tolerance_mm=self.path_tolerance.value() / factor,
                depth_tone=tones.get("depth"),
                row_clearance_mm=(
                    (self.pen_width.value() + converter.WAVE_MIN_EDGE_GAP_MM)
                    / factor
                ),
            )
            # Generator pages are plotted 1:1, so the tab's Artwork scale is
            # applied to the screened marks about the page centre here.
            marks = scale_polylines(marks, factor, width, height)
            if self.registration_marks.isChecked():
                marks = list(marks) + self._registration_crosses()
            # Absolute paper-space corrections for this pen. Applied after
            # scaling so an offset is not multiplied by Artwork scale, and to
            # the registration crosses as well, so a corrected pen brings its
            # crosses onto the reference.
            dx, dy = self._pen_offsets()[channel]
            marks = self._translate_marks(marks, dx, dy)
            layers[channel] = marks
            document = converter.svg_document(
                {channel: marks}, width, height, stroke, order=[channel]
            )
            files[channel] = str(
                write_svg_document(f"cmyk-{channel}", document)
            )
        return layers, files, None

    def _build_calibration_layers(self):
        width = self.page_w.value()
        height = self.page_h.value()
        screen = self.calibration_screen.currentData()
        if screen == "match":
            style = self.style.currentData()
            screen = (
                style
                if style in ("lines", "rectilinear", "crosshatch")
                else "halftone"
            )
        layers, manifest = build_sheet(
            width,
            height,
            margin_mm=self.margin.value(),
            pitch_mm=self.pitch.value(),
            dot_scale=self.dot_size.value() / 100.0,
            pen_width_mm=self.pen_width.value(),
            solid=self.solid_dots.isChecked(),
            gcr_pct=self.gcr.value(),
            weights=self._weights(),
            gamma=self.gamma.value(),
            overdraw=self.overdraw.value(),
            screen=screen,
            levels=self.levels.value(),
        )
        stroke = self.pen_width.value()
        files = {}
        for channel in converter.CHANNELS:
            document = converter.svg_document(
                {channel: layers[channel]}, width, height, stroke,
                order=[channel],
            )
            files[channel] = str(
                write_svg_document(f"cmyk-calibration-{channel}", document)
            )
        return layers, files, manifest

    def build_svg(self):
        self._ensure_layers()
        visible = self._preview_channels()
        self._preview_visible = list(visible)
        QGuiApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
        try:
            document = converter.svg_document(
                {
                    channel: self._layers[channel]
                    for channel in converter.CHANNELS
                },
                self.page_w.value(),
                self.page_h.value(),
                self.pen_width.value(),
                order=list(converter.CHANNELS),
            )
            path = str(write_svg_document(f"{self.NAME}-preview", document))
        finally:
            QGuiApplication.restoreOverrideCursor()
        counts = (
            ", ".join(
                f"{converter.CHANNEL_LABELS[channel]} "
                f"{len(self._layers[channel])}"
                for channel in visible
            )
            if visible
            else "all inks hidden"
        )
        if self.calibration_mode.isChecked():
            self.status.setText(f"Calibration sheet: {counts} marks.")
        else:
            self.status.setText(f"Screened marks: {counts}.")
        if self.host is not None:
            self.host.generator_status(f"CMYK screened: {counts}.")
        return path

    def preview_layers(self):
        """Ordered ``(ink, svg_path)`` pairs for the shared colour preview.

        Called from the preview thread after ``build_svg()`` cached the layers
        on the GUI thread, so this only reads cached state. Every layer is
        returned - including unchecked ones - so the preview checkboxes can
        filter the loaded layers live via ``preview_visible_inks()`` without
        re-screening or re-planning.
        """
        return [
            (channel, self._layer_files[channel])
            for channel in converter.CHANNELS
            if channel in self._layer_files
        ]

    def preview_visible_inks(self):
        """Ink keys the Preview checkboxes currently show."""
        return self._preview_channels()

    def _on_preview_layer_toggled(self, _checked=False):
        """Apply a Preview checkbox to the shared preview immediately."""
        notify = getattr(self.host, "update_preview_visibility", None)
        if callable(notify):
            notify()

    def on_preview_finished(self):
        """Keep the fast preview responsive and defer exact G-code planning.

        The four exact per-ink programs can be expensive on dense screens and
        are only required when the operator saves. Starting them automatically
        made a completed preview look permanently busy, so Save starts and
        owns that work instead.
        """
        message = (
            "Preview ready. Exact four-ink programs will be planned when you "
            "save."
        )
        self.cost_label.setText(message)
        self.status.setText(message)
        if self.host is not None and hasattr(self.host, "generator_status"):
            self.host.generator_status(message)

    def start_analysis(self):
        if self._thread is not None:
            return
        if self._analysis is not None and self._analysis_key == self._control_key():
            return
        if getattr(self.host, "preview_thread", None) is not None:
            self.report_error("Finish or cancel the running preview before planning.")
            return
        try:
            self._ensure_layers()
        except Exception as exc:  # noqa: BLE001 - user-facing setup error
            self.report_error(str(exc))
            return
        channels = self._write_channels()
        if not channels:
            self.report_error("Tick at least one ink to write.")
            return
        if self.host is None or not hasattr(self.host, "analyze_program"):
            self.report_error("The host window does not provide program analysis.")
            return
        entries = [(channel, self._layer_files[channel]) for channel in channels]
        settings = self._effective_settings()
        scale = (
            self.host.motion_estimate_scale()
            if hasattr(self.host, "motion_estimate_scale")
            else converter.DEFAULT_MOTION_ESTIMATE_SCALE
        )
        self._analysis_key = self._control_key()
        self._worker = ProgramAnalysisWorker(self.host, settings, scale, entries)
        self._thread = QThread(self)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.cancelled.connect(self._on_cancelled)
        self._worker.finished.connect(self._thread.quit)
        self._worker.failed.connect(self._thread.quit)
        self._worker.cancelled.connect(self._thread.quit)
        self._thread.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._thread.finished.connect(self._on_thread_finished)
        self._set_planning_state(True)
        self.cost_label.setText("Planning the four ink programs...")
        self.status.setText("Planning the four ink programs...")
        self._thread.start()

    def _set_planning_state(self, running):
        self.cancel_button.setEnabled(bool(running))
        self.save_button.setEnabled(not bool(running))
        notify = getattr(self.host, "generator_planning_changed", None)
        if callable(notify):
            notify(self, bool(running))

    def cancel_analysis(self):
        if self._worker is not None:
            self._worker.cancel()
            self.cancel_button.setEnabled(False)
            self.status.setText("Cancelling planning...")

    def analysis_running(self):
        """True while the layer analysis worker is planning programs."""
        return self._thread is not None

    def _on_progress(self, percent, text):
        self.cost_label.setText(f"{text} {percent}%")
        self.status.setText(text)

    def _on_finished(self, results):
        self._analysis = results
        self.cost_label.setText(format_cost_summary(results))
        self.pass_summary.setText(self._summary_text(results))
        summary = ", ".join(
            f"{converter.CHANNEL_LABELS[channel]} {format_seconds(record['seconds'])}"
            for channel, record in results.items()
        )
        message = f"CMYK per-ink plan ready: {summary}."
        self.status.setText(message)
        if self.host is not None:
            self.host.generator_status(message)
            if hasattr(self.host, "log"):
                for channel, record in results.items():
                    motion = (
                        "x_theta %d / y_theta %d"
                        % (record["x_count"], record["y_count"])
                        if record["x_count"] or record["y_count"]
                        else "XY only (bed parked)"
                    )
                    self.host.log.append(
                        "CMYK %s: %d marks, %s, "
                        "draw %.1f mm, estimate %s."
                        % (
                            converter.CHANNEL_LABELS[channel],
                            record["marks"],
                            motion,
                            record["draw_mm"],
                            format_seconds(record["seconds"]),
                        )
                    )
                errors = self._preflight_errors(results)
                warnings = self._preflight_warnings(results)
                if errors:
                    self.host.log.append(
                        "CMYK preflight BLOCKED: " + "; ".join(errors)
                    )
                elif warnings:
                    self.host.log.append(
                        "CMYK preflight warning: " + "; ".join(warnings)
                    )
        if self._pending_save:
            self._pending_save = False
            self._write_files(results)

    def _on_failed(self, message):
        self.report_error(f"Per-ink planning failed: {message}")
        self.cost_label.setText("Per-ink planning failed.")
        self._pending_save = False

    def _on_cancelled(self):
        self.status.setText("Planning cancelled.")
        self.cost_label.setText("Planning cancelled; the last result is kept.")
        self._pending_save = False
        if self.host is not None and hasattr(self.host, "generator_status"):
            self.host.generator_status("CMYK planning cancelled.")

    def _on_thread_finished(self):
        self._thread = None
        self._worker = None
        self._set_planning_state(False)

    def shutdown_background(self):
        """Cancel and join the background planner (window close)."""
        if self._worker is not None:
            self._worker.cancel()
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(5000)

    def save_all(self, _checked=False):
        del _checked
        channels = self._write_channels()
        if not channels:
            self.report_error("Tick at least one ink to write.")
            return
        if self._analysis is None or self._analysis_key != self._control_key():
            self._pending_save = True
            self.status.setText("Planning the four ink programs before save...")
            self.start_analysis()
            return
        self._write_files(self._analysis)

    def _write_files(self, results):
        entries = [
            (converter.CHANNEL_LABELS[channel].lower(), results[channel]["gcode"])
            for channel in converter.CHANNELS
            if channel in results
        ]
        if not entries:
            self.report_error("Nothing to save; preview first.")
            return
        errors = self._preflight_errors(results)
        if errors:
            message = "CMYK preflight blocked save: " + "; ".join(errors)
            self.report_error(message)
            self.cost_label.setText(message)
            self.pass_summary.setText(self._summary_text(results))
            return
        sheet = bool(self.calibration_mode.isChecked())
        stem = ""
        if getattr(self, "_artwork", ""):
            stem = os.path.splitext(os.path.basename(self._artwork))[0]
        base = ""
        if sheet:
            base = f"{stem or 'cmyk'}-calibration.gcode"
        elif stem:
            base = f"{stem}-cmyk.gcode"
        export = getattr(self.host, "export_program_set", None)
        if not callable(export):
            self.report_error("The host window does not provide batch saving.")
            return
        written = export(entries, None, base)
        manifest_path = None
        set_manifest_path = None
        if written and sheet and self._layers_manifest is not None:
            manifest_path = self._write_manifest(written[0], entries[0][0])
        elif written:
            set_manifest_path = self._write_set_manifest(written, results)
        if written:
            names = ", ".join(os.path.basename(path) for path in written)
            extra = (
                f" Calibration manifest: {manifest_path.name}."
                if manifest_path
                else f" Set manifest: {set_manifest_path.name}."
                if set_manifest_path
                else ""
            )
            self.status.setText(
                f"Saved {len(written)} G-code files ({names}).{extra}"
            )

    def _write_manifest(self, first_path, first_label):
        """Write the calibration manifest next to the saved G-code files."""
        first = Path(first_path)
        tail = f"-{first_label}.gcode"
        stem = first.name[: -len(tail)] if first.name.endswith(tail) else first.stem
        path = first.parent / f"{stem}-calibration.json"
        path.write_text(
            json.dumps(self._layers_manifest, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def _write_set_manifest(self, written, results):
        """Record the complete print recipe and output hashes for a set."""
        first = Path(written[0])
        stem = first.stem
        for channel in converter.CHANNELS:
            suffix = "-" + converter.CHANNEL_LABELS[channel].lower()
            if stem.endswith(suffix):
                stem = stem[: -len(suffix)]
                break
        path = first.parent / f"{stem}-set.json"
        channels = [channel for channel in converter.CHANNELS if channel in results]
        settings = self._effective_settings()
        factor = self.scale_pct.value() / 100.0
        weights = self._weights()
        style = self.style.currentData()
        source_value = getattr(self, "_artwork", "")
        if not source_value:
            artwork_path = getattr(self.host, "artwork_path", None)
            if callable(artwork_path):
                source_value = artwork_path() or ""
        source_path = Path(source_value) if source_value else None
        compensation_path = settings.bed_compensation_path
        row_locked = bool(
            compensation_path and self._wave_spacing_guard_active()
        )
        profile_fingerprint = ""
        full_max_correction_mm = None
        if compensation_path:
            try:
                profile = converter.load_bed_compensation(compensation_path)
            except (OSError, ValueError):
                profile = None
            if profile is not None:
                profile_fingerprint = profile.fingerprint
                full_max_correction_mm = profile.max_correction_mm
        compensation_mode = (
            "row_locked_projection"
            if row_locked
            else "raw_unconstrained"
            if compensation_path
            else "none"
        )
        data = {
            "kind": "cmyk-print-set",
            "version": 3,
            "created": datetime.datetime.now().isoformat(timespec="seconds"),
            "source": {
                "file": source_path.name if source_path else "",
                "sha256": (
                    _sha256_file(source_path)
                    if source_path is not None and source_path.is_file()
                    else ""
                ),
            },
            "page": {
                "width_mm": self.page_w.value(),
                "height_mm": self.page_h.value(),
                "margin_mm": self.margin.value(),
            },
            "frame_center_mm": [
                self.page_w.value() / 2.0,
                self.page_h.value() / 2.0,
            ],
            "bed_motion": self._bed_motion_label(),
            "center_hold_diameter_mm": self.center_hold.value(),
            "theta_mode": settings.theta_mode,
            "bed_compensation_path": settings.bed_compensation_path,
            "bed_compensation": {
                "mode": compensation_mode,
                "profile_fingerprint": profile_fingerprint,
                "full_max_correction_mm": full_max_correction_mm,
                "screen_angles_deg": (
                    dict(converter.SCREEN_ANGLES_DEG) if row_locked else {}
                ),
                "projection": (
                    {
                        "axis": "along-row position",
                        "along_samples": converter.ROW_LOCK_ALONG_SAMPLES,
                        "across_samples": converter.ROW_LOCK_ACROSS_SAMPLES,
                    }
                    if row_locked
                    else None
                ),
                "per_channel_max_correction_mm": {
                    channel: results[channel]["compensation"][
                        "projected_max_correction_mm"
                    ]
                    for channel in converter.CHANNELS
                    if channel in results
                    and results[channel].get("compensation", {}).get("mode")
                    == "row_locked_projection"
                },
            },
            "registration_crosses": self.registration_marks.isChecked(),
            "pen_offsets_mm": {
                channel: list(self._pen_offsets()[channel])
                for channel in converter.CHANNELS
            },
            "screen": {
                "style": style,
                "style_label": self.style.currentText(),
                "dot_pitch_mm": self.pitch.value(),
                "artwork_scale_pct": self.scale_pct.value(),
                "effective_pitch_mm": self.pitch.value() * factor,
                "preserve_exact_row_pitch": (
                    self._wave_spacing_guard_active()
                ),
                "pen_width_mm": self.pen_width.value(),
                "dot_size_pct": self.dot_size.value(),
                "path_tolerance_mm": self.path_tolerance.value(),
                "minimum_centerline_clearance_mm": (
                    self.pen_width.value()
                    + converter.WAVE_MIN_EDGE_GAP_MM
                ),
                "levels": self.levels.value(),
                "overdraw": self.overdraw.value(),
                "solid_dots": self.solid_dots.isChecked(),
                "seed": self.seed.value(),
                "max_marks": self.max_marks.value(),
                "screen_angles_deg": dict(converter.SCREEN_ANGLES_DEG),
                "wave_phase_mode": {
                    "waves": "bounded_row_depth",
                    "waves_even": "identical_translated_rows",
                    "waves_zero": "shared_zero_anchored",
                }.get(style),
            },
            "ink_processing": {
                "auto_levels": self.auto_levels.isChecked(),
                "saturation_pct": self.saturation.value(),
                "contrast_pct": self.contrast.value(),
                "brightness_pct": self.brightness.value(),
                "gamma": self.gamma.value(),
                "gcr_pct": self.gcr.value(),
                "resolution_px": self.resolution.value(),
                "weights": weights,
                "sharpening": {
                    "enabled": self.sharpen.isChecked(),
                    "amount_pct": self.sharpen_amount.value(),
                    "radius_mm": self.sharpen_radius.value(),
                },
            },
            "notes": (
                "Pen offsets apply to artwork programs and the preview only; "
                "the calibration sheet keeps its geometric layout."
            ),
            "files": {
                channel: Path(path_value).name
                for channel, path_value in zip(channels, written)
            },
            "file_sha256": {
                channel: _sha256_file(Path(path_value))
                for channel, path_value in zip(channels, written)
                if Path(path_value).is_file()
            },
            "preflight": {
                channel: results[channel].get("checks")
                for channel in channels
            },
        }
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        return path


def _sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def create_tab(host):
    return CmykTab(host)
