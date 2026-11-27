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

import io
import math

import numpy as np

from .cancellation import check_cancelled
from .geometry import WaveTrail, retag_contour
from .shading import (
    dot_mark_contours,
    greedy_single_line,
    halftone_contours,
    stipple_points,
    tone_terrain_contours,
)
from .wave_rows import (
    DEFAULT_WAVE_DEPTH_INTENSITY,
    DEFAULT_WAVE_PERIOD_PITCHES,
    DEFAULT_WAVE_PERIOD_VARIATION,
    fixed_wave_minimum_pitch_mm,
    INK_FLOOR,
    WAVE_CLEARANCE_SAFETY_MARGIN_MM,
    WAVE_CLEARANCE_SEARCH_STEPS,
    WAVE_COVERAGE_ALONG_SMOOTHING_PITCHES,
    WAVE_COVERAGE_ROW_WINDOW,
    WAVE_DEPTH_ALONG_SMOOTHING_PITCHES,
    WAVE_DEPTH_ROW_WINDOW,
    WAVE_FIXED_FREQUENCY_TONE_GAIN,
    WAVE_FREQUENCY_VARIATION,
    WAVE_MAX_ADJACENT_GAP_FRACTION,
    WAVE_MIN_EDGE_GAP_MM,
    WAVE_NESTED_PITCH_SAFETY_FACTOR,
    _local_frame,
    _point_segment_distance,
    _polyline_pair_is_clear,
    _polyline_segments,
    _segment_distance,
    _smooth_tone_row,
    _smooth_tone_rows,
    _wave_clearance_ok,
    _wave_rows,
)


CHANNELS = ("c", "m", "y", "k")
CHANNEL_LABELS = {"c": "Cyan", "m": "Magenta", "y": "Yellow", "k": "Black"}
# Nominal full-coverage transmittances for the Tombow process-marker set.
# The same values feed separation, the saved preview, and code overlays unless
# a scanned ink profile replaces them.
CHANNEL_COLORS = {
    "c": "#00aeef",
    "m": "#ec008c",
    "y": "#ffff00",
    "k": "#231f20",
}

# Classic rotated screens: C 15, M 75, Y 0, K 45 degrees.
SCREEN_ANGLES_DEG = {"c": 15.0, "m": 75.0, "y": 0.0, "k": 45.0}

# Black usually overpowers the other three pens (the r/PlotterArt threads
# consistently report dialing it down), so its default weight is lower.
DEFAULT_WEIGHTS = {"c": 1.0, "m": 1.0, "y": 1.0, "k": 0.8}

# Nominal full-coverage transmittances for the preview's process ink set.
# A measured profile can override these per image.
NOMINAL_INK_TRANSMITTANCES = {
    channel: tuple(
        int(color.lstrip("#")[index : index + 2], 16) / 255.0
        for index in (0, 2, 4)
    )
    for channel, color in CHANNEL_COLORS.items()
}
# Maximum combined ink coverage (total area coverage) before the separation
# clips. Keeps the four overlaid Wave plates from stacking into a solid black
# puddle where the source asks for pure shadow.
DEFAULT_INK_LIMIT = 3.2


def ink_transmittance_matrix(transmittances=None):
    """Return a ``(4, 3)`` float32 transmittance matrix in CMYK order."""
    import numpy as np

    colors = dict(NOMINAL_INK_TRANSMITTANCES)
    if transmittances:
        colors.update(
            {
                str(channel): value
                for channel, value in transmittances.items()
                if channel in CHANNELS
            }
        )
    matrix = []
    for channel in CHANNELS:
        value = colors[channel]
        if isinstance(value, str):
            text = value.strip().lstrip("#")
            if len(text) != 6:
                raise ValueError(
                    f"{channel} ink colour must be a six-digit hex value"
                )
            triple = [
                int(text[index : index + 2], 16) / 255.0
                for index in (0, 2, 4)
            ]
        else:
            triple = [float(component) for component in tuple(value)[:3]]
            if len(triple) != 3:
                raise ValueError(
                    f"{channel} ink transmittance needs three RGB values"
                )
        matrix.append(np.clip(triple, 1e-4, 1.0))
    return np.asarray(matrix, dtype=np.float32)


