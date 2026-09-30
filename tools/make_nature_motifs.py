"""Draw a folder of black-and-white nature silhouettes for the kaleidoscope app.

Every shape is drawn from code rather than sampled from a photo collection, so
the output is deterministic, pure black on pure white, and safe to plot. Each
image is supersampled and thresholded, which keeps the edges crisp instead of
leaving grey anti-aliased pixels for the tracer to guess at.

Usage::

    python tools\\make_nature_motifs.py                 # writes motifs/nature
    python tools\\make_nature_motifs.py --out some\\dir  # somewhere else

Point the Kaleidoscope Converter's "Motif folder..." button at the result, tick
"Use natural motifs in patterns", and browse seeds.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

SUPERSAMPLE = 4
PIXELS = 320


# -- drawing helpers (all coordinates are 0..1) ---------------------------


def _pts(seq, scale):
    return [(x * scale, y * scale) for x, y in seq]


def poly(draw, seq, scale, fill=0):
    draw.polygon(_pts(seq, scale), fill=fill)


def stroke(draw, seq, scale, width, fill=0):
    draw.line(_pts(seq, scale), fill=fill, width=max(1, int(width * scale)), joint="curve")


def oval(draw, cx, cy, rx, ry, scale, fill=0):
    draw.ellipse(
        [(cx - rx) * scale, (cy - ry) * scale, (cx + rx) * scale, (cy + ry) * scale],
        fill=fill,
    )


def ellipse_arc(draw, cx, cy, rx, ry, start, end, scale, width):
    draw.arc(
        [(cx - rx) * scale, (cy - ry) * scale, (cx + rx) * scale, (cy + ry) * scale],
        start,
        end,
        fill=0,
        width=max(1, int(width * scale)),
    )


def rot(points, degrees, origin=(0.0, 0.0)):
    angle = math.radians(degrees)
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    ox, oy = origin
    return [
        (
            ox + (x - ox) * cos_a - (y - oy) * sin_a,
            oy + (x - ox) * sin_a + (y - oy) * cos_a,
        )
        for x, y in points
    ]


def move(points, dx, dy):
    return [(x + dx, y + dy) for x, y in points]


def leaf_points(
    x0,
    y0,
    angle,
    length,
    width,
    power=0.9,
    lobes=0,
    depth=0.35,
    samples=34,
):
    """A closed leaf outline pointing along *angle* (degrees, y down)."""
    edge = []
    for side in (1.0, -1.0):
        span = range(samples + 1) if side > 0 else range(samples, -1, -1)
        for index in span:
            t = index / samples
            base = math.sin(math.pi * t) ** power
            if lobes:
                base *= 1.0 - depth * (0.5 + 0.5 * math.cos(2.0 * math.pi * lobes * t))
            edge.append((t * length, side * 0.5 * width * base))
    angle_rad = math.radians(angle)
    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
    return [
        (x0 + lx * cos_a - ly * sin_a, y0 + lx * sin_a + ly * cos_a)
        for lx, ly in edge
    ]


def petal_points(cx, cy, angle, length, width, samples=22):
    """A teardrop petal from (cx, cy) pointing along *angle*."""
    pts = []
    for side in (1.0, -1.0):
        span = range(samples + 1) if side > 0 else range(samples, -1, -1)
        for index in span:
            t = index / samples
            r = length * t
            half = 0.5 * width * math.sin(math.pi * t) ** 0.75
            pts.append((r, side * half))
    angle_rad = math.radians(angle)
    cos_a, sin_a = math.cos(angle_rad), math.sin(angle_rad)
    return [
        (cx + lx * cos_a - ly * sin_a, cy + lx * sin_a + ly * cos_a)
        for lx, ly in pts
    ]


def petal_ring(draw, scale, cx, cy, radius, count, length, width, phase=0.0, fill=0):
    for index in range(count):
        angle = 360.0 * index / count + phase
        poly(
            draw,
            move(petal_points(cx, cy, angle, length, width), 0, 0),
            scale,
            fill=fill,
        )


def spiral_points(cx, cy, r0, r1, turns, phase, samples=120, width=0.0):
    pts = []
    for index in range(samples + 1):
        t = index / samples
        angle = math.radians(phase) + 2.0 * math.pi * turns * t
        r = r0 + (r1 - r0) * t
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return pts


def branch(draw, scale, x, y, angle, length, width, depth, spread=28.0, seed=1):
    """A recursive coral / tree branch."""
    if depth <= 0 or length < 0.02:
        return
    angle_rad = math.radians(angle)
    x2 = x + length * math.cos(angle_rad)
    y2 = y + length * math.sin(angle_rad)
    stroke(draw, [(x, y), (x2, y2)], scale, width)
    for index in range(2):
        sign = -1.0 if index == 0 else 1.0
        wobble = ((seed * 37 + depth * 11 + index * 7) % 17 - 8) / 40.0
        branch(
            draw,
            scale,
            x2,
            y2,
            angle + sign * spread * (1.0 + wobble),
            length * (0.62 + 0.06 * index),
            width * 0.68,
            depth - 1,
            spread,
            seed + index + 1,
        )


def star_points(cx, cy, points, outer, inner, phase=0.0, samples=0):
    pts = []
    total = points * 2
    for index in range(total):
        angle = math.radians(phase + 360.0 * index / total)
        r = outer if index % 2 == 0 else inner
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return pts


def quad(p0, p1, p2, samples=24):
    """Points along a quadratic Bezier curve."""
    pts = []
    for index in range(samples + 1):
        t = index / samples
        u = 1.0 - t
        pts.append(
            (
                u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1],
            )
        )
    return pts


def eye(draw, scale, cx, cy, r):
    """A white ring inside a dark shape, read as an eye."""
    oval(draw, cx, cy, r, r, scale, fill=255)
    oval(draw, cx, cy, r * 0.45, r * 0.45, scale, fill=0)


# -- the catalogue -------------------------------------------------------


def leaf_simple(d, s, v):
    width = (0.20, 0.30, 0.15)[v % 3]
    poly(d, leaf_points(0.5, 0.08, 90, 0.84, width, power=(0.8, 1.1, 1.4)[v % 3]), s)
    stroke(d, [(0.5, 0.10), (0.5, 0.94)], s, 0.010)


def leaf_oak(d, s, v):
    poly(d, leaf_points(0.5, 0.08, 90, 0.84, 0.42, power=0.9, lobes=(4, 5, 6)[v % 3], depth=0.42), s)
    stroke(d, [(0.5, 0.10), (0.5, 0.94)], s, 0.011)


def leaf_maple(d, s, v):
    height = (0.90, 0.80, 0.96)[v % 3]
    pts = []
    for index in range(240):
        angle = math.radians(360.0 * index / 240 - 90)
        lobe = 0.5 + 0.5 * math.cos(5.0 * angle + (0.25 if v else -0.25))
        r = 0.11 + 0.25 * lobe ** 2.4
        pts.append((0.5 + r * math.cos(angle), 0.50 + r * height * math.sin(angle)))
    poly(d, pts, s)
    stroke(d, [(0.5, 0.60), (0.5, 0.96)], s, 0.018)


def leaf_ginkgo(d, s, v):
    base_y = 0.90
    spread = (52.0, 62.0)[v % 2]
    radius = (0.46, 0.40)[v % 2]
    fan = [(0.5, base_y)]
    for index in range(61):
        t = index / 60
        angle = -90.0 - spread + 2.0 * spread * t
        scallop = 1.0 + 0.05 * math.cos(math.radians(angle + 90) * 6)
        fan.append(
            (
                0.5 + radius * scallop * math.cos(math.radians(angle)),
                base_y + 0.92 * radius * scallop * math.sin(math.radians(angle)),
            )
        )
    poly(d, fan, s)
    # the notch that makes a ginkgo a ginkgo
    poly(d, [(0.5, base_y - 0.02), (0.455, base_y - radius * 0.86), (0.545, base_y - radius * 0.86)], s, fill=255)
    stroke(d, [(0.5, base_y), (0.5, 0.99)], s, 0.012)


def leaf_fern(d, s, v):
    stroke(d, [(0.5, 0.96), (0.5, 0.14)], s, 0.010)
    pairs = (7, 9, 11)[v % 3]
    for index in range(pairs):
        t = index / (pairs - 1)
        y = 0.90 - 0.74 * t
        length = 0.30 * (1.0 - 0.72 * t) + 0.05
        for side in (-1, 1):
            angle = 90 + side * (58 - 16 * t)
            poly(d, leaf_points(0.5, y, angle, length, 0.11, power=1.1), s)


def leaf_palm(d, s, v):
    stroke(d, [(0.5, 0.96), (0.5, 0.34)], s, 0.014)
    fronds = (9, 11)[v % 2]
    for index in range(fronds):
        t = index / (fronds - 1)
        angle = -160 + 140 * t
        length = 0.46 * (1.0 - 0.35 * abs(t - 0.5))
        poly(d, leaf_points(0.5, 0.40, angle - 90, length, 0.09, power=1.2), s)


def clover(d, s, v):
    r = (0.19, 0.23)[v % 2]
    for index in range(3):
        angle = 120 * index - 90
        cx = 0.5 + 0.28 * r * 2.0 * math.cos(math.radians(angle))
        cy = 0.42 + 0.28 * r * 2.0 * math.sin(math.radians(angle))
        heart = []
        for step in range(60):
            t = 2.0 * math.pi * step / 60
            rr = r * (1.0 + 0.28 * math.cos(t))
            heart.append((cx + rr * math.cos(t), cy + rr * math.sin(t)))
        poly(d, heart, s)
    stroke(d, [(0.5, 0.55), (0.5, 0.96)], s, 0.012)


def flower_daisy(d, s, v):
    petals = (12, 16, 20)[v % 3]
    petal_ring(d, s, 0.5, 0.5, 0, petals, 0.40, 0.13, phase=360.0 / (petals * 2))
    oval(d, 0.5, 0.5, 0.12, 0.12, s)


def flower_sunflower(d, s, v):
    petal_ring(d, s, 0.5, 0.5, 0, 18, 0.42, 0.09)
    petal_ring(d, s, 0.5, 0.5, 0, 18, 0.30, 0.08, phase=10.0)
    oval(d, 0.5, 0.5, 0.17, 0.17, s)
    for index in range(18 if v % 2 else 12):
        angle = 137.5 * index
        r = 0.14 * math.sqrt(index / 18.0)
        oval(
            d,
            0.5 + r * math.cos(math.radians(angle)),
            0.5 + r * math.sin(math.radians(angle)),
            0.014,
            0.014,
            s,
            fill=255,
        )


def flower_tulip(d, s, v):
    cup = []
    for index in range(41):
        t = index / 40
        x = 0.30 + 0.40 * t
        y = 0.44 - 0.16 * math.sin(math.pi * t) ** 0.6
        cup.append((x, y))
    for index in range(40, -1, -1):
        t = index / 40
        cup.append((0.30 + 0.40 * t, 0.44 - 0.02 * math.sin(math.pi * t)))
    poly(d, cup, s)
    for offset in (-0.10, 0.0, 0.10):
        poly(d, petal_points(0.5 + offset, 0.44, 270, 0.24 + (0.04 if offset else 0.0), 0.13), s)
    stroke(d, [(0.5, 0.46), (0.5, 0.94)], s, 0.014)
    poly(d, leaf_points(0.5, 0.72, 40 if v % 2 else 140, 0.26, 0.10), s)


def flower_lotus(d, s, v):
    for row, (count, length, width, phase) in enumerate(
        ((5, 0.34, 0.16, -90), (7, 0.26, 0.13, -90), (4, 0.18, 0.11, -90))
    ):
        petal_ring(d, s, 0.5, 0.62, 0, count, length - 0.03 * row, width, phase=phase)
    poly(d, petal_points(0.5, 0.62, 270, 0.16, 0.10), s)
    oval(d, 0.5, 0.64, 0.46, 0.05, s)


def flower_bell(d, s, v):
    top, height, half = 0.34, 0.34, 0.24
    bell = []
    for index in range(41):
        t = index / 40
        bell.append((0.5 - half * (0.35 + 0.65 * t) ** 0.6, top + height * t))
    for index in range(41):
        t = 1.0 - index / 40
        bell.append((0.5 + half * (0.35 + 0.65 * t) ** 0.6, top + height * t))
    poly(d, bell, s)
    stroke(d, [(0.5, 0.12), (0.5, 0.38)], s, 0.012)
    for index in range(3):
        x = 0.5 + (index - 1) * 0.13
        poly(d, petal_points(x, top + height * 0.96, 100 + 40 * (index - 1), 0.12, 0.08), s)
    for index in range(2):
        poly(d, leaf_points(0.5, 0.80 + 0.08 * index, 200 - 130 * index, 0.22, 0.08), s)


def flower_hibiscus(d, s, v):
    petal_ring(d, s, 0.5, 0.46, 0, 5, 0.40, 0.32, phase=-90)
    oval(d, 0.5, 0.46, 0.09, 0.09, s)
    stroke(d, [(0.5, 0.46), (0.5, 0.24)], s, 0.010)
    for index in range(5):
        angle = 90 * index
        oval(
            d,
            0.5 + 0.07 * math.cos(math.radians(angle)),
            0.24 + 0.05 * math.sin(math.radians(angle)),
            0.022,
            0.022,
            s,
        )


def flower_dandelion(d, s, v):
    rays = (28, 40)[v % 2]
    for index in range(rays):
        angle = 360.0 * index / rays
        end = (0.5 + 0.38 * math.cos(math.radians(angle)), 0.46 + 0.38 * math.sin(math.radians(angle)))
        stroke(d, [(0.5, 0.46), end], s, 0.004)
        oval(d, end[0], end[1], 0.03, 0.03, s, fill=255)
        oval(d, end[0], end[1], 0.03, 0.03, s)
    oval(d, 0.5, 0.46, 0.07, 0.07, s)
    stroke(d, [(0.5, 0.54), (0.5, 0.96)], s, 0.008)


def flower_lavender(d, s, v):
    stroke(d, [(0.5, 0.96), (0.5, 0.30)], s, 0.010)
    spikes = 16 if v % 2 == 0 else 22
    for index in range(spikes):
        t = index / (spikes - 1)
        y = 0.14 + 0.34 * t
        side = -1 if index % 2 else 1
        oval(d, 0.5 + side * 0.045, y, 0.042, 0.026, s)
        oval(d, 0.5, y + 0.028, 0.030, 0.022, s)
    for index in range(5):
        t = index / 4
        angle = 205 - 110 * t
        poly(d, leaf_points(0.5, 0.62 + 0.06 * index, angle + 90, 0.26 - 0.05 * index, 0.045, power=1.3), s)


def tree_conifer(d, s, v):
    tiers = (5, 7)[v % 2]
    for index in range(tiers):
        t = index / (tiers - 1)
        half = 0.40 * (1.0 - 0.72 * t) + 0.05
        y = 0.16 + 0.66 * t
        poly(d, [(0.5 - half, y + 0.16), (0.5, y - 0.08), (0.5 + half, y + 0.16)], s)
    stroke(d, [(0.5, 0.78), (0.5, 0.96)], s, 0.020)


def tree_round(d, s, v):
    stroke(d, [(0.5, 0.96), (0.5, 0.62)], s, 0.024)
    blobs = ((0.5, 0.42, 0.30), (0.30, 0.50, 0.18), (0.70, 0.50, 0.18), (0.5, 0.26, 0.17))
    for index, (cx, cy, r) in enumerate(blobs):
        if index and v % 2:
            continue
        oval(d, cx, cy, r, r * 0.92, s)


def tree_palm(d, s, v):
    trunk = [(0.46, 0.96), (0.50, 0.72), (0.54, 0.50), (0.56, 0.36)]
    stroke(d, trunk, s, 0.026)
    for index in range(7 if v % 2 else 9):
        t = index / (6 if v % 2 else 8)
        angle = -170 + 160 * t
        poly(d, leaf_points(0.56, 0.36, angle - 90, 0.42, 0.10, power=1.15), s)
    oval(d, 0.58, 0.40, 0.045, 0.045, s)


def tree_cypress(d, s, v):
    body = []
    for index in range(61):
        t = index / 60
        w = 0.20 * math.sin(math.pi * (0.06 + 0.9 * t)) ** 0.7 * (1.0 - 0.25 * t)
        body.append((0.5 - w, 0.10 + 0.84 * t))
    for index in range(60, -1, -1):
        t = index / 60
        w = 0.20 * math.sin(math.pi * (0.06 + 0.9 * t)) ** 0.7 * (1.0 - 0.25 * t)
        body.append((0.5 + w, 0.10 + 0.84 * t))
    poly(d, body, s)
    stroke(d, [(0.5, 0.90), (0.5, 0.97)], s, 0.018)


def fish(d, s, v):
    tail = 0.16 if v % 2 else 0.22
    oval(d, 0.46, 0.5, 0.30, 0.17, s)
    poly(d, [(0.70, 0.5), (0.92, 0.5 - tail), (0.88, 0.5), (0.92, 0.5 + tail)], s)
    poly(d, [(0.42, 0.34), (0.52, 0.22), (0.56, 0.36)], s)
    poly(d, [(0.44, 0.66), (0.54, 0.78), (0.58, 0.64)], s)
    eye(d, s, 0.24, 0.46, 0.045)


def jellyfish(d, s, v):
    tentacles = 8 if v % 2 else 11
    dome = []
    for index in range(41):
        t = index / 40
        dome.append((0.16 + 0.68 * t, 0.46 - 0.28 * math.sin(math.pi * t) ** 0.6))
    dome.append((0.84, 0.46))
    dome.append((0.16, 0.46))
    poly(d, dome, s)
    for index in range(tentacles):
        t = (index + 0.5) / tentacles
        x = 0.18 + 0.64 * t
        length = 0.30 + 0.14 * (1.0 - abs(2 * t - 1))
        wobble = 0.05 * ((index % 3) - 1)
        stroke(
            d,
            [
                (x, 0.46),
                (x + wobble, 0.46 + length * 0.5),
                (x - wobble, 0.46 + length),
            ],
            s,
            0.009,
        )


def starfish(d, s, v):
    arms = 5
    pts = []
    for index in range(arms * 2):
        angle = math.radians(-90 + 360.0 * index / (arms * 2))
        r = 0.44 if index % 2 == 0 else (0.20 if v % 2 else 0.15)
        pts.append((0.5 + r * math.cos(angle), 0.5 + r * math.sin(angle)))
    poly(d, pts, s)
    for index in range(arms):
        angle = math.radians(-90 + 360.0 * index / arms)
        for step in range(3):
            r = 0.14 + 0.09 * step
            oval(
                d,
                0.5 + r * math.cos(angle),
                0.5 + r * math.sin(angle),
                0.022,
                0.022,
                s,
                fill=255,
            )


def shell_nautilus(d, s, v):
    turns = (2.6, 3.0)[v % 2]
    outer = spiral_points(0.5, 0.56, 0.06, 0.44, turns, 250)
    inner = spiral_points(0.5, 0.56, 0.03, 0.24, turns, 250)
    poly(d, outer + list(reversed(inner)), s)
    for index in range(9):
        t = index / 8
        stroke(
            d,
            [
                (0.5 + 0.06 * t * math.cos(math.radians(250 + 300 * t)), 0.56),
                (0.5 + (0.06 + 0.38 * t) * math.cos(math.radians(250 + 900 * t)),
                 0.56 + (0.06 + 0.38 * t) * math.sin(math.radians(250 + 900 * t))),
            ],
            s,
            0.006,
        )


def shell_fan(d, s, v):
    ribs = (9, 13)[v % 2]
    fan = [(0.5, 0.90)]
    for index in range(41):
        t = index / 40
        angle = -160 + 140 * t
        r = 0.42 * (1.0 + 0.06 * math.cos(6 * math.pi * t))
        fan.append((0.5 + r * math.cos(math.radians(angle)), 0.86 + r * math.sin(math.radians(angle)) * 0.9))
    poly(d, fan, s)
    for index in range(ribs):
        t = (index + 1) / (ribs + 1)
        angle = -160 + 140 * t
        stroke(
            d,
            [
                (0.5, 0.88),
                (0.5 + 0.40 * math.cos(math.radians(angle)), 0.86 + 0.36 * math.sin(math.radians(angle))),
            ],
            s,
            0.008,
            255,
        )
    poly(d, [(0.46, 0.90), (0.5, 0.74), (0.54, 0.90)], s)


def crab(d, s, v):
    oval(d, 0.5, 0.55, 0.24, 0.17, s)
    for side in (-1, 1):
        poly(
            d,
            [
                (0.5 + side * 0.22, 0.48),
                (0.5 + side * 0.40, 0.34),
                (0.5 + side * 0.46, 0.44),
                (0.5 + side * 0.34, 0.52),
            ],
            s,
        )
        for index in range(3):
            y = 0.55 + 0.08 * index
            stroke(
                d,
                [
                    (0.5 + side * 0.20, y),
                    (0.5 + side * (0.40 + 0.04 * index), y + 0.10 - 0.03 * index),
                ],
                s,
                0.014,
            )
    eye(d, s, 0.44, 0.44, 0.035)
    eye(d, s, 0.56, 0.44, 0.035)


def seahorse(d, s, v):
    body = [
        (0.52, 0.20), (0.44, 0.26), (0.40, 0.38), (0.44, 0.52),
        (0.56, 0.62), (0.62, 0.72), (0.56, 0.82), (0.44, 0.84),
        (0.50, 0.90), (0.64, 0.86), (0.70, 0.74), (0.64, 0.60),
        (0.54, 0.50), (0.52, 0.38), (0.58, 0.28),
    ]
    poly(d, body, s)
    poly(d, [(0.52, 0.20), (0.72, 0.22), (0.60, 0.30)], s)
    for index in range(7 if v % 2 == 0 else 9):
        y = 0.30 + 0.06 * index
        stroke(d, [(0.44, y), (0.34, y + 0.02)], s, 0.008)
    eye(d, s, 0.60, 0.235, 0.028)


def octopus(d, s, v):
    oval(d, 0.5, 0.36, 0.22, 0.20, s)
    arms = 8
    for index in range(arms):
        t = (index + 0.5) / arms
        x = 0.30 + 0.40 * t
        curl = 0.10 if index % 2 else -0.10
        stroke(
            d,
            [
                (x, 0.52),
                (x + curl, 0.68),
                (x - curl * 0.6, 0.84),
                (x + curl, 0.94),
            ],
            s,
            0.014 if v % 2 == 0 else 0.018,
        )
    eye(d, s, 0.44, 0.32, 0.035)
    eye(d, s, 0.56, 0.32, 0.035)


def whale(d, s, v):
    body = [
        (0.14, 0.56), (0.24, 0.42), (0.42, 0.36), (0.62, 0.36),
        (0.76, 0.44), (0.82, 0.54), (0.72, 0.62), (0.52, 0.66), (0.28, 0.64),
    ]
    poly(d, body, s)
    poly(d, [(0.80, 0.52), (0.96, 0.40), (0.92, 0.52), (0.97, 0.62)], s)
    poly(d, [(0.44, 0.60), (0.52, 0.72), (0.60, 0.60)], s)
    if v % 2:
        for index in range(3):
            stroke(
                d,
                [(0.36 + 0.02 * index, 0.36), (0.30 + 0.02 * index, 0.22)],
                s,
                0.008,
            )
    eye(d, s, 0.28, 0.50, 0.030)


def coral(d, s, v):
    branch(d, s, 0.5, 0.94, -90, 0.30, 0.026, 4 if v % 2 == 0 else 5, 30)
    branch(d, s, 0.30, 0.94, -90, 0.20, 0.020, 3, 34, seed=5)
    branch(d, s, 0.70, 0.94, -90, 0.22, 0.022, 3, 32, seed=9)
    oval(d, 0.30, 0.96, 0.30, 0.03, s)


def waves(d, s, v):
    rows = 3 if v % 2 else 4
    for row in range(rows):
        y = 0.30 + 0.16 * row
        amp = 0.07 - 0.01 * row
        pts = []
        for index in range(81):
            t = index / 80
            pts.append((0.06 + 0.88 * t, y + amp * math.sin(2 * math.pi * (2 * t + row * 0.2))))
        stroke(d, pts, s, 0.014)
    oval(d, 0.78, 0.20, 0.07, 0.07, s)


def bird_flying(d, s, v):
    if v % 2:
        body = [(0.06, 0.52), (0.34, 0.34), (0.52, 0.44), (0.70, 0.32), (0.94, 0.50),
                (0.70, 0.50), (0.54, 0.60), (0.30, 0.62)]
    else:
        body = [(0.06, 0.40), (0.36, 0.44), (0.52, 0.34), (0.68, 0.44), (0.94, 0.40),
                (0.72, 0.56), (0.52, 0.54), (0.32, 0.60)]
    poly(d, body, s)
    poly(d, [(0.52, 0.46), (0.58, 0.52), (0.50, 0.50)], s)
    eye(d, s, 0.86, 0.42, 0.020)


def feather(d, s, v):
    stroke(d, [(0.5, 0.96), (0.5, 0.08)], s, 0.010)
    barbs = 20 if v % 2 == 0 else 26
    for index in range(barbs):
        t = index / (barbs - 1)
        y = 0.92 - 0.84 * t
        length = 0.30 * math.sin(math.pi * (0.08 + 0.86 * t)) ** 0.7
        for side in (-1, 1):
            stroke(
                d,
                [(0.5, y), (0.5 + side * length * 0.8, y - length * 0.55)],
                s,
                0.008,
            )


def owl(d, s, v):
    body = [(0.50, 0.14), (0.74, 0.30), (0.82, 0.58), (0.72, 0.86), (0.50, 0.92),
            (0.28, 0.86), (0.18, 0.58), (0.26, 0.30)]
    poly(d, body, s)
    poly(d, [(0.26, 0.30), (0.22, 0.10), (0.40, 0.22)], s)
    poly(d, [(0.74, 0.30), (0.78, 0.10), (0.60, 0.22)], s)
    eye(d, s, 0.40, 0.40, 0.085)
    eye(d, s, 0.60, 0.40, 0.085)
    if v % 2:
        poly(d, [(0.50, 0.50), (0.55, 0.58), (0.45, 0.58)], s, fill=255)


def butterfly(d, s, v):
    span = 0.40 if v % 2 == 0 else 0.46
    poly(d, [(0.5, 0.44), (0.5 - span, 0.20), (0.5 - span * 0.9, 0.46), (0.5 - span * 0.6, 0.62), (0.5, 0.56)], s)
    poly(d, [(0.5, 0.44), (0.5 + span, 0.20), (0.5 + span * 0.9, 0.46), (0.5 + span * 0.6, 0.62), (0.5, 0.56)], s)
    oval(d, 0.5, 0.52, 0.030, 0.14, s)
    oval(d, 0.5, 0.36, 0.036, 0.036, s)
    for side in (-1, 1):
        stroke(d, [(0.5, 0.33), (0.5 + side * 0.12, 0.18)], s, 0.006)
        stroke(d, [(0.5 + side * 0.12, 0.18), (0.5 + side * 0.16, 0.22)], s, 0.006)


def dragonfly(d, s, v):
    oval(d, 0.5, 0.32, 0.045, 0.045, s)
    stroke(d, [(0.5, 0.34), (0.5, 0.90)], s, 0.028 if v % 2 == 0 else 0.022)
    for side in (-1, 1):
        for row, (dy, length) in enumerate(((0.42, 0.34), (0.50, 0.28))):
            poly(
                d,
                [
                    (0.5, 0.40 + 0.06 * row),
                    (0.5 + side * length, dy - 0.04),
                    (0.5 + side * length * 0.9, dy + 0.06),
                ],
                s,
            )


def bee(d, s, v):
    oval(d, 0.5, 0.56, 0.22, 0.15, s)
    for index in range(3):
        x = 0.40 + 0.10 * index
        stroke(d, [(x, 0.42), (x - 0.05, 0.70)], s, 0.014, 255)
    poly(d, [(0.34, 0.46), (0.30, 0.20), (0.56, 0.34)], s)
    poly(d, [(0.62, 0.46), (0.68, 0.20), (0.44, 0.34)], s)
    for side in (-1, 1):
        stroke(d, [(0.30 + side * 0.02, 0.50), (0.14 + side * 0.02, 0.42)], s, 0.008)


def snail(d, s, v):
    turns = (2.4, 2.9)[v % 2]
    shell = spiral_points(0.52, 0.44, 0.04, 0.32, turns, 20)
    thick = []
    for index, (x, y) in enumerate(shell):
        angle = math.radians(20 + 720 * index / max(len(shell) - 1, 1))
        w = 0.14 * (1.0 - 0.7 * index / len(shell))
        thick.append((x + w * math.cos(angle), y + w * math.sin(angle)))
    poly(d, thick + list(reversed(shell)), s)
    poly(d, [(0.20, 0.78), (0.24, 0.62), (0.52, 0.60), (0.72, 0.72), (0.72, 0.82), (0.22, 0.84)], s)
    stroke(d, [(0.24, 0.62), (0.18, 0.52)], s, 0.006)
    stroke(d, [(0.28, 0.62), (0.24, 0.50)], s, 0.006)


def turtle(d, s, v):
    oval(d, 0.5, 0.56, 0.30, 0.22, s)
    for index in range(6 if v % 2 == 0 else 8):
        angle = math.radians(360.0 * index / 6)
        stroke(
            d,
            [(0.5, 0.56), (0.5 + 0.28 * math.cos(angle), 0.56 + 0.20 * math.sin(angle))],
            s,
            0.008,
            255,
        )
    oval(d, 0.5, 0.56, 0.10, 0.08, s, fill=255)
    oval(d, 0.80, 0.52, 0.07, 0.06, s)
    eye(d, s, 0.84, 0.50, 0.020)
    for dx, dy in ((-0.24, -0.16), (0.24, -0.16), (-0.24, 0.16), (0.24, 0.16)):
        oval(d, 0.5 + dx, 0.56 + dy, 0.08, 0.045, s)


def rabbit(d, s, v):
    oval(d, 0.44, 0.62, 0.22, 0.18, s)
    oval(d, 0.66, 0.48, 0.14, 0.13, s)
    ear = 0.24 if v % 2 == 0 else 0.30
    poly(d, leaf_points(0.62, 0.42, -105, ear, 0.09, power=1.2), s)
    poly(d, leaf_points(0.72, 0.42, -75, ear * 0.92, 0.09, power=1.2), s)
    oval(d, 0.22, 0.68, 0.09, 0.08, s)
    eye(d, s, 0.72, 0.46, 0.018)


def cat(d, s, v):
    body = [(0.30, 0.90), (0.30, 0.60), (0.40, 0.40), (0.62, 0.40), (0.72, 0.60),
            (0.72, 0.90)]
    poly(d, body, s)
    oval(d, 0.58, 0.32, 0.155, 0.14, s)
    poly(d, [(0.46, 0.22), (0.52, 0.06), (0.60, 0.20)], s)
    poly(d, [(0.62, 0.20), (0.70, 0.06), (0.74, 0.24)], s)
    if v % 2:
        stroke(d, [(0.74, 0.66), (0.94, 0.44), (0.86, 0.62)], s, 0.018)
    eye(d, s, 0.53, 0.30, 0.022)
    eye(d, s, 0.65, 0.30, 0.022)


def deer(d, s, v):
    poly(d, [(0.30, 0.94), (0.36, 0.62), (0.46, 0.52), (0.62, 0.56), (0.70, 0.72), (0.72, 0.94)], s)
    oval(d, 0.42, 0.40, 0.13, 0.15, s)
    poly(d, [(0.30, 0.40), (0.40, 0.52), (0.56, 0.50), (0.60, 0.30), (0.40, 0.26)], s)
    poly(d, [(0.30, 0.42), (0.16, 0.44), (0.20, 0.52), (0.34, 0.50)], s)
    for side in (-1, 1):
        base_x = 0.45 + side * 0.04
        stroke(d, [(base_x, 0.28), (base_x + side * 0.10, 0.10)], s, 0.012)
        for step, drop in enumerate((0.04, 0.12, 0.20)):
            reach = 0.07 + 0.035 * step
            stroke(
                d,
                [
                    (base_x + side * 0.04, 0.24 - drop + 0.04),
                    (base_x + side * reach, 0.16 - drop * 1.2),
                ],
                s,
                0.009,
            )
        stroke(d, [(base_x + side * 0.06, 0.18), (base_x + side * 0.16, 0.10)], s, 0.009)
    for index in range(4):
        stroke(d, [(0.34 + 0.10 * index, 0.93), (0.34 + 0.10 * index, 0.99)], s, 0.016)
    eye(d, s, 0.35, 0.38, 0.020)


def elephant(d, s, v):
    body = [(0.30, 0.44), (0.56, 0.36), (0.80, 0.44), (0.84, 0.66), (0.76, 0.80),
            (0.34, 0.80), (0.26, 0.62)]
    poly(d, body, s)
    oval(d, 0.28, 0.46, 0.15, 0.15, s)
    oval(d, 0.36, 0.44, 0.15, 0.17, s)
    oval(d, 0.37, 0.44, 0.09, 0.11, s, fill=255)
    trunk = [
        (0.16, 0.44), (0.10, 0.56), (0.09, 0.70), (0.15, 0.80), (0.23, 0.82),
        (0.19, 0.72), (0.17, 0.60), (0.24, 0.50),
    ]
    poly(d, trunk, s)
    for x in (0.36, 0.50, 0.64, 0.76):
        stroke(d, [(x, 0.78), (x, 0.92)], s, 0.028)
    stroke(d, [(0.84, 0.52), (0.94, 0.58), (0.86, 0.66)], s, 0.012)
    if v % 2:
        for index in range(3):
            stroke(d, [(0.34, 0.60 + 0.05 * index), (0.24, 0.62 + 0.05 * index)], s, 0.006, 255)
    eye(d, s, 0.22, 0.42, 0.020)


def mushroom(d, s, v):
    cap_w = (0.40, 0.34)[v % 2]
    cap = []
    for index in range(61):
        t = index / 60
        cap.append(
            (
                0.5 - cap_w + 2.0 * cap_w * t,
                0.56 - 0.30 * math.sin(math.pi * t) ** 0.6,
            )
        )
    cap.append((0.5 + cap_w, 0.58))
    cap.append((0.5 - cap_w, 0.58))
    poly(d, cap, s)
    poly(d, [(0.40, 0.56), (0.60, 0.56), (0.64, 0.90), (0.36, 0.90)], s)
    for index in range(3 if v % 2 == 0 else 5):
        stroke(
            d,
            [
                (0.5, 0.56),
                (0.5 - cap_w + 2.0 * cap_w * (index + 1) / (4 if v % 2 == 0 else 6), 0.56),
            ],
            s,
            0.006,
            255,
        )
    for index in range(4):
        oval(
            d,
            0.5 + (index - 1.5) * 0.12,
            0.40 - 0.03 * (index % 2),
            0.035,
            0.025,
            s,
            fill=255,
        )


def leaf_heart(d, s, v):
    """A spade / redbud leaf: two lobes and a pointed tip."""
    wide = (0.88, 0.80)[v % 2]
    tip = (0.50, 0.08)
    right = quad((0.50, 0.50), (wide, 0.30), (0.50, 0.52), 26)
    left = quad((0.50, 0.52), (1.0 - wide, 0.30), (0.50, 0.50), 26)
    pts = quad(tip, (0.72, 0.24), (0.50, 0.50), 26)
    pts += reversed(quad((0.50, 0.52), (0.28, 0.24), tip, 26))
    poly(d, pts, s)
    stroke(d, [(0.5, 0.52), (0.5, 0.98)], s, 0.014)
    for index in range(3):
        t = 0.2 + 0.18 * index
        y = 0.20 + 0.30 * t
        spread = 0.16 * (1.0 - t) + 0.04
        for side in (-1, 1):
            stroke(d, [(0.5, y), (0.5 + side * spread, y + 0.10)], s, 0.006, 255)


def shell_cowrie(d, s, v):
    oval(d, 0.5, 0.5, 0.32, 0.22, s)
    oval(d, 0.5, 0.5, 0.22, 0.14, s, fill=255)
    oval(d, 0.5, 0.5, 0.17, 0.10, s)
    stroke(d, [(0.28, 0.50), (0.72, 0.50)], s, 0.012, 255)
    for index in range(6 if v % 2 == 0 else 8):
        x = 0.30 + 0.40 * index / (5 if v % 2 == 0 else 7)
        stroke(d, [(x, 0.28), (x + 0.05, 0.36)], s, 0.006, 255)
        stroke(d, [(x, 0.72), (x + 0.05, 0.64)], s, 0.006, 255)


def drop(d, s, v):
    r = (0.27, 0.31)[v % 2]
    cy = 0.60
    oval(d, 0.5, cy, r, r, s)
    poly(d, [(0.5, 0.06), (0.5 - r * 0.92, cy), (0.5 + r * 0.92, cy)], s)
    oval(d, 0.5 - r * 0.35, cy + r * 0.25, r * 0.18, r * 0.26, s, fill=255)


def fox(d, s, v):
    poly(d, [(0.18, 0.94), (0.28, 0.58), (0.48, 0.48), (0.62, 0.62), (0.64, 0.94)], s)
    poly(d, [(0.44, 0.50), (0.62, 0.34), (0.74, 0.56), (0.58, 0.64)], s)
    poly(d, [(0.50, 0.52), (0.44, 0.30), (0.62, 0.46)], s)
    poly(d, [(0.72, 0.46), (0.90, 0.36), (0.82, 0.58), (0.96, 0.62), (0.74, 0.66)], s)
    poly(d, [(0.66, 0.60), (0.78, 0.68), (0.68, 0.72)], s)
    if v % 2:
        stroke(d, [(0.64, 0.86), (0.78, 0.90), (0.66, 0.96)], s, 0.030)
    eye(d, s, 0.56, 0.50, 0.020)


def hedgehog(d, s, v):
    oval(d, 0.48, 0.62, 0.32, 0.22, s)
    spikes = 16 if v % 2 == 0 else 22
    for index in range(spikes):
        t = index / (spikes - 1)
        angle = math.radians(180 + 180 * t)
        x = 0.48 + 0.30 * math.cos(angle)
        y = 0.62 + 0.20 * math.sin(angle)
        stroke(d, [(x, y), (x + 0.07 * math.cos(angle), y + 0.07 * math.sin(angle))], s, 0.010)
    poly(d, [(0.78, 0.54), (0.90, 0.60), (0.84, 0.68), (0.72, 0.68)], s)
    eye(d, s, 0.82, 0.60, 0.018)


def acorn(d, s, v):
    oval(d, 0.5, 0.62, 0.20, 0.24, s)
    cap = [(0.28, 0.44), (0.34, 0.32), (0.5, 0.28), (0.66, 0.32), (0.72, 0.44)]
    poly(d, cap, s)
    for index in range(5 if v % 2 == 0 else 7):
        x = 0.32 + 0.36 * index / (4 if v % 2 == 0 else 6)
        stroke(d, [(x, 0.44), (x, 0.30 - 0.04 * math.sin(math.pi * index / 4))], s, 0.006, 255)
    stroke(d, [(0.5, 0.28), (0.52, 0.18)], s, 0.012)


def pinecone(d, s, v):
    rows = 5 if v % 2 == 0 else 6
    for row in range(rows):
        t = row / (rows - 1)
        width = 0.16 + 0.16 * math.sin(math.pi * (0.15 + 0.7 * t))
        count = 3 + row
        for index in range(count):
            x = 0.5 - width + 2 * width * index / max(count - 1, 1)
            y = 0.24 + 0.58 * t
            poly(d, [(x, y - 0.05), (x + 0.05, y), (x, y + 0.06), (x - 0.05, y)], s)
    stroke(d, [(0.5, 0.16), (0.5, 0.24)], s, 0.012)


def mountain(d, s, v):
    peaks = [(0.04, 0.86), (0.26, 0.34), (0.42, 0.62), (0.60, 0.22), (0.80, 0.58), (0.96, 0.86)]
    poly(d, peaks, s)
    if v % 2:
        poly(d, [(0.60, 0.22), (0.52, 0.40), (0.62, 0.36), (0.68, 0.44), (0.72, 0.34)], s, fill=255)
    oval(d, 0.80, 0.20, 0.08, 0.08, s)


def sun(d, s, v):
    rays = 12 if v % 2 == 0 else 16
    oval(d, 0.5, 0.5, 0.20, 0.20, s)
    for index in range(rays):
        angle = math.radians(360.0 * index / rays)
        stroke(
            d,
            [
                (0.5 + 0.24 * math.cos(angle), 0.5 + 0.24 * math.sin(angle)),
                (0.5 + 0.42 * math.cos(angle), 0.5 + 0.42 * math.sin(angle)),
            ],
            s,
            0.016,
        )


def moon(d, s, v):
    oval(d, 0.5, 0.5, 0.40, 0.40, s)
    offset = 0.20 if v % 2 == 0 else 0.26
    oval(d, 0.5 + offset, 0.42, 0.40, 0.40, s, fill=255)
    for index in range(4):
        angle = 40 + 60 * index
        oval(
            d,
            0.5 + 0.24 * math.cos(math.radians(angle + 180)),
            0.5 + 0.24 * math.sin(math.radians(angle + 180)),
            0.04,
            0.04,
            s,
            fill=255,
        )


def snowflake(d, s, v):
    arms = 6
    for index in range(arms):
        angle = 360.0 * index / arms
        stroke(d, [(0.5, 0.5), (0.5 + 0.42 * math.cos(math.radians(angle)), 0.5 + 0.42 * math.sin(math.radians(angle)))], s, 0.014)
        for step in (0.5, 0.72):
            for side in (-1, 1):
                bx = 0.5 + 0.42 * step * math.cos(math.radians(angle))
                by = 0.5 + 0.42 * step * math.sin(math.radians(angle))
                stroke(
                    d,
                    [
                        (bx, by),
                        (
                            bx + 0.12 * math.cos(math.radians(angle + side * 60)),
                            by + 0.12 * math.sin(math.radians(angle + side * 60)),
                        ),
                    ],
                    s,
                    0.010,
                )
    oval(d, 0.5, 0.5, 0.05, 0.05, s)


def grass_tuft(d, s, v):
    blades = 9 if v % 2 == 0 else 13
    for index in range(blades):
        t = (index + 0.5) / blades
        angle = -90 + (t - 0.5) * 110
        length = 0.62 + 0.24 * math.sin(math.pi * t)
        poly(
            d,
            leaf_points(0.5, 0.94, angle, length, 0.055, power=1.25),
            s,
        )


CATALOGUE = [
    ("leaf", leaf_simple, 3),
    ("leaf-oak", leaf_oak, 3),
    ("leaf-maple", leaf_maple, 2),
    ("leaf-ginkgo", leaf_ginkgo, 2),
    ("leaf-fern", leaf_fern, 3),
    ("leaf-palm", leaf_palm, 2),
    ("clover", clover, 2),
    ("flower-daisy", flower_daisy, 3),
    ("flower-sunflower", flower_sunflower, 2),
    ("flower-tulip", flower_tulip, 2),
    ("flower-lotus", flower_lotus, 2),
    ("flower-bell", flower_bell, 2),
    ("flower-hibiscus", flower_hibiscus, 2),
    ("flower-dandelion", flower_dandelion, 2),
    ("flower-lavender", flower_lavender, 2),
    ("tree-conifer", tree_conifer, 2),
    ("tree-round", tree_round, 2),
    ("tree-palm", tree_palm, 2),
    ("tree-cypress", tree_cypress, 2),
    ("fish", fish, 2),
    ("jellyfish", jellyfish, 2),
    ("starfish", starfish, 2),
    ("shell-nautilus", shell_nautilus, 2),
    ("shell-fan", shell_fan, 2),
    ("crab", crab, 2),
    ("seahorse", seahorse, 2),
    ("octopus", octopus, 2),
    ("whale", whale, 2),
    ("coral", coral, 2),
    ("waves", waves, 2),
    ("bird-flying", bird_flying, 2),
    ("feather", feather, 2),
    ("owl", owl, 2),
    ("butterfly", butterfly, 2),
    ("dragonfly", dragonfly, 2),
    ("bee", bee, 2),
    ("snail", snail, 2),
    ("turtle", turtle, 2),
    ("rabbit", rabbit, 2),
    ("cat", cat, 2),
    ("mushroom", mushroom, 2),
    ("elephant", elephant, 2),
    ("leaf-heart", leaf_heart, 2),
    ("hedgehog", hedgehog, 2),
    ("shell-cowrie", shell_cowrie, 2),
    ("drop", drop, 2),
    ("acorn", acorn, 2),
    ("pinecone", pinecone, 2),
    ("mountain", mountain, 2),
    ("sun", sun, 2),
    ("moon", moon, 2),
    ("snowflake", snowflake, 2),
    ("grass", grass_tuft, 2),
]


def build(out_dir, limit=None):
    from PIL import Image, ImageDraw

    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for name, function, variants in CATALOGUE:
        for variant in range(variants):
            if limit and len(written) >= limit:
                break
            size = PIXELS * SUPERSAMPLE
            image = Image.new("L", (size, size), 255)
            draw = ImageDraw.Draw(image)
            function(draw, size, variant)
            small = image.resize((PIXELS, PIXELS), Image.LANCZOS)
            mono = small.point(lambda value: 0 if value < 160 else 255).convert("1")
            path = out_dir / ("%03d-%s-%d.png" % (len(written) + 1, name, variant + 1))
            mono.save(path, optimize=True)
            written.append(path)
    return written


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(Path(__file__).resolve().parents[1] / "motifs" / "nature"),
        help="folder to write the PNGs into",
    )
    parser.add_argument("--limit", type=int, default=None, help="stop after N images")
    args = parser.parse_args()
    written = build(args.out, args.limit)
    print("wrote %d motif images to %s" % (len(written), args.out))


if __name__ == "__main__":
    main()
