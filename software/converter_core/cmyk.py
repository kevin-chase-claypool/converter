"""CMYK separation and per-channel screening for the CMYK tool.

The separation math follows the MIT-licensed ohnorobo/cmyk-splitter
(``backend/services/cmyk_splitter.py``): RGB is converted to CMY, the gray
component becomes K (gray-component replacement), and CMY is rescaled without
it. This port keeps the same pure Pillow/NumPy shape, adds explicit GCR,
weight and gamma controls, and screens each channel with this repository's own
halftone/stipple primitives so the marks match the existing Fill patterns.

The module is UI-free: the Qt tab writes SVG and the converter turns it into
G-code.
"""

from __future__ import annotations

import math

from .cancellation import check_cancelled
from .shading import dot_mark_contours, halftone_contours, stipple_points

CHANNELS = ("c", "m", "y", "k")
CHANNEL_LABELS = {"c": "Cyan", "m": "Magenta", "y": "Yellow", "k": "Black"}
CHANNEL_COLORS = {
    "c": "#00a6d6",
    "m": "#d6009a",
    "y": "#f0c400",
    "k": "#222222",
}

# Classic rotated screens: C 15, M 75, Y 0, K 45 degrees.
SCREEN_ANGLES_DEG = {"c": 15.0, "m": 75.0, "y": 0.0, "k": 45.0}

# Below this ink coverage a mark is dropped so paper stays clean.
INK_FLOOR = 0.06

# Black usually overpowers the other three pens (the r/PlotterArt threads
# consistently report dialing it down), so its default weight is lower.
DEFAULT_WEIGHTS = {"c": 1.0, "m": 1.0, "y": 1.0, "k": 0.8}


def _weight_map(weights):
    if weights is None:
        return dict(DEFAULT_WEIGHTS)
    if isinstance(weights, dict):
        return {channel: float(weights.get(channel, 1.0)) for channel in CHANNELS}
    values = [float(value) for value in weights]
    if len(values) != len(CHANNELS):
        raise ValueError("weights needs one value per CMYK channel.")
    return dict(zip(CHANNELS, values))


def rgb_to_cmyk_tone(rgb, gcr=1.0, weights=None, gamma=1.0):
    """Return ink-coverage arrays in 0..1 (0 = paper, 1 = full ink).

    ``rgb`` is an ``(h, w, 3)`` array in 0..1. ``gcr`` scales how much of the
    gray component is moved into K (0 = no black extraction, 1 = standard
    GCR), and each channel's coverage is multiplied by its weight before the
    optional ``gamma`` curve is applied.
    """
    import numpy as np

    values = np.asarray(rgb, dtype=np.float32)
    if values.ndim != 3 or values.shape[2] != 3:
        raise ValueError("Expected an (h, w, 3) RGB array.")
    red, green, blue = values[:, :, 0], values[:, :, 1], values[:, :, 2]
    c = 1.0 - red
    m = 1.0 - green
    y = 1.0 - blue
    k = np.minimum(np.minimum(c, m), y) * max(0.0, float(gcr))
    k = np.clip(k, 0.0, 1.0)
    # Standard GCR: remove K from CMY. k == 0 leaves CMY untouched, which is
    # the no-black-ink case.
    denominator = np.maximum(1.0 - k, 1e-6)
    c = np.where(k > 0.0, (c - k) / denominator, c)
    m = np.where(k > 0.0, (m - k) / denominator, m)
    y = np.where(k > 0.0, (y - k) / denominator, y)

    weight_map = _weight_map(weights)
    gamma = max(1e-3, float(gamma))
    tones = {}
    for channel, array in (("c", c), ("m", m), ("y", y), ("k", k)):
        tone = np.clip(array, 0.0, 1.0) * weight_map[channel]
        tone = np.clip(tone, 0.0, 1.0)
        if abs(gamma - 1.0) > 1e-9:
            tone = np.power(tone, gamma)
        tones[channel] = tone.astype(np.float32)
    return tones


