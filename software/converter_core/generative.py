"""Deterministic generative patterns for the kaleidoscope converter.

The point is structured randomness, not noise. Every count, radius and phase
comes from a mathematical sequence - the golden angle, Weyl and van der Corput
low-discrepancy sequences, Fibonacci numbers, primes - so a seed always
produces the same drawing.

A pattern is composed in a single wedge the way an engraved mandala is drawn:
a layered centre (ringed rosette, ray spokes, bead rows), then concentric
*shape rings* - leaves, tulips, lenses, topographic bundles, feathers,
scallops, chevrons, rayed fans, diamond mesh, lace and bead rows - each
internally shaded with nested contour lines, with separator bundles, stud
flowers and bead rows between them, closed by a scalloped multi-line rim.

Detail counts are driven by *physical spacing*: fills, studs, dots, barbs and
hatch lines are placed one every few millimetres along the arc or across the
band, so the drawing gets complicated in the same way a real engraving does -
more elements as there is more room - and the intricacy knob deepens every
layer instead of merely adding rings. Every family draws between angle 0 and
angle ``wedge`` and rests on its band edges, so the caller's clip-and-mirror
step turns each band into a continuous ring instead of a cloud of fragments.
"""

from __future__ import annotations

import math

from .cancellation import check_cancelled

GOLDEN_ANGLE_DEG = 137.50776405003785
PHI = (1.0 + 5.0**0.5) / 2.0
WEYL_ALPHA = PHI - 1.0
TAU = 2.0 * math.pi


def van_der_corput(index, base=2):
    """Low-discrepancy value in [0, 1) for a positive integer *index*."""
    index = max(int(index), 1)
    value = 0.0
    denominator = 1.0
    while index:
        index, remainder = divmod(index, base)
        denominator *= base
        value += remainder / denominator
    return value


def weyl(index, alpha=WEYL_ALPHA):
    """Weyl sequence value in [0, 1): ``index * alpha`` modulo one."""
    return (max(int(index), 0) * alpha) % 1.0


def fibonacci(count):
    """First *count* Fibonacci numbers, starting 1, 1, 2, 3, ..."""
    out = []
    a, b = 1, 1
    for _ in range(max(int(count), 0)):
        out.append(a)
        a, b = b, a + b
    return out


def primes(count):
    """First *count* primes."""
    out = []
    candidate = 2
    while len(out) < max(int(count), 0):
        if all(candidate % p for p in out if p * p <= candidate):
            out.append(candidate)
        candidate += 1
    return out


def _polar(radius, angle):
    return radius * math.cos(angle), radius * math.sin(angle)


def _clamp(value, low, high):
    if high < low:
        return 0.5 * (low + high)
    return max(low, min(high, value))


def _count(length_mm, spacing_mm, low=1, high=240):
    """How many elements of *spacing_mm* fit along *length_mm*."""
    return int(max(low, min(high, length_mm / max(spacing_mm, 0.05))))


def _arc_contour(radius_of, wedge, samples):
    """Sample ``radius_of(t)`` from angle 0 to *wedge*, t in [0, 1]."""
    samples = max(int(samples), 2)
    return [
        _polar(radius_of(index / samples), wedge * index / samples)
        for index in range(samples + 1)
    ]


def _circle(centre, radius, sides=12):
    cx, cy = centre
    return [
        (
            cx + radius * math.cos(TAU * index / sides),
            cy + radius * math.sin(TAU * index / sides),
        )
        for index in range(sides + 1)
    ]


def _ring(centre, radius):
    """A circle whose facet length stays near 2 mm."""
    sides = int(max(12.0, min(96.0, TAU * abs(radius) / 2.0)))
    return _circle(centre, radius, sides)


def _leaf(a0, a1, r_base, r_tip, power, inner_ratio, samples):
    """A closed leaf spanning [a0, a1]; both ends rest on ``r_base``."""
    samples = max(int(samples), 4)
    span = r_tip - r_base
    points = []
    for index in range(samples + 1):
        t = index / samples
        radius = r_base + span * math.sin(math.pi * t) ** power
        points.append(_polar(radius, a0 + (a1 - a0) * t))
    for index in range(samples, -1, -1):
        t = index / samples
        radius = r_base + span * inner_ratio * math.sin(math.pi * t) ** power
        points.append(_polar(radius, a0 + (a1 - a0) * t))
    return points


