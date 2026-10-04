"""Image-shading primitives shared by the vector and image-tone fill paths.

The popular plotter-art photo styles -- stippling, halftone, and single-line
(TSP) -- all reduce to the same two questions: where should a mark go, and how
dark is it there.  These functions take a rectangular ``bounds``, an
``inside(x, y)`` predicate that says whether a point lies in the inked region,
and a ``darkness(x, y)`` callable returning ``0..1``.  The vector path passes a
polygon membership test with a constant tone; the image-tone path passes a
sampled pixel.  Nothing here imports the Qt layer, which keeps the functions
unit-testable without a display.
"""

import bisect
import math
import random

from .cancellation import check_cancelled


# Tone below this is treated as blank paper, so a near-white JPEG background
# does not pick up a sparse film of dots or a line crossing it.
INK_FLOOR = 0.04

# A stipple mark is plotted as a tiny closed circle, not as a fraction of the
# fill spacing: the geometry pipeline drops any contour shorter than
# ``MIN_FILL_SEGMENT_LENGTH`` (1 mm on paper), so a small dash vanishes on a
# bed-filling photo.  A circle of this radius has a ~1.6 mm circumference, which
# survives the filter and reads as one pen dot.
STIPPLE_DOT_RADIUS_MM = 0.25


def stipple_mark_radius(pen_diameter_mm=0.0, minimum_mm=STIPPLE_DOT_RADIUS_MM):
    """On-paper radius of one stipple dot (never smaller than a pen tip)."""
    return max(float(pen_diameter_mm) * 0.5, float(minimum_mm))


def dot_mark_contours(points, radius, steps=12):
    """Draw each point as a small closed circle of ``radius`` (view units)."""
    radius = float(radius)
    if radius <= 0.0:
        return []
    steps = max(6, int(steps))
    circle = [
        (
            math.cos(2.0 * math.pi * i / steps) * radius,
            math.sin(2.0 * math.pi * i / steps) * radius,
        )
        for i in range(steps + 1)
    ]
    circle[-1] = circle[0]
    return [[(x + dx, y + dy) for dx, dy in circle] for x, y in points]


# Random dart throwing saturates at roughly 0.9 accepted points per
# ``min_dist`` squared before the minimum-distance rejection starves it
# (hex packing is ~1.15), so this cap only stops a pathological runaway and
# never clips a normal stipple.
STIPPLE_POINTS_PER_AREA = 0.9
# Dart throwing accepts only a fraction of its candidates, so multiply the
# expected point count to give the sampler enough chances to fill the region.
STIPPLE_ATTEMPTS_PER_POINT = 30
STIPPLE_MAX_POINTS = 60000
STIPPLE_MAX_ATTEMPTS = 1_000_000


def _clamp01(value):
    if value is None:
        return 0.0
    return max(0.0, min(float(value), 1.0))


def _area(bounds):
    left, top, right, bottom = bounds
    return max(0.0, (right - left) * (bottom - top))


