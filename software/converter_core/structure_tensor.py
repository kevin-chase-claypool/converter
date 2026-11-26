"""Edge-following streamline screening for photograph-derived CMYK plates.

The caller supplies one image-form guide: gradients from its luminance and
colour channels form a structure tensor, the tensor is blurred, and its
edge-tangent eigenvector becomes a smooth orientation field. Coherence and
tensor strength blend that shared field toward each plate's fixed screen angle
in weak or flat areas. CMYK plates keep independent tone networks and fallback
directions while following the same image form where it is clear.
"""

from __future__ import annotations

import bisect
import math
from collections import deque

from .cancellation import check_cancelled


EDGE_FLOW_CHROMA_WEIGHT = 0.35
# Tensor trace is the squared gradient energy. Below this floor the guide is
# noise or broad tone, not a form boundary that should redirect every screen.
EDGE_FLOW_STRENGTH_SCALE_FLOOR = 4.0e-7
EDGE_FLOW_STRENGTH_PERCENTILE = 60.0
EDGE_FLOW_COHERENCE_LOW = 0.02
EDGE_FLOW_COHERENCE_HIGH = 0.18
EDGE_FLOW_MAX_PITCH_COMPRESSION = 0.90
EDGE_FLOW_MIN_PITCH_PEN_RATIO = 1.10
EDGE_FLOW_KEYLINE_BASE_WEIGHT = 0.55
EDGE_FLOW_KEYLINE_PERCENTILE = 85.0
EDGE_FLOW_KEYLINE_LOW = 0.30
EDGE_FLOW_KEYLINE_HIGH = 0.80
EDGE_FLOW_DARK_LAYER_START = 0.40
EDGE_FLOW_DARK_LAYER_END = 0.90


def _edge_flow_local_pitch(
    base_pitch,
    tone,
    pen_diameter_mm,
    compression,
):
    """Return the continuous streamline pitch at one local ink tone."""
    base = max(1e-6, float(base_pitch))
    darkness = min(1.0, max(0.0, float(tone)))
    amount = min(
        EDGE_FLOW_MAX_PITCH_COMPRESSION,
        max(0.0, float(compression)),
    )
    pitch = base * (1.0 - amount * darkness)
    pen_floor = (
        max(0.05, float(pen_diameter_mm) * EDGE_FLOW_MIN_PITCH_PEN_RATIO)
        if float(pen_diameter_mm) > 0.0
        else 0.0
    )
    return max(pen_floor, min(base, pitch))


def edge_flow_coverage_factor(
    pen_diameter_mm,
    pitch_mm,
    layers,
):
    """Approximate one channel's rendered occupancy on a shared network."""
    pen_mm = max(0.01, float(pen_diameter_mm))
    pitch = max(0.01, float(pitch_mm))
    layer_count = max(1, min(6, int(layers)))
    return min(1.0, pen_mm / pitch) / math.sqrt(layer_count)


def _path_tone_threshold(
    distance_mm,
    path_key,
    segment_mm,
    layer,
    channel_salt=0,
):
    """Stable tone threshold at one position along a single streamline."""
    segment_mm = max(1e-6, float(segment_mm))
    segment = int(math.floor(max(0.0, float(distance_mm)) / segment_mm))
    value = (
        segment * 374761393
        + int(path_key) * 668265263
        + int(layer) * 3266489917
        + int(channel_salt) * 2246822519
    ) & 0xFFFFFFFF
    value = ((value ^ (value >> 13)) * 1274126177) & 0xFFFFFFFF
    value ^= value >> 16
    return (float(value) + 0.5) / 4294967296.0


def _field_geometry(guide, geometry, max_side=900):
    """Downsample only the direction-field grid, preserving page geometry."""
    import numpy as np
    from PIL import Image

    rows, cols = np.asarray(guide).shape
    factor = min(1.0, float(max_side) / max(1, max(rows, cols)))
    if factor >= 0.999:
        field_geometry = dict(geometry)
        field_geometry["pixels_w"] = cols
        field_geometry["pixels_h"] = rows
        return np.asarray(guide, dtype=np.float32), field_geometry

    field_w = max(8, int(round(cols * factor)))
    field_h = max(8, int(round(rows * factor)))
    image = Image.fromarray(np.asarray(guide, dtype=np.float32), mode="F")
    image = image.resize((field_w, field_h), Image.Resampling.BILINEAR)
    field_geometry = dict(geometry)
    field_geometry["pixels_w"] = field_w
    field_geometry["pixels_h"] = field_h
    return np.asarray(image, dtype=np.float32), field_geometry


def _blur_float_field(field, radius_px):
    """Approximate a Gaussian blur with three separable box passes."""
    import numpy as np

    radius = max(0, int(round(float(radius_px))))
    result = np.asarray(field, dtype=np.float32)
    if radius < 1:
        return result

    def box_pass(values, axis):
        padding = [(0, 0), (0, 0)]
        padding[axis] = (radius, radius)
        padded = np.pad(values, padding, mode="edge")
        cumulative = np.cumsum(padded, axis=axis, dtype=np.float64)
        cumulative_padding = [(0, 0)] * cumulative.ndim
        cumulative_padding[axis] = (1, 0)
        cumulative = np.pad(
            cumulative,
            cumulative_padding,
            mode="constant",
        )
        high = [slice(None)] * cumulative.ndim
        low = [slice(None)] * cumulative.ndim
        high[axis] = slice(2 * radius + 1, None)
        low[axis] = slice(None, -(2 * radius + 1))
        summed = cumulative[tuple(high)] - cumulative[tuple(low)]
        return (summed / (2 * radius + 1)).astype(np.float32)

    for _ in range(3):
        result = box_pass(result, 1)
        result = box_pass(result, 0)
    return result


