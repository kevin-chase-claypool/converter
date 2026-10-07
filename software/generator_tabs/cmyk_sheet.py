"""Labeled CMYK calibration sheet: ladders, mixes, and their manifest.

The sheet is screened with the same primitives as the artwork screens
(``converter_core.cmyk.screen_channel``), so every printed patch exercises
the real mark geometry at the tab's current pitch, dot size, pen width, and
overdraw. The plotted sheet prints only a two-line identification header
(page size, margin, and sheet screen) - the minimum a scan needs so the
deterministic layout can be rebuilt. All cell values and rectangles live in
the returned manifest (used by ``tools/cmyk_calibrate.py`` and
``docs/testing/CMYK_CALIBRATION.md``), not on the paper.

The sheet screen follows the tab's Screen style for the dot and line screens
(halftone dots, line screen, or crosshatch levels): what you calibrate is
what you print. The second ladder row adapts to the screen - dot size, line
pitch, or hatch levels - and the dense spots use a tight mark spacing for
each screen. Ladder cells print raw tone (the per-ink weights are not
applied); the GCR ramp runs the real separation with the page's weights and
gamma.
"""

from __future__ import annotations

import datetime
import math

import converter_core as converter

from ._hershey import text_polylines


SHEET_KIND = "cmyk-calibration-sheet"
SHEET_VERSION = 6

# Layout constants, millimetres.
FIDUCIAL_SIZE_MM = 6.0
FIDUCIAL_ARM_MM = 9.0
FIDUCIAL_INSET_MM = 5.0
CONTENT_INSET_MM = 11.0

HEADER_LINES = 2
HEADER_LINE_MM = 4.2
HEADER_GAP_MM = 1.0

ROW_GAP_MM = 1.5
CELL_GAP_MM = 1.5
MAX_CELL_H_MM = 26.0

HEADER_SIZE_MM = 3.2

COVERAGE_TONES = tuple(step / 10.0 for step in range(1, 11))
DOT_SCALES = (0.20, 0.40, 0.60, 0.80, 1.00, 1.20, 1.40)
LINE_PITCHES = (0.6, 0.8, 1.0, 1.4, 1.8, 2.4, 3.0)
HATCH_LEVELS = (2, 3, 4, 5, 6, 7, 8)
OVERDRAW_STEPS = (1, 2, 3)
GCR_STEPS = (0.0, 0.25, 0.50, 0.75, 1.00)
GRAY_TONE = 0.5
HATCH_TONE = 0.8
MIX_SETS = (
    ("c", "m"),
    ("c", "y"),
    ("m", "y"),
    ("c", "m", "y"),
    ("c", "m", "y", "k"),
)
SPOT_SCALE = 1.40
SHEET_SCREENS = ("lines", "crosshatch", "halftone")


def _fmt(value):
    text = f"{float(value):.3f}"
    return text.rstrip("0").rstrip(".")


def _text_width(text, size_mm):
    """Rendered width of one Hershey line, in millimetres."""
    lines = text_polylines(str(text), 0.0, 0.0, size_mm)
    return max(
        (max(point[0] for point in line) for line in lines), default=0.0
    )


def _serpentine_square(cx, cy, size, pitch):
    """One continuous serpentine stroke that reads as a solid square."""
    half = float(size) / 2.0
    rows = max(2, int(math.ceil(float(size) / max(0.2, float(pitch)))))
    step = float(size) / rows
    points = []
    for row in range(rows):
        y = cy - half + (row + 0.5) * step
        if row % 2 == 0:
            points.extend(((cx - half, y), (cx + half, y)))
        else:
            points.extend(((cx + half, y), (cx - half, y)))
    return points


