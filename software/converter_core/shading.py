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