def _load_color_managed_image(image_path):
    """Open an image as sRGB, applying EXIF orientation and paper alpha."""
    from PIL import Image, ImageCms, ImageOps

    with Image.open(image_path) as source:
        image = ImageOps.exif_transpose(source)
        profile = image.info.get("icc_profile")
        if image.mode in ("RGBA", "LA") or "transparency" in image.info:
            rgba = image.convert("RGBA")
            background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
            background.alpha_composite(rgba)
            image = background.convert("RGB")
        elif profile and image.mode == "RGB":
            try:
                source_profile = ImageCms.ImageCmsProfile(io.BytesIO(profile))
                target_profile = ImageCms.createProfile("sRGB")
                image = ImageCms.profileToProfile(
                    image,
                    source_profile,
                    target_profile,
                    outputMode="RGB",
                    renderingIntent=ImageCms.Intent.PERCEPTUAL,
                )
            except (ImageCms.PyCMSError, OSError, ValueError):
                image = image.convert("RGB")
        else:
            image = image.convert("RGB")
    return image


def _gamma_luminance_target(rgb, gamma):
    """Apply an ink gamma to the target luminance before separation.

    Gamma now means what operators expect: values above 1 darken the picture
    and therefore request more ink. Hue is preserved by scaling the channels
    by the ratio of shaped to original luminance, so a skin tone does not
    shift pink when the picture is darkened.
    """
    import numpy as np

    gamma = max(1e-3, float(gamma))
    if abs(gamma - 1.0) <= 1e-9:
        return rgb
    luminance = rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    shaped = np.power(np.clip(luminance, 0.0, 1.0), gamma)
    ratio = np.divide(
        shaped,
        np.maximum(luminance, 1e-6),
        out=np.ones_like(luminance),
        where=luminance > 1e-6,
    )
    return np.clip(rgb * ratio[:, :, None], 0.0, 1.0)


def multiply_composite_rgb(coverage, transmittances=None):
    """Composite CMYK coverage arrays into RGB via ink transmittances."""
    import numpy as np

    transmission = ink_transmittance_matrix(transmittances)
    result = np.ones(
        (*np.asarray(coverage["c"]).shape, 3),
        dtype=np.float32,
    )
    for index, channel in enumerate(CHANNELS):
        amount = np.clip(
            np.asarray(coverage[channel], dtype=np.float32),
            0.0,
            1.0,
        )[..., None]
        result *= 1.0 - amount * (1.0 - transmission[index])
    return np.clip(result, 0.0, 1.0)


