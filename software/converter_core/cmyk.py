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
from .shading import (
    dot_mark_contours,
    greedy_single_line,
    halftone_contours,
    stipple_points,
    tone_terrain_contours,
)

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


class InkTrail(list):
    """A contour tagged with the ink channel that will draw it.

    The tag rides through the geometry pipeline (``retag_contour`` preserves
    the type and attributes), so the shared OpenGL preview can draw each CMYK
    layer in its own colour without changing the planning or G-code paths.
    """

    def __init__(self, points=(), ink=None):
        super().__init__(points)
        self.ink = ink


def tag_ink(contours, ink):
    """Return the contours as :class:`InkTrail` copies carrying *ink*."""
    return [InkTrail(contour, ink=ink) for contour in contours]


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


def _soft_contrast(rgb, contrast):
    """The tab's contrast curve: linear below 1.0, soft S-curve above."""
    import numpy as np

    contrast = float(contrast)
    if abs(contrast - 1.0) <= 1e-9:
        return rgb
    if contrast < 1.0:
        return np.clip((rgb - 0.5) * contrast + 0.5, 0.0, 1.0)
    if contrast <= 2.0:
        amount = contrast - 1.0
        curve_k = 3.0
    else:
        amount = 1.0
        curve_k = 3.0 + 3.0 * min(contrast - 2.0, 1.0)
    curved = (
        0.5
        + 0.5
        * np.tanh((rgb - 0.5) * curve_k)
        / math.tanh(curve_k / 2.0)
    )
    return np.clip(rgb + (curved - rgb) * amount, 0.0, 1.0)


def _detail_score(tone):
    """Mid tone-weighted gradient energy minus a clipping penalty."""
    import numpy as np

    weight = 4.0 * tone * (1.0 - tone)
    dx = np.abs(np.diff(tone, axis=1))
    dy = np.abs(np.diff(tone, axis=0))
    detail = float(
        (0.5 * (weight[:, :-1] + weight[:, 1:]) * dx).mean()
        + (0.5 * (weight[:-1, :] + weight[1:, :]) * dy).mean()
    )
    clipped = float(((tone < 0.02) | (tone > 0.98)).mean())
    return detail - 0.4 * clipped