def stipple_points(
    bounds,
    inside=None,
    darkness=None,
    min_dist=4.0,
    seed=0,
    ink_floor=INK_FLOOR,
    max_points=None,
    attempts=None,
    cancel_check=None,
):
    """Weighted Poisson-disc stipple points.

    Candidate points are thrown uniformly inside ``bounds`` and accepted when
    they lie in the inked region, their tone is above ``ink_floor``, a random
    draw under the tone succeeds (so a 50% grey pixel accepts half its
    candidates), and they are at least ``min_dist`` from every accepted point.
    The result is a blue-noise dot field whose density follows tone, the look
    behind hand-stippled pen-plot portraits.  A fixed ``seed`` makes the field
    reproducible for the same image.
    """
    left, top, right, bottom = (float(value) for value in bounds)
    if right <= left or bottom <= top:
        return []
    min_dist = float(min_dist)
    if min_dist <= 0.0:
        return []
    if inside is None:
        inside = lambda x, y: True
    if darkness is None:
        darkness = lambda x, y: 1.0
    floor = max(0.0, float(ink_floor))
    rng = random.Random(seed)

    if max_points is None:
        max_points = int(
            _area((left, top, right, bottom))
            / (min_dist * min_dist)
            * STIPPLE_POINTS_PER_AREA
        )
    max_points = max(1, min(int(max_points), STIPPLE_MAX_POINTS))
    if attempts is None:
        attempts = min(max_points * STIPPLE_ATTEMPTS_PER_POINT, STIPPLE_MAX_ATTEMPTS)
    attempts = max(1, int(attempts))

    cell = max(min_dist, 1e-6)
    grid = {}
    points = []

    def cell_key(x, y):
        return (int(math.floor(x / cell)), int(math.floor(y / cell)))

    def min_distance_ok(x, y):
        cx, cy = cell_key(x, y)
        for gx in range(cx - 1, cx + 2):
            for gy in range(cy - 1, cy + 2):
                for px, py in grid.get((gx, gy), ()):
                    dx = px - x
                    dy = py - y
                    if dx * dx + dy * dy < min_dist * min_dist:
                        return False
        return True

    for _ in range(attempts):
        check_cancelled(cancel_check)
        if len(points) >= max_points:
            break
        x = rng.uniform(left, right)
        y = rng.uniform(top, bottom)
        if not inside(x, y):
            continue
        tone = _clamp01(darkness(x, y))
        if tone < floor:
            continue
        # Density follows tone: the darker the pixel, the more candidates pass.
        if rng.random() > tone:
            continue
        if not min_distance_ok(x, y):
            continue
        points.append((x, y))
        grid.setdefault(cell_key(x, y), []).append((x, y))

    return points


def halftone_contours(
    bounds,
    inside=None,
    darkness=None,
    spacing=4.0,
    angle_deg=0.0,
    dot_scale=1.0,
    ink_floor=INK_FLOOR,
    cancel_check=None,
):
    """Classic halftone: fixed-pitch dots whose radius grows with tone.

    The dot grid is a square lattice rotated by ``angle_deg``.  Each dot's
    radius is ``spacing / 2 * sqrt(tone)`` so the *area* of ink tracks tone the
    way a printed halftone screen does; a fully dark pixel reaches half a cell
    and reads as near-solid.  Dots below ``ink_floor`` are dropped, so white
    paper stays clean.
    """
    left, top, right, bottom = (float(value) for value in bounds)
    if right <= left or bottom <= top:
        return []
    spacing = float(spacing)
    if spacing <= 0.0:
        return []
    if inside is None:
        inside = lambda x, y: True
    if darkness is None:
        darkness = lambda x, y: 1.0
    floor = max(0.0, float(ink_floor))
    scale = max(0.0, float(dot_scale))
    ang = math.radians(float(angle_deg))
    ca, sa = math.cos(ang), math.sin(ang)
    cs, sn = math.cos(-ang), math.sin(-ang)

    corners = [(left, top), (right, top), (right, bottom), (left, bottom)]
    rotated = [(x * cs - y * sn, x * sn + y * cs) for x, y in corners]
    min_x = min(point[0] for point in rotated)
    max_x = max(point[0] for point in rotated)
    min_y = min(point[1] for point in rotated)
    max_y = max(point[1] for point in rotated)
    margin = spacing
    min_x -= margin
    max_x += margin
    min_y -= margin
    max_y += margin

    def world(x, y):
        return (x * ca - y * sa, x * sa + y * ca)

    steps = 20
    max_radius = spacing * 0.5
    contours = []
    y = math.floor(min_y / spacing) * spacing
    while y <= max_y:
        check_cancelled(cancel_check)
        x = math.floor(min_x / spacing) * spacing
        while x <= max_x:
            check_cancelled(cancel_check)
            wx, wy = world(x, y)
            if not inside(wx, wy):
                x += spacing
                continue
            tone = _clamp01(darkness(wx, wy))
            if tone < floor:
                x += spacing
                continue
            radius = min(max_radius, max_radius * math.sqrt(tone) * scale)
            if radius <= 1e-9:
                x += spacing
                continue
            contours.append(
                [
                    (
                        wx + math.cos(2.0 * math.pi * i / steps) * radius,
                        wy + math.sin(2.0 * math.pi * i / steps) * radius,
                    )
                    for i in range(steps + 1)
                ]
            )
            x += spacing
        y += spacing
    return contours