def separate_cmyk_composite(
    rgb,
    gcr=1.0,
    weights=None,
    gamma=1.0,
    transmittances=None,
    ink_limit=DEFAULT_INK_LIMIT,
    iterations=8,
):
    """Invert the multiply ink model to produce faithful CMYK coverage.

    ``rgb`` is an ``(h, w, 3)`` array in 0..1. The forward model is the same
    one the preview uses: each ink multiplies the paper white by
    ``1 - coverage * (1 - transmittance)``. Naive complement separation does
    not account for the real inks, so the composite comes out washed, gray,
    and short on black. This function inverts that model per pixel with a
    coordinate descent in log density, seeded by classic gray-component
    replacement, then applies the total-ink limit and per-channel weights.

    ``gcr`` (0..1) controls how much of the gray component the seed moves
    into K before the fine solve; ``weights`` scale each final coverage;
    ``gamma`` shapes the target luminance first (above 1 darkens).
    """
    import numpy as np

    values = np.asarray(rgb, dtype=np.float32)
    if values.ndim != 3 or values.shape[2] != 3:
        raise ValueError("Expected an (h, w, 3) RGB array.")
    target = np.clip(values, 0.0, 1.0)
    target = _gamma_luminance_target(target, gamma)

    transmission = ink_transmittance_matrix(transmittances)
    absorptance = np.clip(1.0 - transmission, 1e-6, 1.0)

    red, green, blue = target[..., 0], target[..., 1], target[..., 2]
    c = 1.0 - red
    m = 1.0 - green
    y = 1.0 - blue
    k = np.minimum(np.minimum(c, m), y) * min(1.0, max(0.0, float(gcr)))
    k = np.clip(k, 0.0, 1.0)
    denominator = np.maximum(1.0 - k, 1e-6)
    c = np.where(k > 0.0, (c - k) / denominator, c)
    m = np.where(k > 0.0, (m - k) / denominator, m)
    y = np.where(k > 0.0, (y - k) / denominator, y)
    inks = np.clip(np.stack([c, m, y, k], axis=-1), 0.0, 1.0)

    target_density = -np.log(np.clip(target, 1e-6, 1.0))

    for _iteration in range(max(1, int(iterations))):
        rendered = np.ones_like(target)
        for index in range(len(CHANNELS)):
            amount = inks[..., index : index + 1]
            rendered *= 1.0 - amount * (1.0 - transmission[index])
        rendered = np.clip(rendered, 1e-6, 1.0)
        residual = target_density - (-np.log(rendered))
        for index in range(len(CHANNELS)):
            amount = inks[..., index : index + 1]
            denominator = 1.0 - amount * absorptance[index]
            gradient = absorptance[index] / np.maximum(denominator, 1e-6)
            numerator = np.sum(residual * gradient, axis=-1)
            norm = np.sum(gradient * gradient, axis=-1) + 1e-9
            step = numerator / norm
            updated = np.clip(amount[..., 0] + step, 0.0, 1.0)
            delta = updated - amount[..., 0]
            inks[..., index] = updated
            residual = residual - delta[..., None] * gradient

    c, m, y, k = (inks[..., index] for index in range(len(CHANNELS)))
    total = c + m + y + k
    ink_limit = max(0.0, float(ink_limit))
    over = np.maximum(0.0, total - ink_limit)
    if np.any(over > 0.0):
        scale = np.where(
            total > ink_limit,
            ink_limit / np.maximum(total, 1e-6),
            1.0,
        )
        c = c * scale
        m = m * scale
        y = y * scale
        k = k * scale

    weight_map = _weight_map(weights)
    tones = {}
    for channel, array in (("c", c), ("m", m), ("y", y), ("k", k)):
        tone = np.clip(array, 0.0, 1.0) * weight_map[channel]
        tones[channel] = np.clip(tone, 0.0, 1.0).astype(np.float32)
    return tones



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
    tagged = []
    for contour in contours:
        item = InkTrail(contour, ink=ink)
        item.__dict__.update(getattr(contour, "__dict__", {}))
        item.ink = ink
        tagged.append(item)
    return tagged


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
    # Above 1.0 the grey component would exceed the ink with the least
    # coverage, which drives C/M/Y negative before they are clipped: the
    # separation stops being monotone and the layer loses its lightest ink.
    # The control tops out at 100 %, and the maths holds there too.
    k = np.minimum(np.minimum(c, m), y) * min(1.0, max(0.0, float(gcr)))
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