def auto_photo_settings(
    image_path,
    resolution_px=256,
    pen_width_mm=None,
    effective_pitch_mm=None,
):
    """Suggest Image-options values that keep a photo's detail legible.

    The tone controls are chosen by searching the exact control chain the
    pipeline applies (auto levels -> soft contrast -> brightness -> ink
    gamma) for the combination with the most mid tone-weighted gradient
    energy and the least clipping, so fine structure is not lost to crushed
    shadows or blown highlights - and whose printed mean tone matches the
    photo's. Very dark or very bright photos are aimed at the edge of the
    printable window instead, because outside it a plot stops showing
    structure at all. Saturation and GCR come from the mean chroma, and
    auto levels stays on. When ``pen_width_mm`` and ``effective_pitch_mm``
    are given (the tab passes its Pen width and Dot pitch x Artwork scale),
    the search renders the rectilinear screen as well: the tone the chain
    asks for is turned into the ink the rows actually lay down
    (``pen / row pitch``, opened up by the screen's light-tone stretch and
    cut off below the ink floor), so a sparse screen gets a darker chain
    instead of a washed-out plot. Returns ``auto_levels``, ``brightness``,
    ``contrast``, ``saturation``, ``gcr`` and ``gamma``.
    """
    from PIL import Image
    import numpy as np

    image = Image.open(image_path).convert("RGB")
    longest = max(image.width, image.height)
    factor = min(1.0, max(32, int(resolution_px)) / float(longest))
    if factor < 1.0:
        image = image.resize(
            (
                max(8, int(round(image.width * factor))),
                max(8, int(round(image.height * factor))),
            ),
            Image.LANCZOS,
        )
    rgb = np.asarray(image, dtype=np.float32) / 255.0
    luminance = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    # Use the colourful quartile, not the mean: a vivid subject against
    # neutral background still counts as vivid.
    chroma = rgb.max(axis=2) - rgb.min(axis=2)
    chroma_p75 = float(np.percentile(chroma, 75.0))

    def clamp(value, low, high):
        return max(low, min(high, value))

    # Vivid photos keep more chroma in C/M/Y and less in K; muted ones lean
    # on a little extra saturation and heavier black instead.
    saturation = (
        clamp(110.0 + (0.35 - chroma_p75) * 80.0, 110.0, 145.0) / 100.0
    )
    gcr = clamp(90.0 - max(0.0, chroma_p75 - 0.20) * 120.0, 60.0, 95.0) / 100.0
    screen = None
    if pen_width_mm is not None and effective_pitch_mm is not None:
        screen = (
            max(0.01, float(pen_width_mm)),
            max(0.01, float(effective_pitch_mm)),
        )

    # The detail search walks the same curve chain the pipeline applies,
    # including the auto-levels stretch, so it scores what the plot will
    # actually show.
    low, high = (
        float(value) for value in np.percentile(luminance, [1.0, 99.0])
    )
    stretched = np.clip(
        (luminance - low) / max(high - low, 1e-3), 0.0, 1.0
    )
    if max(stretched.shape) > 128:
        stretched = stretched[::2, ::2]

    # Aim the print's own mean tone at the photo's, clamped to the window a
    # plot can actually hold: below a mean of 0.30 the sheet is a muddy ink
    # stack and above 0.75 it is mostly paper. The clamp is what keeps very
    # dark photos lifted and very bright ones from being darkened.
    photo_tone = min(max(float(stretched.mean()), 0.30), 0.75)

    best = None
    if screen is None:
        for contrast in (120.0, 150.0, 180.0, 210.0, 240.0, 270.0, 300.0):
            contrasted = _soft_contrast(stretched, contrast / 100.0)
            for brightness in (100.0, 120.0, 140.0, 160.0, 180.0):
                lifted = np.power(contrasted, 100.0 / max(1.0, brightness))
                for gamma in (1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6):
                    printed = 1.0 - np.power(1.0 - lifted, gamma)
                    score = _detail_score(printed) - abs(
                        float(printed.mean()) - photo_tone
                    )
                    if best is None or score > best[0]:
                        best = (score, contrast, brightness, gamma)
    else:
        pen_mm, pitch_mm = screen
        filters = {}
        for channel, color in CHANNEL_COLORS.items():
            text = color.lstrip("#")
            filters[channel] = np.array(
                [int(text[index : index + 2], 16) / 255.0 for index in (0, 2, 4)],
                dtype=np.float32,
            )
        levelled = np.clip(
            (rgb - low) / max(high - low, 1e-3), 0.0, 1.0
        )
        gray = levelled @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        base = np.clip(
            gray[..., None] + (levelled - gray[..., None]) * saturation,
            0.0,
            1.0,
        )
        if max(base.shape[0], base.shape[1]) > 128:
            base = base[::2, ::2]
        luminances = np.array([0.299, 0.587, 0.114], dtype=np.float32)
        for contrast in (120.0, 150.0, 180.0, 210.0, 240.0, 270.0, 300.0):
            contrasted = _soft_contrast(base, contrast / 100.0)
            # The screen model needs the darker half of the controls: with a
            # sparse screen the only way to reach the photo's tone is more
            # ink, i.e. brightness below 100 % and gamma below 1.
            for brightness in (60.0, 80.0, 100.0, 120.0, 140.0, 160.0, 180.0):
                lifted = np.power(contrasted, 100.0 / max(1.0, brightness))
                for gamma in (0.6, 0.8, 1.0, 1.2, 1.4, 1.6):
                    tones = rgb_to_cmyk_tone(
                        lifted, gcr=gcr, weights=(1, 1, 1, 1), gamma=gamma
                    )
                    rendered = np.ones_like(lifted)
                    for channel in CHANNELS:
                        tone = tones[channel]
                        spacing = pitch_mm * (1.0 + 6.0 * (1.0 - tone))
                        coverage = np.where(
                            tone >= INK_FLOOR,
                            np.clip(pen_mm / spacing, 0.0, 1.0),
                            0.0,
                        )
                        rendered *= 1.0 - coverage[..., None] * (
                            1.0 - filters[channel]
                        )
                    rendered_luminance = rendered @ luminances
                    score = _detail_score(rendered_luminance) - abs(
                        float(rendered_luminance.mean()) - photo_tone
                    )
                    if best is None or score > best[0]:
                        best = (score, contrast, brightness, gamma)
    _, contrast, brightness, gamma = best

    def round_up_to(value, step):
        return int(round(value / step) * step)

    return {
        "auto_levels": True,
        "brightness": round_up_to(brightness, 5),
        "contrast": round_up_to(contrast, 5),
        "saturation": round_up_to(saturation * 100.0, 5),
        "gcr": round_up_to(gcr * 100.0, 5),
        "gamma": round(gamma / 0.05) * 0.05,
    }