class _NearestGrid:
    """A small spatial grid for greedy nearest-neighbour removal queries."""

    def __init__(self, points, cell):
        self.points = [tuple(point) for point in points]
        if cell <= 0.0:
            xs = [point[0] for point in self.points]
            ys = [point[1] for point in self.points]
            width = max(xs) - min(xs)
            height = max(ys) - min(ys)
            cell = math.sqrt(max(width * height, 1e-6) / max(len(self.points), 1))
        self.cell = float(cell)
        self.grid = {}
        self.cell_of = []
        for index, (x, y) in enumerate(self.points):
            key = self._key(x, y)
            self.cell_of.append(key)
            self.grid.setdefault(key, []).append(index)
        keys = list(self.grid.keys())
        self.min_gx = min(key[0] for key in keys)
        self.max_gx = max(key[0] for key in keys)
        self.min_gy = min(key[1] for key in keys)
        self.max_gy = max(key[1] for key in keys)

    def _key(self, x, y):
        return (int(math.floor(x / self.cell)), int(math.floor(y / self.cell)))

    def remove(self, index):
        key = self.cell_of[index]
        bucket = self.grid.get(key)
        if bucket:
            if index in bucket:
                bucket.remove(index)
            if not bucket:
                self.grid.pop(key, None)

    def nearest(self, x, y):
        if not self.grid:
            return None
        cx, cy = self._key(x, y)
        best_index = None
        best_d2 = math.inf
        max_radius = max(
            max(cx - self.min_gx, self.max_gx - cx, 0),
            max(cy - self.min_gy, self.max_gy - cy, 0),
        )
        for radius in range(0, max_radius + 1):
            if best_index is not None:
                # A cell in this ring (or any farther ring) is at least
                # ``(radius - 1) * cell`` from the query point, so once that
                # lower bound exceeds the best hit no farther ring can win.
                lower = max(0.0, radius - 1) * self.cell
                if lower * lower >= best_d2:
                    break
            for gx in range(cx - radius, cx + radius + 1):
                for gy in range(cy - radius, cy + radius + 1):
                    if radius > 0 and max(abs(gx - cx), abs(gy - cy)) != radius:
                        continue
                    for index in self.grid.get((gx, gy), ()):
                        px, py = self.points[index]
                        d2 = (px - x) * (px - x) + (py - y) * (py - y)
                        if d2 < best_d2:
                            best_d2 = d2
                            best_index = index
        return best_index


def greedy_single_line(points, cell=None, cancel_check=None):
    """Order points into one continuous line with greedy nearest-neighbour.

    This is the "single-line portrait" (TSP art) construction: stipple points
    are walked nearest-to-nearest so the pen travels once.  It is a greedy
    heuristic, not an optimal tour, which keeps a several-thousand-point photo
    tractable while still reading as one connected path.
    """
    pts = [tuple(point) for point in points]
    if not pts:
        return []
    if len(pts) == 1:
        return [pts[0]]
    grid = _NearestGrid(pts, cell)
    start = 0
    order = [start]
    grid.remove(start)
    current = pts[start]
    while len(order) < len(pts):
        check_cancelled(cancel_check)
        nxt = grid.nearest(*current)
        if nxt is None:
            break
        order.append(nxt)
        grid.remove(nxt)
        current = pts[nxt]
    return [pts[index] for index in order]


# -- terrain (topographic contour) fill --------------------------------------
#
# The `terrain` fill draws a region the way a topographic map draws a hillside:
# contour lines at a fixed elevation interval. The height field is a small
# fractal of deterministic gradient noise, so the lines wander, close around
# peaks, and never echo the region's own outline the way `concentric` insets
# do. Each shade step narrows the contour interval, which is what turns tone
# into ink: a dark region is a steep slope with closely spaced contours.

_TAU = 2.0 * math.pi
_MASK32 = 0xFFFFFFFF

# Sixteen fixed gradient directions, so one noise corner costs a hash and a dot
# product instead of two trig calls.
_TERRAIN_GRADIENTS = tuple(
    (math.cos(_TAU * index / 16.0), math.sin(_TAU * index / 16.0))
    for index in range(16)
)


