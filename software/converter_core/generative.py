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
The seed does not merely rotate the same skeleton: it picks a composition
style (``STYLES`` / ``style_for``), the ring count, the band-width ladder, how
much of the disc the centre and rim take, how tightly each layer packs its
detail and whether a shape repeats once or twice per wedge, so two seeds are
different kinds of design.

Callers can also pass ``motifs`` - traced black-and-white artwork, for example
silhouettes of leaves, shells or fish - to ``random_pattern``. Each shape ring
then draws from a *pool* of seed-chosen motifs instead of a drawn family, so a
folder of natural shapes becomes the source of the diversity while the
separators, studs and rim keep the mandala structure. Copies pick from the pool
as they step along the ring, a share of them overlay a smaller second motif to
form hybrids, and every copy is deliberately larger than its band and drifts in
and out of it, so the shapes overlap rather than sitting in tidy rows.
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


def _roll(seed, slot):
    """A deterministic, well-mixed value in [0, 1) for one (seed, slot).

    A plain Weyl sequence in the seed would advance by a fixed step, so
    consecutive seeds would land in only a few bins of any small choice. This
    scrambles the pair with a SplitMix-style integer finaliser instead: still
    fully deterministic from the seed, but the choices spread evenly.
    """
    value = (
        int(seed) * 0x9E3779B1 + int(slot) * 0x85EBCA6B + 0x165667B1
    ) & 0xFFFFFFFF
    value ^= value >> 15
    value = (value * 0x2545F491) & 0xFFFFFFFF
    value ^= value >> 13
    return value / 4294967296.0


def _pick(seed, slot, count):
    """A deterministic integer in ``0..count-1`` for one (seed, slot)."""
    count = max(int(count), 1)
    return int(_roll(seed, slot) * count) % count


def _density(seed, slot=91):
    """How tightly this seed packs a layer: 0.80 (airy) to 1.30 (packed)."""
    return 0.80 + 0.50 * _roll(seed, slot)


def _shuffled(items, seed):
    """Deterministic Fisher-Yates permutation of *items* from the seed."""
    out = list(items)
    for index in range(len(out) - 1, 0, -1):
        swap = _pick(seed, 100 + index, index + 1)
        out[index], out[swap] = out[swap], out[index]
    return out