def _sharpen_luminance(rgb, amount_pct, radius_mm, mm_per_pixel):
    """Apply an unsharp mask to luminance without shifting hue per channel."""
    import numpy as np
    from PIL import Image, ImageFilter

    amount = max(0.0, float(amount_pct)) / 100.0
    if amount <= 0.0:
        return rgb
    luminance = np.clip(
        rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32),
        0.0,
        1.0,
    )
    gray = Image.fromarray(
        np.rint(luminance * 255.0).astype(np.uint8),
        mode="L",
    )
    radius_px = max(
        0.5,
        float(radius_mm) / max(float(mm_per_pixel), 1e-6),
    )
    blurred = gray.filter(ImageFilter.GaussianBlur(radius_px))
    detail = (
        np.asarray(gray, dtype=np.float32)
        - np.asarray(blurred, dtype=np.float32)
    ) / 255.0
    return np.clip(rgb + detail[:, :, None] * amount, 0.0, 1.0)


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
    style=None,
    dot_pitch_mm=None,
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
    instead of a washed-out plot. A Wave-screen style uses a separate
    exposure-preserving path because its fixed row pitch masks ink rather than
    varying coverage with tone. Returns ``auto_levels``, ``brightness``,
    ``contrast``, ``saturation``, ``gcr`` and ``gamma``, plus wave-specific
    sharpening and row-pitch controls when the source pitch and scale are
    available.
    """
    from PIL import Image
    import numpy as np

    image = _load_color_managed_image(image_path)
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

    def round_up_to(value, step):
        return int(round(value / step) * step)

    style_key = str(style or "").strip().lower()
    if style_key in (
        "waves",
        "waves_even",
        "waves_zero",
        "waves_fixed",
        "waves_fidelity",
    ):
        # The wave screen is a line mask, not a tone-varying line pitch. Keep
        # the source's normal exposure and let composite-aware separation do
        # the colour work, instead of pushing brightness and gamma high
        # enough to wash the plate out (the old failure-state recipe).
        p05, p50, p95 = (
            float(value)
            for value in np.percentile(luminance, [5.0, 50.0, 95.0])
        )
        tonal_range = p95 - p05
        chroma_p90 = float(np.percentile(chroma, 90.0))
        brightness = clamp(120.0 + (0.50 - p50) * 80.0, 105.0, 150.0)
        contrast = clamp(115.0 + (0.65 - tonal_range) * 40.0, 105.0, 150.0)
        gamma = clamp(1.10 + (0.50 - p50) * 0.25, 0.95, 1.35)
        saturation = clamp(105.0 + (0.30 - chroma_p90) * 25.0, 95.0, 110.0)
        gcr = clamp(60.0 - max(0.0, chroma_p90 - 0.15) * 120.0, 20.0, 70.0)
        result = {
            "auto_levels": True,
            "brightness": round_up_to(brightness, 5),
            "contrast": round_up_to(contrast, 5),
            "saturation": round_up_to(saturation, 5),
            "gcr": round_up_to(gcr, 5),
            "gamma": round(gamma / 0.05) * 0.05,
            "sharpen": True,
            "sharpen_pct": 100.0,
            "sharpen_radius_mm": 1.5,
        }
        if (
            pen_width_mm is not None
            and effective_pitch_mm is not None
            and dot_pitch_mm is not None
        ):
            current_effective = max(0.01, float(effective_pitch_mm))
            source_pitch = max(0.01, float(dot_pitch_mm))
            scale = current_effective / source_pitch
            recommended_effective = max(
                current_effective,
                max(0.0, float(pen_width_mm)) * 3.4,
            )
            result["dot_pitch_mm"] = round(
                min(
                    8.0,
                    max(
                        source_pitch,
                        round(recommended_effective / scale / 0.05) * 0.05,
                    ),
                ),
                2,
            )
        return result

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
    transmittances=None,
    ink_limit=DEFAULT_INK_LIMIT,
    auto_levels=True,
    level_clip_pct=1.0,
    sharpen_pct=0.0,
    sharpen_radius_mm=1.5,
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

    ``sharpen_pct`` is an unsharp mask on the luminance (0 disables it): the
    detail layer is added back to all three channels, so facial features
    survive the dot screen instead of dissolving into mid-tone dots.
    """
    from PIL import Image
    import numpy as np

    check_cancelled(cancel_check)
    draw_w = max(5.0, float(width_mm) - 2.0 * float(margin_mm))
    draw_h = max(5.0, float(height_mm) - 2.0 * float(margin_mm))
    image = _load_color_managed_image(image_path)
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

    mm_per_px = (scale_w / pixel_w + scale_h / pixel_h) / 2.0
    rgb = _sharpen_luminance(
        rgb,
        sharpen_pct,
        sharpen_radius_mm,
        mm_per_px,
    )

    # Keep the tonal depth field tied to scene luminance. Ink-density controls
    # may darken or lighten every plate, but they must not flatten the waveform
    # into one frequency before screening.
    depth_luminance = np.clip(
        rgb @ np.array([0.299, 0.587, 0.114], dtype=np.float32),
        0.0,
        1.0,
    )

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

    tones = separate_cmyk_composite(
        rgb,
        gcr=gcr,
        weights=weights,
        gamma=gamma,
        transmittances=transmittances,
        ink_limit=ink_limit,
    )
    # Ink coverage decides where each plate is present; luminance supplies the
    # common scene depth used by wave screens even in a saturated ink channel.
    tones["depth"] = (1.0 - depth_luminance).astype(np.float32)
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
            [
                retag_contour(
                    line,
                    [(x + dx, y + dy) for x, y in line],
                    point_transform=lambda point: (
                        point[0] + dx,
                        point[1] + dy,
                    ),
                )
                for line in polylines
            ]
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
    path_tolerance_mm=0.05,
    depth_tone=None,
    row_clearance_mm=None,
    allow_variable_wave_spacing=False,
    wave_frequency_variation=0.0,
    wave_period_pitches=DEFAULT_WAVE_PERIOD_PITCHES,
    wave_period_variation=DEFAULT_WAVE_PERIOD_VARIATION,
    wave_depth_intensity=DEFAULT_WAVE_DEPTH_INTENSITY,
):
    """Screen one ink channel into mark polylines in page millimetres.

    Styles: ``halftone`` (variable-radius dots), ``stipple`` (blue-noise
    dots), ``lines`` (parallel lines whose pitch follows tone),
    ``rectilinear`` (serpentine rows joined over ink, so a connected region
    costs one M3/M5 cycle), ``crosshatch`` (line families stacked by tone
    level), ``waves`` (sine rows whose amplitude follows tone), ``waves_even``
    (identical translated wave rows with exact instantaneous spacing),
    ``waves_fixed`` (equal row baselines with tone-driven per-row amplitude,
    phase, and phase rate), ``waves_fidelity`` (the same fixed baselines plus
    deterministic per-ink row-density gating and immediate per-row
    scene-luminance contrast spikes), ``waves_zero`` (shared phase with tone-driven row
    amplitude, variable spacing, and exact clearance; legacy diagnostic use
    only), ``gyroid``
    (interference-field contours that flatten into blank paper), ``tsp``
    (one greedy single line through tone stipple points) and ``contours``
    (topographic contour lines of the tone).
    ``overdraw`` redraws every mark up to three times with a sub-pen offset so
    a ballpoint reads darker without changing the geometry.
    ``path_tolerance_mm`` bounds the chord error of resampled wave rows; the
    CMYK tab supplies that budget in its final paper-space units.
    ``row_clearance_mm`` is the minimum shortest-segment separation between
    adjacent visible rows, expressed in the same pre-scale units as
    ``spacing_mm``. It defaults to the pen diameter plus
    ``WAVE_MIN_EDGE_GAP_MM`` for callers that do not apply a later artwork scale.
    Fixed-baseline depth uses ``wave_period_pitches`` as its base wavelength in
    row pitches. ``wave_period_variation`` shortens dark-row periods and
    lengthens light-row periods by up to that fractional amount.
    ``wave_depth_intensity`` applies a bounded contrast curve to the depth
    signal before it drives period and amplitude. In ``waves_fixed`` the
    signal is each ink's locally smoothed depth. In ``waves_fidelity``,
    absolute smoothed ink coverage controls row density while immediate
    adjacent scene-luminance contrast controls each row's amplitude; strong
    contrast cells retain alternating rows so the waveform can use the
    available height. `100 %` is neutral.
    The legacy ``waves`` and ``waves_zero`` styles are promoted to the
    equidistant ``waves_even`` geometry unless ``allow_variable_wave_spacing``
    is explicitly true. Diagnostic comparison tools use that opt-in; normal
    artwork generation cannot silently emit unequal row pitch.
    """
    left = geometry["off_x"]
    top = geometry["off_y"]
    right = left + geometry["width_mm"]
    bottom = top + geometry["height_mm"]
    source_steps = []
    pixels_w = int(geometry.get("pixels_w", 0) or 0)
    pixels_h = int(geometry.get("pixels_h", 0) or 0)
    if pixels_w > 0:
        source_steps.append(float(geometry["width_mm"]) / pixels_w)
    if pixels_h > 0:
        source_steps.append(float(geometry["height_mm"]) / pixels_h)
    contrast_source_step_mm = min(source_steps, default=0.0)
    bounds = (left, top, right, bottom)
    spacing = max(0.2, float(spacing_mm))
    cap = max(16, int(max_marks))
    darkness = tone_sampler(tone, geometry)
    depth_darkness = (
        tone_sampler(depth_tone, geometry)
        if depth_tone is not None
        else None
    )

    def inside(x, y):
        return left <= x <= right and top <= y <= bottom

    style = str(style).strip().lower()
    if style in ("waves", "waves_zero") and not allow_variable_wave_spacing:
        style = "waves_even"
    if style in ("waves_fixed", "waves_fidelity"):
        if row_clearance_mm is None:
            fixed_clearance = (
                max(0.0, float(pen_diameter_mm))
                + WAVE_MIN_EDGE_GAP_MM
            )
        else:
            fixed_clearance = max(0.0, float(row_clearance_mm))
        required_pitch = fixed_wave_minimum_pitch_mm(
            fixed_clearance,
            period_pitches=wave_period_pitches,
            period_variation=wave_period_variation,
            frequency_variation=wave_frequency_variation,
            amplitude_scale=dot_scale,
        )
        if spacing < required_pitch - 1e-9:
            raise ValueError(
                "Variable-depth Wave needs a larger effective pitch for "
                "the selected period and tonal variation: current %.3f mm, "
                "minimum %.3f mm. Increase Dot pitch, reduce Period "
                "variation, or reduce Dot size."
                % (spacing, required_pitch)
            )
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
    elif style in (
        "waves",
        "waves_even",
        "waves_zero",
        "waves_fixed",
        "waves_fidelity",
    ):
        if row_clearance_mm is None:
            minimum_clearance_mm = (
                max(0.0, float(pen_diameter_mm)) + WAVE_MIN_EDGE_GAP_MM
            )
        else:
            minimum_clearance_mm = max(0.0, float(row_clearance_mm))
        marks = _wave_rows(
            darkness,
            bounds,
            angle_deg,
            spacing,
            max(0.1, float(dot_scale)),
            cancel_check=cancel_check,
            path_tolerance_mm=path_tolerance_mm,
            depth_darkness=depth_darkness,
            equal_spacing=(style == "waves_even"),
            zero_anchored_depth=(style == "waves_zero"),
            fixed_baseline_depth=style in (
                "waves_fixed",
                "waves_fidelity",
            ),
            minimum_clearance_mm=minimum_clearance_mm,
            wave_frequency_variation=wave_frequency_variation,
            wave_period_pitches=wave_period_pitches,
            wave_period_variation=wave_period_variation,
            wave_depth_intensity=wave_depth_intensity,
            seed=seed,
            fidelity_row_density=(style == "waves_fidelity"),
            row_pen_diameter_mm=pen_diameter_mm,
            contrast_source_step_mm=contrast_source_step_mm,
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
            row_index = getattr(points, "wave_row_index", None)
            row_baseline = getattr(points, "wave_baseline_mm", None)
            row_policy = getattr(points, "wave_row_policy", None)
            row_period = getattr(
                points,
                "wave_period_pitches",
                None,
            )
            row_period_variation = getattr(
                points,
                "wave_period_variation",
                None,
            )
            row_depth_intensity = getattr(
                points,
                "wave_depth_intensity",
                None,
            )
            row_attribute = (
                f' data-wave-row="{int(row_index)}"'
                if row_index is not None
                else ""
            )
            baseline_attribute = (
                ' data-wave-baseline="%s,%s"'
                % (_fmt(row_baseline[0]), _fmt(row_baseline[1]))
                if row_baseline is not None
                else ""
            )
            policy_attribute = (
                f' data-wave-policy="{row_policy}"'
                if row_policy is not None
                else ""
            )
            period_attribute = (
                f' data-wave-period-pitches="{float(row_period):.6f}"'
                if row_period is not None
                else ""
            )
            period_variation_attribute = (
                " data-wave-period-variation="
                f'"{float(row_period_variation):.6f}"'
                if row_period_variation is not None
                else ""
            )
            depth_intensity_attribute = (
                " data-wave-depth-intensity="
                f'"{float(row_depth_intensity):.6f}"'
                if row_depth_intensity is not None
                else ""
            )
            registration_id = getattr(
                points,
                "registration_mark_id",
                None,
            )
            registration_arm = getattr(
                points,
                "registration_mark_arm",
                None,
            )
            registration_center = getattr(
                points,
                "registration_mark_center_mm",
                None,
            )
            registration_offset = getattr(
                points,
                "registration_mark_pen_offset_mm",
                None,
            )
            registration_attributes = ""
            if registration_id is not None and registration_center is not None:
                offset = registration_offset or (0.0, 0.0)
                registration_attributes = (
                    ' data-registration-mark="%s"'
                    ' data-registration-arm="%s"'
                    ' data-registration-center="%s,%s"'
                    ' data-registration-pen-offset="%s,%s"'
                    % (
                        registration_id,
                        registration_arm or "unknown",
                        _fmt(registration_center[0]),
                        _fmt(registration_center[1]),
                        _fmt(offset[0]),
                        _fmt(offset[1]),
                    )
                )
            body.append(
                f"<polyline{row_attribute}{baseline_attribute}"
                f"{policy_attribute}{period_attribute}"
                f"{period_variation_attribute}{depth_intensity_attribute}"
                f"{registration_attributes} "
                f"points=\"{pairs}\"/>"
            )
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
