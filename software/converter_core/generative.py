"""Deterministic generative patterns for the kaleidoscope converter.

The point is structured randomness, not noise. Every count, radius and phase
comes from a mathematical sequence - the golden angle, Weyl and van der Corput
low-discrepancy sequences, Fibonacci numbers, primes - so a seed always
produces the same drawing, and the intricacy knob only changes how much of the
sequence is used.

A pattern is composed in a single wedge the way an engraved mandala is drawn:
a rayed centre rosette, then concentric *shape rings* - large leaves, tulips,
lenses, topographic bands, feathers, scallops, chevrons or rayed fans - each
filled with nested contour lines, separated by tight multi-line rings with
flower studs, and closed by a scalloped, beaded rim. Every family draws between
angle 0 and angle ``wedge`` and rests on its band edges, so the caller's
clip-and-mirror step turns each ring into a continuous band of shapes with
mirrored cusps at the sector seams instead of a cloud of broken fragments.
Intricacy raises the ring count and the shading depth, so the top of the range
reads as an engraving rather than a few outline rings.
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


def _arc_contour(radius_of, wedge, samples):
    """Sample ``radius_of(t)`` from angle 0 to *wedge*, t in [0, 1]."""
    samples = max(int(samples), 2)
    return [
        _polar(radius_of(index / samples), wedge * index / samples)
        for index in range(samples + 1)
    ]


def _circle(centre, radius, sides=14):
    cx, cy = centre
    return [
        (
            cx + radius * math.cos(TAU * index / sides),
            cy + radius * math.sin(TAU * index / sides),
        )
        for index in range(sides + 1)
    ]


def _ring(centre, radius):
    """A circle whose facet length stays near 2 mm, for rings that read as arcs."""
    sides = int(max(12.0, min(72.0, TAU * abs(radius) / 2.0)))
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


# -- shape rings ---------------------------------------------------------
#
# Each family draws one ring of shapes inside the band r_in..r_out of a single
# wedge. Every curve reaches both seam angles or rests on the band edges, so
# the mirrored copies join into a continuous ring, and every detail count only
# grows with ``level`` so the intricacy knob never removes shading.


def _leaf_ring(r_in, r_out, wedge, level, seed, cancel_check=None):
    """One large shaded leaf per wedge - the engraver's basic shape."""
    span = r_out - r_in
    power = 0.60 + 0.35 * van_der_corput(seed + 1, 5)
    samples = 26 + 3 * level
    out = [_leaf(0.0, wedge, r_in, r_out, power, 0.35, samples)]
    fills = 2 + level // 2
    for index in range(fills):
        check_cancelled(cancel_check)
        ratio = (index + 1) / (fills + 1)
        out.append(
            _arc_contour(
                lambda t, ratio=ratio: r_in
                + span * ratio * math.sin(math.pi * t) ** power,
                wedge,
                samples,
            )
        )
    return out


def _tulip(r_in, r_out, wedge, level, seed, cancel_check=None):
    """A tall centre lobe between two side lobes, shaded from the inside."""
    span = r_out - r_in
    power = 0.55 + 0.30 * van_der_corput(seed + 3, 5)
    samples = 22 + 3 * level
    low, high = 0.18 * wedge, 0.82 * wedge
    out = [
        _leaf(low, high, r_in, r_out, power, 0.30, samples),
        _leaf(0.0, 0.46 * wedge, r_in, r_in + 0.72 * span, power, 0.30, samples),
        _leaf(0.54 * wedge, wedge, r_in, r_in + 0.72 * span, power, 0.30, samples),
    ]
    fills = 1 + level // 3
    for index in range(fills):
        check_cancelled(cancel_check)
        ratio = (index + 1) / (fills + 1)
        out.append(
            _arc_contour(
                lambda t, ratio=ratio: r_in
                + span
                * ratio
                * math.sin(math.pi * _clamp((t - 0.18) / 0.64, 0.0, 1.0))
                ** power,
                wedge,
                samples,
            )
        )
    return out


