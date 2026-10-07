"""Labeled CMYK calibration sheet: ladders, mixes, and their manifest.

The sheet is screened with the same primitives as the artwork screens
(``converter_core.cmyk.screen_channel``), so every printed patch exercises
the real dot geometry at the tab's current pitch, dot size, pen width, and
overdraw. Cells are labeled with their parameter values (Hershey stroke text
drawn by the black pen), so the plotted sheet is self-describing, and the
returned manifest records every patch rectangle in page millimetres for
``tools/cmyk_calibrate.py``.

The sheet always uses the halftone dot screen with solid spiral dots: the
ladders calibrate dot size, dot gain, overdraw, and ink overprint, which are
properties of the dot screens. Other screen styles keep their normal artwork
path. Ladder cells print raw tone (the per-ink weights are not applied);
the GCR ramp runs the real separation with the page's weights and gamma.
"""

from __future__ import annotations

import datetime
import math

import converter_core as converter

from ._hershey import text_polylines


SHEET_KIND = "cmyk-calibration-sheet"
SHEET_VERSION = 1

# Layout constants, millimetres.
FIDUCIAL_SIZE_MM = 6.0
FIDUCIAL_ARM_MM = 9.0
FIDUCIAL_INSET_MM = 5.0
CONTENT_INSET_MM = 11.0

HEADER_LINES = 3
HEADER_LINE_MM = 4.2
HEADER_GAP_MM = 1.0
FOOTER_LINES = 2
FOOTER_LINE_MM = 3.4
FOOTER_GAP_MM = 0.8

CAPTION_STRIP_MM = 4.6
LABEL_STRIP_MM = 4.2
ROW_GAP_MM = 1.5
CELL_GAP_MM = 1.5

HEADER_SIZE_MM = 3.2
CAPTION_SIZE_MM = 2.9
LABEL_SIZE_MM = 2.9
FOOTER_SIZE_MM = 2.5

COVERAGE_TONES = tuple(step / 10.0 for step in range(1, 11))
DOT_SCALES = (0.20, 0.40, 0.60, 0.80, 1.00, 1.20, 1.40)
OVERDRAW_STEPS = (1, 2, 3)
GCR_STEPS = (0.0, 0.25, 0.50, 0.75, 1.00)
GRAY_TONE = 0.5
MIX_SETS = (("c", "m"), ("c", "y"), ("m", "y"), ("c", "m", "y"))
SPOT_SCALE = 1.40

CAPTIONS = (
    "COVERAGE % - raw tone, one row per ink (C, M, Y, K from the top)",
    "DOT SIZE % at 50% tone (C, M, Y, K rows), then OVERDRAW 1x / 2x / 3x",
    "GCR % on a 50% gray - full separation at the page's weights and gamma",
    "MIXES at full tone, dense single-ink spots, then blank paper",
)

MIN_PAGE_HINT = (
    "The calibration sheet needs a page of about 110 x 180 mm or more; "
    "raise Width/Height (or lower Margin) in the Page group."
)


