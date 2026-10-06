"""Shared raster helpers for the high-quality tools.

Marching-squares contour extraction, segment stitching, Douglas-Peucker
simplification, Chaikin smoothing, and Otsu thresholding. Written for this
repository; numpy is imported lazily by the callers that need it.
"""

from __future__ import annotations

import math


def _lerp(first, second, level, value_first, value_second):
    if abs(value_second - value_first) < 1e-12:
        return (first[0] + second[0]) / 2.0, (first[1] + second[1]) / 2.0
    t = (level - value_first) / (value_second - value_first)
    t = max(0.0, min(1.0, t))
    return first[0] + (second[0] - first[0]) * t, first[1] + (second[1] - first[1]) * t


def marching_squares(grid, level):
    """Return stitched contour polylines for one level (grid coordinates)."""
    import numpy as np

    values = np.asarray(grid, dtype=float)
    rows, cols = values.shape
    segments = []
    for y in range(rows - 1):
        for x in range(cols - 1):
            top_left = (x, y)
            top_right = (x + 1, y)
            bottom_right = (x + 1, y + 1)
            bottom_left = (x, y + 1)
            v0 = values[y, x]
            v1 = values[y, x + 1]
            v2 = values[y + 1, x + 1]
            v3 = values[y + 1, x]
            index = (
                (1 if v0 >= level else 0)
                | (2 if v1 >= level else 0)
                | (4 if v2 >= level else 0)
                | (8 if v3 >= level else 0)
            )
            if index in (0, 15):
                continue
            edges = {
                0: _lerp(top_left, top_right, level, v0, v1),
                1: _lerp(top_right, bottom_right, level, v1, v2),
                2: _lerp(bottom_left, bottom_right, level, v3, v2),
                3: _lerp(top_left, bottom_left, level, v0, v3),
            }
            table = {
                1: [(3, 0)],
                2: [(0, 1)],
                3: [(3, 1)],
                4: [(1, 2)],
                5: [(3, 2), (0, 1)],
                6: [(0, 2)],
                7: [(3, 2)],
                8: [(2, 3)],
                9: [(2, 0)],
                10: [(0, 1), (2, 3)],
                11: [(2, 1)],
                12: [(1, 3)],
                13: [(1, 0)],
                14: [(0, 3)],
            }
            for first_edge, second_edge in table[index]:
                segments.append((edges[first_edge], edges[second_edge]))
    return stitch_segments(segments)


def _key(point):
    return (round(point[0], 4), round(point[1], 4))


def stitch_segments(segments):
    """Chain unordered segments into polylines by matching endpoints."""
    starts = {}
    for segment in list(segments):
        starts.setdefault(_key(segment[0]), []).append(segment)
    used = set()
    polylines = []
    for segment in segments:
        if id(segment) in used:
            continue
        used.add(id(segment))
        chain = [segment[0], segment[1]]
        extended = True
        while extended:
            extended = False
            tail = _key(chain[-1])
            for candidate in starts.get(tail, ()):
                if id(candidate) in used:
                    continue
                used.add(id(candidate))
                chain.append(candidate[1])
                extended = True
                break
            if extended:
                continue
            head = _key(chain[0])
            for candidate in starts.get(head, ()):
                if id(candidate) in used:
                    continue
                used.add(id(candidate))
                chain.insert(0, candidate[1])
                extended = True
                break
        if len(chain) >= 2:
            polylines.append(chain)
    return polylines


def simplify_path(points, epsilon):
    """Douglas-Peucker simplification (iterative, depth-safe)."""
    if len(points) < 3 or epsilon <= 0:
        return list(points)
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        start, end = stack.pop()
        if end <= start + 1:
            continue
        first = points[start]
        last = points[end]
        dx = last[0] - first[0]
        dy = last[1] - first[1]
        norm = math.hypot(dx, dy) or 1.0
        worst = -1.0
        index = start
        for position in range(start + 1, end):
            px, py = points[position]
            distance = abs(
                dy * px - dx * py + last[0] * first[1] - last[1] * first[0]
            ) / norm
            if distance > worst:
                worst = distance
                index = position
        if worst > epsilon:
            keep[index] = True
            stack.append((start, index))
            stack.append((index, end))
    return [point for point, flag in zip(points, keep) if flag]


def chaikin(points, passes=1, closed=False):
    """Corner-cutting smoothing; keeps the first/last point for open paths."""
    if passes <= 0 or len(points) < 3:
        return list(points)
    result = list(points)
    for _ in range(int(passes)):
        if closed:
            source = result + [result[0]]
        else:
            source = result
        smoothed = [] if closed else [source[0]]
        for first, second in zip(source, source[1:]):
            smoothed.append(
                (
                    0.75 * first[0] + 0.25 * second[0],
                    0.75 * first[1] + 0.25 * second[1],
                )
            )
            smoothed.append(
                (
                    0.25 * first[0] + 0.75 * second[0],
                    0.25 * first[1] + 0.75 * second[1],
                )
            )
        if not closed:
            smoothed.append(source[-1])
        result = smoothed
    return result


def otsu_threshold(gray):
    """Return the Otsu threshold (0-255) for a 2D grayscale array."""
    import numpy as np

    values = np.asarray(gray, dtype=float)
    histogram, _edges = np.histogram(values, bins=256, range=(0.0, 255.0))
    total = values.size
    if not total:
        return 127.0
    sum_total = float(np.dot(np.arange(256), histogram))
    weight_background = 0.0
    sum_background = 0.0
    best_variance = -1.0
    best_threshold = 127.0
    for threshold in range(256):
        weight_background += histogram[threshold]
        if weight_background == 0:
            continue
        weight_foreground = total - weight_background
        if weight_foreground == 0:
            break
        sum_background += threshold * histogram[threshold]
        mean_background = sum_background / weight_background
        mean_foreground = (sum_total - sum_background) / weight_foreground
        variance = (
            weight_background
            * weight_foreground
            * (mean_background - mean_foreground) ** 2
        )
        if variance > best_variance:
            best_variance = variance
            best_threshold = float(threshold)
    return best_threshold