def _arc(centre, radius, start, end, samples=10):
    """An arc around *centre* from angle *start* to *end*."""
    cx, cy = centre
    samples = max(int(samples), 2)
    return [
        (
            cx + radius * math.cos(start + (end - start) * index / samples),
            cy + radius * math.sin(start + (end - start) * index / samples),
        )
        for index in range(samples + 1)
    ]


def _nested_arcs(r_in, r_out, wedge, power, spacing, samples, cancel_check=None):
    """Contour lines nested inside a leaf profile, one every *spacing* mm."""
    span = r_out - r_in
    count = _count(span, spacing, 2, 40)
    out = []
    for index in range(count):
        check_cancelled(cancel_check)
        ratio = (index + 1) / (count + 1)
        out.append(
            _arc_contour(
                lambda t, ratio=ratio: r_in
                + span * ratio * math.sin(math.pi * t) ** power,
                wedge,
                samples,
            )
        )
    return out


# -- shape rings ---------------------------------------------------------
#
# Each family draws one ring of shapes inside the band r_in..r_out of a single
# wedge. Every curve reaches both seam angles or rests on the band edges, so
# the mirrored copies join into a continuous ring, and every detail count is
# spacing-driven so more room always means more drawing.


def _shade_spacing(level):
    """Contour-line spacing inside a shape: tightens as intricacy rises."""
    return 2.6 - 0.14 * level


def _leaf_ring(r_in, r_out, wedge, level, seed, cancel_check=None):
    """A large leaf with nested sub-leaves, contour fills and a vein."""
    span = r_out - r_in
    power = 0.60 + 0.35 * van_der_corput(seed + 1, 5)
    samples = 30 + 3 * level
    out = [_leaf(0.0, wedge, r_in, r_out, power, 0.30, samples)]
    nests = 1 + level // 3
    for index in range(nests):
        check_cancelled(cancel_check)
        ratio = 1.0 - 0.75 * (index + 1) / (nests + 1)
        out.append(
            _leaf(
                0.06 * wedge,
                0.94 * wedge,
                r_in,
                r_in + span * ratio,
                power + 0.10,
                0.30,
                samples,
            )
        )
    out.extend(
        _nested_arcs(
            r_in, r_out, wedge, power, _shade_spacing(level), samples, cancel_check
        )
    )
    mid = 0.5 * wedge
    out.append([_polar(r_in, mid), _polar(r_in + 0.98 * span, mid)])
    return out


def _tulip(r_in, r_out, wedge, level, seed, cancel_check=None):
    """A tall centre lobe between two side lobes, all contour-shaded."""
    span = r_out - r_in
    power = 0.55 + 0.30 * van_der_corput(seed + 3, 5)
    samples = 24 + 3 * level
    low, high = 0.18 * wedge, 0.82 * wedge
    out = [
        _leaf(low, high, r_in, r_out, power, 0.28, samples),
        _leaf(0.0, 0.46 * wedge, r_in, r_in + 0.72 * span, power, 0.28, samples),
        _leaf(0.54 * wedge, wedge, r_in, r_in + 0.72 * span, power, 0.28, samples),
    ]
    window = lambda t: _clamp((t - 0.18) / 0.64, 0.0, 1.0)
    count = _count(span, _shade_spacing(level), 2, 40)
    for index in range(count):
        check_cancelled(cancel_check)
        ratio = (index + 1) / (count + 1)
        out.append(
            _arc_contour(
                lambda t, ratio=ratio: r_in
                + span * ratio * math.sin(math.pi * window(t)) ** power,
                wedge,
                samples,
            )
        )
    for side in (0.14, 0.86):
        check_cancelled(cancel_check)
        bead = 0.10 * span
        out.append(_ring(_polar(r_in + span * 0.62, side * wedge), bead))
    return out