def _fmt(value):
    text = f"{float(value):.3f}"
    return text.rstrip("0").rstrip(".")


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
        self.layers = {channel: [] for channel in converter.CHANNELS}
        self.patches = []
        self.fiducials = []
        self._index = 0

    def text(self, value, x, y, size_mm, align="left"):
        for line in text_polylines(str(value), x, y, size_mm, align=align):
            if len(line) >= 2:
                self.layers["k"].append(line)

    def screen(self, channel, rect, tone, dot_scale, overdraw=None):
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
            style="halftone",
            spacing_mm=self.pitch_mm,
            dot_scale=float(dot_scale),
            angle_deg=converter.SCREEN_ANGLES_DEG[channel],
            seed=0,
            max_marks=20000,
            pen_diameter_mm=self.pen_width_mm,
            levels=4,
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
    ):
        self._index += 1
        for channel in channels:
            self.layers[channel].extend(
                self.screen(channel, rect, tones[channel], dot_scale, overdraw)
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
        self.patches.append(patch)

    def fiducial(self, cx, cy):
        self.fiducials.append({"x": round(cx, 3), "y": round(cy, 3)})
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
):
    """Return ``(layers, manifest)`` for the labeled calibration sheet.

    ``layers`` maps a channel to page-millimetre polylines in the same shape
    the tab writes to per-ink SVGs. ``manifest`` is JSON-ready and records
    the page, the settings, the four fiducials, and every patch rectangle.
    """
    import numpy as np

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
        + len(CAPTIONS) * CAPTION_STRIP_MM
        + rows * (LABEL_STRIP_MM + ROW_GAP_MM)
        + FOOTER_LINES * FOOTER_LINE_MM
        + FOOTER_GAP_MM
    )
    if width < 70.0 or height - fixed < rows * 4.5:
        raise ValueError(MIN_PAGE_HINT)
    cell_h = min(18.0, (height - fixed) / rows)

    def cell_width(count):
        cell_w = (width - CELL_GAP_MM * (count - 1)) / count
        if cell_w < 5.0:
            raise ValueError(MIN_PAGE_HINT)
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

    weight_map = _weight_map(weights)
    y = top
    date = datetime.date.today().isoformat()
    header = (
        f"CMYK CALIBRATION SHEET - {date}",
        (
            f"halftone dots | pitch {_fmt(builder.pitch_mm)} mm | "
            f"dot {int(round(builder.dot_scale * 100))}% | "
            f"pen {_fmt(builder.pen_width_mm)} mm | "
            f"overdraw {builder.overdraw}"
        ),
        (
            f"GCR {_fmt(gcr_pct)}% | gamma {_fmt(gamma)} | weights "
            "C/M/Y/K "
            + "/".join(
                f"{int(round(weight_map[channel] * 100))}"
                for channel in converter.CHANNELS
            )
            + "%"
        ),
    )
    for index, line in enumerate(header):
        builder.text(
            line,
            left,
            y + HEADER_SIZE_MM + index * HEADER_LINE_MM,
            HEADER_SIZE_MM,
        )
    y += HEADER_LINES * HEADER_LINE_MM + HEADER_GAP_MM

    def caption(text_value):
        nonlocal y
        builder.text(
            text_value, left, y + CAPTION_SIZE_MM, CAPTION_SIZE_MM
        )
        y += CAPTION_STRIP_MM

    def row(cells, cell_w):
        nonlocal y
        cell_top = y + LABEL_STRIP_MM
        for index, spec in enumerate(cells):
            x = left + index * (cell_w + CELL_GAP_MM)
            builder.text(
                spec["label"],
                x + cell_w / 2.0,
                y + LABEL_SIZE_MM,
                LABEL_SIZE_MM,
                align="center",
            )
            builder.cell(
                (x, cell_top, cell_w, cell_h),
                label=spec["label"],
                **spec["cell"],
            )
        y = cell_top + cell_h + ROW_GAP_MM

    caption(CAPTIONS[0])
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

    caption(CAPTIONS[1])
    for channel in converter.CHANNELS:
        cells = [
            {
                "label": f"{int(round(scale * 100))}",
                "cell": {
                    "block": "dots",
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
        row(cells, ladder_w)

    caption(CAPTIONS[2])
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

    caption(CAPTIONS[3])
    cells = [
        {
            "label": "+".join(channel.upper() for channel in combo),
            "cell": {
                "block": "mix",
                "channels": combo,
                "tones": {channel: 1.0 for channel in combo},
                "dot_scale": SPOT_SCALE,
            },
        }
        for combo in MIX_SETS
    ]
    cells += [
        {
            "label": channel.upper(),
            "cell": {
                "block": "spot",
                "channels": (channel,),
                "tones": {channel: 1.0},
                "dot_scale": SPOT_SCALE,
            },
        }
        for channel in converter.CHANNELS
    ]
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

    builder.text(
        "Print C, M, Y, K in order, let the ink dry, then scan or photograph "
        "the sheet flat.",
        left,
        y + FOOTER_SIZE_MM,
        FOOTER_SIZE_MM,
    )
    y += FOOTER_LINE_MM
    builder.text(
        r"Fit: python tools\cmyk_calibrate.py scan.png --manifest "
        "<sheet>-calibration.json",
        left,
        y + FOOTER_SIZE_MM,
        FOOTER_SIZE_MM,
    )

    if y + FOOTER_SIZE_MM > bottom + 1e-6:
        raise ValueError(MIN_PAGE_HINT)

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
            "style": "halftone",
            "solid_dots": builder.solid,
            "pitch_mm": round(builder.pitch_mm, 4),
            "dot_scale": round(builder.dot_scale, 4),
            "pen_width_mm": round(builder.pen_width_mm, 4),
            "overdraw": builder.overdraw,
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