def edge_preserving_simplify(
    image,
    radius_mm,
    mm_per_px,
    epsilon=0.01,
):
    """Smooth low-contrast texture while retaining strong image boundaries.

    This is a compact self-guided filter. It uses the same soft box blur as the
    structure tensor, so the converter does not acquire another imaging
    dependency. ``radius_mm`` is measured on the finished page.
    """
    import numpy as np

    values = np.asarray(image, dtype=np.float32)
    radius = max(
        0,
        int(
            round(
                max(0.0, float(radius_mm))
                / max(1e-6, float(mm_per_px))
            )
        ),
    )
    if radius < 1 or values.size == 0:
        return values.copy()

    source = values if values.ndim == 3 else values[..., None]
    output = np.empty_like(source, dtype=np.float32)
    threshold = max(1e-8, float(epsilon))
    for index in range(source.shape[2]):
        channel = source[..., index]
        mean = _blur_float_field(channel, radius)
        variance = np.maximum(
            _blur_float_field(channel * channel, radius) - mean * mean,
            0.0,
        )
        gain = variance / (variance + threshold)
        offset = mean - gain * mean
        output[..., index] = (
            _blur_float_field(gain, radius) * channel
            + _blur_float_field(offset, radius)
        )
    result = np.clip(output, 0.0, 1.0)
    return result if values.ndim == 3 else result[..., 0]


def _structure_tensor_components(guide, geometry, smoothing_mm):
    """Return the edge tangent, guidance weight, and confidence field."""
    import numpy as np

    if (
        isinstance(guide, (tuple, list))
        and guide
        and all(np.asarray(field).ndim == 2 for field in guide)
    ):
        fields = tuple(np.asarray(field, dtype=np.float32) for field in guide)
    else:
        guide_values = np.asarray(guide, dtype=np.float32)
        if guide_values.ndim == 2:
            fields = (guide_values,)
        elif guide_values.ndim == 3 and guide_values.shape[2] >= 3:
            # Keep colour-only boundaries, but make luminance the primary form
            # guide. Summing raw RGB gradients equally let chrome-heavy JPEG
            # boundaries redirect facial streamlines and produced a painted-mask
            # look. Two opponent-colour fields contribute at reduced amplitude,
            # which preserves equal-luminance edges without overpowering forms.
            red = guide_values[:, :, 0]
            green = guide_values[:, :, 1]
            blue = guide_values[:, :, 2]
            luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
            fields = (
                luminance,
                EDGE_FLOW_CHROMA_WEIGHT * (red - green),
                EDGE_FLOW_CHROMA_WEIGHT * (0.5 * (red + green) - blue),
            )
        elif guide_values.ndim == 3 and guide_values.shape[2] >= 1:
            fields = tuple(
                guide_values[:, :, index]
                for index in range(guide_values.shape[2])
            )
        else:
            raise ValueError(
                "Structure guide must be a 2D image or a sequence of 2D fields."
            )

    jxx = None
    jxy = None
    jyy = None
    field_geometry = None
    for source in fields:
        field, current_geometry = _field_geometry(source, geometry)
        field_geometry = current_geometry
        gradient_y, gradient_x = np.gradient(field)
        channel_jxx = gradient_x * gradient_x
        channel_jxy = gradient_x * gradient_y
        channel_jyy = gradient_y * gradient_y
        if jxx is None:
            jxx = channel_jxx
            jxy = channel_jxy
            jyy = channel_jyy
        else:
            jxx += channel_jxx
            jxy += channel_jxy
            jyy += channel_jyy

    if field_geometry is None:
        raise ValueError("Structure guide must contain at least one channel.")

    pixel_x = field_geometry["width_mm"] / max(1, field_geometry["pixels_w"])
    pixel_y = field_geometry["height_mm"] / max(1, field_geometry["pixels_h"])
    pixel_mm = max(1e-6, 0.5 * (pixel_x + pixel_y))
    blur_radius = max(0.0, float(smoothing_mm)) / pixel_mm
    jxx = _blur_float_field(jxx, blur_radius)
    jxy = _blur_float_field(jxy, blur_radius)
    jyy = _blur_float_field(jyy, blur_radius)

    trace = jxx + jyy
    delta = jxx - jyy
    root = np.sqrt(delta * delta + 4.0 * jxy * jxy)
    safe_root = np.maximum(root, 1e-8)
    coherence = np.clip(root / np.maximum(trace, 1e-8), 0.0, 1.0)
    positive_trace = trace[trace > 1e-12]
    strength_scale = (
        max(
            EDGE_FLOW_STRENGTH_SCALE_FLOOR,
            float(
                np.percentile(
                    positive_trace,
                    EDGE_FLOW_STRENGTH_PERCENTILE,
                )
            ),
        )
        if positive_trace.size
        else EDGE_FLOW_STRENGTH_SCALE_FLOOR
    )
    keyline_scale = (
        max(
            EDGE_FLOW_STRENGTH_SCALE_FLOOR,
            float(
                np.percentile(
                    positive_trace,
                    EDGE_FLOW_KEYLINE_PERCENTILE,
                )
            ),
        )
        if positive_trace.size
        else EDGE_FLOW_STRENGTH_SCALE_FLOOR
    )
    strength_floor = strength_scale * 0.02
    strength = np.clip(
        (trace - strength_floor)
        / max(1e-8, strength_scale - strength_floor),
        0.0,
        1.0,
    )
    keyline_energy = np.clip(
        (trace - strength_floor)
        / max(1e-8, keyline_scale - strength_floor),
        0.0,
        1.0,
    )

    cos_twice = np.clip(delta / safe_root, -1.0, 1.0)
    sin_twice = np.clip(2.0 * jxy / safe_root, -1.0, 1.0)
    sin_phi = np.sqrt(np.clip((1.0 - cos_twice) * 0.5, 0.0, 1.0))
    sin_phi = np.where(sin_twice < 0.0, -sin_phi, sin_phi)
    cos_phi = np.sqrt(np.clip((1.0 + cos_twice) * 0.5, 0.0, 1.0))

    coherence_gate = np.clip(
        (coherence - EDGE_FLOW_COHERENCE_LOW)
        / (EDGE_FLOW_COHERENCE_HIGH - EDGE_FLOW_COHERENCE_LOW),
        0.0,
        1.0,
    )
    # Coherence and tensor strength describe different parts of confidence.
    # Multiplying them twice suppresses broad facial planes even when their
    # isophotes are clear. The square root keeps the blend continuous while
    # allowing moderate gradients to retain the shared form direction.
    guided = np.sqrt(np.clip(coherence_gate * strength, 0.0, 1.0))
    keyline = np.sqrt(np.clip(coherence * keyline_energy, 0.0, 1.0))
    return (
        (-sin_phi).astype(np.float32),
        cos_phi.astype(np.float32),
        guided.astype(np.float32),
        keyline.astype(np.float32),
        field_geometry,
    )