def _arc_contour(radius_of, wedge, samples, start=0.0):
    """Sample ``radius_of(t)`` over *wedge* radians from *start*, t in [0, 1]."""
    samples = max(int(samples), 2)
    return [
        _polar(radius_of(index / samples), start + wedge * index / samples)
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


def _nested_arcs(
    r_in, r_out, wedge, power, spacing, samples, cancel_check=None, start=0.0
):
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
                start,
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


def _motif_extent(motif):
    """Bounding width and circumradius of a motif in its own units."""
    xs = [x for contour in motif for x, _ in contour]
    ys = [y for contour in motif for _, y in contour]
    if not xs:
        return 0.0, 0.0
    width = max(max(xs) - min(xs), max(ys) - min(ys))
    radius = max(math.hypot(x, y) for contour in motif for x, y in contour)
    return width, radius


def _place_motif(motif, scale, rotation, centre, flip=False):
    """Scale, optionally mirror, rotate and move a motif to *centre*."""
    cos_a, sin_a = math.cos(rotation), math.sin(rotation)
    cx, cy = centre
    out = []
    for contour in motif:
        points = []
        for x, y in contour:
            sx = x * scale
            sy = (-y if flip else y) * scale
            points.append(
                (cx + sx * cos_a - sy * sin_a, cy + sx * sin_a + sy * cos_a)
            )
        out.append(points)
    return out


def _radial_support(motif, phi):
    """How far the motif reaches along a direction *phi* (motif units).

    Scaling by the circumradius alone does not guarantee that a copy reaches
    into the neighbouring ring: a wide shape turned across the band reaches
    sideways instead. Scaling by this support makes the radial reach explicit
    whatever the rotation is.
    """
    cos_p, sin_p = math.cos(phi), math.sin(phi)
    return max(
        abs(x * cos_p + y * sin_p) for contour in motif for x, y in contour
    )


def _motif_ring(
    motif_pool,
    r_in,
    r_out,
    wedge,
    level,
    seed,
    cancel_check=None,
    limit=None,
    floor=None,
):
    """Fill a band with a *mix* of motifs from *motif_pool*.

    The pool holds the traced artworks this ring may use. Copies step along the
    arc and pick from the pool as they go, so one ring can braid a leaf into a
    shell into a fish; a share of the copies also overlay a smaller second motif
    from the pool, which reads as a hybrid shape. Copies are deliberately bigger
    than the band and drift in and out of it, so neighbouring shapes overlap
    instead of sitting in tidy rows; ``limit`` and ``floor`` keep that spill
    inside the design radius and clear of the centre. The seed chooses
    orientation, tilt, mirroring, packing and how far the copies spill.
    """
    pool = [motif for motif in motif_pool if motif]
    if not pool:
        return []
    span = r_out - r_in
    extents = [_motif_extent(motif) for motif in pool]
    width_max = max(width for width, _ in extents)
    radius_max = max(radius for _, radius in extents)
    if radius_max <= 1e-9:
        return []
    mid = 0.5 * (r_in + r_out)
    jitter = 0.10 * span
    # Bigger than the band on purpose: the shapes are meant to overlap the
    # rings on either side of them. With at most 0.10 span of drift, even the
    # lowest copy still reaches 0.52 span past the band's middle, so every
    # copy overlaps its neighbour rather than only the lucky ones.
    extent = span * (0.62 + 0.18 * _roll(seed, 216))
    if limit is not None:
        extent = min(extent, max(limit * 0.999 - mid - jitter, 0.12 * span))
    if floor is not None:
        extent = min(extent, max(mid - jitter - floor, 0.12 * span))
    scale = extent / radius_max
    flip = _roll(seed, 211) < 0.50
    tilt = 0.55 * (2.0 * _roll(seed, 212) - 1.0)
    packed = 0.75 + 0.35 * _roll(seed, 215)
    arc = wedge * mid
    count = max(1, min(3, int(arc * packed / max(width_max * scale, 1e-6))))
    out = []
    for index in range(count):
        check_cancelled(cancel_check)
        angle = wedge * (index + 0.5) / count
        rotation = angle
        rotation += tilt * (2.0 * weyl(index + seed) - 1.0)
        mirror = flip and index % 2 == 1
        centre_r = mid + jitter * (2.0 * weyl(index + seed + 1) - 1.0)
        if floor is not None:
            centre_r = max(centre_r, floor + extent)
        if limit is not None:
            centre_r = min(centre_r, limit * 0.999 - extent)
        primary = pool[_pick(seed + 7 * index, 300, len(pool))]
        support = _radial_support(primary, angle - rotation)
        copy_scale = _clamp(
            extent / max(support, 0.5 * radius_max), 0.6 * scale, 1.6 * scale
        )
        out.extend(
            _place_motif(
                primary, copy_scale, rotation, _polar(centre_r, angle), mirror
            )
        )
        # Nested copies of pool motifs fill the shape: 0.70, then 0.46 of the
        # original. Three concentric outlines read the way the hatching inside
        # an engraved leaf reads, without the plotter dragging a solid band.
        for tier, (shrink, chance, turn) in enumerate(
            ((0.70, 0.85, 0.55), (0.46, 0.60, 1.30)), start=1
        ):
            if _roll(seed + index, 301 + tier) >= chance:
                continue
            inner = pool[_pick(seed + 5 * index + tier, 302 + tier, len(pool))]
            out.extend(
                _place_motif(
                    inner,
                    copy_scale * shrink,
                    rotation + turn * (2.0 * _roll(seed + index, 305 + tier) - 1.0),
                    _polar(centre_r, angle),
                    not mirror,
                )
            )
    return out


def _leaf_ring(r_in, r_out, wedge, level, seed, cancel_check=None):
    """One or two large leaves with nested sub-leaves, contour fills and veins."""
    span = r_out - r_in
    power = 0.45 + 0.60 * van_der_corput(seed + 1, 5)
    samples = 30 + 3 * level
    density = _density(seed)
    repeat = 1 + _pick(seed, 11, 2)
    nests = 1 + level // 3
    out = []
    for rep in range(repeat):
        check_cancelled(cancel_check)
        a0 = wedge * rep / repeat
        a1 = wedge * (rep + 1) / repeat
        mid, half = 0.5 * (a0 + a1), 0.5 * (a1 - a0)
        out.append(_leaf(a0, a1, r_in, r_out, power, 0.30, samples))
        for index in range(nests):
            check_cancelled(cancel_check)
            ratio = 1.0 - 0.75 * (index + 1) / (nests + 1)
            out.append(
                _leaf(
                    mid - 0.88 * half,
                    mid + 0.88 * half,
                    r_in,
                    r_in + span * ratio,
                    power + 0.10,
                    0.30,
                    samples,
                )
            )
        out.append([_polar(r_in, mid), _polar(r_in + 0.98 * span, mid)])
        out.extend(
            _nested_arcs(
                r_in,
                r_out,
                a1 - a0,
                power,
                _shade_spacing(level) * density,
                samples,
                cancel_check,
                a0,
            )
        )
    return out


def _tulip(r_in, r_out, wedge, level, seed, cancel_check=None):
    """A tall centre lobe between two side lobes, all contour-shaded."""
    span = r_out - r_in
    power = 0.55 + 0.30 * van_der_corput(seed + 3, 5)
    samples = 24 + 3 * level
    density = _density(seed)
    low = (0.12 + 0.10 * weyl(seed + 21)) * wedge
    high = wedge - low
    side = 0.58 + 0.20 * weyl(seed + 22)
    out = [
        _leaf(low, high, r_in, r_out, power, 0.28, samples),
        _leaf(0.0, 0.46 * wedge, r_in, r_in + side * span, power, 0.28, samples),
        _leaf(0.54 * wedge, wedge, r_in, r_in + side * span, power, 0.28, samples),
    ]
    lo, hi = low / wedge, high / wedge

    def window(t):
        return _clamp((t - lo) / max(hi - lo, 1e-6), 0.0, 1.0)

    count = _count(span, _shade_spacing(level) * density, 2, 40)
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
    for tip in (0.14, 0.86):
        check_cancelled(cancel_check)
        bead = 0.10 * span
        out.append(_ring(_polar(r_in + side * span, tip * wedge), bead))
    return out


def _lens(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Two arcs of different bulge crossing at the seams, bead-strung."""
    span = r_out - r_in
    samples = 34 + 4 * level
    density = _density(seed)
    repeat = 1 + _pick(seed, 12, 2)
    bulges = (0.45 + 0.55 * weyl(seed + 2), 1.20 + 0.90 * weyl(seed + 4))
    out = []
    for rep in range(repeat):
        check_cancelled(cancel_check)
        a0 = wedge * rep / repeat
        arc = wedge / repeat
        for power in bulges:
            out.append(
                _arc_contour(
                    lambda t, power=power: r_in
                    + span * math.sin(math.pi * t) ** power,
                    arc,
                    samples,
                    a0,
                )
            )
        out.extend(
            _nested_arcs(
                r_in,
                r_out,
                arc,
                bulges[0],
                _shade_spacing(level) * density,
                samples,
                cancel_check,
                a0,
            )
        )
        mid = r_in + 0.5 * span
        count = _count(arc * mid, (6.0 - 0.2 * level) * density, 2, 40)
        for index in range(count):
            check_cancelled(cancel_check)
            t = (index + 0.5) / count
            out.append(_circle(_polar(mid, a0 + arc * t), 0.05 * span, 10))
    return out


def _bundle(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Nested topographic arches with radial ticks."""
    span = r_out - r_in
    density = _density(seed)
    power = 0.50 + 0.55 * weyl(seed + 5)
    samples = 34 + 4 * level
    out = []
    lines = _count(span, _shade_spacing(level) * density, 3, 48)
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
    ticks = _count(wedge * r_out, (9.0 - 0.4 * level) * density, 2, 30)
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
    density = _density(seed)
    power = 0.40 + 0.50 * van_der_corput(seed + 6, 3)
    spine = 0.50 + 0.28 * weyl(seed + 7)
    fork_every = 2 + _pick(seed, 13, 3)
    samples = 34 + 4 * level

    def envelope(t):
        return r_in + span * math.sin(math.pi * t) ** power

    out = [
        _arc_contour(envelope, wedge, samples),
        _arc_contour(lambda t: r_in + span * spine, wedge, samples),
    ]
    barbs = _count(wedge * r_out, (7.0 - 0.35 * level) * density, 4, 90)
    for index in range(barbs):
        check_cancelled(cancel_check)
        t = (index + 0.5) / barbs
        base = r_in + span * spine
        tip = envelope(t)
        angle = wedge * t
        out.append([_polar(min(base, tip), angle), _polar(max(base, tip), angle)])
        if index % fork_every == 0:
            fork = span * 0.10
            out.append([_polar(tip, angle), _polar(max(tip - fork, r_in), angle - 0.12 * wedge / barbs)])
            out.append([_polar(tip, angle), _polar(max(tip - fork, r_in), angle + 0.12 * wedge / barbs)])
        if level >= 5 and index % fork_every == 1:
            bead = 0.045 * span
            out.append(_circle(_polar(max(tip - bead, r_in), angle), bead, 8))
    return out


def _scallop(r_in, r_out, wedge, level, seed, cancel_check=None):
    """A stack of nested wave lines with a bead on every crest."""
    mid = 0.5 * (r_in + r_out)
    half = 0.5 * (r_out - r_in)
    density = _density(seed)
    waves = 1 + _pick(seed, 14, 4)
    phase = TAU * weyl(seed + 1)
    lines = _count(2.0 * half, 2.2 * density, 2, 14)
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
    crests = _count(
        wedge * (r_in + r_out) * 0.5, (5.0 - 0.2 * level) * density, 1, 40
    )
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
    density = _density(seed)
    arc = wedge * (r_in + r_out) * 0.5
    teeth = _count(arc, (16.0 - 0.8 * level) * density, 1, 24)
    rise = 0.45 + 0.5 * van_der_corput(seed + 2, 3)
    peak = r_in + (r_out - r_in) * rise
    samples = 14 + 2 * level
    inner_row = level >= 4 and _roll(seed, 15) < 0.8
    apex_beads = level >= 6 and _roll(seed, 16) < 0.8
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
        if inner_row:
            out.append(
                [_polar(r_in, a0), _polar(inner, 0.5 * (a0 + a1)), _polar(r_in, a1)]
            )
        if apex_beads:
            out.append(_circle(_polar(peak - 0.10 * (r_out - r_in), 0.5 * (a0 + a1)), 0.06 * (r_out - r_in), 8))
    out.append(_arc_contour(lambda t: r_out, wedge, 8 + 2 * level))
    return out


def _rays(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Rayed fan with a tip arc, alternating beam lengths and tip beads."""
    span = r_out - r_in
    density = _density(seed)
    count = _count(wedge * r_in, (7.0 - 0.35 * level) * density, 1, 60)
    beamed = level >= 5 and _roll(seed, 17) < 0.75
    out = []
    for index in range(count):
        check_cancelled(cancel_check)
        t = (index + 0.5) / count
        a = wedge * t
        half_width = 0.14 * wedge / count
        reach = r_in + span * (0.72 + 0.28 * van_der_corput(index + 1 + seed, 3))
        out.append([_polar(r_in, a - half_width), _polar(reach, a), _polar(r_in, a + half_width)])
        if beamed:
            out.append(_circle(_polar(reach - 0.05 * span, a), 0.04 * span, 8))
    out.append(_arc_contour(lambda t: r_out, wedge, 24 + 3 * level))
    return out


def _mesh(r_in, r_out, wedge, level, seed, cancel_check=None):
    """A diamond lattice: two families of slanted lines crossing."""
    span = r_out - r_in
    density = _density(seed)
    arc = wedge * (r_in + r_out) * 0.5
    count = _count(arc, (6.0 - 0.28 * level) * density, 3, 90)
    slant = 1.5 * wedge / count
    if _roll(seed, 18) < 0.5:
        slant = -slant
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
    density = _density(seed)
    rows = _count(span, 3.6 * density, 2, 14)
    row_h = span / rows
    arc_r = 0.45 * row_h
    eyes = level >= 4 and _roll(seed, 19) < 0.8
    out = []
    for row in range(rows):
        check_cancelled(cancel_check)
        rho = r_in + (row + 0.95) * row_h
        count = _count(wedge * rho, (4.4 - 0.15 * level) * density, 2, 90)
        offset = 0.5 * (row % 2)
        for index in range(count):
            angle = wedge * (index + 0.5 + offset) / count
            half = rho * wedge / count * 0.60
            delta = math.asin(_clamp(half / max(arc_r, 1e-6), -1.0, 1.0))
            cx, cy = _polar(max(rho - arc_r, 0.01), angle)
            out.append(
                _arc((cx, cy), arc_r, angle - delta, angle + delta, 9)
            )
            if eyes and (index + row) % 2 == 0:
                eye = 0.20 * arc_r
                out.append(_circle(_polar(rho - eye, angle), eye, 8))
    return out


def _beadrow(r_in, r_out, wedge, level, seed, cancel_check=None):
    """Several rows of beads and stud flowers packed through the band."""
    span = r_out - r_in
    density = _density(seed)
    rows = _count(span, 3.4 * density, 2, 14)
    row_h = span / rows
    flower_every = 2 + _pick(seed, 20, 3)
    out = []
    for row in range(rows):
        check_cancelled(cancel_check)
        rho = r_in + (row + 0.5) * row_h
        size = min(0.34 * row_h, 1.8)
        count = _count(wedge * rho, (3.6 - 0.12 * level) * density, 2, 90)
        for index in range(count):
            t = (index + 0.5) / count
            wobble = 0.20 * row_h * (2.0 * weyl(index + seed + row) - 1.0)
            centre_r = _clamp(
                rho + wobble, r_in + 1.1 * size, r_out - 1.1 * size
            )
            centre = _polar(centre_r, wedge * t)
            if (index + row) % flower_every == 0:
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

# Each seed draws from one of these style pools, so two seeds are not just the
# same skeleton with the textures swapped: they are different kinds of design.
STYLES = ("floral", "geometric", "woven", "beaded", "mixed")

_STYLE_POOLS = {
    "floral": ("leaf", "tulip", "lens", "scallop", "feather", "beadrow"),
    "geometric": ("mesh", "chevron", "rays", "lace", "bundle", "lens"),
    "woven": ("mesh", "lace", "feather", "bundle", "scallop", "chevron"),
    "beaded": ("beadrow", "lace", "leaf", "scallop", "lens", "chevron"),
    "mixed": FAMILIES,
}


def style_for(seed):
    """The composition style this seed draws from."""
    return STYLES[_pick(seed, 0, len(STYLES))]


def _ring_count(seed, level):
    """How many shape rings this seed draws at this intricacy."""
    return 3 + (2 * level) // 3 + _pick(seed, 1, 3) - 1


def _motif_ring_count(seed, level):
    """Fewer, thicker rings when natural motifs carry the design.

    A ring of small repeated shapes reads as texture; a ring of a few large
    ones reads as the shape. Motif mode therefore trades ring count for scale.
    """
    return 2 + level // 3 + _pick(seed, 1, 3) - 1


def motif_plan(seed, intricacy, count, per_ring=None):
    """The pool of motifs each shape ring draws from.

    Returns one list of motif indices per shape ring; copies inside a ring pick
    from that pool, so a ring combines several natural shapes rather than
    repeating one. ``random_pattern`` builds the same pools, so a caller that
    traces only the indices listed here never misses one. The pool size grows
    with intricacy unless *per_ring* overrides it.
    """
    if count <= 0:
        return []
    level = max(1, min(int(intricacy), 10))
    seed = int(seed) % 100000
    picks = min(int(per_ring) if per_ring else 1 + level // 4, int(count))
    pools = []
    for ring in range(_motif_ring_count(seed, level)):
        pool = []
        for slot in range(max(picks, 1)):
            index = _pick(seed, 200 + 40 * slot + ring, count)
            if index not in pool:
                pool.append(index)
        pools.append(pool)
    return pools


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
        _arc_contour(
            lambda t, r=radius * (1.0 - 0.07 * index): r, wedge, 14 + 2 * level
        )
        for index in range(1 + _pick(seed, 26, 3))
    ]
    nests = 1 + _pick(seed, 25, 3) + level // 4
    for index in range(nests):
        check_cancelled(cancel_check)
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
    out.append(_ring((0.0, 0.0), radius * (0.10 + 0.08 * weyl(seed + 31))))
    if level >= 4 and _roll(seed, 27) < 0.75:
        out.extend(
            _dots(
                radius * 0.66,
                wedge,
                (4.0 - 0.15 * level) * _density(seed, 94),
                radius * 0.035,
                seed,
                cancel_check,
            )
        )
    return out


def _starburst(radius, wedge, level, seed, cancel_check=None):
    """A ray ring: uneven spokes between two rings, beads between the rays."""
    if radius <= 2.0:
        return []
    spokes = _count(
        wedge * radius, (9.0 - 0.4 * level) * _density(seed, 93), 3, 40
    )
    inner = radius * 0.50
    outer = radius * 0.95
    beads = level >= 4 and _roll(seed, 29) < 0.75
    out = []
    for index in range(spokes):
        check_cancelled(cancel_check)
        angle = wedge * (index + 0.5) / spokes
        length = inner + (outer - inner) * (0.35 + 0.65 * weyl(index + seed + 1))
        out.append([_polar(inner, angle), _polar(length, angle)])
        if beads:
            out.append(_circle(_polar(inner, angle), 0.035 * radius, 8))
    rings = 2 + _pick(seed, 28, 3)
    for index in range(rings):
        out.append(_ring((0.0, 0.0), radius * (0.50 + 0.45 * (index + 1) / rings)))
    return out


def _rim(radius, wedge, level, seed, cancel_check=None):
    """Scalloped multi-line outer boundary with stud and dot rows."""
    density = _density(seed, 92)
    waves = _count(wedge * radius, (13.0 - 0.6 * level) * density, 3, 60)
    amp = radius * (0.008 + 0.012 * _roll(seed, 21))
    lines = 2 + _pick(seed, 22, 4)
    out = [
        _arc_contour(
            lambda t: radius - amp + amp * math.cos(TAU * waves * t),
            wedge,
            18 + 6 * waves,
        )
    ]
    for index in range(lines):
        check_cancelled(cancel_check)
        out.append(
            _arc_contour(
                lambda t, r=radius * (0.990 - 0.010 * index): r,
                wedge,
                26 + 3 * level,
            )
        )
    if _roll(seed, 23) < 0.8:
        out.extend(
            _studs(
                radius * 0.930,
                radius * 0.026,
                (4.0 - 0.15 * level) * density,
                radius * (0.005 + 0.0006 * level),
                wedge,
                seed + 3,
                cancel_check,
            )
        )
    if level >= 5 and _roll(seed, 24) < 0.7:
        out.extend(
            _dots(radius * 0.955, wedge, 4.5 - 0.2 * level, radius * 0.008, seed + 7, cancel_check)
        )
    return out


def random_pattern(
    seed=0,
    intricacy=5,
    radius_mm=180.0,
    wedge_deg=15.0,
    motifs=None,
    cancel_check=None,
):
    """Return a mandala in millimetres, centred on the origin, y up.

    ``intricacy`` 1..10 deepens every layer: more shape rings, tighter contour
    shading inside each shape, and denser separators, studs and bead rows.
    ``wedge_deg`` must be the wedge the caller will clip to
    (``180/divisions``) because every ring is composed inside exactly one wedge.

    ``motifs`` is an optional list of traced artworks (each a list of contours
    in millimetres, centred on the origin, y up). When given, every shape ring
    is filled with copies of a seed-chosen motif instead of a drawn family, and
    the seed also chooses the copy count, orientation and mirroring. Empty or
    missing motifs fall back to the drawn families for that ring.
    """
    seed = int(seed) % 100000
    level = max(1, min(int(intricacy), 10))
    radius = max(float(radius_mm), 1.0)
    wedge = math.radians(max(float(wedge_deg), 0.5))
    motifs = list(motifs) if motifs else []
    plan = motif_plan(seed, level, len(motifs))

    # The seed chooses the kind of design, not just its phases: the style pool,
    # the ring count, the band-width profile, how much of the disc the centre
    # and the rim take, and how tightly each layer packs its detail.
    order = _shuffled(_STYLE_POOLS[style_for(seed)], seed)
    rings = _motif_ring_count(seed, level) if plan else _ring_count(seed, level)
    centre_r = radius * (0.055 + 0.020 * _roll(seed, 2) + 0.006 * level)
    gap = radius * (0.010 + 0.014 * _roll(seed, 3))
    outer = radius * (0.855 + 0.075 * _roll(seed, 4))
    ladder = 0.60 + 0.60 * _roll(seed, 5)
    dressed = _pick(seed, 6, 4)
    burst = level >= 3 and _roll(seed, 7) < 0.75
    span_total = outer - centre_r
    edges = [
        centre_r + span_total * (index / rings) ** ladder
        for index in range(rings + 1)
    ]

    contours = []
    contours.extend(_rosette(centre_r, wedge, level, seed + 5, cancel_check))
    if burst:
        contours.extend(_starburst(centre_r, wedge, level, seed + 9, cancel_check))
    if plan and level >= 4 and _roll(seed, 8) < 0.45:
        _, motif_radius = _motif_extent(motifs[plan[0][0]])
        if motif_radius > 1e-9:
            contours.extend(
                _place_motif(
                    motifs[plan[0][0]],
                    centre_r * 0.72 / motif_radius,
                    0.0,
                    (0.0, 0.0),
                )
            )

    for ring in range(rings):
        check_cancelled(cancel_check)
        name = order[ring % len(order)]
        r_in = edges[ring]
        r_out = max(edges[ring + 1] - gap, r_in + radius * 0.03)
        pool = [motifs[index] for index in plan[ring]] if plan else []
        if any(pool):
            contours.extend(
                _motif_ring(
                    pool,
                    r_in,
                    r_out,
                    wedge,
                    level,
                    seed + 17 * ring + 1,
                    cancel_check,
                    limit=radius,
                    floor=radius * 0.03,
                )
            )
        else:
            contours.extend(
                _FUNCTIONS[name](
                    r_in, r_out, wedge, level, seed + 17 * ring + 1, cancel_check
                )
            )
        center_line = r_out + 0.5 * gap
        contours.extend(
            _separator(
                center_line,
                radius,
                wedge,
                # Motif rings are the subject; do not let the separator
                # bundles grow into heavy rings that swallow them.
                level if not plan else max(2, level // 4),
                seed + ring,
                cancel_check,
            )
        )
        if ring < rings - 1:
            mode = _pick(seed + 37 * ring, 30, 4) if dressed == 3 else dressed
            if mode in (1, 3):
                contours.extend(
                    _studs(
                        center_line,
                        gap * 0.9,
                        (5.0 - 0.2 * level) * _density(seed + ring, 95),
                        radius * (0.004 + 0.0003 * level),
                        wedge,
                        seed + 50 + ring,
                        cancel_check,
                    )
                )
            if mode in (2, 3):
                contours.extend(
                    _dots(
                        center_line,
                        wedge,
                        (4.2 - 0.18 * level) * _density(seed + ring, 96),
                        radius * (0.0025 + 0.0002 * level),
                        seed + 70 + ring,
                        cancel_check,
                    )
                )

    contours.extend(_rim(radius, wedge, level, seed + 31, cancel_check))
    return contours
