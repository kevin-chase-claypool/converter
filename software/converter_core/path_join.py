"""Join contours whose endpoints already touch.

This is deliberately a local, conservative operation. Unlike a general
continuous-pen painter, it never connects across a meaningful white gap: the
optional tolerance only absorbs SVG rounding or a hairline separation smaller
than the configured pen.
"""

import math

from .cancellation import check_cancelled


DEFAULT_JOIN_TOLERANCE_MM = 0.02


def _grid_key(point, cell_mm):
    return (
        int(math.floor(point[0] / cell_mm)),
        int(math.floor(point[1] / cell_mm)),
    )


def _endpoint_distance(first, second):
    return math.hypot(second[0] - first[0], second[1] - first[1])


def _turn_penalty(incoming, outgoing):
    incoming_length = math.hypot(incoming[0], incoming[1])
    outgoing_length = math.hypot(outgoing[0], outgoing[1])
    if incoming_length <= 1e-12 or outgoing_length <= 1e-12:
        return 1.0
    cosine = (
        incoming[0] * outgoing[0] + incoming[1] * outgoing[1]
    ) / (incoming_length * outgoing_length)
    return 1.0 - max(-1.0, min(1.0, cosine))


def join_touching_contours(
    contours,
    tolerance_mm=DEFAULT_JOIN_TOLERANCE_MM,
    cancel_check=None,
):
    """Join untagged open contours whose endpoints touch within tolerance.

    Returns ``(joined_contours, stats)``. Wave/Fill tagged contours are left
    untouched because their source identity and row ordering are semantically
    significant.
    """
    tolerance = max(float(tolerance_mm), 0.0)
    before = len(contours)
    if not contours:
        return [], {
            "before": 0,
            "after": 0,
            "joined": 0,
            "tolerance_mm": tolerance,
            "enabled": False,
        }
    if any(type(contour) is not list for contour in contours):
        return list(contours), {
            "before": before,
            "after": before,
            "joined": 0,
            "tolerance_mm": tolerance,
            "enabled": False,
            "reason": "tagged contours",
        }

    lines = [
        [(float(x), float(y)) for x, y in contour]
        for contour in contours
        if len(contour) >= 2
    ]
    if len(lines) < 2:
        return lines, {
            "before": before,
            "after": len(lines),
            "joined": max(0, before - len(lines)),
            "tolerance_mm": tolerance,
            "enabled": True,
        }

    cell_mm = max(tolerance, 1e-6)
    endpoints = {}
    eligible = [True] * len(lines)
    for index, line in enumerate(lines):
        check_cancelled(cancel_check)
        if _endpoint_distance(line[0], line[-1]) <= tolerance:
            eligible[index] = False
            continue
        for side, point in ((0, line[0]), (1, line[-1])):
            endpoints.setdefault(_grid_key(point, cell_mm), []).append(
                (index, side)
            )

    def candidates_for(point):
        gx, gy = _grid_key(point, cell_mm)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for index, side in endpoints.get((gx + dx, gy + dy), ()):
                    if not eligible[index]:
                        continue
                    endpoint = lines[index][0 if side == 0 else -1]
                    if _endpoint_distance(point, endpoint) <= tolerance + 1e-9:
                        yield index, side, endpoint

    used = [False] * len(lines)
    chains = []
    for start_index, start_line in enumerate(lines):
        check_cancelled(cancel_check)
        if used[start_index] or not eligible[start_index]:
            continue
        used[start_index] = True
        chain = list(start_line)
        while len(chain) >= 2:
            check_cancelled(cancel_check)
            incoming = (
                chain[-1][0] - chain[-2][0],
                chain[-1][1] - chain[-2][1],
            )
            best = None
            for index, side, endpoint in candidates_for(chain[-1]):
                if used[index]:
                    continue
                candidate = lines[index]
                oriented = candidate if side == 0 else list(reversed(candidate))
                outgoing = (
                    oriented[1][0] - oriented[0][0],
                    oriented[1][1] - oriented[0][1],
                )
                rank = (
                    _endpoint_distance(chain[-1], endpoint),
                    _turn_penalty(incoming, outgoing),
                    index,
                )
                if best is None or rank < best[0]:
                    best = (rank, index, oriented)
            if best is None:
                break
            _rank, index, oriented = best
            used[index] = True
            chain.extend(oriented[1:])
        chains.append(chain)

    # Closed contours and anything nested under a tagged type remain exactly
    # as they were, with their original traversal left to the normal planner.
    for index, contour in enumerate(contours):
        if len(contour) < 2 or used[index]:
            continue
        chains.append([(float(x), float(y)) for x, y in contour])

    return chains, {
        "before": before,
        "after": len(chains),
        "joined": max(0, before - len(chains)),
        "tolerance_mm": tolerance,
        "enabled": True,
    }