def structure_tensor_fields(guide, geometry, smoothing_mm):
    """Return shared tangent, confidence, keyline, and field geometry."""
    return _structure_tensor_components(
        guide,
        geometry,
        max(0.1, float(smoothing_mm)),
    )


def structure_field_diagnostic(guide, geometry, smoothing_mm):
    """Render undirected tangent orientation with confidence as brightness.

    The hue repeats every 180 degrees, so reversing an eigenvector cannot change
    the diagnostic colour. Weak or incoherent regions approach black; bright
    colours mean the shared image direction is confidently steering the trace.
    """
    import numpy as np

    tangent_x, tangent_y, guided, keyline, _field_geometry = (
        _structure_tensor_components(
            guide,
            geometry,
            max(0.1, float(smoothing_mm)),
        )
    )
    angle = np.arctan2(tangent_y, tangent_x) % np.pi
    hue = angle / np.pi
    sector = np.floor(hue * 6.0).astype(np.int16) % 6
    fraction = hue * 6.0 - np.floor(hue * 6.0)
    saturation = 0.82
    value = np.clip(0.18 + 0.82 * guided, 0.0, 1.0)
    p = value * (1.0 - saturation)
    q = value * (1.0 - saturation * fraction)
    t = value * (1.0 - saturation * (1.0 - fraction))
    channels = [
        np.select(
            [sector == 0, sector == 1, sector == 2, sector == 3, sector == 4],
            [value, q, p, p, t],
            default=value,
        ),
        np.select(
            [sector == 0, sector == 1, sector == 2, sector == 3, sector == 4],
            [t, value, value, q, p],
            default=p,
        ),
        np.select(
            [sector == 0, sector == 1, sector == 2, sector == 3, sector == 4],
            [p, p, t, value, value],
            default=q,
        ),
    ]
    rgb = np.stack(channels, axis=-1)
    edge_glow = np.clip(keyline, 0.0, 1.0)[..., None] * 0.35
    rgb = rgb + edge_glow
    return np.clip(rgb * 255.0, 0, 255).astype(np.uint8)


def _blend_structure_velocity(
    tangent_x,
    tangent_y,
    guided,
    fallback_angle_deg,
):
    """Blend one tangent field toward a fixed screen direction."""
    import numpy as np

    fallback_radians = math.radians(float(fallback_angle_deg))
    fallback_x = math.cos(fallback_radians)
    fallback_y = math.sin(fallback_radians)
    velocity_x = guided * tangent_x + (1.0 - guided) * fallback_x
    velocity_y = guided * tangent_y + (1.0 - guided) * fallback_y
    norm = np.maximum(np.hypot(velocity_x, velocity_y), 1e-8)
    return (
        (velocity_x / norm).astype(np.float32),
        (velocity_y / norm).astype(np.float32),
    )


def _structure_tensor_velocity(guide, geometry, smoothing_mm, fallback_angle_deg):
    """Return edge-following vectors and edge confidence for one field."""
    tangent_x, tangent_y, guided, _keyline, field_geometry = (
        _structure_tensor_components(guide, geometry, smoothing_mm)
    )
    velocity_x, velocity_y = _blend_structure_velocity(
        tangent_x,
        tangent_y,
        guided,
        fallback_angle_deg,
    )
    return velocity_x, velocity_y, guided, field_geometry


def _bilinear_velocity(velocity_x, velocity_y, field_geometry, x, y):
    """Sample a normalized vector field at a page coordinate."""
    left = float(field_geometry["off_x"])
    top = float(field_geometry["off_y"])
    width = max(1e-8, float(field_geometry["width_mm"]))
    height = max(1e-8, float(field_geometry["height_mm"]))
    if not (left <= x <= left + width and top <= y <= top + height):
        return 0.0, 0.0

    rows, cols = velocity_x.shape
    px = (x - left) / width * max(0, cols - 1)
    py = (y - top) / height * max(0, rows - 1)
    x0 = max(0, min(cols - 1, int(math.floor(px))))
    y0 = max(0, min(rows - 1, int(math.floor(py))))
    x1 = min(cols - 1, x0 + 1)
    y1 = min(rows - 1, y0 + 1)
    fx = max(0.0, min(1.0, px - x0))
    fy = max(0.0, min(1.0, py - y0))

    def sample(field):
        return (
            field[y0, x0] * (1.0 - fx) * (1.0 - fy)
            + field[y0, x1] * fx * (1.0 - fy)
            + field[y1, x0] * (1.0 - fx) * fy
            + field[y1, x1] * fx * fy
        )

    return float(sample(velocity_x)), float(sample(velocity_y))


def _bilinear_scalar(field, field_geometry, x, y):
    """Sample one field at a page coordinate."""
    left = float(field_geometry["off_x"])
    top = float(field_geometry["off_y"])
    width = max(1e-8, float(field_geometry["width_mm"]))
    height = max(1e-8, float(field_geometry["height_mm"]))
    if not (left <= x <= left + width and top <= y <= top + height):
        return 0.0

    rows, cols = field.shape
    px = (x - left) / width * max(0, cols - 1)
    py = (y - top) / height * max(0, rows - 1)
    x0 = max(0, min(cols - 1, int(math.floor(px))))
    y0 = max(0, min(rows - 1, int(math.floor(py))))
    x1 = min(cols - 1, x0 + 1)
    y1 = min(rows - 1, y0 + 1)
    fx = max(0.0, min(1.0, px - x0))
    fy = max(0.0, min(1.0, py - y0))
    return float(
        field[y0, x0] * (1.0 - fx) * (1.0 - fy)
        + field[y0, x1] * fx * (1.0 - fy)
        + field[y1, x0] * (1.0 - fx) * fy
        + field[y1, x1] * fx * fy
    )