def _lens(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Two arcs of different bulge crossing at the seams - a lens ring."""
    span = r_out - r_in
    samples = 30 + 4 * level
    bulges = (0.60 + 0.40 * weyl(seed + 2), 1.40 + 0.60 * weyl(seed + 4))
    out = []
    for power in bulges:
        check_cancelled(cancel_check)
        out.append(
            _arc_contour(
                lambda t, power=power: r_in
                + span * math.sin(math.pi * t) ** power,
                wedge,
                samples,
            )
        )
    fills = level // 3
    for index in range(fills):
        ratio = (index + 1) / (fills + 1)
        out.append(
            _arc_contour(
                lambda t, ratio=ratio: r_in
                + span * ratio * math.sin(math.pi * t) ** bulges[0],
                wedge,
                samples,
            )
        )
    return out


def _bundle(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Nested arches from the inner edge outward - topographic shading."""
    span = r_out - r_in
    lines = 2 + level // 2
    power = 0.70 + 0.20 * weyl(seed + 5)
    samples = 30 + 4 * level
    out = []
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
    return out


def _feather(r_in, r_out, wedge, level, seed, cancel_check=None):
    """A spine with radial barbs - the striped fern look."""
    span = r_out - r_in
    power = 0.50 + 0.30 * van_der_corput(seed + 6, 3)
    spine = 0.62 + 0.10 * weyl(seed + 7)
    samples = 30 + 4 * level

    def envelope(t):
        return r_in + span * math.sin(math.pi * t) ** power

    out = [
        _arc_contour(envelope, wedge, samples),
        _arc_contour(lambda t: r_in + span * spine, wedge, samples),
    ]
    barbs = 6 + level
    for index in range(barbs):
        check_cancelled(cancel_check)
        t = (index + 0.5) / barbs
        base = r_in + span * spine
        tip = envelope(t)
        out.append(
            [_polar(min(base, tip), wedge * t), _polar(max(base, tip), wedge * t)]
        )
    return out


def _scallop(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Undulating full-span arcs - the classic wave-trim band."""
    mid = 0.5 * (r_in + r_out)
    half = 0.5 * (r_out - r_in)
    waves = 2 + seed % 3
    phase = TAU * weyl(seed + 1)
    lines = 1 + level // 3
    samples = 30 + 12 * waves
    out = []
    for line in range(lines):
        check_cancelled(cancel_check)
        amp = half * (0.50 + 0.30 * van_der_corput(line + 1, 3))
        bias = half * 0.20 * (2.0 * weyl(seed + 3 * line + 7) - 1.0)
        centre = mid + bias

        def radius_of(t, centre=centre, amp=amp, phase=phase):
            return centre + amp * math.cos(TAU * waves * t + phase)

        out.append(_arc_contour(radius_of, wedge, samples))
    out.append(_arc_contour(lambda t: r_out, wedge, 8 + 2 * waves))
    return out


def _chevron(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Triangle teeth sitting on the inner edge of the band."""
    teeth = 1 + level // 5
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
        if level >= 6:
            inner = r_in + 0.45 * (peak - r_in)
            out.append(
                [
                    _polar(r_in, a0),
                    _polar(inner, 0.5 * (a0 + a1)),
                    _polar(r_in, a1),
                ]
            )
    out.append(_arc_contour(lambda t: r_out, wedge, 8 + 2 * level))
    return out


def _rays(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Tapered beams with a bead at each tip."""
    count = 1 + level // 4
    span = r_out - r_in
    bead = 0.045 + 0.035 * van_der_corput(seed + 4, 3)
    out = []
    for index in range(count):
        check_cancelled(cancel_check)
        a = wedge * (index + 0.5) / count
        half_width = 0.16 * wedge / count
        out.append(
            [
                _polar(r_in, a - half_width),
                _polar(r_out, a),
                _polar(r_in, a + half_width),
            ]
        )
        if level >= 6:
            out.append(_circle(_polar(r_out - 1.3 * bead * span, a), bead * span))
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
}


# -- ornaments and framing ----------------------------------------------


def _flower(centre, size, seed):
    """A small stud flower: a bead eye ringed by bead petals."""
    petals = 5 + seed % 2
    cx, cy = centre
    out = [_circle(centre, size * 0.34, sides=10)]
    for index in range(petals):
        angle = TAU * index / petals + 0.6 * weyl(seed + index, WEYL_ALPHA)
        dx, dy = _polar(size * 0.66, angle)
        out.append(_circle((cx + dx, cy + dy), size * 0.30, sides=10))
    return out


def _studs(circle_r, band, count, size, wedge, seed, cancel_check=None):
    """A ring of small flowers and beads riding between two shape rings."""
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
            out.append(_circle(centre, size * 0.55, sides=10))
        else:
            out.extend(_flower(centre, size, seed + index))
    return out


def _separator(radius_at, outer, wedge, level, seed, cancel_check=None):
    """Two to four tight rings that separate one shape ring from the next."""
    lines = 2 + level // 4
    spacing = 0.007 * outer
    out = []
    for index in range(lines):
        check_cancelled(cancel_check)
        ring = radius_at + spacing * (index - (lines - 1) / 2.0)
        out.append(_arc_contour(lambda t, ring=ring: ring, wedge, 26 + level))
    return out


def _rosette(radius, wedge, level, seed, cancel_check=None):
    """The centre: a shaded petal flower inside a ring, with a bead eye."""
    if radius <= 1.0:
        return []
    check_cancelled(cancel_check)
    power = 0.60 + 0.35 * van_der_corput(seed + 1, 3)
    samples = 20 + 3 * level
    out = [_arc_contour(lambda t: radius, wedge, 10 + 2 * level)]
    out.append(_leaf(0.0, wedge, radius * 0.30, radius * 0.94, power, 0.42, samples))
    out.append(_ring((0.0, 0.0), radius * 0.17))
    if level >= 4:
        out.append(_ring((0.0, 0.0), radius * 0.32))
    if level >= 7:
        out.append(
            _leaf(0.0, wedge, radius * 0.30, radius * 0.66, power + 0.2, 0.40, samples)
        )
    return out


def _starburst(radius, wedge, level, seed, cancel_check=None):
    """Fine spokes of uneven length between a few tight rings."""
    if radius <= 2.0:
        return []
    # The mirror step repeats this wedge 2 * divisions times, so the inner
    # radius has to keep the copies apart: spokes that reach too far in turn
    # the centre into an inked blob.
    spokes = 3 + level // 4
    inner = radius * 0.50
    outer = radius * 0.95
    out = []
    for index in range(spokes):
        check_cancelled(cancel_check)
        angle = wedge * (index + 0.5) / spokes
        length = inner + (outer - inner) * (0.35 + 0.65 * weyl(index + seed + 1))
        out.append([_polar(inner, angle), _polar(length, angle)])
    for ratio in (0.50, 0.72):
        out.append(_ring((0.0, 0.0), radius * ratio))
    return out


def _rim(radius, wedge, level, seed, cancel_check=None):
    """The scalloped, multi-line outer boundary with its stud ring."""
    waves = 5 + level // 2
    amp = 0.014 * radius
    out = [
        _arc_contour(
            lambda t: radius - amp + amp * math.cos(TAU * waves * t),
            wedge,
            18 + 6 * waves,
        )
    ]
    out.append(_arc_contour(lambda t: radius * 0.975, wedge, 20 + 4 * level))
    if level >= 4:
        out.append(_arc_contour(lambda t: radius * 0.958, wedge, 20 + 4 * level))
    count = 2 + level // 2
    size = radius * (0.011 + 0.001 * level)
    out.extend(
        _studs(radius * 0.936, radius * 0.028, count, size, wedge, seed + 3, cancel_check)
    )
    return out


def random_pattern(seed=0, intricacy=5, radius_mm=180.0, wedge_deg=15.0, cancel_check=None):
    """Return a mandala in millimetres, centred on the origin, y up.

    ``intricacy`` 1..10 grows the ring count and the shading depth inside every
    shape. ``wedge_deg`` must be the wedge the caller will clip to
    (``180/divisions``) because every ring is composed inside exactly one wedge.
    """
    seed = int(seed) % 100000
    level = max(1, min(int(intricacy), 10))
    radius = max(float(radius_mm), 1.0)
    wedge = math.radians(max(float(wedge_deg), 0.5))

    rings = 2 + level // 3
    centre_r = radius * (0.11 + 0.008 * level)
    gap = radius * 0.030
    outer = radius * 0.900
    height = max((outer - centre_r - (rings - 1) * gap) / rings, radius * 0.05)

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
        if level >= 4 and ring % 2 == 0:
            contours.extend(
                _studs(
                    center_line,
                    gap * 0.7,
                    2 + level // 3,
                    radius * (0.008 + 0.0008 * level),
                    wedge,
                    seed + 50 + ring,
                    cancel_check,
                )
            )

    contours.extend(_rim(radius, wedge, level, seed + 31, cancel_check))
    return contours