def _terrain_hash(ix, iy, seed):
    """A deterministic 32-bit hash of one integer lattice corner."""
    value = ((ix * 0x27D4EB2D) ^ (iy * 0x165667B1) ^ (seed * 0x9E3779B1)) & _MASK32
    value ^= value >> 15
    value = (value * 0x2C1B3C6D) & _MASK32
    value ^= value >> 12
    value = (value * 0x297A2D39) & _MASK32
    value ^= value >> 15
    return value


def _terrain_noise(x, y, seed):
    """One octave of smooth gradient noise, roughly in [-0.7, 0.7]."""
    x0 = math.floor(x)
    y0 = math.floor(y)
    x1 = x0 + 1
    y1 = y0 + 1
    fx = x - x0
    fy = y - y0
    u = fx * fx * fx * (fx * (fx * 6.0 - 15.0) + 10.0)
    v = fy * fy * fy * (fy * (fy * 6.0 - 15.0) + 10.0)
    # Computed inline: this runs once per grid sample per octave, and a nested
    # corner() helper dominated the profile of a bed-filling photo.
    gx, gy = _TERRAIN_GRADIENTS[_terrain_hash(x0, y0, seed) & 15]
    n00 = gx * fx + gy * fy
    gx, gy = _TERRAIN_GRADIENTS[_terrain_hash(x1, y0, seed) & 15]
    n10 = gx * (fx - 1.0) + gy * fy
    gx, gy = _TERRAIN_GRADIENTS[_terrain_hash(x0, y1, seed) & 15]
    n01 = gx * fx + gy * (fy - 1.0)
    gx, gy = _TERRAIN_GRADIENTS[_terrain_hash(x1, y1, seed) & 15]
    n11 = gx * (fx - 1.0) + gy * (fy - 1.0)
    nx0 = n00 + (n10 - n00) * u
    nx1 = n01 + (n11 - n01) * u
    return nx0 + (nx1 - nx0) * v


def terrain_height(x, y, feature_scale, seed=0, octaves=3):
    """Terrain elevation at one point, for a given hill size.

    The result is centred on 0.5 and stays near [0, 1] for normal hill sizes;
    it is not clipped, so a peak is a real peak instead of a plateau at 1.0.
    """
    scale = max(float(feature_scale), 1e-9)
    total = 0.0
    amplitude = 1.0
    norm = 0.0
    for octave in range(max(1, int(octaves))):
        total += _terrain_noise(x / scale, y / scale, int(seed) + 1013 * octave) * amplitude
        norm += amplitude
        amplitude *= 0.5
        scale *= 0.5
    return 0.5 + 0.7 * (total / norm)


def _terrain_crossing(x0, y0, v0, x1, y1, v1, level):
    """Point where the segment's sampled values cross one contour level."""
    denom = v1 - v0
    t = 0.5 if abs(denom) < 1e-12 else (level - v0) / denom
    if t < 0.0:
        t = 0.0
    elif t > 1.0:
        t = 1.0
    return (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)