def _tone_gated_runs(
    points,
    tone_at,
    threshold,
    tone_segment,
    path_key,
    layer,
    minimum_length,
    edge_at=None,
    keyline_strength=0.0,
    edge_quiet=0.0,
    bridge_mm=0.0,
    coverage_scale=None,
    channel_salt=0,
):
    """Split one traced path into local tone and optional keyline runs.

    A positive ``bridge_mm`` retains short non-inking gaps inside the current
    run. The connector still follows the traced streamline, so a dark passage
    costs one pen-down cycle instead of a lift and independent M3/M5 pair for
    every local phase break. Gaps longer than the bridge remain paper.
    ``coverage_scale`` supplies the shared Edge-flow occupancy budget. The
    ``channel_salt`` decorrelates each ink's deterministic phase while every
    ink still samples the same path coordinates.
    """
    runs = []
    current = []
    bridge = max(0.0, float(bridge_mm))
    ink_flags = []
    cumulative = [0.0]
    for first, second in zip(points, points[1:]):
        cumulative.append(
            cumulative[-1]
            + math.hypot(
                second[0] - first[0],
                second[1] - first[1],
            )
        )
    for index, point in enumerate(points):
        point_tone = float(tone_at(point[0], point[1]))
        if coverage_scale is None:
            coverage = (
                min(1.0, max(0.0, point_tone))
                if layer == 0
                else min(
                    1.0,
                    max(
                        0.0,
                        (point_tone - threshold)
                        / max(1e-6, 1.0 - threshold),
                    ),
                )
            )
        else:
            coverage = min(
                1.0,
                max(0.0, point_tone)
                * max(0.0, float(coverage_scale)),
            )
        if edge_at is not None and (
            keyline_strength > 0.0 or edge_quiet > 0.0
        ):
            edge = min(1.0, max(0.0, float(edge_at(point[0], point[1]))))
            keyline = min(
                1.0,
                max(0.0, (edge - 0.30) / 0.45),
            )
            if edge_quiet > 0.0:
                coverage *= 1.0 - min(1.0, edge_quiet) * keyline
            if layer == 0 and keyline_strength > 0.0:
                coverage = max(coverage, keyline * keyline_strength)
        ink = (
            coverage > 0.0
            and _path_tone_threshold(
                cumulative[index],
                path_key,
                tone_segment,
                layer,
                channel_salt,
            )
            < float(coverage)
        )
        ink_flags.append(bool(ink))

    gap_start = None
    for index, (point, ink) in enumerate(zip(points, ink_flags)):
        if ink:
            if current and gap_start is not None:
                gap = cumulative[index] - cumulative[gap_start]
                if gap <= bridge + 1e-9:
                    current.extend(points[gap_start:index + 1])
                else:
                    runs.append(current)
                    current = [point]
            else:
                current.append(point)
            gap_start = None
        elif current and gap_start is None:
            gap_start = index

        if current and gap_start is not None:
            gap = cumulative[index] - cumulative[gap_start]
            if gap > bridge + 1e-9:
                runs.append(current)
                current = []
                gap_start = None
    if current:
        runs.append(current)
    return [
        run
        for run in runs
        if len(run) >= 2
        and sum(
            math.hypot(
                second[0] - first[0],
                second[1] - first[1],
            )
            for first, second in zip(run, run[1:])
        )
        >= minimum_length
    ]


def _coherent_ink_runs(
    points,
    channel_at,
    channels,
    threshold,
    minimum_length,
    ink_floor,
    layer_support_at=None,
    layer_support_threshold=0.0,
    edge_at=None,
    keyline_strength=0.0,
    edge_quiet=0.0,
    bridge_mm=0.0,
    hold_mm=4.0,
    mix_ratio=0.72,
):
    """Assign contiguous local ink planes along one shared streamline.

    Unlike the path-local stochastic tone gate, this helper smooths each
    channel's coverage along arc length and keeps membership continuous. A
    second ink is retained only when it is close enough to the dominant tone to
    read as part of the same color plane.
    """
    if len(points) < 2:
        return {}

    channel_names = tuple(channels)
    if not channel_names:
        return {}
    cumulative = [0.0]
    for first, second in zip(points, points[1:]):
        cumulative.append(
            cumulative[-1]
            + math.hypot(second[0] - first[0], second[1] - first[1])
        )

    samples = {channel: [] for channel in channel_names}
    keyline_values = []
    for x, y in points:
        keyline = 0.0
        if edge_at is not None and (
            keyline_strength > 0.0 or edge_quiet > 0.0
        ):
            keyline = min(
                1.0,
                max(
                    0.0,
                    (
                        float(edge_at(x, y))
                        - EDGE_FLOW_KEYLINE_LOW
                    )
                    / (EDGE_FLOW_KEYLINE_HIGH - EDGE_FLOW_KEYLINE_LOW),
                ),
            )
        keyline_values.append(keyline)
        for channel in channel_names:
            value = min(
                1.0,
                max(0.0, float(channel_at[channel](x, y))),
            )
            if channel != "k" and edge_quiet > 0.0:
                value *= 1.0 - min(1.0, float(edge_quiet)) * keyline
            if channel == "k" and keyline_strength > 0.0:
                value *= EDGE_FLOW_KEYLINE_BASE_WEIGHT
                value = max(
                    value,
                    keyline * min(1.0, float(keyline_strength)),
                )
            samples[channel].append(value)

    half_window = max(0.25, float(hold_mm) * 0.5)
    smoothed = {}
    for channel in channel_names:
        values = samples[channel]
        prefix = [0.0]
        for value in values:
            prefix.append(prefix[-1] + value)
        channel_values = []
        for index in range(len(points)):
            low = bisect.bisect_left(
                cumulative,
                cumulative[index] - half_window,
            )
            high = bisect.bisect_right(
                cumulative,
                cumulative[index] + half_window,
            )
            count = max(1, high - low)
            channel_values.append(
                (prefix[high] - prefix[low]) / count
            )
        smoothed[channel] = channel_values

    active_floor = max(float(ink_floor), float(threshold))
    flags = {channel: [False] * len(points) for channel in channel_names}
    for index in range(len(points)):
        if (
            layer_support_at is not None
            and float(layer_support_at(*points[index]))
            < float(layer_support_threshold)
        ):
            continue
        scores = {
            channel: smoothed[channel][index]
            for channel in channel_names
        }
        strongest = max(scores.values(), default=0.0)
        if strongest < active_floor:
            continue
        primary = max(channel_names, key=scores.get)
        for channel in channel_names:
            score = scores[channel]
            if score >= active_floor and (
                channel == primary
                or score >= strongest * max(0.0, float(mix_ratio))
            ):
                flags[channel][index] = True

    bridge = max(0.0, float(bridge_mm))
    runs = {}
    for channel in channel_names:
        channel_flags = flags[channel]
        index = 0
        while index < len(channel_flags):
            if not channel_flags[index]:
                gap_start = index
                while index < len(channel_flags) and not channel_flags[index]:
                    index += 1
                if (
                    0 < gap_start
                    and index < len(channel_flags)
                    and cumulative[index] - cumulative[gap_start] <= bridge
                ):
                    for fill in range(gap_start, index):
                        channel_flags[fill] = True
                continue
            start = index
            while index < len(channel_flags) and channel_flags[index]:
                index += 1
            end = index
            if end - start < 2:
                continue
            run = points[start:end]
            run_length = sum(
                math.hypot(second[0] - first[0], second[1] - first[1])
                for first, second in zip(run, run[1:])
            )
            if run_length >= minimum_length:
                runs.setdefault(channel, []).append(run)
    return runs


