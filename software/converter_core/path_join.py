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


def chain_nearby_contours(
    contours,
    max_gap_mm=0.0,
    closed_tolerance_mm=DEFAULT_JOIN_TOLERANCE_MM,
    cancel_check=None,
):
    """Chain open contours through short bridges to save M3/M5 cycles.

    Unlike :func:`join_touching_contours`, this consumes short open contours
    too. It greedily follows the nearest unused endpoint within ``max_gap_mm``
    and draws the bridge implicitly by placing the next contour head-to-tail.
    The bridge therefore leaves visible ink; callers should expose the gap as
    an explicit speed-versus-appearance tradeoff.

    Closed contours, tagged path subclasses, and malformed one-point paths are
    preserved unchanged. The result is deterministic for a fixed input and
    gap. ``bridged_mm`` reports the additional ink length introduced by the
    connectors.
    """
    max_gap = max(0.0, float(max_gap_mm))
    closed_tolerance = max(0.0, float(closed_tolerance_mm))
    before = len(contours)
    if max_gap <= 1e-9 or len(contours) < 2:
        return list(contours), {
            "before": before,
            "after": before,
            "joined": 0,
            "connections": 0,
            "bridged_mm": 0.0,
            "max_gap_mm": max_gap,
            "enabled": False,
        }

    lines = []
    preserved = []
    for contour in contours:
        if type(contour) is not list:
            preserved.append(contour)
            continue
        points = [(float(x), float(y)) for x, y in contour]
        if len(points) < 2:
            preserved.append(contour)
            continue
        if (
            _endpoint_distance(points[0], points[-1])
            <= closed_tolerance + 1e-9
        ):
            preserved.append(contour)
            continue
        lines.append(points)

    if len(lines) < 2:
        return list(contours), {
            "before": before,
            "after": before,
            "joined": 0,
            "connections": 0,
            "bridged_mm": 0.0,
            "max_gap_mm": max_gap,
            "enabled": False,
        }

    cell_mm = max(max_gap, 1e-6)
    endpoints = {}
    for index, line in enumerate(lines):
        for side, point in ((0, line[0]), (1, line[-1])):
            endpoints.setdefault(_grid_key(point, cell_mm), []).append(
                (index, side)
            )

    used = [False] * len(lines)

    def oriented_line(index, side):
        line = lines[index]
        return line if side == 0 else list(reversed(line))

    def candidates_for(point):
        gx, gy = _grid_key(point, cell_mm)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for index, side in endpoints.get((gx + dx, gy + dy), ()):
                    if used[index]:
                        continue
                    endpoint = lines[index][side]
                    gap = _endpoint_distance(point, endpoint)
                    if gap <= max_gap + 1e-9:
                        yield gap, index, side

    chains = []
    connections = 0
    bridged_mm = 0.0
    for start_index in range(len(lines)):
        check_cancelled(cancel_check)
        if used[start_index]:
            continue
        line = lines[start_index]
        if line[-1] < line[0]:
            line = list(reversed(line))
        used[start_index] = True
        chain = list(line)
        while len(chain) >= 2:
            check_cancelled(cancel_check)
            incoming = (
                chain[-1][0] - chain[-2][0],
                chain[-1][1] - chain[-2][1],
            )
            best = None
            for gap, index, side in candidates_for(chain[-1]):
                oriented = oriented_line(index, side)
                outgoing = (
                    oriented[1][0] - oriented[0][0],
                    oriented[1][1] - oriented[0][1],
                )
                rank = (
                    gap + 0.15 * max_gap * _turn_penalty(incoming, outgoing),
                    gap,
                    index,
                    side,
                )
                if best is None or rank < best[0]:
                    best = (rank, gap, index, oriented)
            if best is None:
                break
            _rank, gap, index, oriented = best
            used[index] = True
            connections += 1
            bridged_mm += gap
            if gap > 1e-9:
                chain.append(oriented[0])
            chain.extend(oriented[1:])
        chains.append(chain)

    result = chains + preserved
    return result, {
        "before": before,
        "after": len(result),
        "joined": max(0, before - len(result)),
        "connections": connections,
        "bridged_mm": bridged_mm,
        "max_gap_mm": max_gap,
        "closed_or_tagged": len(preserved),
        "enabled": True,
    }