def prepare_image_tones(
    image_path,
    width_mm,
    height_mm,
    margin_mm=6.0,
    resolution_px=700,
    saturation=1.0,
    contrast=1.0,
    gcr=1.0,
    weights=None,
    gamma=1.0,
    cancel_check=None,
):
    """Load a raster, fit it to the page, and return ``(tones, geometry)``.

    The image is aspect-fit inside the page margins and downsampled so its
    longest side is at most ``resolution_px``. ``geometry`` records where the
    image sits in page millimetres so the screen can sample tone per dot.
    """
    from PIL import Image
    import numpy as np

    check_cancelled(cancel_check)
    draw_w = max(5.0, float(width_mm) - 2.0 * float(margin_mm))
    draw_h = max(5.0, float(height_mm) - 2.0 * float(margin_mm))
    image = Image.open(image_path).convert("RGB")
    scale = min(draw_w / image.width, draw_h / image.height)
    scale_w = max(1.0, image.width * scale)
    scale_h = max(1.0, image.height * scale)
    off_x = (float(width_mm) - scale_w) / 2.0
    off_y = (float(height_mm) - scale_h) / 2.0

    target = max(16, int(resolution_px))
    longest = max(image.width, image.height)
    factor = min(1.0, target / float(longest))
    pixel_w = max(8, int(round(image.width * factor)))
    pixel_h = max(8, int(round(image.height * factor)))
    image = image.resize((pixel_w, pixel_h), Image.LANCZOS)
    rgb = np.asarray(image, dtype=np.float32) / 255.0

    saturation = float(saturation)
    if abs(saturation - 1.0) > 1e-9:
        gray = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        rgb = gray[:, :, None] + (rgb - gray[:, :, None]) * saturation
        rgb = np.clip(rgb, 0.0, 1.0)
    contrast = float(contrast)
    if abs(contrast - 1.0) > 1e-9:
        rgb = np.clip((rgb - 0.5) * contrast + 0.5, 0.0, 1.0)

    tones = rgb_to_cmyk_tone(rgb, gcr=gcr, weights=weights, gamma=gamma)
    geometry = {
        "off_x": off_x,
        "off_y": off_y,
        "width_mm": scale_w,
        "height_mm": scale_h,
        "pixels_w": pixel_w,
        "pixels_h": pixel_h,
    }
    return tones, geometry


def tone_sampler(tone, geometry):
    """Nearest-pixel tone callback in page millimetres."""
    rows, cols = tone.shape
    off_x = geometry["off_x"]
    off_y = geometry["off_y"]
    width = geometry["width_mm"]
    height = geometry["height_mm"]

    def sample(x, y):
        if not (off_x <= x <= off_x + width and off_y <= y <= off_y + height):
            return 0.0
        ix = int((x - off_x) / width * cols)
        iy = int((y - off_y) / height * rows)
        ix = 0 if ix < 0 else cols - 1 if ix >= cols else ix
        iy = 0 if iy < 0 else rows - 1 if iy >= rows else iy
        return float(tone[iy, ix])

    return sample


def screen_channel(
    tone,
    geometry,
    style="halftone",
    spacing_mm=3.0,
    dot_scale=1.0,
    angle_deg=0.0,
    seed=0,
    max_marks=5000,
    pen_diameter_mm=0.3,
    cancel_check=None,
):
    """Screen one ink channel into closed dot contours in page millimetres."""
    left = geometry["off_x"]
    top = geometry["off_y"]
    right = left + geometry["width_mm"]
    bottom = top + geometry["height_mm"]
    bounds = (left, top, right, bottom)
    spacing = max(0.2, float(spacing_mm))
    cap = max(16, int(max_marks))
    darkness = tone_sampler(tone, geometry)

    def inside(x, y):
        return left <= x <= right and top <= y <= bottom

    if str(style).strip().lower() == "stipple":
        points = stipple_points(
            bounds,
            inside,
            darkness,
            min_dist=spacing,
            seed=seed,
            max_points=cap,
            cancel_check=cancel_check,
        )
        radius = max(float(pen_diameter_mm) / 2.0, spacing * 0.12) * max(
            0.1, float(dot_scale)
        )
        return dot_mark_contours(points, radius, steps=8)

    area = max(0.0, (right - left) * (bottom - top))
    estimate = area / (spacing * spacing) if spacing > 0.0 else 0.0
    if estimate > cap:
        # Grow the pitch rather than dropping marks so the screen stays even.
        spacing *= math.sqrt(estimate / cap)
    return halftone_contours(
        bounds,
        inside,
        darkness,
        spacing=spacing,
        angle_deg=angle_deg,
        dot_scale=dot_scale,
        ink_floor=INK_FLOOR,
        cancel_check=cancel_check,
        steps=8,
    )


def _fmt(value):
    text = f"{float(value):.3f}"
    return text.rstrip("0").rstrip(".")


def svg_document(layers, width_mm, height_mm, stroke_mm=0.3, order=None):
    """Return an SVG with one colour-stroked group per ink channel.

    ``layers`` maps a channel key to a polyline list. Pass ``order`` to keep
    the document order stable (cyan, magenta, yellow, black by default).
    """
    order = list(order) if order is not None else [
        channel for channel in CHANNELS if channel in layers
    ]
    body = []
    for channel in order:
        polylines = layers.get(channel) or []
        body.append(
            f'<g fill="none" stroke="{CHANNEL_COLORS.get(channel, "#111111")}" '
            f'stroke-width="{_fmt(stroke_mm)}" stroke-linecap="round" '
            f'stroke-linejoin="round" data-ink="{channel}">'
        )
        for points in polylines:
            if len(points) < 2:
                continue
            pairs = " ".join(f"{_fmt(x)},{_fmt(y)}" for x, y in points)
            body.append(f'<polyline points="{pairs}"/>')
        body.append("</g>")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{_fmt(width_mm)}mm" '
        f'height="{_fmt(height_mm)}mm" viewBox="0 0 {_fmt(width_mm)} {_fmt(height_mm)}">\n'
        f'<rect x="0" y="0" width="{_fmt(width_mm)}" height="{_fmt(height_mm)}" '
        'fill="#ffffff"/>\n'
        + "\n".join(body)
        + "\n</svg>\n"
    )