class _SheetBuilder:
    """Accumulates per-ink polylines and the patch manifest."""

    def __init__(
        self,
        page_width_mm,
        page_height_mm,
        margin_mm,
        pitch_mm,
        dot_scale,
        pen_width_mm,
        solid,
        gcr_pct,
        weights,
        gamma,
        overdraw,
        screen="halftone",
        levels=4,
        build_marks=True,
    ):
        self.page_width_mm = float(page_width_mm)
        self.page_height_mm = float(page_height_mm)
        self.margin_mm = max(0.0, float(margin_mm))
        self.pitch_mm = max(0.2, float(pitch_mm))
        self.dot_scale = max(0.05, float(dot_scale))
        self.pen_width_mm = max(0.05, float(pen_width_mm))
        self.solid = bool(solid)
        self.gcr_pct = float(gcr_pct)
        self.weights = weights
        self.gamma = float(gamma)
        self.overdraw = max(1, min(3, int(overdraw)))
        self.screen_style = str(screen)
        self.levels = max(2, min(5, int(levels)))
        self.build_marks = bool(build_marks)
        self.layers = {channel: [] for channel in converter.CHANNELS}
        self.patches = []
        self.fiducials = []
        self._index = 0

    def text(self, value, x, y, size_mm, align="left"):
        if not self.build_marks:
            return
        for line in text_polylines(str(value), x, y, size_mm, align=align):
            if len(line) >= 2:
                self.layers["k"].append(line)

    def screen(
        self,
        channel,
        rect,
        tone,
        dot_scale,
        overdraw=None,
        pitch_mm=None,
        levels=None,
    ):
        if not self.build_marks:
            return []
        import numpy as np

        left, top, width, height = (float(value) for value in rect)
        tone_array = np.full((2, 2), float(tone), dtype="float32")
        geometry = {
            "off_x": left,
            "off_y": top,
            "width_mm": width,
            "height_mm": height,
            "pixels_w": 2,
            "pixels_h": 2,
        }
        return converter.screen_channel(
            tone_array,
            geometry,
            style=self.screen_style,
            spacing_mm=self.pitch_mm if pitch_mm is None else float(pitch_mm),
            dot_scale=float(dot_scale),
            angle_deg=converter.SCREEN_ANGLES_DEG[channel],
            seed=0,
            max_marks=20000,
            pen_diameter_mm=self.pen_width_mm,
            levels=self.levels if levels is None else int(levels),
            overdraw=self.overdraw if overdraw is None else int(overdraw),
            solid=self.solid,
        )

    def cell(
        self,
        rect,
        *,
        block,
        label,
        channels,
        tones,
        dot_scale,
        overdraw=None,
        gcr=None,
        pitch_mm=None,
        levels=None,
    ):
        self._index += 1
        for channel in channels:
            self.layers[channel].extend(
                self.screen(
                    channel,
                    rect,
                    tones[channel],
                    dot_scale,
                    overdraw,
                    pitch_mm=pitch_mm,
                    levels=levels,
                )
            )
        patch = {
            "id": f"{block}-{self._index:03d}",
            "block": block,
            "label": str(label),
            "channels": list(channels),
            "tones": {
                str(channel): round(float(value), 4)
                for channel, value in tones.items()
            },
            "dot_scale": round(float(dot_scale), 4),
            "overdraw": self.overdraw if overdraw is None else int(overdraw),
            "rect_mm": [round(float(value), 3) for value in rect],
        }
        if gcr is not None:
            patch["gcr"] = round(float(gcr), 4)
        if pitch_mm is not None:
            patch["pitch_mm"] = round(float(pitch_mm), 4)
        if levels is not None:
            patch["levels"] = int(levels)
        self.patches.append(patch)

    def fiducial(self, cx, cy):
        self.fiducials.append({"x": round(cx, 3), "y": round(cy, 3)})
        if not self.build_marks:
            return
        self.layers["k"].append(
            _serpentine_square(
                cx,
                cy,
                FIDUCIAL_SIZE_MM,
                max(0.25, self.pen_width_mm * 1.1),
            )
        )
        half = FIDUCIAL_ARM_MM / 2.0
        for channel in converter.CHANNELS:
            self.layers[channel].append([(cx - half, cy), (cx + half, cy)])
            self.layers[channel].append([(cx, cy - half), (cx, cy + half)])


def _weight_map(weights):
    if isinstance(weights, dict):
        return {
            channel: float(weights.get(channel, 1.0))
            for channel in converter.CHANNELS
        }
    if weights is None:
        return dict(converter.DEFAULT_WEIGHTS)
    values = [float(value) for value in weights]
    if len(values) != len(converter.CHANNELS):
        raise ValueError("weights needs one value per CMYK channel.")
    return dict(zip(converter.CHANNELS, values))