def _marching_squares(values, xs, ys, levels, cancel_check=None):
    """Segments of the level sets of a grid of samples.

    One point (axis-aligned) per cell corner: ``values[row][col]`` sits at
    ``(xs[col], ys[row])``. Edges are interpolated in a canonical corner order
    (top: c0->c1, right: c1->c2, bottom: c3->c2, left: c0->c3), so the two
    cells that share an edge compute the same crossing point bit for bit and
    the segments can be chained exactly.
    """
    segments = []
    for row in range(len(ys) - 1):
        check_cancelled(cancel_check)
        upper = values[row]
        lower = values[row + 1]
        y0 = ys[row]
        y1 = ys[row + 1]
        for col in range(len(xs) - 1):
            v00 = upper[col]
            v10 = upper[col + 1]
            v11 = lower[col + 1]
            v01 = lower[col]
            low = min(v00, v10, v11, v01)
            high = max(v00, v10, v11, v01)
            start = bisect.bisect_right(levels, low)
            if start >= len(levels) or levels[start] > high:
                continue
            x0 = xs[col]
            x1 = xs[col + 1]
            for level in levels[start:]:
                if level > high:
                    break
                edge_top = _terrain_crossing(x0, y0, v00, x1, y0, v10, level)
                edge_right = _terrain_crossing(x1, y0, v10, x1, y1, v11, level)
                edge_bottom = _terrain_crossing(x0, y1, v01, x1, y1, v11, level)
                edge_left = _terrain_crossing(x0, y0, v00, x0, y1, v01, level)
                case = (
                    (1 if v00 > level else 0)
                    | (2 if v10 > level else 0)
                    | (4 if v11 > level else 0)
                    | (8 if v01 > level else 0)
                )
                if case == 1 or case == 14:
                    segments.append((edge_left, edge_top))
                elif case == 2 or case == 13:
                    segments.append((edge_top, edge_right))
                elif case == 3 or case == 12:
                    segments.append((edge_left, edge_right))
                elif case == 4 or case == 11:
                    segments.append((edge_right, edge_bottom))
                elif case == 6 or case == 9:
                    segments.append((edge_top, edge_bottom))
                elif case == 7 or case == 8:
                    segments.append((edge_left, edge_bottom))
                elif case == 5:
                    # Saddle: put the segments on the sides the centre value
                    # says are connected, which is the standard asymptotic
                    # decider.
                    if (v00 + v10 + v11 + v01) * 0.25 > level:
                        segments.append((edge_top, edge_right))
                        segments.append((edge_left, edge_bottom))
                    else:
                        segments.append((edge_left, edge_top))
                        segments.append((edge_right, edge_bottom))
                elif case == 10:
                    if (v00 + v10 + v11 + v01) * 0.25 > level:
                        segments.append((edge_left, edge_top))
                        segments.append((edge_right, edge_bottom))
                    else:
                        segments.append((edge_top, edge_right))
                        segments.append((edge_left, edge_bottom))
    return segments