def prepare_image_tones(
    image_path,
    width_mm,
    height_mm,
    margin_mm=6.0,
    brightness=100.0,
    resolution_px=700,
    saturation=1.0,
    contrast=1.0,
    gcr=1.0,
    weights=None,
    gamma=1.0,
    auto_levels=True,
    level_clip_pct=1.0,
    cancel_check=None,
):
    """Load a raster, fit it to the page, and return ``(tones, geometry)``.

    The image is aspect-fit inside the page margins and downsampled so its
    longest side is at most ``resolution_px``. ``geometry`` records where the
    image sits in page millimetres so the screen can sample tone per dot.

    ``auto_levels`` stretches the luminance between the 1st and 99th
    percentiles before separation, so a low-key or hazy photo uses the whole
    tonal range instead of screening into one flat mid-tone. Disable it for
    images that are already well exposed.
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

    if auto_levels:
        luminance = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        clip = max(0.0, min(float(level_clip_pct), 20.0))
        low, high = np.percentile(luminance, [clip, 100.0 - clip])
        spread = float(high) - float(low)
        if spread > 1e-3:
            rgb = np.clip((rgb - float(low)) / spread, 0.0, 1.0)

    saturation = float(saturation)
    if abs(saturation - 1.0) > 1e-9:
        gray = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
        rgb = gray[:, :, None] + (rgb - gray[:, :, None]) * saturation
        rgb = np.clip(rgb, 0.0, 1.0)
    contrast = float(contrast)
    if abs(contrast - 1.0) > 1e-9:
        rgb = _soft_contrast(rgb, contrast)

    brightness = float(brightness)
    if abs(brightness - 100.0) > 1e-9:
        # Shadow-weighted lift: a gamma curve that brightens mid tones and
        # shadows while keeping the black and white points (no clipping).
        exponent = 100.0 / max(1.0, brightness)
        rgb = np.power(np.clip(rgb, 0.0, 1.0), exponent)

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


def _local_frame(bounds, angle_deg):
    """Rotated bounding box of a rectangle plus the local->world basis."""
    left, top, right, bottom = (float(value) for value in bounds)
    angle = math.radians(float(angle_deg))
    ca, sa = math.cos(angle), math.sin(angle)
    cs, sn = math.cos(-angle), math.sin(-angle)
    corners = [(left, top), (right, top), (right, bottom), (left, bottom)]
    rotated = [(x * cs - y * sn, x * sn + y * cs) for x, y in corners]
    return (
        min(point[0] for point in rotated),
        max(point[0] for point in rotated),
        min(point[1] for point in rotated),
        max(point[1] for point in rotated),
        ca,
        sa,
    )


def _line_runs(
    darkness,
    bounds,
    angle_deg,
    spacing,
    threshold,
    adaptive=False,
    connect=False,
    light_stretch=2.0,
    min_length_mm=0.8,
    cancel_check=None,
):
    """Parallel line family, broken into runs where tone is above threshold.

    With ``adaptive`` the next line's pitch grows in light areas and stays at
    the requested spacing in dark ones, so one tone-driven line screen covers
    a continuous tonal range instead of discrete levels. With ``connect``
    consecutive overlapping runs are stitched into serpentine chains (never
    across blank paper), so one connected region costs one M3/M5 pen cycle.
    ``light_stretch`` scales how far the pitch opens in the lightest tones;
    the coverage range of one ink is roughly ``light_stretch + 1`` to 1.
    """
    min_x, max_x, min_y, max_y, ca, sa = _local_frame(bounds, angle_deg)
    spacing = max(0.2, float(spacing))
    sample_step = max(0.3, min(spacing * 0.5, 1.0))
    rows = []
    eased_tone = None
    y = min_y + spacing * 0.5
    while y <= max_y:
        check_cancelled(cancel_check)
        samples = []
        x = min_x
        while x <= max_x:
            wx = x * ca - y * sa
            wy = x * sa + y * ca
            samples.append((x, darkness(wx, wy)))
            x += sample_step
        current = []
        row_runs = []
        for x_value, value in samples:
            if value >= threshold:
                current.append((x_value, y))
            elif current:
                if (len(current) - 1) * sample_step >= min_length_mm:
                    row_runs.append(list(current))
                current = []
        if current and (len(current) - 1) * sample_step >= min_length_mm:
            row_runs.append(list(current))
        rows.append(row_runs)
        if adaptive:
            # Follow the ink the row actually lays down (not the blank paper
            # between runs) and ease it over a few rows: a row that crosses
            # both the subject and the background used to shift the pitch in
            # one step, which reads as banding in smooth areas.
            inked = [value for _x, value in samples if value >= threshold]
            if inked:
                mean_tone = sum(inked) / len(inked)
                eased_tone = (
                    mean_tone
                    if eased_tone is None
                    else eased_tone + (mean_tone - eased_tone) * 0.5
                )
            elif eased_tone is None:
                eased_tone = 0.0
            y += spacing * (
                1.0 + float(light_stretch) * (1.0 - eased_tone)
            )
        else:
            y += spacing
    groups = (
        _stitch_runs(rows, darkness, ca, sa, threshold)
        if connect
        else [run for row_runs in rows for run in row_runs]
    )
    return [
        [(px * ca - py * sa, px * sa + py * ca) for px, py in group]
        for group in groups
    ]


def _stitch_runs(rows, darkness, ca, sa, threshold):
    """Join overlapping runs of consecutive rows into serpentine chains.

    A connector is only drawn when it stays over ink (its midpoint samples
    at or above ``threshold``), so a chain never crosses blank paper. Each
    run continues at most one chain and each chain grows by at most one run
    per row, so rows that break into several dashes still chain column-wise
    instead of only matching the row's last dash.
    """
    finished = []
    open_chains = []
    for row_runs in rows:
        continued = [False] * len(open_chains)
        new_open = []
        for run in row_runs:
            span = (
                min(run[0][0], run[-1][0]),
                max(run[0][0], run[-1][0]),
            )
            candidates = []
            for index, chain in enumerate(open_chains):
                if continued[index]:
                    continue
                last_span = chain["span"]
                overlap = min(last_span[1], span[1]) - max(
                    last_span[0], span[0]
                )
                if overlap > 0.0:
                    candidates.append((overlap, index))
            candidates.sort(reverse=True)
            joined = False
            for _overlap, index in candidates:
                chain = open_chains[index]
                point = chain["points"][-1]
                oriented = (
                    run
                    if abs(point[0] - run[0][0])
                    <= abs(point[0] - run[-1][0])
                    else list(reversed(run))
                )
                next_point = oriented[0]
                mx = (point[0] + next_point[0]) / 2.0
                my = (point[1] + next_point[1]) / 2.0
                wx = mx * ca - my * sa
                wy = mx * sa + my * ca
                if darkness(wx, wy) < threshold:
                    continue
                chain["points"].extend(oriented)
                chain["span"] = span
                continued[index] = True
                new_open.append(chain)
                joined = True
                break
            if not joined:
                new_open.append({"points": list(run), "span": span})
        for index, chain in enumerate(open_chains):
            if not continued[index]:
                finished.append(chain["points"])
        open_chains = new_open
    for chain in open_chains:
        finished.append(chain["points"])
    return finished


def _wave_rows(
    darkness,
    bounds,
    angle_deg,
    spacing,
    amplitude_scale,
    min_length_mm=0.8,
    cancel_check=None,
):
    """Sine rows whose amplitude follows tone (flat white draws nothing)."""
    min_x, max_x, min_y, max_y, ca, sa = _local_frame(bounds, angle_deg)
    spacing = max(0.2, float(spacing))
    sample_step = max(0.25, min(spacing * 0.25, 0.8))
    amplitude_max = spacing * 0.5 * max(0.05, float(amplitude_scale))
    wavelength = spacing * 2.0
    rows = []
    y = min_y + spacing * 0.5
    while y <= max_y:
        check_cancelled(cancel_check)
        current = []
        x = min_x
        while x <= max_x:
            wx = x * ca - y * sa
            wy = x * sa + y * ca
            value = darkness(wx, wy)
            if value >= INK_FLOOR:
                offset = (
                    amplitude_max
                    * value
                    * math.sin(2.0 * math.pi * x / wavelength)
                )
                current.append((x, y + offset))
            elif current:
                if (len(current) - 1) * sample_step >= min_length_mm:
                    rows.append(
                        [
                            (px * ca - py * sa, px * sa + py * ca)
                            for px, py in current
                        ]
                    )
                current = []
            x += sample_step
        if current and (len(current) - 1) * sample_step >= min_length_mm:
            rows.append(
                [(px * ca - py * sa, px * sa + py * ca) for px, py in current]
            )
        y += spacing
    return rows


def _field_contours(tone, geometry, spacing, kind="contours", cancel_check=None):
    """Topographic contour lines of the tone, or of a tone-modulated field."""
    bounds = (
        geometry["off_x"],
        geometry["off_y"],
        geometry["off_x"] + geometry["width_mm"],
        geometry["off_y"] + geometry["height_mm"],
    )
    pixel_mm = max(
        geometry["width_mm"] / max(1, geometry["pixels_w"]),
        geometry["height_mm"] / max(1, geometry["pixels_h"]),
    )
    step = max(pixel_mm, min(float(spacing) * 0.4, pixel_mm * 4.0))
    base = tone_sampler(tone, geometry)
    blur = float(spacing) * 0.25
    if str(kind) == "gyroid":
        k = 2.0 * math.pi / max(0.5, float(spacing))

        def field(x, y):
            value = base(x, y)
            if value <= 0.0:
                return 0.0
            wave = math.sin(k * x) * math.cos(k * y) + math.sin(k * y) * math.cos(k * x)
            # wave is in [-2, 2]; tone scales the relief so white paper is flat.
            return max(0.0, min(1.0, 0.5 + 0.25 * value * wave))

        darkness = field
        blur = 0.0
    else:
        darkness = base
    return tone_terrain_contours(
        bounds,
        float(spacing),
        darkness,
        step=step,
        blur=blur,
        max_cells=60000,
        cancel_check=cancel_check,
    )


def _apply_overdraw(polylines, passes, spacing):
    """Redraw every mark with a small deterministic offset (ink darkening)."""
    passes = int(passes)
    if passes <= 1 or not polylines:
        return polylines
    passes = min(3, passes)
    radius = min(0.25, max(0.04, float(spacing) * 0.05))
    out = list(polylines)
    for index in range(1, passes):
        angle = 2.0 * math.pi * index / passes
        dx = math.cos(angle) * radius * index
        dy = math.sin(angle) * radius * index
        out.extend(
            [[(x + dx, y + dy) for x, y in line] for line in polylines]
        )
    return out


def _spiral_mark(cx, cy, radius, turns=2.0, steps=14):
    """One Archimedean spiral from the centre out to ``radius``.

    A plotted pen dot is an outline; a two-turn spiral reads as a filled dot
    at pen width while keeping every mark one continuous pen-down stroke.
    """
    steps = max(8, int(steps))
    points = []
    for index in range(steps + 1):
        t = index / steps
        angle = 2.0 * math.pi * turns * t
        points.append(
            (cx + math.cos(angle) * radius * t, cy + math.sin(angle) * radius * t)
        )
    return points


def solid_dots(contours, turns=2.0, steps=14):
    """Convert closed dot contours (circles) into solid-reading spirals."""
    marks = []
    for contour in contours:
        xs = [point[0] for point in contour]
        ys = [point[1] for point in contour]
        if len(contour) < 3 or not xs:
            continue
        radius = 0.5 * (max(xs) - min(xs))
        if radius <= 1e-9:
            continue
        marks.append(
            _spiral_mark(
                sum(xs) / len(xs), sum(ys) / len(ys), radius, turns, steps
            )
        )
    return marks


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
    levels=4,
    overdraw=1,
    solid=True,
    cancel_check=None,
):
    """Screen one ink channel into mark polylines in page millimetres.

    Styles: ``halftone`` (variable-radius dots), ``stipple`` (blue-noise
    dots), ``lines`` (parallel lines whose pitch follows tone),
    ``rectilinear`` (serpentine rows joined over ink, so a connected region
    costs one M3/M5 cycle), ``crosshatch`` (line families stacked by tone
    level), ``waves`` (sine rows whose amplitude follows tone), ``gyroid``
    (interference-field contours that flatten into blank paper), ``tsp``
    (one greedy single line through tone stipple points) and ``contours``
    (topographic contour lines of the tone).
    ``overdraw`` redraws every mark up to three times with a sub-pen offset so
    a ballpoint reads darker without changing the geometry.
    """
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

    style = str(style).strip().lower()
    if style == "stipple":
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
        marks = dot_mark_contours(points, radius, steps=8)
    elif style == "lines":
        marks = _line_runs(
            darkness,
            bounds,
            angle_deg,
            spacing,
            INK_FLOOR,
            adaptive=True,
            cancel_check=cancel_check,
        )
    elif style == "rectilinear":
        marks = _line_runs(
            darkness,
            bounds,
            angle_deg,
            spacing,
            INK_FLOOR,
            adaptive=True,
            connect=True,
            light_stretch=6.0,
            cancel_check=cancel_check,
        )
    elif style == "crosshatch":
        # Four families keep the classic 45-degree screen; further families
        # spread evenly over the half turn so no direction repeats.
        passes = max(1, int(levels) - 1)
        step = 180.0 / max(4, passes)
        marks = []
        for index in range(passes):
            check_cancelled(cancel_check)
            threshold = (index + 1) / float(passes + 1)
            marks.extend(
                _line_runs(
                    darkness,
                    bounds,
                    float(angle_deg) + index * step,
                    spacing,
                    threshold,
                    cancel_check=cancel_check,
                )
            )
    elif style == "waves":
        marks = _wave_rows(
            darkness,
            bounds,
            angle_deg,
            spacing,
            max(0.1, float(dot_scale)),
            cancel_check=cancel_check,
        )
    elif style == "tsp":
        points = stipple_points(
            bounds,
            inside,
            darkness,
            min_dist=spacing,
            seed=seed,
            max_points=cap,
            cancel_check=cancel_check,
        )
        line = greedy_single_line(points, cell=spacing, cancel_check=cancel_check)
        marks = [line] if len(line) >= 2 else []
    elif style == "gyroid":
        marks = _field_contours(
            tone, geometry, spacing, kind="gyroid", cancel_check=cancel_check
        )
    elif style == "contours":
        marks = _field_contours(
            tone, geometry, spacing, kind="contours", cancel_check=cancel_check
        )
    else:
        area = max(0.0, (right - left) * (bottom - top))
        estimate = area / (spacing * spacing) if spacing > 0.0 else 0.0
        if estimate > cap:
            # Grow the pitch rather than dropping marks so the screen stays even.
            spacing *= math.sqrt(estimate / cap)
        marks = halftone_contours(
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
        if solid:
            marks = solid_dots(marks)
    return _apply_overdraw(marks, overdraw, spacing)


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
            f'stroke-linejoin="round" style="mix-blend-mode: multiply" '
            f'data-ink="{channel}">'
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