def build_sheet(
    page_width_mm,
    page_height_mm,
    *,
    margin_mm=6.0,
    pitch_mm=1.2,
    dot_scale=0.75,
    pen_width_mm=0.3,
    solid=True,
    gcr_pct=100.0,
    weights=None,
    gamma=1.0,
    overdraw=1,
    screen="halftone",
    levels=4,
    marks=True,
):
    """Return ``(layers, manifest)`` for the labeled calibration sheet.

    ``layers`` maps a channel to page-millimetre polylines in the same shape
    the tab writes to per-ink SVGs. ``manifest`` is JSON-ready and records
    the page, the settings, the four fiducials, and every patch rectangle.
    ``marks=False`` skips all screening and returns empty layers; the
    manifest is unchanged, so a scan can be analyzed without re-screening.
    """
    import numpy as np

    screen = str(screen).strip().lower()
    if screen not in SHEET_SCREENS:
        raise ValueError(f"screen must be one of {SHEET_SCREENS}.")
    page_w = float(page_width_mm)
    page_h = float(page_height_mm)
    margin = max(0.0, float(margin_mm))
    builder = _SheetBuilder(
        page_w,
        page_h,
        margin,
        pitch_mm,
        dot_scale,
        pen_width_mm,
        solid,
        gcr_pct,
        weights,
        gamma,
        overdraw,
        screen=screen,
        levels=levels,
        build_marks=marks,
    )
    weight_map = _weight_map(weights)
    if screen == "lines":
        screen_line = (
            f"screen lines | pitch {_fmt(builder.pitch_mm)} mm"
        )
    elif screen == "crosshatch":
        screen_line = (
            f"screen crosshatch | pitch {_fmt(builder.pitch_mm)} mm | "
            f"levels {builder.levels}"
        )
    else:
        screen_line = (
            f"screen dots | pitch {_fmt(builder.pitch_mm)} mm | "
            f"dot {int(round(builder.dot_scale * 100))}%"
        )
    header = (
        f"CMYK CALIBRATION - page {_fmt(page_w)}x{_fmt(page_h)} mm | "
        f"margin {_fmt(margin)} mm",
        screen_line,
    )

    left = margin + CONTENT_INSET_MM
    right = page_w - margin - CONTENT_INSET_MM
    top = margin + CONTENT_INSET_MM
    bottom = page_h - margin - CONTENT_INSET_MM
    width = right - left
    height = bottom - top
    rows = len(converter.CHANNELS) * 2 + 2  # two ladders per ink, GCR, mixes
    fixed = (
        HEADER_LINES * HEADER_LINE_MM
        + HEADER_GAP_MM
        + rows * ROW_GAP_MM
    )
    required_text_mm = max(
        _text_width(line, HEADER_SIZE_MM) for line in header
    )
    min_content_w = required_text_mm + 1.0
    min_content_h = fixed + rows * 4.5
    if width < min_content_w or height < min_content_h:
        pad = 2.0 * (margin + CONTENT_INSET_MM)
        raise ValueError(
            "The calibration sheet needs a page of at least about "
            f"{math.ceil(min_content_w + pad)} x "
            f"{math.ceil(min_content_h + pad)} mm at this margin; raise "
            "Width/Height (or lower Margin) in the Page group."
        )
    cell_h = min(MAX_CELL_H_MM, (height - fixed) / rows)

    def cell_width(count):
        cell_w = (width - CELL_GAP_MM * (count - 1)) / count
        if cell_w < 5.0:
            raise ValueError(
                "The calibration sheet needs a wider page; raise Width (or "
                "lower Margin) in the Page group."
            )
        return cell_w

    ladder_w = cell_width(len(COVERAGE_TONES))
    gcr_w = cell_width(len(GCR_STEPS))
    mix_w = cell_width(len(MIX_SETS) + len(converter.CHANNELS) + 1)

    # Corner fiducials first; the content box stays clear of the arms.
    inset = margin + FIDUCIAL_INSET_MM
    for cx, cy in (
        (inset, inset),
        (page_w - inset, inset),
        (inset, page_h - inset),
        (page_w - inset, page_h - inset),
    ):
        builder.fiducial(cx, cy)

    y = top
    for index, line in enumerate(header):
        builder.text(
            line,
            left,
            y + HEADER_SIZE_MM + index * HEADER_LINE_MM,
            HEADER_SIZE_MM,
        )
    y += HEADER_LINES * HEADER_LINE_MM + HEADER_GAP_MM

    def row(cells, cell_w):
        nonlocal y
        for index, spec in enumerate(cells):
            x = left + index * (cell_w + CELL_GAP_MM)
            builder.cell(
                (x, y, cell_w, cell_h),
                label=spec["label"],
                **spec["cell"],
            )
        y += cell_h + ROW_GAP_MM

    for channel in converter.CHANNELS:
        cells = [
            {
                "label": f"{int(round(tone * 100))}",
                "cell": {
                    "block": "coverage",
                    "channels": (channel,),
                    "tones": {channel: tone},
                    "dot_scale": builder.dot_scale,
                },
            }
            for tone in COVERAGE_TONES
        ]
        row(cells, ladder_w)

    for channel in converter.CHANNELS:
        if screen == "lines":
            cells = [
                {
                    "label": _fmt(value),
                    "cell": {
                        "block": "steps",
                        "channels": (channel,),
                        "tones": {channel: 1.0},
                        "dot_scale": 1.0,
                        "pitch_mm": value,
                    },
                }
                for value in LINE_PITCHES
            ]
        elif screen == "crosshatch":
            cells = [
                {
                    "label": str(value),
                    "cell": {
                        "block": "steps",
                        "channels": (channel,),
                        "tones": {channel: HATCH_TONE},
                        "dot_scale": 1.0,
                        "levels": value,
                    },
                }
                for value in HATCH_LEVELS
            ]
        else:
            cells = [
                {
                    "label": f"{int(round(scale * 100))}",
                    "cell": {
                        "block": "steps",
                        "channels": (channel,),
                        "tones": {channel: GRAY_TONE},
                        "dot_scale": scale,
                    },
                }
                for scale in DOT_SCALES
            ]
        cells += [
            {
                "label": f"{step}x",
                "cell": {
                    "block": "overdraw",
                    "channels": (channel,),
                    "tones": {channel: GRAY_TONE},
                    "dot_scale": builder.dot_scale,
                    "overdraw": step,
                },
            }
            for step in OVERDRAW_STEPS
        ]
        row(cells, cell_width(len(cells)))

    gray = np.full((1, 1, 3), GRAY_TONE, dtype="float32")
    cells = []
    for value in GCR_STEPS:
        tones = converter.rgb_to_cmyk_tone(
            gray, gcr=value, weights=weights, gamma=gamma
        )
        tone_map = {
            channel: float(tones[channel][0, 0])
            for channel in converter.CHANNELS
        }
        active = tuple(
            channel
            for channel in converter.CHANNELS
            if tone_map[channel] > 0.0
        )
        cells.append(
            {
                "label": f"{int(round(value * 100))}",
                "cell": {
                    "block": "gcr",
                    "channels": active,
                    "tones": tone_map,
                    "dot_scale": builder.dot_scale,
                    "gcr": value,
                },
            }
        )
    row(cells, gcr_w)

    dense_pitch = max(0.35, builder.pen_width_mm * 1.15)

    def dense_cell(block, channels):
        cell = {
            "block": block,
            "channels": channels,
            "tones": {channel: 1.0 for channel in channels},
            "dot_scale": SPOT_SCALE if screen == "halftone" else 1.0,
        }
        if screen in ("lines", "crosshatch"):
            cell["pitch_mm"] = dense_pitch
        if screen == "crosshatch":
            cell["levels"] = 4
        return cell

    cells = [
        {
            "label": "+".join(channel.upper() for channel in combo),
            "cell": dense_cell("mix", combo),
        }
        for combo in MIX_SETS
    ]
    for channel in converter.CHANNELS:
        cells.append(
            {
                "label": channel.upper(),
                "cell": dense_cell("spot", (channel,)),
            }
        )
    cells.append(
        {
            "label": "PAPER",
            "cell": {
                "block": "paper",
                "channels": (),
                "tones": {},
                "dot_scale": builder.dot_scale,
            },
        }
    )
    row(cells, mix_w)

    if y - ROW_GAP_MM > bottom + 1e-6:
        raise ValueError(
            "The calibration sheet needs a taller page; raise Height (or "
            "lower Margin) in the Page group."
        )

    manifest = {
        "kind": SHEET_KIND,
        "version": SHEET_VERSION,
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
        "page": {
            "width_mm": round(page_w, 3),
            "height_mm": round(page_h, 3),
            "margin_mm": round(margin, 3),
        },
        "sheet_settings": {
            "style": screen,
            "solid_dots": builder.solid,
            "pitch_mm": round(builder.pitch_mm, 4),
            "dot_scale": round(builder.dot_scale, 4),
            "pen_width_mm": round(builder.pen_width_mm, 4),
            "overdraw": builder.overdraw,
            "levels": builder.levels,
            "gcr_pct": round(builder.gcr_pct, 3),
            "gamma": round(builder.gamma, 4),
            "weights": {
                channel: round(weight_map[channel], 4)
                for channel in converter.CHANNELS
            },
        },
        "fiducials_mm": builder.fiducials,
        "patches": builder.patches,
        "notes": (
            "Print the four G-code files on one sheet in C, M, Y, K order; "
            "scan the sheet flat and run tools/cmyk_calibrate.py with this "
            "manifest."
        ),
    }
    return builder.layers, manifest
