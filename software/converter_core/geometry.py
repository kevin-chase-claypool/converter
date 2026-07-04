import math
import re
from xml.etree import ElementTree as ET
from .cancellation import check_cancelled
from .settings import pattern_size_values

GEOMETRY_VERSION = "2.2-patterns"  # concentric loops stay continuous and inside fill bounds
COMMAND_RE = re.compile(r"[MmZzLlHhVvCcSsQqTtAa]|[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
NUMBER_RE = re.compile(r"[-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?")
UNIT_RE = re.compile(r"^\s*([-+]?(?:\d*\.\d+|\d+\.?)(?:[eE][-+]?\d+)?)([a-zA-Z%]*)\s*$")

class Matrix:
    def __init__(self, a=1.0, b=0.0, c=0.0, d=1.0, e=0.0, f=0.0):
        self.a, self.b, self.c, self.d, self.e, self.f = a, b, c, d, e, f

    def __matmul__(self, other):
        return Matrix(
            self.a * other.a + self.c * other.b,
            self.b * other.a + self.d * other.b,
            self.a * other.c + self.c * other.d,
            self.b * other.c + self.d * other.d,
            self.a * other.e + self.c * other.f + self.e,
            self.b * other.e + self.d * other.f + self.f,
        )

    def apply(self, x, y):
        return (self.a * x + self.c * y + self.e, self.b * x + self.d * y + self.f)


def strip_ns(tag):
    return tag.split("}", 1)[-1] if "}" in tag else tag


def parse_length(value, default=0.0):
    if value is None:
        return default
    match = UNIT_RE.match(value)
    if not match:
        return default
    number = float(match.group(1))
    unit = match.group(2)
    factors = {"": 1.0, "px": 25.4 / 96.0, "mm": 1.0, "cm": 10.0, "in": 25.4, "pt": 25.4 / 72.0, "pc": 25.4 / 6.0}
    return number * factors.get(unit, 1.0)


def parse_points(points):
    nums = [float(x) for x in NUMBER_RE.findall(points or "")]
    return list(zip(nums[0::2], nums[1::2]))


def parse_transform(text):
    if not text:
        return Matrix()
    result = Matrix()
    for name, raw_args in re.findall(r"([a-zA-Z]+)\(([^)]*)\)", text):
        args = [float(x) for x in NUMBER_RE.findall(raw_args)]
        name = name.lower()
        m = Matrix()
        if name == "matrix" and len(args) >= 6:
            m = Matrix(*args[:6])
        elif name == "translate":
            m = Matrix(e=args[0] if args else 0.0, f=args[1] if len(args) > 1 else 0.0)
        elif name == "scale":
            sx = args[0] if args else 1.0
            sy = args[1] if len(args) > 1 else sx
            m = Matrix(a=sx, d=sy)
        elif name == "rotate" and args:
            angle = math.radians(args[0])
            rot = Matrix(math.cos(angle), math.sin(angle), -math.sin(angle), math.cos(angle), 0.0, 0.0)
            if len(args) >= 3:
                cx, cy = args[1], args[2]
                m = Matrix(e=cx, f=cy) @ rot @ Matrix(e=-cx, f=-cy)
            else:
                m = rot
        elif name == "skewx" and args:
            m = Matrix(c=math.tan(math.radians(args[0])))
        elif name == "skewy" and args:
            m = Matrix(b=math.tan(math.radians(args[0])))
        result = result @ m
    return result


def use_href(element):
    return element.get("href") or element.get("{http://www.w3.org/1999/xlink}href") or element.get("xlink:href")


def style_value(element, name):
    if element.get(name) is not None:
        return element.get(name)
    style = element.get("style") or ""
    for part in style.split(";"):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        if key.strip() == name:
            return value.strip()
    return None


def stroke_width(element):
    value = style_value(element, "stroke-width")
    if not value:
        return 0.0
    return parse_length(value, 0.0)


def has_visible_stroke(element):
    stroke = style_value(element, "stroke")
    return stroke is not None and stroke.strip().lower() != "none" and stroke_width(element) > 0


def has_visible_fill(element):
    fill = style_value(element, "fill")
    if fill is not None and fill.strip().lower() == "none":
        return False
    opacity = style_value(element, "fill-opacity")
    if opacity is not None:
        try:
            if float(opacity) <= 0:
                return False
        except ValueError:
            pass
    return True


def parse_svg_color(value):
    if value is None:
        return (0.0, 0.0, 0.0)
    text = value.strip().lower()
    if not text or text == "none" or text.startswith("url("):
        return None
    named = {
        "black": (0.0, 0.0, 0.0),
        "white": (1.0, 1.0, 1.0),
        "red": (1.0, 0.0, 0.0),
        "green": (0.0, 0.5019607843, 0.0),
        "blue": (0.0, 0.0, 1.0),
        "gray": (0.5019607843, 0.5019607843, 0.5019607843),
        "grey": (0.5019607843, 0.5019607843, 0.5019607843),
    }
    if text in named:
        return named[text]
    if text.startswith("#"):
        raw = text[1:]
        if len(raw) == 3:
            raw = "".join(ch * 2 for ch in raw)
        if len(raw) >= 6:
            try:
                return tuple(int(raw[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
            except ValueError:
                return None
    match = re.match(r"rgba?\(([^)]*)\)", text)
    if match:
        parts = [part.strip() for part in match.group(1).split(",")]
        if len(parts) >= 3:
            out = []
            for part in parts[:3]:
                if part.endswith("%"):
                    out.append(max(0.0, min(float(part[:-1]) / 100.0, 1.0)))
                else:
                    out.append(max(0.0, min(float(part) / 255.0, 1.0)))
            return tuple(out)
    return None


def fill_darkness(element):
    color = parse_svg_color(style_value(element, "fill"))
    if color is None:
        color = (0.0, 0.0, 0.0)
    r, g, b = color
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    darkness = 1.0 - luminance
    opacity = 1.0
    for name in ("fill-opacity", "opacity"):
        value = style_value(element, name)
        if value is None:
            continue
        try:
            opacity *= max(0.0, min(float(value), 1.0))
        except ValueError:
            pass
    return max(0.0, min(darkness * opacity, 1.0))


def hatch_angles_for_tone(base_angle, levels, angle_step, darkness):
    levels = max(1, int(levels))
    active = max(0, min(levels, int(math.ceil(darkness * levels))))
    return [base_angle + i * angle_step for i in range(active)]


def normalized_hatch_pattern(pattern):
    text = str(pattern or "crosshatch").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "line": "linear",
        "lines": "linear",
        "rectilinear": "linear",
        "hatch": "linear",
        "cross": "crosshatch",
        "cross_hatch": "crosshatch",
        "grid": "crosshatch",
        "diag": "diagonal",
        "diagonal_cross": "diagonal_crosshatch",
        "diagonal_cross_hatch": "diagonal_crosshatch",
        "diamond": "diamonds",
        "triangle": "triangular",
        "triangles": "triangular",
        "tri": "triangular",
        "hex": "hexagonal",
        "hexagon": "hexagonal",
        "honeycomb": "hexagonal",
        "circle": "circles",
        "dot": "dots",
        "wave": "waves",
        "sine": "waves",
        "sinusoidal": "waves",
        "isometric": "cubic",
        "iso": "cubic",
        "cube": "cubic",
        "concentric_ring": "concentric",
        "rings": "concentric",
        "inset": "concentric",
    }
    supported = {
        "linear",
        "crosshatch",
        "diagonal",
        "diagonal_crosshatch",
        "diamonds",
        "triangular",
        "hexagonal",
        "circles",
        "dots",
        "waves",
        "gyroid",
        "cubic",
        "concentric",
    }
    return aliases.get(text, text if text in supported else "crosshatch")


def pattern_angles(base_angle, levels, angle_step, darkness, pattern):
    pattern = normalized_hatch_pattern(pattern)
    if pattern == "linear":
        return [base_angle]
    elif pattern == "crosshatch":
        offsets = (0.0, 90.0)
    elif pattern == "diagonal":
        return [base_angle + 45.0]
    elif pattern == "diagonal_crosshatch":
        offsets = (45.0, 135.0)
    elif pattern == "triangular":
        offsets = (0.0, 60.0, 120.0)
    else:
        return [base_angle]
    return [base_angle + offset for offset in offsets]


def active_shade_layers(levels, darkness):
    levels = max(1, int(levels))
    return max(0, min(levels, int(math.ceil(max(0.0, min(float(darkness), 1.0)) * levels))))


def density_spacing(spacing, levels, darkness):
    active = active_shade_layers(levels, darkness)
    if active <= 0:
        return None
    return max(float(spacing) / math.sqrt(active), 1e-6)


def point_in_polygon(point, polygon):
    x, y = point
    inside = False
    pts = polygon
    if len(pts) < 3:
        return False
    for a, b in zip(pts, pts[1:] + pts[:1]):
        x1, y1 = a
        x2, y2 = b
        if ((y1 > y) != (y2 > y)) and x < (x2 - x1) * (y - y1) / max(y2 - y1, 1e-12) + x1:
            inside = not inside
    return inside


def point_on_segment(point, a, b, tol=1e-7):
    px, py = point
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    length2 = dx * dx + dy * dy
    if length2 <= tol * tol:
        return math.hypot(px - ax, py - ay) <= tol
    cross = (px - ax) * dy - (py - ay) * dx
    if abs(cross) > tol * math.sqrt(length2):
        return False
    dot = (px - ax) * dx + (py - ay) * dy
    return -tol <= dot <= length2 + tol


def point_on_polygon_boundary(point, polygon, tol=1e-7):
    if len(polygon) < 2:
        return False
    pts = polygon if polygon[0] == polygon[-1] else polygon + [polygon[0]]
    return any(point_on_segment(point, a, b, tol) for a, b in zip(pts, pts[1:]))


def point_in_region(point, polygons):
    if any(point_on_polygon_boundary(point, polygon) for polygon in polygons):
        return True
    return sum(1 for polygon in polygons if point_in_polygon(point, polygon)) % 2 == 1


def clip_segment_to_region(a, b, polygons):
    if not polygons:
        return []
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    ts = [0.0, 1.0]
    for polygon in polygons:
        if len(polygon) < 3:
            continue
        pts = polygon if polygon[0] == polygon[-1] else polygon + [polygon[0]]
        for p1, p2 in zip(pts, pts[1:]):
            ex, ey = p2[0] - p1[0], p2[1] - p1[1]
            denom = dx * ey - dy * ex
            if abs(denom) <= 1e-12:
                continue
            qx, qy = p1[0] - ax, p1[1] - ay
            t = (qx * ey - qy * ex) / denom
            u = (qx * dy - qy * dx) / denom
            if -1e-9 <= t <= 1.0 + 1e-9 and -1e-9 <= u <= 1.0 + 1e-9:
                ts.append(max(0.0, min(1.0, t)))
    ts = sorted(ts)
    deduped = []
    for t in ts:
        if not deduped or abs(t - deduped[-1]) > 1e-7:
            deduped.append(t)
    segments = []
    for t0, t1 in zip(deduped, deduped[1:]):
        if t1 - t0 <= 1e-7:
            continue
        mid = (t0 + t1) / 2.0
        mid_point = (ax + dx * mid, ay + dy * mid)
        if point_in_region(mid_point, polygons):
            segments.append([
                (ax + dx * t0, ay + dy * t0),
                (ax + dx * t1, ay + dy * t1),
            ])
    return segments


def clip_segment_to_polygon(a, b, polygon):
    return clip_segment_to_region(a, b, [polygon])


def clip_polyline_to_region(points, polygons):
    clipped = []
    for a, b in zip(points, points[1:]):
        clipped.extend(clip_segment_to_region(a, b, polygons))
    return clipped


def clip_polyline_to_polygon(points, polygon):
    return clip_polyline_to_region(points, [polygon])


def chain_segments_to_paths(segments, precision=5):
    """Turn independent line segments into longer pen-down paths.

    The lattice generators naturally produce a graph. A greedy edge traversal
    reduces pen cycles by walking connected unused edges until it reaches a dead
    end/branch exhaustion. Edges are still drawn once; the ordering just changes
    from one contour per edge to one contour per graph trail.
    """
    clean = []
    for segment in segments:
        if len(segment) < 2:
            continue
        a, b = segment[0], segment[-1]
        if distance(a, b) > 1e-9:
            clean.append((a, b))
    if not clean:
        return []

    def key(point):
        return (round(point[0], precision), round(point[1], precision))

    points = {}
    adjacency = {}
    for index, (a, b) in enumerate(clean):
        ka, kb = key(a), key(b)
        points.setdefault(ka, a)
        points.setdefault(kb, b)
        adjacency.setdefault(ka, []).append((index, kb))
        adjacency.setdefault(kb, []).append((index, ka))

    unused = set(range(len(clean)))

    def unused_degree(k):
        return sum(1 for edge_index, _other in adjacency.get(k, ()) if edge_index in unused)

    def choose_start():
        odd = [k for k in adjacency if unused_degree(k) % 2 == 1 and unused_degree(k) > 0]
        if odd:
            return min(odd, key=lambda k: unused_degree(k))
        return next((k for k in adjacency if unused_degree(k) > 0), None)

    def take_next(k, previous_key=None):
        candidates = [(edge_index, other) for edge_index, other in adjacency.get(k, ()) if edge_index in unused]
        if not candidates:
            return None
        if previous_key is not None and len(candidates) > 1:
            non_backtrack = [item for item in candidates if item[1] != previous_key]
            if non_backtrack:
                candidates = non_backtrack
        return min(candidates, key=lambda item: unused_degree(item[1]))

    paths = []
    while unused:
        start = choose_start()
        if start is None:
            break
        path_keys = [start]
        current = start
        previous = None
        while True:
            item = take_next(current, previous)
            if item is None:
                break
            edge_index, other = item
            unused.remove(edge_index)
            previous, current = current, other
            path_keys.append(current)
        if len(path_keys) >= 2:
            paths.append([points[k] for k in path_keys])
    return paths


def rotated_region_bounds(polygons, angle_deg):
    ang = math.radians(angle_deg)
    cs, sn = math.cos(-ang), math.sin(-ang)
    points = [(x * cs - y * sn, x * sn + y * cs) for polygon in polygons for x, y in polygon]
    if not points:
        return (0.0, 0.0, 0.0, 0.0)
    return (
        min(x for x, _ in points),
        min(y for _, y in points),
        max(x for x, _ in points),
        max(y for _, y in points),
    )


def line_region_contours(polygons, spacing, angle_deg=0.0, cancel_check=None):
    if spacing <= 0 or not polygons:
        return []
    ang = math.radians(angle_deg)
    ca, sa = math.cos(ang), math.sin(ang)
    min_x, min_y, max_x, max_y = rotated_region_bounds(polygons, angle_deg)
    if max_y <= min_y:
        return []

    def world(x, y):
        return (x * ca - y * sa, x * sa + y * ca)

    contours = []
    # Snap to global grid so multiple angle families phase-align correctly
    # (all families share reference lines at multiples of spacing from origin)
    y = math.floor(min_y / spacing) * spacing
    row = 0
    while y <= max_y:
        check_cancelled(cancel_check)
        start = world(min_x - spacing, y)
        end = world(max_x + spacing, y)
        segments = clip_segment_to_region(start, end, polygons)
        if row % 2:
            segments = [[seg[1], seg[0]] for seg in reversed(segments)]
        contours.extend(segments)
        y += spacing
        row += 1
    return contours


def mark_grid_contours(polygons, spacing, angle_deg=0.0, mark="dots", cancel_check=None):
    if spacing <= 0 or not polygons:
        return []
    ang = math.radians(angle_deg)
    cs, sn = math.cos(-ang), math.sin(-ang)
    ca, sa = math.cos(ang), math.sin(ang)
    min_x, min_y, max_x, max_y = rotated_region_bounds(polygons, angle_deg)
    margin = spacing * 2.0
    min_x -= margin
    max_x += margin
    min_y -= margin
    max_y += margin
    circle_radius = max(spacing * 0.16, 0.05)
    dot_radius = max(spacing * 0.055, 0.03)
    row_step = spacing * math.sqrt(3.0) / 2.0
    steps = 10
    contours = []

    def world(x, y):
        return (x * ca - y * sa, x * sa + y * ca)

    # Snap to global grid
    y = math.floor((min_y - margin) / row_step) * row_step + row_step * 0.5
    row = 0
    while y <= max_y:
        check_cancelled(cancel_check)
        x_origin = math.floor((min_x - margin) / spacing) * spacing
        x = x_origin + spacing * (0.5 if row % 2 == 0 else 1.0)
        while x <= max_x:
            check_cancelled(cancel_check)
            center = world(x, y)
            if mark == "circles":
                circle = [
                    (
                        center[0] + math.cos(2.0 * math.pi * i / steps) * circle_radius,
                        center[1] + math.sin(2.0 * math.pi * i / steps) * circle_radius,
                    )
                    for i in range(steps + 1)
                ]
                contours.extend(clip_polyline_to_region(circle, polygons))
            elif point_in_region(center, polygons):
                dot = [
                    (center[0] - dot_radius, center[1]),
                    (center[0] + dot_radius, center[1]),
                ]
                contours.extend(clip_segment_to_region(dot[0], dot[1], polygons))
            x += spacing
        y += row_step
        row += 1
    return contours


def tile_shape_contours(polygons, spacing, angle_deg=0.0, shape="diamonds", cancel_check=None):
    if spacing <= 0 or not polygons:
        return []
    ang = math.radians(angle_deg)
    cs, sn = math.cos(-ang), math.sin(-ang)
    ca, sa = math.cos(ang), math.sin(ang)
    min_x, min_y, max_x, max_y = rotated_region_bounds(polygons, angle_deg)
    margin = spacing * 2.0
    min_x -= margin
    max_x += margin
    min_y -= margin
    max_y += margin
    contours = []

    def world(x, y):
        return (x * ca - y * sa, x * sa + y * ca)

    def add_clipped_polyline(points):
        shaped = [world(x, y) for x, y in points]
        contours.extend(clip_polyline_to_region(shaped, polygons))

    seen_segments = set()

    def add_clipped_segment(a, b):
        key_a = (round(a[0], 6), round(a[1], 6))
        key_b = (round(b[0], 6), round(b[1], 6))
        key = tuple(sorted((key_a, key_b)))
        if key in seen_segments:
            return
        seen_segments.add(key)
        contours.extend(clip_segment_to_region(world(*a), world(*b), polygons))

    def add_grid_segment(a, b):
        add_clipped_segment(a, b)

    if shape == "circles":
        radius = max(spacing * 0.5, 0.05)
        steps = 18
        row_step = radius * math.sqrt(3.0)
        # Snap to global grid so pattern is independent of polygon position
        y = math.floor((min_y - radius) / row_step) * row_step
        row = 0
        while y <= max_y + radius:
            check_cancelled(cancel_check)
            x_origin = math.floor((min_x - radius) / (radius * 2.0)) * (radius * 2.0)
            x = x_origin + (radius if row % 2 else 0.0)
            while x <= max_x + radius:
                check_cancelled(cancel_check)
                add_clipped_polyline([
                    (
                        x + math.cos(2.0 * math.pi * i / steps) * radius,
                        y + math.sin(2.0 * math.pi * i / steps) * radius,
                    )
                    for i in range(steps + 1)
                ])
                x += radius * 2.0
            y += row_step
            row += 1
        return contours

    if shape == "hexagonal":
        radius = max(spacing * 0.5, 0.05)
        x_step = radius * 1.5
        y_step = radius * math.sqrt(3.0)
        # Snap to global grid
        x_origin = math.floor((min_x - radius) / x_step) * x_step
        col = 0
        x = x_origin
        while x <= max_x + radius:
            check_cancelled(cancel_check)
            y_base = math.floor((min_y - radius) / y_step) * y_step
            y = y_base + (y_step * 0.5 if col % 2 else 0.0)
            while y <= max_y + radius:
                check_cancelled(cancel_check)
                vertices = [
                    (
                        x + math.cos(math.radians(60.0 * i)) * radius,
                        y + math.sin(math.radians(60.0 * i)) * radius,
                    )
                    for i in range(7)
                ]
                for a, b in zip(vertices, vertices[1:]):
                    add_clipped_segment(a, b)
                y += y_step
            x += x_step
            col += 1
        return chain_segments_to_paths(contours)

    if shape == "triangular":
        side = max(spacing, 0.05)
        row_step = side * math.sqrt(3.0) / 2.0
        i_min = int(math.floor((min_x - max_y - side) / side)) - 2
        i_max = int(math.ceil((max_x - min_y + side) / side)) + 2
        j_min = int(math.floor((min_y - row_step) / row_step)) - 1
        j_max = int(math.ceil((max_y + row_step) / row_step)) + 1

        def point(i, j):
            return ((i + j * 0.5) * side, j * row_step)

        for j in range(j_min, j_max + 1):
            check_cancelled(cancel_check)
            for i in range(i_min, i_max + 1):
                check_cancelled(cancel_check)
                p = point(i, j)
                add_grid_segment(p, point(i + 1, j))
                add_grid_segment(p, point(i, j + 1))
                add_grid_segment(p, point(i - 1, j + 1))
        return chain_segments_to_paths(contours)

    half = max(spacing * 0.5, 0.05)
    x_min = int(math.floor((min_x - half) / half)) - 1
    x_max = int(math.ceil((max_x + half) / half)) + 1
    y_min = int(math.floor((min_y - half) / half)) - 1
    y_max = int(math.ceil((max_y + half) / half)) + 1
    for j in range(y_min, y_max + 1):
        check_cancelled(cancel_check)
        y = j * half
        for i in range(x_min, x_max + 1):
            check_cancelled(cancel_check)
            x = i * half
            # Rhombic lattice: every vertex connects to the two vertices in the
            # next column. Adjacent diamonds share these vertices instead of
            # being stamped as isolated cells.
            add_grid_segment((x, y), (x + half, y + half))
            add_grid_segment((x, y), (x + half, y - half))
    return chain_segments_to_paths(contours)


def wave_region_contours(polygons, spacing, angle_deg=0.0, amplitude=None, wavelength=None, cancel_check=None):
    """Sinusoidal wave fill lines clipped to the region."""
    if spacing <= 0 or not polygons:
        return []
    if amplitude is None:
        amplitude = spacing * 0.42   # nearly-touching waves — clearly curved
    if wavelength is None:
        wavelength = spacing * 2.0   # longer wavelength = more obviously sinusoidal
    ang = math.radians(angle_deg)
    ca, sa = math.cos(ang), math.sin(ang)
    min_x, min_y, max_x, max_y = rotated_region_bounds(polygons, angle_deg)
    if max_y <= min_y:
        return []
    width = max_x - min_x + 4.0 * spacing
    steps_per_wave = 24   # smoother curves

    def world(x, y):
        return (x * ca - y * sa, x * sa + y * ca)

    contours = []
    y = math.floor((min_y - spacing) / spacing) * spacing
    row = 0
    while y <= max_y + spacing:
        check_cancelled(cancel_check)
        n_steps = max(4, int(width / max(wavelength, 1e-6) * steps_per_wave))
        phase = math.pi if row % 2 else 0.0
        points = [
            world(
                min_x - 2.0 * spacing + i * width / n_steps,
                y + amplitude * math.sin(2.0 * math.pi * (i / n_steps) * (width / wavelength) + phase),
            )
            for i in range(n_steps + 1)
        ]
        contours.extend(clip_polyline_to_region(points, polygons))
        y += spacing
        row += 1
    return contours


def gyroid_region_contours(polygons, spacing, angle_deg=0.0, cancel_check=None):
    """Gyroid-like 2D implicit infill clipped to the region.

    This follows the common slicer-style visual language: a continuous-looking
    sinusoidal lattice, not a pair of straight hatch families.
    """
    if spacing <= 0 or not polygons:
        return []
    ang = math.radians(angle_deg)
    ca, sa = math.cos(ang), math.sin(ang)
    min_x, min_y, max_x, max_y = rotated_region_bounds(polygons, angle_deg)
    if max_x <= min_x or max_y <= min_y:
        return []
    margin = spacing * 1.5
    min_x -= margin
    max_x += margin
    min_y -= margin
    max_y += margin
    cell = max(spacing / 6.0, 0.1)
    k = 2.0 * math.pi / max(spacing * 2.0, 1e-6)

    def field(x, y):
        return math.sin(x * k) * math.cos(y * k) + math.sin(y * k) * math.cos(x * k)

    def world(x, y):
        return (x * ca - y * sa, x * sa + y * ca)

    def interp(p0, v0, p1, v1):
        denom = v0 - v1
        t = 0.5 if abs(denom) < 1e-12 else max(0.0, min(1.0, v0 / denom))
        return (p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t)

    contours = []
    y = math.floor(min_y / cell) * cell
    while y < max_y:
        check_cancelled(cancel_check)
        x = math.floor(min_x / cell) * cell
        while x < max_x:
            check_cancelled(cancel_check)
            pts = [(x, y), (x + cell, y), (x + cell, y + cell), (x, y + cell)]
            vals = [field(px, py) for px, py in pts]
            crossings = []
            for i, j in ((0, 1), (1, 2), (2, 3), (3, 0)):
                vi, vj = vals[i], vals[j]
                if (vi <= 0.0 < vj) or (vj <= 0.0 < vi):
                    crossings.append(interp(pts[i], vi, pts[j], vj))
            if len(crossings) == 2:
                contours.extend(clip_segment_to_region(world(*crossings[0]), world(*crossings[1]), polygons))
            elif len(crossings) == 4:
                contours.extend(clip_segment_to_region(world(*crossings[0]), world(*crossings[1]), polygons))
                contours.extend(clip_segment_to_region(world(*crossings[2]), world(*crossings[3]), polygons))
            x += cell
        y += cell
    return contours


def _polygon_signed_area2(pts):
    n = len(pts)
    return sum(
        (pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1])
        for i in range(n)
    )


def contour_inside_region(contour, polygons):
    if len(contour) < 2:
        return False
    checks = list(contour)
    checks.extend(((a[0] + b[0]) / 2.0, (a[1] + b[1]) / 2.0) for a, b in zip(contour, contour[1:]))
    return all(point_in_region(point, polygons) for point in checks)


def inset_polygon_simple(polygon, offset):
    """Inset a polygon by *offset* (positive = toward interior).

    Works accurately for convex polygons; concave polygons may produce
    self-intersections at sharp inward corners, which are left to the caller
    to detect via area collapse.
    """
    pts = polygon[:-1] if (len(polygon) > 1 and polygon[0] == polygon[-1]) else list(polygon)
    n = len(pts)
    if n < 3:
        return []
    area2 = _polygon_signed_area2(pts)
    winding = 1.0 if area2 > 0 else -1.0

    new_pts = []
    for i in range(n):
        a = pts[(i - 1) % n]
        b = pts[i]
        c = pts[(i + 1) % n]
        d1x, d1y = b[0] - a[0], b[1] - a[1]
        d2x, d2y = c[0] - b[0], c[1] - b[1]
        l1 = math.hypot(d1x, d1y)
        l2 = math.hypot(d2x, d2y)
        if l1 < 1e-9 or l2 < 1e-9:
            new_pts.append(b)
            continue
        # Inward unit normals
        n1x, n1y = -winding * d1y / l1,  winding * d1x / l1
        n2x, n2y = -winding * d2y / l2,  winding * d2x / l2
        # Bisector
        bx, by = n1x + n2x, n1y + n2y
        bl = math.hypot(bx, by)
        if bl < 1e-9:
            new_pts.append((b[0] + n1x * offset, b[1] + n1y * offset))
            continue
        dot = n1x * (bx / bl) + n1y * (by / bl)
        if abs(dot) < 1e-9:
            new_pts.append((b[0] + n1x * offset, b[1] + n1y * offset))
        else:
            d = offset / dot
            new_pts.append((b[0] + bx / bl * d, b[1] + by / bl * d))

    if len(new_pts) < 3:
        return []
    return new_pts + [new_pts[0]]


def concentric_region_contours(polygons, spacing, cancel_check=None):
    """Progressively inset each polygon ring, producing concentric contours."""
    if spacing <= 0 or not polygons:
        return []
    contours = []
    for polygon in polygons:
        check_cancelled(cancel_check)
        if len(polygon) < 3:
            continue
        outer = polygon[:-1] if (len(polygon) > 1 and polygon[0] == polygon[-1]) else list(polygon)
        if len(outer) < 3:
            continue
        outer_area2 = _polygon_signed_area2(outer)
        outer_sign = 1.0 if outer_area2 >= 0 else -1.0
        prev_abs = abs(outer_area2)
        current = list(polygon)
        if not contour_inside_region(current, polygons):
            continue
        for _ in range(500):
            check_cancelled(cancel_check)
            inset = inset_polygon_simple(current, spacing)
            if len(inset) < 3:
                break
            inner = inset[:-1] if inset[0] == inset[-1] else inset
            if len(inner) < 3:
                break
            area2 = _polygon_signed_area2(inner)
            abs_area2 = abs(area2)
            # Stop if polygon inverted (winding flipped) or area grew (diverging) or collapsed
            inner_sign = 1.0 if area2 >= 0 else -1.0
            if inner_sign != outer_sign or abs_area2 >= prev_abs or abs_area2 < spacing * spacing * 0.25:
                break
            if not contour_inside_region(inset, polygons):
                break
            prev_abs = abs_area2
            contours.append(inset)
            current = inset
    return contours


def _pattern_spacing(pattern, fill_spacing, pattern_sizes=None, triangle_size=0.0):
    value = 0.0
    if pattern_sizes:
        value = float(pattern_sizes.get(pattern, 0.0))
    elif pattern == "triangular":
        value = float(triangle_size)
    return max(value if value > 0.0 else fill_spacing, 1e-6)


def fill_pattern_contours(polygon, spacing, base_angle, levels, angle_step, darkness, pattern, triangle_size=0.0, pattern_sizes=None, cancel_check=None):
    return fill_region_pattern_contours([polygon], spacing, base_angle, levels, angle_step, darkness, pattern, triangle_size, pattern_sizes, cancel_check)


def fill_region_pattern_contours(polygons, spacing, base_angle, levels, angle_step, darkness, pattern, triangle_size=0.0, pattern_sizes=None, cancel_check=None):
    check_cancelled(cancel_check)
    pattern = normalized_hatch_pattern(pattern)
    fill_spacing = density_spacing(spacing, levels, darkness)
    if fill_spacing is None:
        return []
    if pattern == "dots":
        return mark_grid_contours(polygons, _pattern_spacing(pattern, fill_spacing, pattern_sizes, triangle_size), base_angle, "dots", cancel_check)
    if pattern in ("circles", "diamonds", "hexagonal", "triangular"):
        pattern_spacing = _pattern_spacing(pattern, fill_spacing, pattern_sizes, triangle_size)
        return tile_shape_contours(polygons, pattern_spacing, base_angle, pattern, cancel_check)
    if pattern == "waves":
        return wave_region_contours(polygons, _pattern_spacing(pattern, fill_spacing, pattern_sizes, triangle_size), base_angle, cancel_check=cancel_check)
    if pattern == "gyroid":
        return gyroid_region_contours(polygons, _pattern_spacing(pattern, fill_spacing, pattern_sizes, triangle_size), base_angle, cancel_check)
    if pattern == "concentric":
        return concentric_region_contours(polygons, _pattern_spacing(pattern, fill_spacing, pattern_sizes, triangle_size), cancel_check)
    if pattern == "cubic":
        # Isometric cube grid: three line families at 30°, 90°, 150°
        cubic_spacing = _pattern_spacing(pattern, fill_spacing, pattern_sizes, triangle_size)
        out = []
        for angle in (base_angle + 30.0, base_angle + 90.0, base_angle + 150.0):
            check_cancelled(cancel_check)
            out.extend(line_region_contours(polygons, cubic_spacing, angle, cancel_check))
        return out
    angles = pattern_angles(base_angle, levels, angle_step, darkness, pattern)
    out = []
    for angle in angles:
        check_cancelled(cancel_check)
        out.extend(line_region_contours(polygons, fill_spacing, angle, cancel_check))
    return out


def hatch_polygon(polygon, spacing, angle_deg=0.0):
    if spacing <= 0 or len(polygon) < 3:
        return []
    ang = math.radians(angle_deg)
    cs, sn = math.cos(-ang), math.sin(-ang)
    rot = [(x * cs - y * sn, x * sn + y * cs) for x, y in polygon]
    if (rot[0][0] - rot[-1][0]) ** 2 + (rot[0][1] - rot[-1][1]) ** 2 > 1e-9:
        rot.append(rot[0])
    min_y = min(p[1] for p in rot)
    max_y = max(p[1] for p in rot)
    if max_y - min_y < spacing:
        return []
    ca, sa = math.cos(ang), math.sin(ang)
    n = len(rot)
    runs = []
    y = min_y + spacing * 0.5
    while y < max_y:
        xs = []
        for i in range(n - 1):
            y1, y2 = rot[i][1], rot[i + 1][1]
            if (y1 <= y < y2) or (y2 <= y < y1):
                t = (y - y1) / (y2 - y1)
                xs.append(rot[i][0] + t * (rot[i + 1][0] - rot[i][0]))
        xs.sort()
        pairs = []
        for k in range(0, len(xs) - 1, 2):
            pairs.append((xs[k], xs[k + 1]))
        if pairs:
            runs.append((y, pairs))
        y += spacing
    if not runs:
        return []

    def world(x, y):
        return (x * ca - y * sa, x * sa + y * ca)

    chains = []
    for run_index, (y, pairs) in enumerate(runs):
        reversed_pass = (run_index % 2) == 1
        ordered_pairs = list(reversed(pairs)) if reversed_pass else pairs
        for x_left, x_right in ordered_pairs:
            if reversed_pass:
                start_x, end_x = x_right, x_left
            else:
                start_x, end_x = x_left, x_right
            start_pt = world(start_x, y)
            end_pt = world(end_x, y)
            chains.append([start_pt, end_pt])
    return chains


def stroke_expanded_contours(contours, width):
    if width <= 0:
        return contours
    expanded = []
    half = width / 2.0
    for contour in contours:
        if len(contour) < 2:
            continue
        if distance(contour[0], contour[-1]) <= 1e-9:
            expanded.append(contour)
            continue
        for a, b in zip(contour, contour[1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            length = math.hypot(dx, dy)
            if length <= 1e-9:
                continue
            nx, ny = -dy / length * half, dx / length * half
            expanded.append([
                (a[0] + nx, a[1] + ny),
                (b[0] + nx, b[1] + ny),
                (b[0] - nx, b[1] - ny),
                (a[0] - nx, a[1] - ny),
                (a[0] + nx, a[1] + ny),
            ])
    return expanded
def distance(a, b):
    return math.hypot(b[0] - a[0], b[1] - a[1])


def cubic(p0, p1, p2, p3, t):
    u = 1.0 - t
    return (u**3*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t**3*p3[0], u**3*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t**3*p3[1])


def quad(p0, p1, p2, t):
    u = 1.0 - t
    return (u*u*p0[0] + 2*u*t*p1[0] + t*t*p2[0], u*u*p0[1] + 2*u*t*p1[1] + t*t*p2[1])


def add_curve(points, fn, start, end, tolerance):
    rough = distance(start, end)
    steps = max(8, min(240, int(rough / max(tolerance, 0.01)) + 8))
    for i in range(1, steps + 1):
        points.append(fn(i / steps))


def path_to_contours(d, tolerance, cancel_check=None):
    tokens = COMMAND_RE.findall(d or "")
    contours, points = [], []
    i, cmd = 0, None
    current = start = (0.0, 0.0)
    last_cubic = last_quad = None

    def is_cmd(idx):
        return idx < len(tokens) and re.match(r"^[A-Za-z]$", tokens[idx])

    def read_float():
        nonlocal i
        check_cancelled(cancel_check)
        value = float(tokens[i])
        i += 1
        return value

    def absolutize(p, absolute):
        return p if absolute else (current[0] + p[0], current[1] + p[1])

    def line_to(p):
        nonlocal current
        points.append(p)
        current = p

    while i < len(tokens):
        check_cancelled(cancel_check)
        if is_cmd(i):
            cmd = tokens[i]
            i += 1
        if cmd is None:
            break
        absolute = cmd.isupper()
        op = cmd.upper()
        if op == "M":
            first = True
            while i + 1 < len(tokens) and not is_cmd(i):
                p = absolutize((read_float(), read_float()), absolute)
                if first:
                    if len(points) > 1:
                        contours.append(points)
                    points = [p]
                    current = start = p
                    first = False
                else:
                    line_to(p)
            cmd = "L" if absolute else "l"
        elif op == "L":
            while i + 1 < len(tokens) and not is_cmd(i):
                line_to(absolutize((read_float(), read_float()), absolute))
        elif op == "H":
            while i < len(tokens) and not is_cmd(i):
                x = read_float()
                line_to((x, current[1]) if absolute else (current[0] + x, current[1]))
        elif op == "V":
            while i < len(tokens) and not is_cmd(i):
                y = read_float()
                line_to((current[0], y) if absolute else (current[0], current[1] + y))
        elif op == "C":
            while i + 5 < len(tokens) and not is_cmd(i):
                c1 = absolutize((read_float(), read_float()), absolute)
                c2 = absolutize((read_float(), read_float()), absolute)
                p = absolutize((read_float(), read_float()), absolute)
                p0 = current
                add_curve(points, lambda t, p0=p0, c1=c1, c2=c2, p=p: cubic(p0, c1, c2, p, t), p0, p, tolerance)
                current, last_cubic, last_quad = p, c2, None
        elif op == "S":
            while i + 3 < len(tokens) and not is_cmd(i):
                c1 = (2*current[0] - last_cubic[0], 2*current[1] - last_cubic[1]) if last_cubic else current
                c2 = absolutize((read_float(), read_float()), absolute)
                p = absolutize((read_float(), read_float()), absolute)
                p0 = current
                add_curve(points, lambda t, p0=p0, c1=c1, c2=c2, p=p: cubic(p0, c1, c2, p, t), p0, p, tolerance)
                current, last_cubic, last_quad = p, c2, None
        elif op == "Q":
            while i + 3 < len(tokens) and not is_cmd(i):
                c = absolutize((read_float(), read_float()), absolute)
                p = absolutize((read_float(), read_float()), absolute)
                p0 = current
                add_curve(points, lambda t, p0=p0, c=c, p=p: quad(p0, c, p, t), p0, p, tolerance)
                current, last_quad, last_cubic = p, c, None
        elif op == "T":
            while i + 1 < len(tokens) and not is_cmd(i):
                c = (2*current[0] - last_quad[0], 2*current[1] - last_quad[1]) if last_quad else current
                p = absolutize((read_float(), read_float()), absolute)
                p0 = current
                add_curve(points, lambda t, p0=p0, c=c, p=p: quad(p0, c, p, t), p0, p, tolerance)
                current, last_quad, last_cubic = p, c, None
        elif op == "A":
            while i + 6 < len(tokens) and not is_cmd(i):
                read_float(); read_float(); read_float(); read_float(); read_float()
                line_to(absolutize((read_float(), read_float()), absolute))
                last_cubic = last_quad = None
        elif op == "Z":
            if points and distance(points[-1], start) > 1e-9:
                points.append(start)
            if len(points) > 1:
                contours.append(points)
            points = []
            current = start
            last_cubic = last_quad = None
        else:
            break
        if op not in ("C", "S"):
            last_cubic = None
        if op not in ("Q", "T"):
            last_quad = None
    if len(points) > 1:
        contours.append(points)
    return contours


def element_contours(element, tolerance, hatch_spacing=0.0, hatch_angle=0.0, hatch_pattern="crosshatch", shade_levels=1, shade_angle_step=90.0, expand_strokes=True, triangle_size=0.0, pattern_sizes=None, cancel_check=None):
    check_cancelled(cancel_check)
    tag = strip_ns(element.tag)
    contours = []
    if tag == "path":
        contours = path_to_contours(element.get("d"), tolerance, cancel_check)
    elif tag == "line":
        contours = [[(parse_length(element.get("x1")), parse_length(element.get("y1"))), (parse_length(element.get("x2")), parse_length(element.get("y2")))]]
    elif tag in ("polyline", "polygon"):
        pts = parse_points(element.get("points"))
        if tag == "polygon" and pts and pts[0] != pts[-1]:
            pts.append(pts[0])
        contours = [pts] if len(pts) > 1 else []
    elif tag == "rect":
        x, y = parse_length(element.get("x")), parse_length(element.get("y"))
        w, h = parse_length(element.get("width")), parse_length(element.get("height"))
        contours = [[(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]] if w > 0 and h > 0 else []
    elif tag in ("circle", "ellipse"):
        cx, cy = parse_length(element.get("cx")), parse_length(element.get("cy"))
        rx = parse_length(element.get("r") if tag == "circle" else element.get("rx"))
        ry = parse_length(element.get("r") if tag == "circle" else element.get("ry"))
        if rx > 0 and ry > 0:
            steps = max(24, min(360, int(2 * math.pi * max(rx, ry) / max(tolerance, 0.01))))
            contours = [[(cx + rx * math.cos(2 * math.pi * n / steps), cy + ry * math.sin(2 * math.pi * n / steps)) for n in range(steps + 1)]]
    fill_lines = []
    if hatch_spacing > 0 and has_visible_fill(element):
        darkness = fill_darkness(element)
        fill_polygons = [contour for contour in contours if len(contour) >= 3]
        if fill_polygons:
            fill_lines.extend(fill_region_pattern_contours(fill_polygons, hatch_spacing, hatch_angle, shade_levels, shade_angle_step, darkness, hatch_pattern, triangle_size, pattern_sizes, cancel_check))
    if expand_strokes and has_visible_stroke(element):
        contours = stroke_expanded_contours(contours, stroke_width(element))
    return contours + fill_lines


def parse_svg_geometry(svg_path, tolerance, flip_y, hatch_spacing=0.0, hatch_angle=0.0, hatch_pattern="crosshatch", shade_levels=1, shade_angle_step=90.0, expand_strokes=True, triangle_size=0.0, pattern_sizes=None, cancel_check=None):
    check_cancelled(cancel_check)
    tree = ET.parse(svg_path)
    root = tree.getroot()
    height = parse_length(root.get("height"), 0.0)
    view_box_height = 0.0
    view_box = root.get("viewBox")
    if view_box:
        nums = [float(x) for x in NUMBER_RE.findall(view_box)]
        if len(nums) == 4:
            view_box_height = nums[3]
            if not height:
                height = nums[3]

    id_map = {node.get("id"): node for node in root.iter() if node.get("id")}
    contours = []

    def walk(node, matrix, referenced=False, seen=None):
        check_cancelled(cancel_check)
        seen = seen or set()
        tag = strip_ns(node.tag)
        if tag in ("defs", "symbol") and not referenced:
            return
        combined = matrix @ parse_transform(node.get("transform"))
        if tag == "use":
            href = use_href(node)
            if href and href.startswith("#"):
                target_id = href[1:]
                target = id_map.get(target_id)
                if target is not None and target_id not in seen:
                    walk(target, combined @ Matrix(e=parse_length(node.get("x")), f=parse_length(node.get("y"))), True, seen | {target_id})
            return
        for contour in element_contours(node, tolerance, hatch_spacing, hatch_angle, hatch_pattern, shade_levels, shade_angle_step, expand_strokes, triangle_size, pattern_sizes, cancel_check):
            check_cancelled(cancel_check)
            contours.append([combined.apply(x, y) for x, y in contour])
        for child in list(node):
            walk(child, combined, referenced, seen)

    walk(root, Matrix())
    if flip_y:
        source_height = view_box_height or height or max((y for contour in contours for _, y in contour), default=0.0)
        contours = [[(x, source_height - y) for x, y in contour] for contour in contours]
    return contours


def apply_geometry_settings(contours, settings):
    contours = [[(x * settings.scale, y * settings.scale) for x, y in contour] for contour in contours]
    if getattr(settings, "compensate_pen_width", True):
        contours = compensate_physical_pen_width(contours, settings.pen_diameter_mm)
    return contours


def read_svg(svg_path, settings):
    contours = parse_svg_geometry(
        svg_path,
        settings.tolerance,
        settings.flip_y,
        float(getattr(settings, "hatch_spacing_mm", 0.0)),
        float(getattr(settings, "hatch_angle_deg", 0.0)),
        str(getattr(settings, "hatch_pattern", "crosshatch")),
        int(getattr(settings, "shade_levels", 1)),
        float(getattr(settings, "shade_angle_step_deg", 90.0)),
        True,
        float(getattr(settings, "triangle_size_mm", 0.0)),
        pattern_size_values(settings),
    )
    return apply_geometry_settings(contours, settings)


def contour_bounds(contours):
    pts = [point for contour in contours for point in contour]
    if not pts:
        return (0.0, 0.0, 0.0, 0.0)
    min_x = min(x for x, _ in pts)
    max_x = max(x for x, _ in pts)
    min_y = min(y for _, y in pts)
    max_y = max(y for _, y in pts)
    return min_x, min_y, max_x, max_y


def compensate_physical_pen_width(contours, pen_diameter):
    pen_diameter = max(float(pen_diameter), 0.0)
    if pen_diameter <= 0 or not contours:
        return contours
    min_x, min_y, max_x, max_y = contour_bounds(contours)
    span_x = max_x - min_x
    span_y = max_y - min_y
    if span_x <= pen_diameter and span_y <= pen_diameter:
        return contours
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    sx = max((span_x - pen_diameter) / span_x, 0.0) if span_x > pen_diameter else 1.0
    sy = max((span_y - pen_diameter) / span_y, 0.0) if span_y > pen_diameter else 1.0
    # Preserve lattice angles and circular features. The old independent X/Y
    # shrink distorted equilateral/hex patterns whenever the artwork bbox was
    # not square.
    scale = min(sx, sy)
    return [
        [(center_x + (x - center_x) * scale, center_y + (y - center_y) * scale) for x, y in contour]
        for contour in contours
    ]


def filtered_contour(contour):
    out = []
    for point in contour:
        if not out or distance(out[-1], point) > 1e-6:
            out.append(point)
    return out


def format_float(value):
    text = f"{value:.4f}".rstrip("0").rstrip(".")
    return text if text else "0"


def unwrap_angle(angle, previous):
    if previous is None:
        return angle
    while angle - previous > 180.0:
        angle -= 360.0
    while angle - previous < -180.0:
        angle += 360.0
    return angle



def contour_center(contours):
    pts = [point for contour in contours for point in contour]
    if not pts:
        return (0.0, 0.0)
    min_x = min(x for x, _ in pts)
    max_x = max(x for x, _ in pts)
    min_y = min(y for _, y in pts)
    max_y = max(y for _, y in pts)
    return ((min_x + max_x) / 2.0, (min_y + max_y) / 2.0)


def clip_segment_to_circle(a, b, center, radius):
    cx, cy = center
    ax, ay = a[0] - cx, a[1] - cy
    bx, by = b[0] - cx, b[1] - cy
    r2 = radius * radius
    a_in = ax * ax + ay * ay <= r2
    b_in = bx * bx + by * by <= r2
    if a_in and b_in:
        return a, b
    dx = bx - ax
    dy = by - ay
    A = dx * dx + dy * dy
    if A < 1e-18:
        return None
    B = 2.0 * (ax * dx + ay * dy)
    C = ax * ax + ay * ay - r2
    disc = B * B - 4.0 * A * C
    if disc < 0:
        return None
    sq = math.sqrt(disc)
    t1 = (-B - sq) / (2.0 * A)
    t2 = (-B + sq) / (2.0 * A)
    t_lo = max(0.0, min(t1, t2))
    t_hi = min(1.0, max(t1, t2))
    if t_hi <= t_lo:
        return None
    p_lo = (a[0] + t_lo * (b[0] - a[0]), a[1] + t_lo * (b[1] - a[1]))
    p_hi = (a[0] + t_hi * (b[0] - a[0]), a[1] + t_hi * (b[1] - a[1]))
    if a_in:
        return a, p_hi
    if b_in:
        return p_lo, b
    return p_lo, p_hi


def clip_contours_to_bed(contours, center, radius, cancel_check=None):
    if radius <= 0 or not contours:
        return list(contours)
    cx, cy = center
    r2 = radius * radius
    tol2 = max(radius * 1e-7, 1e-9) ** 2
    out = []
    for contour in contours:
        check_cancelled(cancel_check)
        if len(contour) < 2:
            continue
        current = []
        prev = contour[0]
        if (prev[0] - cx) ** 2 + (prev[1] - cy) ** 2 <= r2:
            current = [prev]
        for point in contour[1:]:
            check_cancelled(cancel_check)
            clipped = clip_segment_to_circle(prev, point, center, radius)
            point_in = (point[0] - cx) ** 2 + (point[1] - cy) ** 2 <= r2
            if clipped is None:
                if len(current) >= 2:
                    out.append(current)
                current = []
            else:
                cl_a, cl_b = clipped
                if not current:
                    current = [cl_a, cl_b]
                else:
                    last = current[-1]
                    if (cl_a[0] - last[0]) ** 2 + (cl_a[1] - last[1]) ** 2 > tol2:
                        if len(current) >= 2:
                            out.append(current)
                        current = [cl_a, cl_b]
                    else:
                        current.append(cl_b)
                if not point_in:
                    if len(current) >= 2:
                        out.append(current)
                    current = []
            prev = point
        if len(current) >= 2:
            out.append(current)
    return out
