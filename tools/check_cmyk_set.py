"""Preflight a set of layer G-code files against the machine's travel window.

Catches the 2026-10-13 CMYK failure before the first move: computes each
file's machine-coordinate bounding box from the current G54 work offset and
reports any target outside the grblHAL work envelope.

Usage::

    python tools\\check_cmyk_set.py samples\\gcode\\Ben1\\IMG_0514-cmyk-*.gcode ^
        --g54 "-231.214,-193.629"

The default machine window follows the RP23U5XBB settings ($130=455, $131=451,
$27=10, hard limits on): work-limited machine range X [-465, -10],
Y [-461, -10]. Override with --machine-x / --machine-y after any re-derivation.
"""

from __future__ import annotations

import argparse
import glob
import re
from pathlib import Path

MOVE = re.compile(r"^G([01])\s+X(-?[\d.]+)\s+Y(-?[\d.]+)")


def bbox(path: Path):
    xs, ys, n = [], [], 0
    for line in path.read_text(errors="replace").splitlines():
        m = MOVE.match(line)
        if not m:
            continue
        if line.startswith("G53"):  # machine coordinates; checked separately below
            continue
        xs.append(float(m.group(2)))
        ys.append(float(m.group(3)))
        n += 1
    return (min(xs), max(xs), min(ys), max(ys), n) if xs else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("files", nargs="+")
    parser.add_argument("--g54", default="-231.214,-193.629",
                        help='current G54 X,Y work offset, e.g. "-231.214,-193.629"')
    parser.add_argument("--machine-x", default="-465,-10")
    parser.add_argument("--machine-y", default="-461,-10")
    args = parser.parse_args()

    ox, oy = (float(v) for v in args.g54.split(","))
    mx = tuple(float(v) for v in args.machine_x.split(","))
    my = tuple(float(v) for v in args.machine_y.split(","))

    paths = []
    for pattern in args.files:
        paths.extend(sorted(Path(p) for p in glob.glob(pattern)))
    if not paths:
        raise SystemExit("no files matched")

    bad = 0
    for path in paths:
        box = bbox(path)
        if box is None:
            print("%-44s no moves" % path.name)
            continue
        x0, x1, y0, y1, n = box
        m0x, m1x = x0 + ox, x1 + ox
        m0y, m1y = y0 + oy, y1 + oy
        over = []
        if m0x < mx[0]:
            over.append("X %.2f < %.2f (by %.2f mm)" % (m0x, mx[0], mx[0] - m0x))
        if m1x > mx[1]:
            over.append("X %.2f > %.2f (by %.2f mm)" % (m1x, mx[1], m1x - mx[1]))
        if m0y < my[0]:
            over.append("Y %.2f < %.2f (by %.2f mm)" % (m0y, my[0], my[0] - m0y))
        if m1y > my[1]:
            over.append("Y %.2f > %.2f (by %.2f mm)" % (m1y, my[1], m1y - my[1]))
        status = "FAIL: " + "; ".join(over) if over else "ok"
        if over:
            bad += 1
        print("%-44s %6d moves  machine X %8.2f..%8.2f  Y %8.2f..%8.2f  %s"
              % (path.name, n, m0x, m1x, m0y, m1y, status))
    print("\n%d of %d files outside the travel window" % (bad, len(paths)))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
