"""Kaleidoscope designs: trace a source, then mirror it into N sectors.

This is the whole "kaleidoscope converter" core. It deliberately does *not*
plan motion: it produces ordinary contours so the existing converter pipeline
(`plan_program`, `contours_to_gcode`, the polar planner, the fill and the
preview) can be reused unchanged.

The construction is the classic mirror kaleidoscope:

1. the source is centred on the origin and scaled once,
2. every contour is clipped to a half-wedge of ``180 / divisions`` degrees,
3. that half-wedge is placed ``2 * divisions`` times around the circle,
   alternating mirrored copies, which tiles 360 degrees exactly.

Set ``mirror=False`` to repeat the half-wedge without reflecting it, which
gives a pinwheel look instead of a mirror symmetry.
"""

from __future__ import annotations

import math

from .cancellation import check_cancelled
from .geometry import contour_bounds, distance

RASTER_SUFFIXES = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff", ".webp")


def is_raster_source(path):
    """True when *path* is an image the tracer can read."""
    return str(path).lower().endswith(RASTER_SUFFIXES)


def simplify(points, tolerance):
    """Douglas-Peucker simplify, iterative so long contours cannot recurse."""
    tolerance = max(float(tolerance), 0.0)
    if tolerance <= 0.0 or len(points) < 3:
        return list(points)
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        first, last = stack.pop()
        if last <= first + 1:
            continue
        x1, y1 = points[first]
        x2, y2 = points[last]
        dx, dy = x2 - x1, y2 - y1
        norm = math.hypot(dx, dy)
        best = -1.0
        best_index = -1
        for index in range(first + 1, last):
            x, y = points[index]
            if norm <= 1e-12:
                deviation = math.hypot(x - x1, y - y1)
            else:
                deviation = abs(dy * (x - x1) - dx * (y - y1)) / norm
            if deviation > best:
                best = deviation
                best_index = index
        if best > tolerance and best_index > 0:
            keep[best_index] = True
            stack.append((first, best_index))
            stack.append((best_index, last))
    return [point for point, kept in zip(points, keep) if kept]


def _marching_squares(mask):
    """Boundary polylines of a boolean mask, in pixel units (y grows down).

    Only cells that straddle the boundary are visited, so cost scales with the
    outline length rather than with the image area.
    """
    import numpy as np

    grid = np.asarray(mask, dtype=bool)
    if grid.ndim != 2 or grid.size == 0:
        return []
    padded = np.zeros((grid.shape[0] + 2, grid.shape[1] + 2), dtype=bool)
    padded[1:-1, 1:-1] = grid
    top = padded[:-1, :-1]
    top_right = padded[:-1, 1:]
    bottom_left = padded[1:, :-1]
    bottom_right = padded[1:, 1:]
    corners = top.astype(np.uint8) | (top_right.astype(np.uint8) << 1)
    corners |= bottom_left.astype(np.uint8) << 3
    corners |= bottom_right.astype(np.uint8) << 2
    active = (corners != 0) & (corners != 15)
    rows, cols = np.nonzero(active)

    segments = []
    for row, col in zip(rows.tolist(), cols.tolist()):
        case = int(corners[row, col])
        # Edge midpoints of this cell, in the source pixel frame.
        north = (col - 1 + 0.5, row - 1)
        east = (col - 1 + 1.0, row - 1 + 0.5)
        south = (col - 1 + 0.5, row - 1 + 1.0)
        west = (col - 1, row - 1 + 0.5)
        table = {
            1: ((west, north),),
            2: ((north, east),),
            3: ((west, east),),
            4: ((east, south),),
            5: ((west, north), (east, south)),
            6: ((north, south),),
            7: ((west, south),),
            8: ((south, west),),
            9: ((north, south),),
            10: ((north, east), (south, west)),
            11: ((east, south),),
            12: ((east, west),),
            13: ((north, east),),
            14: ((west, north),),
        }
        segments.extend(table.get(case, ()))
    return _link_segments(segments)


def _link_segments(segments):
    """Join marching-squares segments into polylines, closing loops."""
    from collections import defaultdict

    def key(point):
        return (round(point[0], 4), round(point[1], 4))

    adjacency = defaultdict(list)
    for index, (start, end) in enumerate(segments):
        adjacency[key(start)].append(index)
        adjacency[key(end)].append(index)
    used = [False] * len(segments)
    polylines = []
    for index in range(len(segments)):
        if used[index]:
            continue
        used[index] = True
        start, end = segments[index]
        chain = [start, end]
        while True:
            tail = key(chain[-1])
            nxt = next((i for i in adjacency[tail] if not used[i]), None)
            if nxt is None:
                break
            used[nxt] = True
            a, b = segments[nxt]
            chain.append(b if key(a) == tail else a)
        while True:
            head = key(chain[0])
            nxt = next((i for i in adjacency[head] if not used[i]), None)
            if nxt is None:
                break
            used[nxt] = True
            a, b = segments[nxt]
            chain.insert(0, b if key(a) == head else a)
        polylines.append(chain)
    return polylines


