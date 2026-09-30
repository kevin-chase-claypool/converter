"""Deterministic generative patterns for the kaleidoscope converter.

The point is structured randomness, not noise. Every count, radius and phase
comes from a mathematical sequence - the golden angle, Weyl and van der Corput
low-discrepancy sequences, Fibonacci numbers, primes - so a seed always
produces the same drawing, and the intricacy knob only changes how much of the
sequence is used.

A pattern is composed in a single wedge: a central rosette, then a geometric
ladder of concentric bands (scallops, petals, wicker, rays, beads, chevrons or
spirals), closed by an outer rim. Every family draws curves that span the wedge
from angle 0 to angle ``wedge`` and meet the band edges, so the caller's
clip-and-mirror step turns each band into a continuous ring with mirrored cusps
at the sector seams - the classic kaleidoscope look - instead of a cloud of
broken fragments.
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


def _leaf(a0, a1, r_base, r_tip, power, inner_ratio, samples):
    """A closed petal spanning [a0, a1]; both ends rest on ``r_base``."""
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


# -- band families -------------------------------------------------------
#
# Each family draws into the band r_in..r_out of a single wedge and returns a
# list of contours. Curves reach both seam angles so the mirrored copies join
# into rings; sample counts and line counts only grow with ``level`` so the
# intricacy knob never removes detail.


def _scallop(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Undulating full-span arcs - the classic wave-trim band."""
    mid = 0.5 * (r_in + r_out)
    half = 0.5 * (r_out - r_in)
    waves = 2 + seed % 3
    phase = TAU * weyl(seed + 1)
    lines = 1 + level // 6
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


def _petals(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Garlands of closed leaves; nested outlines when intricate."""
    span = r_out - r_in
    count = 1 + seed % 2
    power = 0.55 + 0.35 * van_der_corput(seed + 1, 5)
    samples = 24 + 4 * level
    out = []
    for index in range(count):
        check_cancelled(cancel_check)
        a0 = wedge * index / count
        a1 = wedge * (index + 1) / count
        out.append(_leaf(a0, a1, r_in, r_out, power, 0.45, samples))
        if level >= 6:
            out.append(
                _leaf(a0, a1, r_in, r_in + 0.62 * span, power + 0.25, 0.42, samples)
            )
    return out


def _wicker(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Two opposed sine arcs that braid across the band."""
    mid = 0.5 * (r_in + r_out)
    half = 0.5 * (r_out - r_in)
    waves = 1 + seed % 2
    phase = TAU * weyl(seed + 5)
    amp = 0.75 * half
    samples = 34 + 14 * waves
    out = []
    for sign in (1.0, -1.0):
        check_cancelled(cancel_check)

        def radius_of(t, sign=sign):
            return mid + sign * amp * math.sin(TAU * waves * t + phase)

        out.append(_arc_contour(radius_of, wedge, samples))
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
            out.append(
                _circle(_polar(r_out - 1.3 * bead * span, a), bead * span)
            )
    return out


def _beads(r_in, r_out, wedge, level, seed, cancel_check=None):
    """A string of jewels riding a gentle wave through the band."""
    mid = 0.5 * (r_in + r_out)
    half = 0.5 * (r_out - r_in)
    count = 3 + level // 2 + seed % 2
    waves = 1 + (seed // 3) % 2
    phase = TAU * weyl(seed + 11)
    out = []
    for index in range(count):
        check_cancelled(cancel_check)
        t = (index + 0.5) / count
        bead = half * (0.16 + 0.20 * van_der_corput(index + 1 + seed, 3))
        climb = (half - 1.1 * bead) * math.sin(TAU * waves * t + phase)
        centre_r = _clamp(mid + climb, r_in + 1.1 * bead, r_out - 1.1 * bead)
        out.append(_circle(_polar(centre_r, wedge * t), bead))
    return out


def _chevron(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Triangle teeth sitting on the inner edge of the band."""
    teeth = 1 + seed % 2
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


def _spiral(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Nested swooshes that read as pinwheel arms once mirrored."""
    span = r_out - r_in
    samples = 34 + 6 * level
    power = 0.8 + 0.5 * weyl(seed + 3)
    arms = 2 + (1 if level >= 6 else 0)
    out = []
    for arm in range(arms):
        check_cancelled(cancel_check)
        low = arm / arms
        high = (arm + 1) / arms

        def radius_of(t, low=low, high=high):
            eased = low + (high - low) * t
            return r_in + span * eased**power

        out.append(_arc_contour(radius_of, wedge, samples))
    return out


FAMILIES = ("scallop", "petals", "wicker", "rays", "beads", "chevron", "spiral")

_FUNCTIONS = {
    "scallop": _scallop,
    "petals": _petals,
    "wicker": _wicker,
    "rays": _rays,
    "beads": _beads,
    "chevron": _chevron,
    "spiral": _spiral,
}


def _rosette(radius, wedge, level, seed, cancel_check=None):
    """The centre: a petal flower inside a ring, with a bead at the eye."""
    if radius <= 1.0:
        return []
    check_cancelled(cancel_check)
    power = 0.60 + 0.35 * van_der_corput(seed + 1, 3)
    samples = 20 + 3 * level
    out = [_arc_contour(lambda t: radius, wedge, 10 + 2 * level)]
    out.append(_leaf(0.0, wedge, radius * 0.30, radius * 0.94, power, 0.42, samples))
    out.append(_circle((0.0, 0.0), radius * 0.17))
    if level >= 4:
        out.append(_circle((0.0, 0.0), radius * 0.32))
    return out


def random_pattern(seed=0, intricacy=5, radius_mm=180.0, wedge_deg=15.0, cancel_check=None):
    """Return a mandala in millimetres, centred on the origin, y up.

    ``intricacy`` 1..10 grows the band count, wave counts and bead strings.
    ``wedge_deg`` must be the wedge the caller will clip to (``180/divisions``)
    because every band is composed inside exactly one wedge.
    """
    seed = int(seed) % 100000
    level = max(1, min(int(intricacy), 10))
    radius = max(float(radius_mm), 1.0)
    wedge = math.radians(max(float(wedge_deg), 0.5))

    bands = 2 + level // 3
    inner = 0.14 + 0.012 * level
    edges = [
        radius * (inner + (1.0 - inner) * (index / bands) ** 0.86)
        for index in range(bands + 1)
    ]

    contours = []
    contours.extend(_rosette(edges[0], wedge, level, seed + 5, cancel_check))
    for band in range(bands):
        check_cancelled(cancel_check)
        name = FAMILIES[(seed + 3 * band) % len(FAMILIES)]
        contours.extend(
            _FUNCTIONS[name](
                edges[band], edges[band + 1], wedge, level, seed + 17 * band + 1, cancel_check
            )
        )

    contours.append(_arc_contour(lambda t: radius, wedge, 12 + level))
    if level >= 4:
        contours.append(_arc_contour(lambda t: radius * 0.994, wedge, 12 + level))
    if level >= 5:
        bead = radius * (0.008 + 0.003 * (level - 5))
        count = 2 + level // 3 + seed % 2
        for index in range(count):
            check_cancelled(cancel_check)
            angle = wedge * (index + 0.5) / count
            contours.append(_circle(_polar(radius - 1.3 * bead, angle), bead))
    return contours