def _contour_grid_geometry(bounds, step, min_step=0.0, max_cells=None):
    """Shared sampling geometry for a contour grid over *bounds*."""
    left, top, right, bottom = (float(value) for value in bounds)
    if right <= left or bottom <= top:
        return None
    step = max(float(step), float(min_step), 1e-6)
    cols = max(1, int(math.ceil((right - left) / step)))
    rows = max(1, int(math.ceil((bottom - top) / step)))
    limit = TERRAIN_MAX_CELLS if max_cells is None else max(1, int(max_cells))
    while (cols + 1) * (rows + 1) > limit:
        cols = max(1, (cols + 1) // 2)
        rows = max(1, (rows + 1) // 2)
    step_x = (right - left) / cols
    step_y = (bottom - top) / rows
    # One shared coordinate list per axis: a neighbouring cell must compute the
    # shared crossing from the *same* two floats, so `left + (col + 1) * step`
    # and `x0 + step` cannot be allowed to differ by an ulp.
    xs = [left + col * step_x for col in range(cols + 1)]
    ys = [top + row * step_y for row in range(rows + 1)]
    return xs, ys


def _stitch_contour_segments(segments):
    """Walk marching-squares segments into continuous contour lines.

    Shared cell edges are interpolated from the same two samples in the same
    order, so the two crossing points are bit-identical and the endpoints can
    be used as dict keys directly.
    """
    if not segments:
        return []

    endpoints = {}
    for index, (a, b) in enumerate(segments):
        endpoints.setdefault(a, []).append((index, 0))
        endpoints.setdefault(b, []).append((index, 1))
    used = [False] * len(segments)

    def take(point_key):
        bucket = endpoints.get(point_key)
        while bucket:
            index, end = bucket.pop()
            if not used[index]:
                return index, end
        return None

    paths = []
    for index, (a, b) in enumerate(segments):
        if used[index]:
            continue
        used[index] = True
        line = [a, b]
        while True:
            item = take(line[-1])
            if item is None:
                break
            next_index, end = item
            used[next_index] = True
            seg_a, seg_b = segments[next_index]
            line.append(seg_b if end == 0 else seg_a)
        while True:
            item = take(line[0])
            if item is None:
                break
            next_index, end = item
            used[next_index] = True
            seg_a, seg_b = segments[next_index]
            line.insert(0, seg_b if end == 0 else seg_a)
        paths.append(line)
    return paths


# A level ladder this fine is already far beyond what the pen and the paper
# filter can resolve; the cap only stops a pathological spacing choice from
# building an enormous list of levels.
TERRAIN_MAX_LEVELS = 96
# Callers pass bigger grids for big fills in view units; this bounds the work
# one region may cost regardless of the units the artwork is authored in.
TERRAIN_MAX_CELLS = 262144
# The sum of three noise octaves has a gentler typical slope than the straight
# ramp `pitch / feature` assumes, so an uncalibrated ladder draws lines about
# 1.8x farther apart than the requested pitch. This factor was measured as the
# one that makes the average on-paper contour pitch equal `Fill spacing` for
# hill sizes from 4x to 16x the spacing.
TERRAIN_PITCH_CALIBRATION = 0.55


def terrain_contours(
    bounds,
    spacing,
    feature_scale=0.0,
    phase=0.5,
    seed=0,
    octaves=3,
    min_step=0.0,
    max_cells=None,
    cancel_check=None,
):
    """Topographic contour lines of a deterministic terrain field.

    ``spacing`` is the requested contour pitch: where the field's slope is
    typical, neighbouring lines sit about this far apart (in the caller's
    units). ``feature_scale`` is the width of one hill; 0 means eight times the
    spacing. ``phase`` chooses which rung of the level ladder is drawn, so
    shade layers can stack finer intervals without redrawing the same lines.
    The returned polylines are chained, so one contour line is one pen-down
    stroke.
    """
    left, top, right, bottom = (float(value) for value in bounds)
    if right <= left or bottom <= top:
        return []
    spacing = float(spacing)
    if spacing <= 0.0 or not math.isfinite(spacing):
        return []
    feature = float(feature_scale)
    if feature <= 0.0 or not math.isfinite(feature):
        feature = spacing * 8.0
    # A contour can only be resolved if the sample grid is finer than both the
    # line pitch and the hill, and the clamp keeps at least a few ladder rungs
    # when a caller asks for a spacing wider than the hill itself.
    pitch = min(spacing, feature / 4.0)
    step = min(pitch * 0.5, feature / 8.0)
    geometry = _contour_grid_geometry(
        (left, top, right, bottom), step, min_step, max_cells
    )
    if geometry is None:
        return []
    xs, ys = geometry
    cols = len(xs) - 1
    rows = len(ys) - 1

    interval = pitch * TERRAIN_PITCH_CALIBRATION / feature
    if interval < 1.0 / TERRAIN_MAX_LEVELS:
        interval = 1.0 / TERRAIN_MAX_LEVELS
    phase = float(phase) % 1.0
    first = int(math.ceil(-phase))
    last = int(math.floor(1.0 / interval - phase))
    levels = [(index + phase) * interval for index in range(first, last + 1)]
    if not levels:
        return []

    values = [
        [
            terrain_height(xs[col], ys[row], feature, seed, octaves)
            for col in range(cols + 1)
        ]
        for row in range(rows + 1)
    ]
    return _stitch_contour_segments(
        _marching_squares(values, xs, ys, levels, cancel_check)
    )


# The coarea identity gives the average gap between level sets as
# `area x interval / total variation`, so sizing the interval from the image's
# mean tone gradient makes `Fill spacing` mean the average gap directly. The
# factor stays a named constant because it was measured (4.09 mm and 2.03 mm
# achieved for 4 mm and 2 mm requested on a portrait) and may need retuning if
# the sampling or the smoothing changes.
TERRAIN_TONE_CALIBRATION = 1.0
# 256 tone levels is 0.4% apart, far below what the pen can show; the cap only
# stops a nearly flat image from requesting an enormous ladder.
TERRAIN_TONE_MAX_LEVELS = 256


def _box_blur(values, radius):
    """Separable moving-average blur of a rectangular grid of floats."""
    if radius <= 0 or not values:
        return values

    def blur_line(line):
        count = len(line)
        prefix = [0.0] * (count + 1)
        running = 0.0
        for index, value in enumerate(line):
            running += value
            prefix[index + 1] = running
        out = [0.0] * count
        for index in range(count):
            low = max(0, index - radius)
            high = min(count, index + radius + 1)
            out[index] = (prefix[high] - prefix[low]) / (high - low)
        return out

    rows = [blur_line(row) for row in values]
    height = len(rows)
    width = len(rows[0])
    out = [[0.0] * width for _ in range(height)]
    for col in range(width):
        column = blur_line([rows[row][col] for row in range(height)])
        for row in range(height):
            out[row][col] = column[row]
    return out


def tone_terrain_contours(
    bounds,
    spacing,
    darkness,
    step=None,
    blur=0.0,
    min_step=0.0,
    max_cells=None,
    cancel_check=None,
):
    """Contour lines of the shading itself - a topographic map of the tone.

    ``darkness(x, y)`` returns 0..1, and is used as the elevation, so the lines
    trace the image's own features instead of a synthetic field. ``spacing`` is
    the average gap between neighbouring lines: the level interval is chosen
    from the image's mean tone gradient (the coarea identity), so a busy photo
    and a soft one both draw at roughly the requested density. ``step`` is the
    sampling grid pitch (0 follows half the spacing; a caller with access to
    the source pixels passes something finer so thin features are not skipped).
    ``blur`` is the smoothing radius in the caller's units - larger values
    generalise the shading into broader landforms.
    """
    left, top, right, bottom = (float(value) for value in bounds)
    if right <= left or bottom <= top:
        return []
    spacing = float(spacing)
    if spacing <= 0.0 or not math.isfinite(spacing):
        return []
    pitch = spacing * 0.5 if step is None else float(step)
    geometry = _contour_grid_geometry(
        (left, top, right, bottom), pitch, min_step, max_cells
    )
    if geometry is None:
        return []
    xs, ys = geometry
    sample_rows = len(ys)
    sample_cols = len(xs)
    step_x = (right - left) / (sample_cols - 1)
    step_y = (bottom - top) / (sample_rows - 1)

    values = []
    for y in ys:
        check_cancelled(cancel_check)
        row = [_clamp01(darkness(x, y)) for x in xs]
        values.append(row)

    blur = float(blur)
    if blur > 0.0:
        cell = 0.5 * (step_x + step_y)
        values = _box_blur(values, max(1, int(round(blur / max(cell, 1e-9)))))

    # Mean tone gradient magnitude over the inked area: the coarea identity
    # turns it into the average gap between level sets, so a linear ramp draws
    # lines exactly `spacing` apart and a photo is calibrated by its own
    # content. Blank paper is left out - it draws no lines, and counting it
    # would tighten the inked area's pitch to compensate for area the pen
    # never touches.
    gradient = 0.0
    inked = 0
    ink_tone = 0.0
    for row in range(sample_rows - 1):
        check_cancelled(cancel_check)
        upper = values[row]
        lower = values[row + 1]
        for col in range(sample_cols - 1):
            cell_tone = (upper[col] + upper[col + 1] + lower[col + 1] + lower[col]) * 0.25
            if cell_tone <= INK_FLOOR:
                continue
            dx = (upper[col + 1] - upper[col]) / step_x
            dy = (lower[col] - upper[col]) / step_y
            gradient += math.hypot(dx, dy)
            ink_tone += cell_tone
            inked += 1
    if inked == 0:
        return []
    mean_gradient = gradient / inked
    if mean_gradient <= 1e-12:
        # A flat image has no contours to draw.
        return []
    interval = spacing * mean_gradient * TERRAIN_TONE_CALIBRATION
    if interval < 1.0 / TERRAIN_TONE_MAX_LEVELS:
        interval = 1.0 / TERRAIN_TONE_MAX_LEVELS
    if interval >= 1.0:
        # A hard, thin drawing (a scanned line, a step edge) can have a mean
        # slope so steep that the requested gap exceeds the whole tone range.
        # One line through the middle of the ink still traces the subject.
        mean_ink_tone = ink_tone / inked
        levels = [mean_ink_tone] if 0.0 < mean_ink_tone < 1.0 else []
    else:
        level_count = max(1, int(math.floor(1.0 / interval)))
        levels = [(index + 0.5) * interval for index in range(level_count)]
    return _stitch_contour_segments(
        _marching_squares(values, xs, ys, levels, cancel_check)
    )