def _lens(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Two arcs of different bulge crossing at the seams, bead-strung."""
    span = r_out - r_in
    samples = 34 + 4 * level
    bulges = (0.60 + 0.40 * weyl(seed + 2), 1.40 + 0.60 * weyl(seed + 4))
    out = []
    for power in bulges:
        check_cancelled(cancel_check)
        out.append(
            _arc_contour(
                lambda t, power=power: r_in + span * math.sin(math.pi * t) ** power,
                wedge,
                samples,
            )
        )
    out.extend(
        _nested_arcs(
            r_in, r_out, wedge, bulges[0], _shade_spacing(level), samples, cancel_check
        )
    )
    mid = r_in + 0.5 * span
    count = _count(wedge * mid, 6.0 - 0.2 * level, 2, 40)
    for index in range(count):
        check_cancelled(cancel_check)
        t = (index + 0.5) / count
        bead = 0.05 * span
        out.append(_circle(_polar(mid, wedge * t), bead, 10))
    return out


def _bundle(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Nested topographic arches with radial ticks."""
    span = r_out - r_in
    power = 0.70 + 0.20 * weyl(seed + 5)
    samples = 34 + 4 * level
    out = []
    lines = _count(span, _shade_spacing(level), 3, 48)
    for index in range(lines):
        check_cancelled(cancel_check)
        amp = span * (1.0 - index / lines)
        out.append(
            _arc_contour(
                lambda t, amp=amp: r_in + amp * math.sin(math.pi * t) ** power,
                wedge,
                samples,
            )
        )
    ticks = _count(wedge * r_out, 9.0 - 0.4 * level, 2, 30)
    for index in range(ticks):
        check_cancelled(cancel_check)
        t = (index + 0.5) / ticks
        inner = r_in + span * (index % 3) * 0.25
        outer = r_in + span * (0.55 + 0.45 * van_der_corput(index + 1 + seed, 3))
        out.append([_polar(inner, wedge * t), _polar(outer, wedge * t)])
    return out


def _feather(r_in, r_out, wedge, level, seed, cancel_check=None):
    """A spine with radial barbs, forked at their tips, beaded every third."""
    span = r_out - r_in
    power = 0.50 + 0.30 * van_der_corput(seed + 6, 3)
    spine = 0.62 + 0.10 * weyl(seed + 7)
    samples = 34 + 4 * level

    def envelope(t):
        return r_in + span * math.sin(math.pi * t) ** power

    out = [
        _arc_contour(envelope, wedge, samples),
        _arc_contour(lambda t: r_in + span * spine, wedge, samples),
    ]
    barbs = _count(wedge * r_out, 7.0 - 0.35 * level, 4, 90)
    for index in range(barbs):
        check_cancelled(cancel_check)
        t = (index + 0.5) / barbs
        base = r_in + span * spine
        tip = envelope(t)
        angle = wedge * t
        out.append([_polar(min(base, tip), angle), _polar(max(base, tip), angle)])
        if index % 3 == 0:
            fork = span * 0.10
            out.append([_polar(tip, angle), _polar(max(tip - fork, r_in), angle - 0.12 * wedge / barbs)])
            out.append([_polar(tip, angle), _polar(max(tip - fork, r_in), angle + 0.12 * wedge / barbs)])
        if level >= 5 and index % 3 == 1:
            bead = 0.045 * span
            out.append(_circle(_polar(max(tip - bead, r_in), angle), bead, 8))
    return out


def _scallop(r_in, r_out, wedge, level, seed, cancel_check=None):
    """A stack of nested wave lines with a bead on every crest."""
    mid = 0.5 * (r_in + r_out)
    half = 0.5 * (r_out - r_in)
    waves = 2 + seed % 3
    phase = TAU * weyl(seed + 1)
    lines = _count(2.0 * half, 2.2, 2, 14)
    samples = 30 + 12 * waves
    out = []
    for line in range(lines):
        check_cancelled(cancel_check)
        amp = half * (0.35 + 0.45 * (line + 1) / lines)
        bias = half * 0.20 * (2.0 * weyl(seed + 3 * line + 7) - 1.0)
        centre = mid + bias

        def radius_of(t, centre=centre, amp=amp, phase=phase):
            return centre + amp * math.cos(TAU * waves * t + phase)

        out.append(_arc_contour(radius_of, wedge, samples))
    crests = _count(wedge * (r_in + r_out) * 0.5, 5.0 - 0.2 * level, 1, 40)
    for index in range(crests):
        check_cancelled(cancel_check)
        t = (index + 0.5) / crests
        if (index + seed) % 2:
            continue
        out.append(
            _circle(_polar(mid + half * 0.30, wedge * t), 0.05 * (r_out - r_in), 8)
        )
    return out


def _chevron(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Triangle teeth with nested inner teeth and beaded apexes."""
    arc = wedge * (r_in + r_out) * 0.5
    teeth = _count(arc, 16.0 - 0.8 * level, 1, 24)
    rise = 0.45 + 0.5 * van_der_corput(seed + 2, 3)
    peak = r_in + (r_out - r_in) * rise
    samples = 14 + 2 * level
    out = []
    for tooth in range(teeth):
        check_cancelled(cancel_check)
        a0 = wedge * tooth / teeth
        a1 = wedge * (tooth + 1) / teeth
        base = [
            _polar(r_in, a0 + (a1 - a0) * index / samples)
            for index in range(samples + 1)
        ]
        out.append(base + [_polar(peak, 0.5 * (a0 + a1))])
        inner = r_in + 0.45 * (peak - r_in)
        if level >= 4:
            out.append(
                [_polar(r_in, a0), _polar(inner, 0.5 * (a0 + a1)), _polar(r_in, a1)]
            )
        if level >= 6:
            out.append(_circle(_polar(peak - 0.10 * (r_out - r_in), 0.5 * (a0 + a1)), 0.06 * (r_out - r_in), 8))
    out.append(_arc_contour(lambda t: r_out, wedge, 8 + 2 * level))
    return out


def _rays(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Rayed fan with a tip arc, alternating beam lengths and tip beads."""
    span = r_out - r_in
    count = _count(wedge * r_in, 7.0 - 0.35 * level, 1, 60)
    out = []
    for index in range(count):
        check_cancelled(cancel_check)
        t = (index + 0.5) / count
        a = wedge * t
        half_width = 0.14 * wedge / count
        reach = r_in + span * (0.72 + 0.28 * van_der_corput(index + 1 + seed, 3))
        out.append([_polar(r_in, a - half_width), _polar(reach, a), _polar(r_in, a + half_width)])
        if level >= 5:
            out.append(_circle(_polar(reach - 0.05 * span, a), 0.04 * span, 8))
    out.append(_arc_contour(lambda t: r_out, wedge, 24 + 3 * level))
    return out


def _mesh(r_in, r_out, wedge, level, seed, cancel_check=None):
    """A diamond lattice: two families of slanted lines crossing."""
    span = r_out - r_in
    arc = wedge * (r_in + r_out) * 0.5
    count = _count(arc, 6.0 - 0.28 * level, 3, 90)
    slant = 1.5 * wedge / count
    out = []
    for index in range(count):
        check_cancelled(cancel_check)
        a = wedge * (index + 0.5) / count
        out.append([_polar(r_in, a), _polar(r_out, _clamp(a + slant, 0.0, wedge))])
        out.append([_polar(r_in, _clamp(a + slant, 0.0, wedge)), _polar(r_out, a)])
    out.append(_arc_contour(lambda t: r_in, wedge, 20 + 2 * level))
    out.append(_arc_contour(lambda t: r_out, wedge, 20 + 2 * level))
    return out


def _lace(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Rows of overlapping scale arcs with bead eyes."""
    span = r_out - r_in
    rows = _count(span, 3.6, 2, 14)
    row_h = span / rows
    arc_r = 0.45 * row_h
    out = []
    for row in range(rows):
        check_cancelled(cancel_check)
        rho = r_in + (row + 0.95) * row_h
        count = _count(wedge * rho, 4.4 - 0.15 * level, 2, 90)
        offset = 0.5 * (row % 2)
        for index in range(count):
            angle = wedge * (index + 0.5 + offset) / count
            half = rho * wedge / count * 0.60
            delta = math.asin(_clamp(half / max(arc_r, 1e-6), -1.0, 1.0))
            cx, cy = _polar(max(rho - arc_r, 0.01), angle)
            out.append(
                _arc((cx, cy), arc_r, angle - delta, angle + delta, 9)
            )
            if level >= 4 and (index + row) % 2 == 0:
                eye = 0.20 * arc_r
                out.append(_circle(_polar(rho - eye, angle), eye, 8))
    return out


def _beadrow(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Several rows of beads and stud flowers packed through the band."""
    span = r_out - r_in
    rows = _count(span, 3.4, 2, 14)
    row_h = span / rows
    out = []
    for row in range(rows):
        check_cancelled(cancel_check)
        rho = r_in + (row + 0.5) * row_h
        size = min(0.34 * row_h, 1.8)
        count = _count(wedge * rho, 3.6 - 0.12 * level, 2, 90)
        for index in range(count):
            t = (index + 0.5) / count
            wobble = 0.20 * row_h * (2.0 * weyl(index + seed + row) - 1.0)
            centre_r = _clamp(
                rho + wobble, r_in + 1.1 * size, r_out - 1.1 * size
            )
            centre = _polar(centre_r, wedge * t)
            if (index + row) % 3 == 0:
                out.extend(_flower(centre, size, seed + index + row))
            else:
                out.append(_circle(centre, size * 0.55, 10))
    return out


FAMILIES = (
    "leaf",
    "tulip",
    "lens",
    "bundle",
    "feather",
    "scallop",
    "chevron",
    "rays",
    "mesh",
    "lace",
    "beadrow",
)

_FUNCTIONS = {
    "leaf": _leaf_ring,
    "tulip": _tulip,
    "lens": _lens,
    "bundle": _bundle,
    "feather": _feather,
    "scallop": _scallop,
    "chevron": _chevron,
    "rays": _rays,
    "mesh": _mesh,
    "lace": _lace,
    "beadrow": _beadrow,
}


# -- ornaments and framing ----------------------------------------------


def _flower(centre, size, seed):
    """A small stud flower: a bead eye ringed by bead petals."""
    petals = 5 + seed % 2
    cx, cy = centre
    out = [_circle(centre, size * 0.34, 10)]
    for index in range(petals):
        angle = TAU * index / petals + 0.6 * weyl(seed + index, WEYL_ALPHA)
        dx, dy = _polar(size * 0.66, angle)
        out.append(_circle((cx + dx, cy + dy), size * 0.30, 10))
    return out


def _studs(circle_r, band, spacing, size, wedge, seed, cancel_check=None):
    """A ring of small flowers and beads, one every *spacing* millimetres."""
    count = _count(wedge * circle_r, spacing, 1, 90)
    out = []
    for index in range(count):
        check_cancelled(cancel_check)
        wobble = 0.5 * band * (2.0 * weyl(index + seed) - 1.0)
        centre_r = _clamp(
            circle_r + wobble,
            circle_r - 0.5 * band + 1.2 * size,
            circle_r + 0.5 * band - 1.2 * size,
        )
        centre = _polar(centre_r, wedge * (index + 0.5) / count)
        if index % 2:
            out.append(_circle(centre, size * 0.55, 10))
        else:
            out.extend(_flower(centre, size, seed + index))
    return out


def _dots(circle_r, wedge, spacing, size, seed, cancel_check=None):
    """A ring of tiny beads, one every *spacing* millimetres."""
    count = _count(wedge * circle_r, spacing, 1, 160)
    out = []
    for index in range(count):
        check_cancelled(cancel_check)
        if (index + seed) % 4 == 3:
            continue
        out.append(
            _circle(_polar(circle_r, wedge * (index + 0.5) / count), size, 8)
        )
    return out


def _separator(radius_at, outer, wedge, level, seed, cancel_check=None):
    """A tight bundle of rings separating one shape ring from the next."""
    lines = 3 + level // 2
    spacing = 0.0045 * outer
    out = []
    for index in range(lines):
        check_cancelled(cancel_check)
        ring = radius_at + spacing * (index - (lines - 1) / 2.0)
        out.append(_arc_contour(lambda t, ring=ring: ring, wedge, 30 + 2 * level))
    return out


def _rosette(radius, wedge, level, seed, cancel_check=None):
    """The inner centre: nested petal leaves inside two tight rings."""
    if radius <= 1.0:
        return []
    check_cancelled(cancel_check)
    power = 0.60 + 0.35 * van_der_corput(seed + 1, 3)
    samples = 24 + 4 * level
    out = [
        _arc_contour(lambda t: radius, wedge, 14 + 2 * level),
        _arc_contour(lambda t: radius * 0.86, wedge, 14 + 2 * level),
    ]
    nests = 2 + level // 3
    for index in range(nests):
        ratio = 1.0 - 0.72 * (index + 1) / (nests + 1)
        out.append(
            _leaf(
                0.05 * wedge,
                0.95 * wedge,
                radius * 0.22,
                radius * (0.22 + 0.72 * ratio),
                power,
                0.35,
                samples,
            )
        )
    out.append(_ring((0.0, 0.0), radius * 0.20))
    out.append(_ring((0.0, 0.0), radius * 0.12))
    if level >= 4:
        out.extend(_dots(radius * 0.66, wedge, 4.0 - 0.15 * level, radius * 0.035, seed, cancel_check))
    return out


def _starburst(radius, wedge, level, seed, cancel_check=None):
    """A ray ring: uneven spokes between two rings, beads between the rays."""
    if radius <= 2.0:
        return []
    spokes = _count(wedge * radius, 9.0 - 0.4 * level, 3, 40)
    inner = radius * 0.50
    outer = radius * 0.95
    out = []
    for index in range(spokes):
        check_cancelled(cancel_check)
        angle = wedge * (index + 0.5) / spokes
        length = inner + (outer - inner) * (0.35 + 0.65 * weyl(index + seed + 1))
        out.append([_polar(inner, angle), _polar(length, angle)])
        if level >= 4:
            out.append(
                _circle(_polar(inner, angle), 0.035 * radius, 8)
            )
    for ratio in (0.50, 0.72, 0.95):
        out.append(_ring((0.0, 0.0), radius * ratio))
    return out


def _rim(radius, wedge, level, seed, cancel_check=None):
    """Scalloped multi-line outer boundary with stud and dot rows."""
    waves = _count(wedge * radius, 11.0 - 0.5 * level, 4, 60)
    amp = 0.014 * radius
    out = [
        _arc_contour(
            lambda t: radius - amp + amp * math.cos(TAU * waves * t),
            wedge,
            18 + 6 * waves,
        )
    ]
    for index in range(2 + level // 3):
        check_cancelled(cancel_check)
        out.append(
            _arc_contour(lambda t, r=radius * (0.988 - 0.011 * index): r, wedge, 26 + 3 * level)
        )
    out.extend(
        _studs(
            radius * 0.930,
            radius * 0.026,
            4.0 - 0.15 * level,
            radius * (0.006 + 0.0006 * level),
            wedge,
            seed + 3,
            cancel_check,
        )
    )
    if level >= 5:
        out.extend(
            _dots(radius * 0.955, wedge, 4.5 - 0.2 * level, radius * 0.008, seed + 7, cancel_check)
        )
    return out


def random_pattern(seed=0, intricacy=5, radius_mm=180.0, wedge_deg=15.0, cancel_check=None):
    """Return a mandala in millimetres, centred on the origin, y up.

    ``intricacy`` 1..10 deepens every layer: more shape rings, tighter contour
    shading inside each shape, and denser separators, studs and bead rows.
    ``wedge_deg`` must be the wedge the caller will clip to
    (``180/divisions``) because every ring is composed inside exactly one wedge.
    """
    seed = int(seed) % 100000
    level = max(1, min(int(intricacy), 10))
    radius = max(float(radius_mm), 1.0)
    wedge = math.radians(max(float(wedge_deg), 0.5))

    rings = 3 + (2 * level) // 3
    centre_r = radius * (0.075 + 0.009 * level)
    gap = radius * 0.018
    outer = radius * 0.900
    height = max((outer - centre_r - (rings - 1) * gap) / rings, radius * 0.04)

    contours = []
    contours.extend(_rosette(centre_r, wedge, level, seed + 5, cancel_check))
    if level >= 3:
        contours.extend(_starburst(centre_r, wedge, level, seed + 9, cancel_check))

    for ring in range(rings):
        check_cancelled(cancel_check)
        name = FAMILIES[(seed + 5 * ring) % len(FAMILIES)]
        r_in = centre_r + ring * (height + gap)
        r_out = r_in + height
        contours.extend(
            _FUNCTIONS[name](r_in, r_out, wedge, level, seed + 17 * ring + 1, cancel_check)
        )
        center_line = r_out + 0.5 * gap
        contours.extend(
            _separator(center_line, radius, wedge, level, seed + ring, cancel_check)
        )
        if ring < rings - 1 and level >= 2:
            contours.extend(
                _studs(
                    center_line,
                    gap * 0.9,
                    5.0 - 0.2 * level,
                    radius * (0.004 + 0.0003 * level),
                    wedge,
                    seed + 50 + ring,
                    cancel_check,
                )
            )

    contours.extend(_rim(radius, wedge, level, seed + 31, cancel_check))
    return contours