def trace_structure_streamlines(
    guide,
    geometry,
    spacing,
    fallback_angle_deg,
    layers,
    max_marks,
    pen_diameter_mm,
    path_tolerance_mm,
    smoothing_mm,
    seed,
    ink_floor,
    tone_at,
    support_at=None,
    pitch_compression=0.0,
    keylines=False,
    color_quiet=0.0,
    tone_segment_mm=None,
    max_path_mm=None,
    bridge_mm=0.0,
    cancel_check=None,
):
    """Trace evenly spaced streamlines through one tone-derived tensor.

    ``layers`` is the maximum number of overlapping streamline networks. Each
    network owns an equal part of the ink's tone range, and a deterministic
    path-local threshold keeps only the fraction of each traced path that the
    local tone asks for. The break positions depend on distance along that
    streamline, so adjacent paths do not form a visible block matrix.
    ``support_at`` controls whether the form continues through a local colour
    gap; ``tone_at`` still decides which parts of that path receive this ink.
    ``pitch_compression`` reduces the spacing between neighbouring streamlines
    continuously as local ink tone approaches full darkness. It is normalized
    from 0 (fixed pitch) to 1 (maximum compression).
    ``bridge_mm`` retains short tone-off gaps inside one pen-down run so the
    local screen does not multiply toolhead cycles in dense passages.
    """
    import numpy as np

    left = float(geometry["off_x"])
    top = float(geometry["off_y"])
    right = left + float(geometry["width_mm"])
    bottom = top + float(geometry["height_mm"])
    area = max(1e-6, (right - left) * (bottom - top))
    layer_count = max(1, min(6, int(layers)))
    cap = max(16, int(max_marks))
    # A seed is only a candidate: occupancy merges many of them into a long
    # streamline and the actual mark count is checked below. Budget several
    # candidates per allowed mark so the UI's fine pitch is not silently
    # coarsened on large pages before tracing has a chance to merge them.
    seed_cap = max(32, (cap * 8) // layer_count)
    base_pitch = max(float(spacing), math.sqrt(area / max(1, seed_cap)))
    velocity_x, velocity_y, edge_field, field_geometry = (
        _structure_tensor_velocity(
            guide,
            geometry,
            max(0.1, float(smoothing_mm)),
            fallback_angle_deg,
        )
    )
    field_w = max(1, int(field_geometry["pixels_w"]))
    field_h = max(1, int(field_geometry["pixels_h"]))
    pixel_x = field_geometry["width_mm"] / field_w
    pixel_y = field_geometry["height_mm"] / field_h
    pixel_mm = max(1e-6, 0.5 * (pixel_x + pixel_y))
    step_mm = max(
        pixel_mm * 0.72,
        min(base_pitch * 0.28, max(0.10, float(path_tolerance_mm) * 1.8)),
    )
    minimum_pen_gap = (
        max(0.0, float(pen_diameter_mm))
        * EDGE_FLOW_MIN_PITCH_PEN_RATIO
    )
    minimum_length = max(1.0, base_pitch * 0.45)
    tone_segment = (
        max(0.8, min(8.0, float(tone_segment_mm)))
        if tone_segment_mm is not None
        else max(
            4.0,
            min(
                8.0,
                max(
                    base_pitch * 3.0,
                    max(0.0, float(pen_diameter_mm)) * 3.0,
                ),
            ),
        )
    )
    visible_minimum_length = max(
        0.5,
        min(
            2.5,
            max(
                minimum_length,
                max(0.0, float(pen_diameter_mm)) * 0.75,
            ),
        ),
    )
    maximum_steps = max(
        32,
        min(4000, int((right - left + bottom - top) / step_mm)),
    )

    def sample_velocity(x, y):
        return _bilinear_velocity(velocity_x, velocity_y, field_geometry, x, y)

    def sample_edge(x, y):
        return _bilinear_scalar(edge_field, field_geometry, x, y)

    def field_cell(x, y):
        ix = int((x - left) / max(1e-8, right - left) * field_w)
        iy = int((y - top) / max(1e-8, bottom - top) * field_h)
        return max(0, min(field_w - 1, ix)), max(0, min(field_h - 1, iy))

    path_limit = (
        max(0.1, float(max_path_mm)) * 0.5
        if max_path_mm is not None
        else None
    )

    support_sampler = tone_at if support_at is None else support_at
    pitch_sampler = lambda x, y: _edge_flow_local_pitch(
        base_pitch,
        tone_at(x, y),
        pen_diameter_mm,
        pitch_compression,
    )

    def trace(direction, start_x, start_y, threshold, occupied):
        points = []
        x, y = start_x, start_y
        traveled = 0.0
        for _ in range(maximum_steps):
            vx, vy = sample_velocity(x, y)
            if abs(vx) + abs(vy) < 1e-6:
                break
            mid_x = x + direction * vx * step_mm * 0.5
            mid_y = y + direction * vy * step_mm * 0.5
            mx, my = sample_velocity(mid_x, mid_y)
            if abs(mx) + abs(my) < 1e-6:
                mx, my = vx, vy
            next_x = x + direction * mx * step_mm
            next_y = y + direction * my * step_mm
            traveled += math.hypot(next_x - x, next_y - y)
            x, y = next_x, next_y
            if not (left <= x <= right and top <= y <= bottom):
                break
            if support_sampler(x, y) < max(float(ink_floor), threshold):
                break
            ix, iy = field_cell(x, y)
            if occupied[iy, ix]:
                break
            points.append((x, y))
            if path_limit is not None and traveled >= path_limit:
                break
        return points

    marks = []
    for layer in range(layer_count):
        check_cancelled(cancel_check)
        # Layer zero covers the open-paper end of the tonal range. Deeper
        # layers take progressively darker bands, so their density grows only
        # after the previous network has reached full coverage.
        threshold = 0.0 if layer == 0 else float(layer) / layer_count
        occupied = np.zeros((field_h, field_w), dtype=bool)
        queued = np.zeros((field_h, field_w), dtype=bool)
        pending = deque()
        phase_x = (float(seed) + 0.61803398875 * (layer + 1)) % 1.0
        phase_y = (float(seed) * 0.377 + 0.75487766625 * (layer + 1)) % 1.0
        x0 = left + phase_x * base_pitch
        y0 = top + phase_y * base_pitch

        def reserve_path(points):
            """Reserve each point with its local pen-safe separation."""
            for px, py in points:
                local_pitch = pitch_sampler(px, py)
                separation = max(
                    minimum_pen_gap,
                    local_pitch * (0.72 if layer else 0.58),
                )
                radius = max(
                    1,
                    int(
                        math.ceil(
                            separation / max(pixel_x, pixel_y)
                        )
                    ),
                )
                cx, cy = field_cell(px, py)
                xlo = max(0, cx - radius)
                xhi = min(field_w, cx + radius + 1)
                ylo = max(0, cy - radius)
                yhi = min(field_h, cy + radius + 1)
                occupied[ylo:yhi, xlo:xhi] = True

        def enqueue_neighbour(seed_x, seed_y):
            if (
                not (left <= seed_x <= right and top <= seed_y <= bottom)
                or support_sampler(seed_x, seed_y)
                < max(float(ink_floor), threshold)
            ):
                return
            sx, sy = field_cell(seed_x, seed_y)
            if occupied[sy, sx] or queued[sy, sx]:
                return
            queued[sy, sx] = True
            pending.append((seed_x, seed_y))

        def queue_neighbours(points):
            """Seed parallel streamlines at the local compressed pitch."""
            traveled = 0.0
            next_seed = 0.0
            for first, second in zip(points, points[1:]):
                traveled += math.hypot(
                    second[0] - first[0],
                    second[1] - first[1],
                )
                if traveled < next_seed:
                    continue
                local_pitch = pitch_sampler(first[0], first[1])
                vx, vy = sample_velocity(first[0], first[1])
                norm = math.hypot(vx, vy)
                if norm <= 1e-8:
                    continue
                normal_x = -vy / norm
                normal_y = vx / norm
                for direction in (-1.0, 1.0):
                    enqueue_neighbour(
                        first[0] + direction * normal_x * local_pitch,
                        first[1] + direction * normal_y * local_pitch,
                    )
                next_seed = traveled + max(
                    step_mm * 4.0,
                    minimum_pen_gap,
                    local_pitch * 0.65,
                )

        def try_candidate(start_x, start_y):
            """Trace and emit one candidate, then fill its neighbourhood."""
            if (
                support_sampler(start_x, start_y)
                < max(float(ink_floor), threshold)
            ):
                return False
            ix, iy = field_cell(start_x, start_y)
            if occupied[iy, ix]:
                return False

            back = trace(-1.0, start_x, start_y, threshold, occupied)
            forward = trace(1.0, start_x, start_y, threshold, occupied)
            points = (
                list(reversed(back))
                + [(start_x, start_y)]
                + forward
            )
            length = sum(
                math.hypot(
                    second[0] - first[0],
                    second[1] - first[1],
                )
                for first, second in zip(points, points[1:])
            )
            accepted = len(points) >= 3 and length >= minimum_length
            if accepted:
                path_key = (
                    int(round((start_x - left) / base_pitch)) * 73856093
                    ^ int(round((start_y - top) / base_pitch)) * 19349663
                    ^ int(seed) * 83492791
                    ^ int(layer) * 2654435761
                ) & 0xFFFFFFFF
                visible_runs = _tone_gated_runs(
                    points,
                    tone_at,
                    threshold,
                    tone_segment,
                    path_key,
                    layer,
                    visible_minimum_length,
                    (
                        sample_edge
                        if keylines or color_quiet > 0.0
                        else None
                    ),
                    0.92 if keylines else 0.0,
                    color_quiet,
                    bridge_mm,
                )
                marks.extend(visible_runs)
                if len(marks) > cap:
                    del marks[cap:]

            # Reserve even a short path so a later seed cannot duplicate it.
            reserve_path(points)
            if accepted and float(pitch_compression) > 0.0:
                queue_neighbours(points)
            return accepted

        y = y0
        row = 0
        while y <= bottom and len(marks) < cap:
            check_cancelled(cancel_check)
            x = x0 + (0.5 * base_pitch if row % 2 else 0.0)
            while x <= right and len(marks) < cap:
                try_candidate(x, y)
                while pending and len(marks) < cap:
                    next_x, next_y = pending.popleft()
                    try_candidate(next_x, next_y)
                x += pitch_sampler(x, y)
            y += base_pitch
            row += 1

    return marks


def trace_shared_structure_streamlines(
    guide,
    tones,
    geometry,
    spacing,
    fallback_angle_deg,
    layers,
    max_marks,
    pen_diameter_mm,
    path_tolerance_mm,
    smoothing_mm,
    seed,
    ink_floor,
    channels,
    keylines=False,
    color_quiet=0.0,
    tone_segment_mm=None,
    max_path_mm=None,
    bridge_mm=0.0,
    pitch_compression=0.0,
    color_mode="phase",
    fallback_angles_deg=None,
    color_hold_mm=4.0,
    color_mix_ratio=0.72,
    dark_layer_start=EDGE_FLOW_DARK_LAYER_START,
    dark_layer_end=EDGE_FLOW_DARK_LAYER_END,
    cancel_check=None,
):
    """Trace one common streamline network and gate every ink along it.

    The geometry is generated once from the maximum channel coverage, so each
    path has one position and direction for all process inks. Per-channel tone
    still decides which arc-length segments receive each ink. Independent
    deterministic phases prevent similar tone fields from selecting the exact
    same segments and turning every shared path into four-ink black. The shared
    coordinates still permit local process-colour mixtures where ink segments
    coincide, without returning to four independent, drifting path networks.
    ``pitch_compression`` contracts neighbouring common paths as the strongest
    local ink coverage darkens.

    ``color_mode="coherent"`` replaces stochastic per-channel arc-length gates
    with contiguous local ink planes. Ordinary shared mode keeps its established
    phase-gated behavior. ``fallback_angles_deg`` optionally gives each density
    layer its own fixed screen direction where the image field is weak.
    ``dark_layer_start`` and ``dark_layer_end`` place the first extra and final
    coherent scene-depth layers; layer zero always carries the base network.
    """
    import numpy as np

    channel_names = tuple(channels)
    if not channel_names:
        return {}
    left = float(geometry["off_x"])
    top = float(geometry["off_y"])
    right = left + float(geometry["width_mm"])
    bottom = top + float(geometry["height_mm"])
    area = max(1e-6, (right - left) * (bottom - top))
    layer_count = max(1, min(6, int(layers)))
    cap = max(16, int(max_marks))
    seed_cap = max(32, (cap * 8) // layer_count)
    base_pitch = max(float(spacing), math.sqrt(area / max(1, seed_cap)))
    # Shared layers reuse one path network instead of four independent ones.
    # Normalize the per-channel occupancy and salt each phase so similar tones
    # do not select the same arc lengths. Auto uses this same area factor, so
    # its estimate reflects the sparse stroke geometry instead of raw tone.
    shared_coverage_scale = edge_flow_coverage_factor(
        pen_diameter_mm,
        base_pitch,
        layer_count,
    )
    channel_salts = {
        channel: index + 1
        for index, channel in enumerate(channel_names)
    }
    coverage_field = np.maximum.reduce(
        [np.asarray(tones[channel], dtype=np.float32) for channel in channel_names]
    )
    coverage_at = lambda x, y: _bilinear_scalar(
        coverage_field,
        geometry,
        x,
        y,
    )
    layer_support_field = np.asarray(
        tones.get("depth", coverage_field),
        dtype=np.float32,
    )
    layer_support_at = lambda x, y: _bilinear_scalar(
        layer_support_field,
        geometry,
        x,
        y,
    )
    channel_at = {
        channel: (
            lambda x, y, field=np.asarray(
                tones[channel],
                dtype=np.float32,
            ): _bilinear_scalar(field, geometry, x, y)
        )
        for channel in channel_names
    }

    coherent_color = str(color_mode).strip().lower() == "coherent"
    shadow_start = min(
        0.98,
        max(0.0, float(dark_layer_start)),
    )
    shadow_end = min(
        1.0,
        max(shadow_start + 1.0e-6, float(dark_layer_end)),
    )
    fallback_angles = (
        tuple(float(value) for value in fallback_angles_deg)
        if fallback_angles_deg is not None
        else (float(fallback_angle_deg),)
    )
    if not fallback_angles:
        fallback_angles = (float(fallback_angle_deg),)
    tangent_x, tangent_y, edge_field, keyline_field, field_geometry = (
        _structure_tensor_components(
            guide,
            geometry,
            max(0.1, float(smoothing_mm)),
        )
    )
    velocity_x, velocity_y = _blend_structure_velocity(
        tangent_x,
        tangent_y,
        edge_field,
        fallback_angles[0],
    )
    field_w = max(1, int(field_geometry["pixels_w"]))
    field_h = max(1, int(field_geometry["pixels_h"]))
    pixel_x = field_geometry["width_mm"] / field_w
    pixel_y = field_geometry["height_mm"] / field_h
    pixel_mm = max(1e-6, 0.5 * (pixel_x + pixel_y))
    step_mm = max(
        pixel_mm * 0.72,
        min(base_pitch * 0.28, max(0.10, float(path_tolerance_mm) * 1.8)),
    )
    minimum_pen_gap = (
        max(0.0, float(pen_diameter_mm))
        * EDGE_FLOW_MIN_PITCH_PEN_RATIO
    )
    minimum_length = max(1.0, base_pitch * 0.45)
    tone_segment = (
        max(0.8, min(8.0, float(tone_segment_mm)))
        if tone_segment_mm is not None
        else max(
            4.0,
            min(
                8.0,
                max(
                    base_pitch * 3.0,
                    max(0.0, float(pen_diameter_mm)) * 3.0,
                ),
            ),
        )
    )
    visible_minimum_length = max(
        0.5,
        min(
            2.5,
            max(
                minimum_length,
                max(0.0, float(pen_diameter_mm)) * 0.75,
            ),
        ),
    )
    maximum_steps = max(
        32,
        min(4000, int((right - left + bottom - top) / step_mm)),
    )

    def sample_velocity(x, y):
        return _bilinear_velocity(velocity_x, velocity_y, field_geometry, x, y)

    def sample_edge(x, y):
        return _bilinear_scalar(edge_field, field_geometry, x, y)

    def sample_keyline(x, y):
        return _bilinear_scalar(keyline_field, field_geometry, x, y)

    def field_cell(x, y):
        ix = int((x - left) / max(1e-8, right - left) * field_w)
        iy = int((y - top) / max(1e-8, bottom - top) * field_h)
        return max(0, min(field_w - 1, ix)), max(0, min(field_h - 1, iy))

    path_limit = (
        max(0.1, float(max_path_mm)) * 0.5
        if max_path_mm is not None
        else None
    )

    def trace(direction, start_x, start_y, threshold, occupied):
        points = []
        x, y = start_x, start_y
        traveled = 0.0
        for _ in range(maximum_steps):
            vx, vy = sample_velocity(x, y)
            if abs(vx) + abs(vy) < 1e-6:
                break
            mid_x = x + direction * vx * step_mm * 0.5
            mid_y = y + direction * vy * step_mm * 0.5
            mx, my = sample_velocity(mid_x, mid_y)
            if abs(mx) + abs(my) < 1e-6:
                mx, my = vx, vy
            next_x = x + direction * mx * step_mm
            next_y = y + direction * my * step_mm
            traveled += math.hypot(next_x - x, next_y - y)
            x, y = next_x, next_y
            if not (left <= x <= right and top <= y <= bottom):
                break
            support_threshold = (
                float(ink_floor)
                if coherent_color
                else max(float(ink_floor), threshold)
            )
            if coverage_at(x, y) < support_threshold:
                break
            ix, iy = field_cell(x, y)
            if occupied[iy, ix]:
                break
            points.append((x, y))
            if path_limit is not None and traveled >= path_limit:
                break
        return points

    pitch_tone_at = (
        layer_support_at
        if coherent_color
        else coverage_at
    )
    pitch_sampler = lambda x, y: _edge_flow_local_pitch(
        base_pitch,
        pitch_tone_at(x, y),
        pen_diameter_mm,
        pitch_compression,
    )

    marks = {channel: [] for channel in channel_names}
    path_count = 0
    for layer in range(layer_count):
        check_cancelled(cancel_check)
        velocity_x, velocity_y = _blend_structure_velocity(
            tangent_x,
            tangent_y,
            edge_field,
            fallback_angles[layer % len(fallback_angles)],
        )
        threshold = (
            0.0
            if layer == 0
            else (
                shadow_start
                + (
                    shadow_end
                    - shadow_start
                )
                * (layer - 1)
                / max(1, layer_count - 1)
            )
        )
        occupied = np.zeros((field_h, field_w), dtype=bool)
        queued = np.zeros((field_h, field_w), dtype=bool)
        pending = deque()
        phase_x = (float(seed) + 0.61803398875 * (layer + 1)) % 1.0
        phase_y = (float(seed) * 0.377 + 0.75487766625 * (layer + 1)) % 1.0
        x0 = left + phase_x * base_pitch
        y0 = top + phase_y * base_pitch

        def reserve_path(points):
            for px, py in points:
                local_pitch = pitch_sampler(px, py)
                separation = max(
                    minimum_pen_gap,
                    local_pitch * (0.72 if layer else 0.58),
                )
                radius = max(
                    1,
                    int(
                        math.ceil(
                            separation / max(pixel_x, pixel_y)
                        )
                    ),
                )
                cx, cy = field_cell(px, py)
                xlo = max(0, cx - radius)
                xhi = min(field_w, cx + radius + 1)
                ylo = max(0, cy - radius)
                yhi = min(field_h, cy + radius + 1)
                occupied[ylo:yhi, xlo:xhi] = True

        def enqueue_neighbour(seed_x, seed_y):
            if (
                not (left <= seed_x <= right and top <= seed_y <= bottom)
                or coverage_at(seed_x, seed_y)
                < max(float(ink_floor), threshold)
                or (
                    coherent_color
                    and layer_support_at(seed_x, seed_y) < threshold
                )
            ):
                return
            sx, sy = field_cell(seed_x, seed_y)
            if occupied[sy, sx] or queued[sy, sx]:
                return
            queued[sy, sx] = True
            pending.append((seed_x, seed_y))

        def queue_neighbours(points):
            traveled = 0.0
            next_seed = 0.0
            for first, second in zip(points, points[1:]):
                traveled += math.hypot(
                    second[0] - first[0],
                    second[1] - first[1],
                )
                if traveled < next_seed:
                    continue
                local_pitch = pitch_sampler(first[0], first[1])
                vx, vy = sample_velocity(first[0], first[1])
                norm = math.hypot(vx, vy)
                if norm <= 1e-8:
                    continue
                normal_x = -vy / norm
                normal_y = vx / norm
                for direction in (-1.0, 1.0):
                    enqueue_neighbour(
                        first[0] + direction * normal_x * local_pitch,
                        first[1] + direction * normal_y * local_pitch,
                    )
                next_seed = traveled + max(
                    step_mm * 4.0,
                    minimum_pen_gap,
                    local_pitch * 0.65,
                )

        def try_candidate(start_x, start_y):
            nonlocal path_count
            if (
                coverage_at(start_x, start_y)
                < max(float(ink_floor), threshold)
                or (
                    coherent_color
                    and layer_support_at(start_x, start_y) < threshold
                )
            ):
                return False
            ix, iy = field_cell(start_x, start_y)
            if occupied[iy, ix]:
                return False

            back = trace(-1.0, start_x, start_y, threshold, occupied)
            forward = trace(1.0, start_x, start_y, threshold, occupied)
            points = (
                list(reversed(back))
                + [(start_x, start_y)]
                + forward
            )
            length = sum(
                math.hypot(
                    second[0] - first[0],
                    second[1] - first[1],
                )
                for first, second in zip(points, points[1:])
            )
            accepted = len(points) >= 3 and length >= minimum_length
            if accepted:
                if coherent_color:
                    visible = _coherent_ink_runs(
                        points,
                        channel_at,
                        channel_names,
                        threshold,
                        visible_minimum_length,
                        ink_floor,
                        layer_support_at if coherent_color else None,
                        threshold if coherent_color else 0.0,
                        sample_keyline,
                        0.86 if keylines else 0.0,
                        color_quiet,
                        bridge_mm,
                        color_hold_mm,
                        color_mix_ratio,
                    )
                    for channel in channel_names:
                        marks[channel].extend(visible.get(channel, []))
                        if len(marks[channel]) > cap:
                            del marks[channel][cap:]
                else:
                    path_key = (
                        int(round((start_x - left) / base_pitch)) * 73856093
                        ^ int(round((start_y - top) / base_pitch)) * 19349663
                        ^ int(seed) * 83492791
                        ^ int(layer) * 2654435761
                    ) & 0xFFFFFFFF
                    for channel in channel_names:
                        quiet = (
                            min(1.0, max(0.0, float(color_quiet)))
                            if channel != "k"
                            else 0.0
                        )
                        visible_runs = _tone_gated_runs(
                            points,
                            channel_at[channel],
                            threshold,
                            tone_segment,
                            path_key,
                            layer,
                            visible_minimum_length,
                            (
                                sample_edge
                                if (keylines and channel == "k") or quiet > 0.0
                                else None
                            ),
                            0.92 if keylines and channel == "k" else 0.0,
                            quiet,
                            bridge_mm,
                            shared_coverage_scale,
                            channel_salts[channel],
                        )
                        marks[channel].extend(visible_runs)
                        if len(marks[channel]) > cap:
                            del marks[channel][cap:]
                path_count += 1

            reserve_path(points)
            if accepted and float(pitch_compression) > 0.0:
                queue_neighbours(points)
            return accepted

        y = y0
        row = 0
        while y <= bottom and path_count < cap:
            check_cancelled(cancel_check)
            x = x0 + (0.5 * base_pitch if row % 2 else 0.0)
            while x <= right and path_count < cap:
                try_candidate(x, y)
                while pending and path_count < cap:
                    next_x, next_y = pending.popleft()
                    try_candidate(next_x, next_y)
                x += pitch_sampler(x, y)
            y += base_pitch
            row += 1

    return marks
