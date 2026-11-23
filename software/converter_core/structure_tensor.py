"""Edge-following streamline screening for photograph-derived CMYK plates.

The caller supplies one guide image: gradients form a structure tensor, the
tensor is blurred, and its edge-tangent eigenvector becomes a smooth
orientation field. Coherence and tensor strength blend that field toward the
plate's fixed screen angle in weak or flat areas. CMYK plates share the
luminance guide but keep independent tone networks and screen directions.
"""

from __future__ import annotations

import math

from .cancellation import check_cancelled


EDGE_FLOW_CHROMA_WEIGHT = 0.35
# Tensor trace is the squared gradient energy. Below this floor the guide is
# noise or broad tone, not a form boundary that should redirect every screen.
EDGE_FLOW_STRENGTH_SCALE_FLOOR = 1.0e-4


def _path_tone_threshold(distance_mm, path_key, segment_mm, layer):
    """Stable tone threshold at one position along a single streamline."""
    segment_mm = max(1e-6, float(segment_mm))
    segment = int(math.floor(max(0.0, float(distance_mm)) / segment_mm))
    value = (
        segment * 374761393
        + int(path_key) * 668265263
        + int(layer) * 3266489917
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
        return np.asarray(guide, dtype=np.float32), dict(geometry)

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


def _structure_tensor_velocity(guide, geometry, smoothing_mm, fallback_angle_deg):
    """Return edge-following vectors and edge confidence for one field."""
    import numpy as np

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
        raise ValueError("Structure guide must be a 2D or channel-last image.")

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
            float(np.percentile(positive_trace, 85)),
        )
        if positive_trace.size
        else EDGE_FLOW_STRENGTH_SCALE_FLOOR
    )
    strength_floor = strength_scale * 0.08
    strength = np.clip(
        (trace - strength_floor)
        / max(1e-8, strength_scale - strength_floor),
        0.0,
        1.0,
    )

    cos_twice = np.clip(delta / safe_root, -1.0, 1.0)
    sin_twice = np.clip(2.0 * jxy / safe_root, -1.0, 1.0)
    sin_phi = np.sqrt(np.clip((1.0 - cos_twice) * 0.5, 0.0, 1.0))
    sin_phi = np.where(sin_twice < 0.0, -sin_phi, sin_phi)
    cos_phi = np.sqrt(np.clip((1.0 + cos_twice) * 0.5, 0.0, 1.0))

    fallback_radians = math.radians(float(fallback_angle_deg))
    fallback_x = math.cos(fallback_radians)
    fallback_y = math.sin(fallback_radians)
    coherence_gate = np.clip((coherence - 0.10) / 0.25, 0.0, 1.0)
    guided = coherence_gate * strength
    velocity_x = guided * (-sin_phi) + (1.0 - guided) * fallback_x
    velocity_y = guided * cos_phi + (1.0 - guided) * fallback_y
    norm = np.maximum(np.hypot(velocity_x, velocity_y), 1e-8)
    return (
        (velocity_x / norm).astype(np.float32),
        (velocity_y / norm).astype(np.float32),
        guided.astype(np.float32),
        field_geometry,
    )


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
):
    """Split one traced path into local tone and optional keyline runs."""
    runs = []
    current = []
    distance = 0.0
    for index, point in enumerate(points):
        point_tone = float(tone_at(point[0], point[1]))
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
                distance,
                path_key,
                tone_segment,
                layer,
            )
            < float(coverage)
        )
        if ink:
            current.append(point)
        elif current:
            runs.append(current)
            current = []
        if index + 1 < len(points):
            distance += math.hypot(
                points[index + 1][0] - point[0],
                points[index + 1][1] - point[1],
            )
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
    keylines=False,
    color_quiet=0.0,
    tone_segment_mm=None,
    max_path_mm=None,
    cancel_check=None,
):
    """Trace evenly spaced streamlines through one tone-derived tensor.

    ``layers`` is the maximum number of overlapping streamline networks. Each
    network owns an equal part of the ink's tone range, and a deterministic
    path-local threshold keeps only the fraction of each traced path that the
    local tone asks for. The break positions depend on distance along that
    streamline, so adjacent paths do not form a visible block matrix.
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
    minimum_pen_gap = max(0.0, float(pen_diameter_mm)) * 0.72
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
            if tone_at(x, y) < max(float(ink_floor), threshold):
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
        separation = max(
            minimum_pen_gap,
            base_pitch * (0.72 if layer else 0.58),
        )
        radius = max(1, int(math.ceil(separation / max(pixel_x, pixel_y))))
        phase_x = (float(seed) + 0.61803398875 * (layer + 1)) % 1.0
        phase_y = (float(seed) * 0.377 + 0.75487766625 * (layer + 1)) % 1.0
        x0 = left + phase_x * base_pitch
        y0 = top + phase_y * base_pitch

        y = y0
        row = 0
        while y <= bottom and len(marks) < cap:
            check_cancelled(cancel_check)
            x = x0 + (0.5 * base_pitch if row % 2 else 0.0)
            while x <= right and len(marks) < cap:
                if tone_at(x, y) < max(float(ink_floor), threshold):
                    x += base_pitch
                    continue
                ix, iy = field_cell(x, y)
                if occupied[iy, ix]:
                    x += base_pitch
                    continue

                back = trace(-1.0, x, y, threshold, occupied)
                forward = trace(1.0, x, y, threshold, occupied)
                points = list(reversed(back)) + [(x, y)] + forward
                length = sum(
                    math.hypot(
                        second[0] - first[0],
                        second[1] - first[1],
                    )
                    for first, second in zip(points, points[1:])
                )
                if len(points) >= 3 and length >= minimum_length:
                    path_key = (
                        int(round((x - left) / base_pitch)) * 73856093
                        ^ int(round((y - top) / base_pitch)) * 19349663
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
                    )
                    marks.extend(visible_runs)
                    if len(marks) > cap:
                        del marks[cap:]

                # Reserve the path so later seeds in this plate cannot place a
                # neighbouring duplicate within one pen envelope.
                for px, py in points:
                    cx, cy = field_cell(px, py)
                    xlo = max(0, cx - radius)
                    xhi = min(field_w, cx + radius + 1)
                    ylo = max(0, cy - radius)
                    yhi = min(field_h, cy + radius + 1)
                    occupied[ylo:yhi, xlo:xhi] = True
                x += base_pitch
            y += base_pitch
            row += 1

    return marks
