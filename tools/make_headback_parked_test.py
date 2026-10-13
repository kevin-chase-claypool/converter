"""Generate the back-of-head A/B test programs for the scallop stretch.

Reads the heraldic program the operator plotted, extracts the two pen-down
runs that draw the back-of-head outline - the inner line and the outer
scalloped line, in file order - and writes test programs built from the same
bed-frame points, so every copy is the identical paper shape.

Modes:
  default (combined)  one program with two copies side by side:
                      upper = bed turns exactly like the real plot (21 A
                      reversals), lower = bed parked (pure X/Y).
  --split             two programs that draw at the SAME location:
                      `--out`  = the original bed motion;
                      `--out-parked` = identical geometry, bed parked.
                      Run one with each pen colour over the same sheet; the
                      divergence between the colours is the kinematic error.

Usage:
    python tools\\make_headback_parked_test.py
    python tools\\make_headback_parked_test.py --split
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

RATIO = 12.03324
MOVE = re.compile(
    r"^(G[01])\s+X(-?[\d.]+)\s+Y(-?[\d.]+)(?:\s+A(-?[\d.]+))?"
    r"(?:\s+F([\d.]+))?\s*(?:\(([^)]*)\))?\s*$"
)
SET_A = re.compile(r"^G0\s+A(-?[\d.]+)\s*(?:\(.*\))?\s*$")

# Bed-frame window containing the scalloped stretch that prints collapsed.
WINDOW = {"x": (12.0, 36.0), "y": (42.0, 76.0)}
COPY1_CENTER = (-28.0, 40.0)
COPY2_CENTER = (-28.0, -22.0)
FEED_CLAMP = (80.0, 2500.0)

SOURCE = ROOT / "samples" / "gcode" / "garysmith793-heraldic-4062900.gcode"
OUTPUT = ROOT / "samples" / "gcode" / "headback-parked-test.gcode"
SPLIT_OUTPUT = ROOT / "samples" / "gcode" / "headback-test-bed.gcode"
SPLIT_PARKED = ROOT / "samples" / "gcode" / "headback-test-parked.gcode"


def to_bed(x: float, y: float, a: float) -> tuple[float, float]:
    t = math.radians(a / RATIO)
    c, s = math.cos(-t), math.sin(-t)
    return (x * c - y * s, x * s + y * c)


def to_machine(bed_x: float, bed_y: float, a: float) -> tuple[float, float]:
    t = math.radians(a / RATIO)
    c, s = math.cos(t), math.sin(t)
    return (bed_x * c - bed_y * s, bed_x * s + bed_y * c)


def fmt(v: float) -> str:
    return ("%.4f" % v).rstrip("0").rstrip(".")


class Move:
    __slots__ = ("x", "y", "a", "f", "label", "kind", "bed")

    def __init__(self, kind, x, y, a, f, label):
        self.kind = kind
        self.x = x
        self.y = y
        self.a = a
        self.f = f
        self.label = label
        self.bed = to_bed(x, y, a)


def parse_source(path: Path):
    moves: list[Move] = []
    runs: list[list[int]] = []
    pen_down = False
    current_run: list[int] | None = None
    last = {"x": 0.0, "y": 0.0, "a": 0.0}
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = raw.strip()
        if line.startswith("M3"):
            pen_down = True
            current_run = []
            continue
        if line.startswith("M5"):
            pen_down = False
            if current_run:
                runs.append(current_run)
            current_run = None
            continue
        mA = SET_A.match(line)
        if mA:
            last["a"] = float(mA.group(1))
            continue
        m = MOVE.match(line)
        if not m:
            continue
        kind = m.group(1)
        x = float(m.group(2))
        y = float(m.group(3))
        a = float(m.group(4)) if m.group(4) else last["a"]
        f = float(m.group(5)) if m.group(5) else 0.0
        label = (m.group(6) or "").strip()
        move = Move(kind, x, y, a, f, label)
        moves.append(move)
        last = {"x": x, "y": y, "a": a}
        if pen_down and current_run is not None and kind == "G1":
            current_run.append(len(moves) - 1)
    if current_run:
        runs.append(current_run)
    return moves, runs


def in_window(p, margin=0.0):
    return (
        WINDOW["x"][0] - margin <= p[0] <= WINDOW["x"][1] + margin
        and WINDOW["y"][0] - margin <= p[1] <= WINDOW["y"][1] + margin
    )


def collect(moves, runs):
    hits = []
    for run in runs:
        count = sum(1 for i in run if in_window(moves[i].bed))
        if count >= 20:
            hits.append((run, count))
    if len(hits) != 2:
        raise SystemExit(
            "expected exactly two pen-down runs in the window, found %d" % len(hits)
        )
    (run1, n1), (run2, n2) = hits
    print("run 1: %d in-window moves (of %d in the run)" % (n1, len(run1)))
    print("run 2: %d in-window moves (of %d in the run)" % (n2, len(run2)))

    def bounds(run):
        inside = [i for i in run if in_window(moves[i].bed)]
        return max(run[0], inside[0] - 1), min(run[-1], inside[-1] + 1)

    s1, e1 = bounds(run1)
    s2, e2 = bounds(run2)
    seq1 = list(range(s1, e1 + 1))
    seq2 = list(range(s2, e2 + 1))
    pts = {i: moves[i].bed for i in range(len(moves))}
    xs = [pts[i][0] for i in seq1 + seq2]
    ys = [pts[i][1] for i in seq1 + seq2]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    return {
        "moves": moves,
        "pts": pts,
        "seq1": seq1,
        "seq2": seq2,
        "t1": (COPY1_CENTER[0] - cx, COPY1_CENTER[1] - cy),
        "t2": (COPY2_CENTER[0] - cx, COPY2_CENTER[1] - cy),
        "a_start": moves[seq1[0] - 1].a,
        "a_end": moves[seq2[-1]].a,
        "centre": (cx, cy),
    }


def paper_speed(d, i):
    moves = d["moves"]
    prev, cur = moves[i - 1], moves[i]
    motion = math.hypot(cur.x - prev.x, cur.y - prev.y, cur.a - prev.a)
    paper = math.hypot(cur.bed[0] - prev.bed[0], cur.bed[1] - prev.bed[1])
    duration = motion / max(cur.f, 1e-9)
    if duration <= 0 or paper <= 0:
        return FEED_CLAMP[0]
    return min(max(paper / duration, FEED_CLAMP[0]), FEED_CLAMP[1])


def emit_header(lines, source_name, notes):
    lines.append("(head-back A/B test - generated by make_headback_parked_test.py)")
    lines.append("(source: %s)" % source_name)
    lines.extend("(%s)" % n for n in notes)
    lines.extend(["G21", "G90", "G94", "G17", "G54", "G0 F3000", "M5",
                  "G65 P115 Q0 A1 W2"])


def emit_pen_down(lines, first):
    lines.append("M3")
    lines.append("G65 P115 Q1 B12 A1 W2" if first else "G65 P115 Q1 A1 W2")
    lines.append("G1 F350")


def emit_pen_up(lines):
    lines.append("M5")
    lines.append("G65 P115 Q1 A1 W2")


def emit_postamble(lines):
    emit_pen_up(lines)
    lines.append("M65 P0")
    lines.append("G65 P115 Q0 A3 W1")
    lines.append("M64 P0")
    lines.append("G53 G1 X-10 Y-436 F3000 (park home)")
    lines.append("M2")


def emit_turning(lines, d, t, feed_scale=1.0):
    moves, pts = d["moves"], d["pts"]
    seq1, seq2 = d["seq1"], d["seq2"]
    pose = seq1[0] - 1
    mx, my = to_machine(pts[pose][0] + t[0], pts[pose][1] + t[1], moves[pose].a)
    lines.append("G0 A%s" % fmt(moves[pose].a))
    lines.append("G0 X%s Y%s" % (fmt(mx), fmt(my)))
    emit_pen_down(lines, True)
    for i in seq1:
        mx, my = to_machine(pts[i][0] + t[0], pts[i][1] + t[1], moves[i].a)
        lines.append("G1 X%s Y%s A%s F%s (%s)"
                     % (fmt(mx), fmt(my), fmt(moves[i].a), fmt(moves[i].f * feed_scale),
                        moves[i].label or "draw"))
    emit_pen_up(lines)
    pose = seq2[0] - 1
    mx, my = to_machine(pts[pose][0] + t[0], pts[pose][1] + t[1], moves[pose].a)
    lines.append("G0 X%s Y%s A%s (reposition, pen up)" % (fmt(mx), fmt(my), fmt(moves[pose].a)))
    emit_pen_down(lines, False)
    for i in seq2:
        mx, my = to_machine(pts[i][0] + t[0], pts[i][1] + t[1], moves[i].a)
        lines.append("G1 X%s Y%s A%s F%s (%s)"
                     % (fmt(mx), fmt(my), fmt(moves[i].a), fmt(moves[i].f * feed_scale),
                        moves[i].label or "draw"))
    emit_pen_up(lines)


def emit_parked(lines, d, t):
    moves, pts = d["moves"], d["pts"]
    seq1, seq2 = d["seq1"], d["seq2"]
    a_park = d["a_end"]
    lines.append("G0 A%s (park the bed)" % fmt(a_park))
    pose = seq1[0] - 1
    mx, my = to_machine(pts[pose][0] + t[0], pts[pose][1] + t[1], a_park)
    lines.append("G0 X%s Y%s" % (fmt(mx), fmt(my)))
    emit_park_down(lines, True)
    for i in seq1:
        mx, my = to_machine(pts[i][0] + t[0], pts[i][1] + t[1], a_park)
        lines.append("G1 X%s Y%s F%s (parked)" % (fmt(mx), fmt(my), fmt(paper_speed(d, i))))
    emit_pen_up(lines)
    pose = seq2[0] - 1
    mx, my = to_machine(pts[pose][0] + t[0], pts[pose][1] + t[1], a_park)
    lines.append("G0 X%s Y%s" % (fmt(mx), fmt(my)))
    emit_park_down(lines, False)
    for i in seq2:
        mx, my = to_machine(pts[i][0] + t[0], pts[i][1] + t[1], a_park)
        lines.append("G1 X%s Y%s F%s (parked)" % (fmt(mx), fmt(my), fmt(paper_speed(d, i))))
    emit_pen_up(lines)


def emit_park_down(lines, first):
    lines.append("M3")
    lines.append("G65 P115 Q1 B12 A1 W2" if first else "G65 P115 Q1 A1 W2")
    lines.append("G1 F350")


def verify(path: Path, d, layout, expect_turning):
    vmoves, vruns = parse_source(path)
    draw = [r for r in vruns if len(r) > 4]
    print("verification %s: %d pen-down runs (expect %d)" % (path.name, len(draw), len(layout)))
    if len(draw) != len(layout):
        return
    worst = 0.0
    for run, (seq, t) in zip(draw, layout):
        for out_i, src_i in zip(run, seq):
            ex = vmoves[out_i].bed[0] - (d["pts"][src_i][0] + t[0])
            ey = vmoves[out_i].bed[1] - (d["pts"][src_i][1] + t[1])
            worst = max(worst, math.hypot(ex, ey))
    print("  max shape error vs source: %.4f mm" % worst)
    if expect_turning:
        a = [vmoves[i].a for run in draw for i in run]
        flips = sum(
            1 for k in range(1, len(a) - 1)
            if (a[k] - a[k - 1]) * (a[k + 1] - a[k]) < 0
            and abs(a[k] - a[k - 1]) > 0.01 and abs(a[k + 1] - a[k]) > 0.01
        )
        print("  A direction reversals: %d" % flips)
    else:
        a = [vmoves[i].a for run in draw for i in run]
        print("  A range: %.3f deg" % (max(a) - min(a)))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default=str(SOURCE))
    ap.add_argument("--out", default=None)
    ap.add_argument("--out-parked", default=None)
    ap.add_argument("--split", action="store_true",
                    help="write two single-copy files that overlay at the same spot")
    ap.add_argument("--feed-scale", type=float, default=1.0,
                    help="scale the bed-turning copy's draw feeds (e.g. 0.25 = 4x slower)")
    args = ap.parse_args()

    moves, runs = parse_source(Path(args.source))
    d = collect(moves, runs)
    print("shape bbox centre (%.1f, %.1f); offsets %s / %s"
          % (d["centre"][0], d["centre"][1], d["t1"], d["t2"]))
    src_name = Path(args.source).name

    if args.split:
        out = Path(args.out) if args.out else SPLIT_OUTPUT
        parked = Path(args.out_parked) if args.out_parked else (
            out.with_name(out.stem + "-parked.gcode") if args.out else SPLIT_PARKED
        )
        lines = []
        emit_header(lines, src_name, [
            "copy A: the back-of-head stretch with the bed turning exactly as",
            "in the real plot, including its 21 A-direction reversals",
            "run this first, note the pen, then swap to the second pen and",
            "run the parked copy on the same sheet - the divergence between",
            "the two colours is the kinematic error",
        ])
        emit_turning(lines, d, d["t1"], feed_scale=args.feed_scale)
        emit_postamble(lines)
        out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("wrote %s (%d lines)" % (out, len(lines)))

        lines = []
        emit_header(lines, src_name, [
            "copy B: the identical back-of-head stretch with the bed parked",
            "pure X/Y - zero A reversals",
            "run after the bed-turning copy with the second pen;",
            "same location, same shape",
        ])
        emit_parked(lines, d, d["t1"])
        emit_postamble(lines)
        parked.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print("wrote %s (%d lines)" % (parked, len(lines)))

        verify(out, d, [(d["seq1"], d["t1"]), (d["seq2"], d["t1"])], expect_turning=True)
        verify(parked, d, [(d["seq1"], d["t1"]), (d["seq2"], d["t1"])], expect_turning=False)
        return

    out = Path(args.out) if args.out else OUTPUT
    lines = []
    emit_header(lines, src_name, [
        "upper copy: as printed, bed turns, same A reversals as the real plot",
        "lower copy: identical paper shape, bed parked at A%s" % fmt(d["a_end"]),
        "both copies face the same way; compare the outline band of each",
    ])
    emit_turning(lines, d, d["t1"], feed_scale=args.feed_scale)
    emit_parked(lines, d, d["t2"])
    emit_postamble(lines)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote %s (%d lines)" % (out, len(lines)))
    verify(out, d, [(d["seq1"], d["t1"]), (d["seq2"], d["t1"]),
                    (d["seq1"], d["t2"]), (d["seq2"], d["t2"])],
           expect_turning=True)


if __name__ == "__main__":
    main()