def trace_raster(
    path,
    max_side=900,
    threshold=0.5,
    invert=False,
    tolerance=0.6,
    cancel_check=None,
):
    """Trace a PNG/JPG into closed contours, in pixel units with y down.

    ``threshold`` is the darkness cut (0 = everything, 1 = nothing) and
    ``tolerance`` simplifies the traced outline in pixels. The caller flips y
    and scales the result into millimetres.
    """
    from PIL import Image
    import numpy as np

    check_cancelled(cancel_check)
    image = Image.open(path).convert("L")
    width, height = image.size
    scale = min(1.0, float(max_side) / max(width, height, 1))
    if scale < 1.0:
        image = image.resize(
            (max(1, int(width * scale)), max(1, int(height * scale))),
            Image.LANCZOS,
        )
    pixels = np.asarray(image, dtype=np.float32) / 255.0
    threshold = min(max(float(threshold), 0.0), 1.0)
    mask = pixels >= threshold if invert else pixels < threshold
    contours = []
    for chain in _marching_squares(mask):
        check_cancelled(cancel_check)
        if len(chain) < 4:
            continue
        simplified = simplify(chain, tolerance)
        if len(simplified) >= 4:
            contours.append(simplified)
    return contours


def normalize_source(contours, target_size_mm, center=None, flip_y=False):
    """Centre *contours* on the origin and scale the longer side to *target_size_mm*.

    ``center`` overrides the bounding-box centre, which is how the kaleidoscope
    apex is placed on a feature instead of on the artwork's bbox centre.
    """
    if not contours:
        return [], 1.0
    min_x, min_y, max_x, max_y = contour_bounds(contours)
    base_x = (min_x + max_x) / 2.0 if center is None else float(center[0])
    base_y = (min_y + max_y) / 2.0 if center is None else float(center[1])
    span = max(max_x - min_x, max_y - min_y, 1e-9)
    scale = max(float(target_size_mm), 1e-9) / span
    out = []
    for contour in contours:
        points = [((x - base_x) * scale, (y - base_y) * scale) for x, y in contour]
        if flip_y:
            points = [(x, -y) for x, y in points]
        out.append(points)
    return out, scale


def _clip_halfplane(points, keep):
    """Clip an open polyline to the half-plane where ``keep(point)`` is true."""
    if not points:
        return []
    pieces = []
    previous = points[0]
    previous_kept = keep(previous)
    current = [previous] if previous_kept else []
    for point in points[1:]:
        kept = keep(point)
        if kept != previous_kept:
            crossing = _boundary_point(previous, point, keep)
            if kept:
                current = [crossing, point]
            else:
                current.append(crossing)
                if len(current) >= 2:
                    pieces.append(current)
                current = []
        elif kept:
            current.append(point)
        previous = point
        previous_kept = kept
    if current and len(current) >= 2:
        pieces.append(current)
    return pieces


def _boundary_point(a, b, keep, iterations=24):
    """Bisect the crossing of ``keep`` between a kept and an unkept point."""
    lo, hi = a, b
    lo_kept = keep(lo)
    for _ in range(iterations):
        mid = ((lo[0] + hi[0]) * 0.5, (lo[1] + hi[1]) * 0.5)
        if keep(mid) == lo_kept:
            lo = mid
        else:
            hi = mid
    return lo


def clip_to_wedge(contours, wedge_deg, cancel_check=None):
    """Clip contours to the half-wedge ``0..wedge_deg`` about the origin."""
    limit = math.tan(math.radians(max(float(wedge_deg), 1e-6)))

    def upper(point):
        return point[1] >= -1e-9

    def lower(point):
        return point[1] <= point[0] * limit + 1e-9

    out = []
    for contour in contours:
        check_cancelled(cancel_check)
        for piece in _clip_halfplane(contour, upper):
            for kept in _clip_halfplane(piece, lower):
                if len(kept) >= 2:
                    out.append(list(kept))
    return out


def kaleidoscope(contours, divisions, mirror=True, angle_offset_deg=0.0, cancel_check=None):
    """Repeat the source half-wedge ``2 * divisions`` times around the origin."""
    count = max(1, int(divisions))
    wedge = 180.0 / count
    pieces = clip_to_wedge(contours, wedge, cancel_check)
    offset = float(angle_offset_deg)
    out = []
    for index in range(2 * count):
        if mirror and index % 2:
            rotated = math.radians(offset + (index + 1) * wedge)
            reflect = True
        else:
            rotated = math.radians(offset + index * wedge)
            reflect = False
        cos_a, sin_a = math.cos(rotated), math.sin(rotated)
        for piece in pieces:
            check_cancelled(cancel_check)
            points = [(x, -y) for x, y in piece] if reflect else piece
            out.append(
                [
                    (x * cos_a - y * sin_a, x * sin_a + y * cos_a)
                    for x, y in points
                ]
            )
    return out
