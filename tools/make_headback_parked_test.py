"""Generate the bed-parked A/B test for the back-of-head scallop stretch.

Reads the heraldic program the operator plotted (source g-code), extracts the
two pen-down runs that draw the back-of-head outline - the inner line and the
outer scalloped line, in file order, with the pen-up travel between them -
and writes a standalone test program containing two copies of that geometry:

  copy 1 ("as printed"): the same paper geometry with the original A sequence
          - including the 16 A-direction reversals of the real plot - placed
          at COPY1_CENTER;
  copy 2 ("bed parked"): the identical paper geometry with A held constant,
          so the bed never turns, placed 62 mm below copy 1.

The two copies are constructed from the same bed-frame points, so their paper
shapes are identical; only the kinematics differ. Run it on a fresh sheet and
compare the outline band width of the two copies.

Usage:
    python tools\\make_headback_parked_test.py
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

# Bed-frame window containing the scalloped stretch that prints collapsed.
WINDOW = {"x": (12.0, 36.0), "y": (42.0, 76.0)}
WINDOW_MARGIN = 6.0
COPY1_CENTER = (-28.0, 40.0)
COPY2_CENTER = (-28.0, -22.0)
FEED_CLAMP = (80.0, 2500.0)

SOURCE = ROOT / "samples" / "gcode" / "garysmith793-heraldic-4062900.gcode"
OUTPUT = ROOT / "samples" / "gcode" / "headback-parked-test.gcode"


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


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default=str(SOURCE))
    ap.add_argument("--out", default=str(OUTPUT))
    args = ap.parse_args()

    moves, runs = parse_source(Path(args.source))
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

    def window_bounds(run):
        inside = [i for i in run if in_window(moves[i].bed)]
        first, last_idx = inside[0], inside[-1]
        start = max(run[0], first - 1)
        end = min(run[-1], last_idx + 1)
        return start, end

    s1, e1 = window_bounds(run1)
    s2, e2 = window_bounds(run2)
    seq1 = list(range(s1, e1 + 1))
    seq2 = list(range(s2, e2 + 1))
    travel = list(range(e1 + 1, s2))
    sequence = seq1 + travel + seq2

    pts = {i: moves[i].bed for i in range(len(moves))}
    xs = [pts[i][0] for i in seq1 + seq2]
    ys = [pts[i][1] for i in seq1 + seq2]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    t1 = (COPY1_CENTER[0] - cx, COPY1_CENTER[1] - cy)
    t2 = (COPY2_CENTER[0] - cx, COPY2_CENTER[1] - cy)
    print("shape bbox centre (%.1f, %.1f); copy offsets %s / %s" % (cx, cy, t1, t2))

    a_start = moves[seq1[0] - 1].a
    a_end = moves[seq2[-1]].a
    theta_park = a_end / RATIO

    lines: list[str] = []
    lines.append("(head-back bed-parked A/B test - generated by make_headback_parked_test.py)")
    lines.append("(source: %s)" % Path(args.source).name)
    lines.append("(upper copy: as printed, bed turns, same A reversals as the real plot)")
    lines.append("(lower copy: identical paper shape, bed parked at A%.3f)" % a_end)
    lines.append("(both copies face the same way; compare the outline band width of each)")
    lines.append("G21")
    lines.append("G90")
    lines.append("G94")
    lines.append("G17")
    lines.append("G54")
    lines.append("G0 F3000")
    lines.append("M5")
    lines.append("G65 P115 Q0 A1 W2")

    # ---- copy 1: original kinematics, translated paper geometry ----
    first_pose = seq1[0] - 1
    px, py = moves[first_pose].bed[0] + t1[0], moves[first_pose].bed[1] + t1[1]
    mx, my = to_machine(px, py, moves[first_pose].a)
    lines.append("G0 A%s" % fmt(a_start))
    lines.append("G0 X%s Y%s" % (fmt(mx), fmt(my)))
    lines.append("M3")
    lines.append("G65 P115 Q1 B12 A1 W2")
    lines.append("G1 F350")
    for i in seq1:
        px, py = pts[i][0] + t1[0], pts[i][1] + t1[1]
        mx, my = to_machine(px, py, moves[i].a)
        lines.append(
            "G1 X%s Y%s A%s F%s (%s)" % (fmt(mx), fmt(my), fmt(moves[i].a), fmt(moves[i].f), moves[i].label or "draw")
        )
    lines.append("M5")
    lines.append("G65 P115 Q1 A1 W2")
    pose = seq2[0] - 1
    px, py = pts[pose][0] + t1[0], pts[pose][1] + t1[1]
    mx, my = to_machine(px, py, moves[pose].a)
    lines.append("G0 X%s Y%s A%s (reposition, pen up)" % (fmt(mx), fmt(my), fmt(moves[pose].a)))
    lines.append("M3")
    lines.append("G65 P115 Q1 A1 W2")
    lines.append("G1 F350")
    for i in seq2:
        px, py = pts[i][0] + t1[0], pts[i][1] + t1[1]
        mx, my = to_machine(px, py, moves[i].a)
        lines.append(
            "G1 X%s Y%s A%s F%s (%s)" % (fmt(mx), fmt(my), fmt(moves[i].a), fmt(moves[i].f), moves[i].label or "draw")
        )
    lines.append("M5")
    lines.append("G65 P115 Q1 A1 W2")

    def paper_speed(i):
        prev = moves[i - 1]
        cur = moves[i]
        motion = math.hypot(cur.x - prev.x, cur.y - prev.y, cur.a - prev.a)
        paper = math.hypot(cur.bed[0] - prev.bed[0], cur.bed[1] - prev.bed[1])
        duration = motion / max(cur.f, 1e-9)
        if duration <= 0 or paper <= 0:
            return FEED_CLAMP[0]
        return min(max(paper / duration, FEED_CLAMP[0]), FEED_CLAMP[1])

    # ---- copy 2: identical paper shape, bed parked ----
    pose = seq1[0] - 1
    px, py = pts[pose][0] + t2[0], pts[pose][1] + t2[1]
    mx, my = to_machine(px, py, theta_park * RATIO)
    lines.append("(copy 2: bed parked)")
    lines.append("G0 X%s Y%s" % (fmt(mx), fmt(my)))
    lines.append("M3")
    lines.append("G65 P115 Q1 A1 W2")
    lines.append("G1 F350")
    for i in seq1:
        px, py = pts[i][0] + t2[0], pts[i][1] + t2[1]
        mx, my = to_machine(px, py, theta_park * RATIO)
        lines.append("G1 X%s Y%s F%s (parked)" % (fmt(mx), fmt(my), fmt(paper_speed(i))))
    lines.append("M5")
    lines.append("G65 P115 Q1 A1 W2")
    pose = seq2[0] - 1
    px, py = pts[pose][0] + t2[0], pts[pose][1] + t2[1]
    mx, my = to_machine(px, py, theta_park * RATIO)
    lines.append("G0 X%s Y%s" % (fmt(mx), fmt(my)))
    lines.append("M3")
    lines.append("G65 P115 Q1 A1 W2")
    lines.append("G1 F350")
    for i in seq2:
        px, py = pts[i][0] + t2[0], pts[i][1] + t2[1]
        mx, my = to_machine(px, py, theta_park * RATIO)
        lines.append("G1 X%s Y%s F%s (parked)" % (fmt(mx), fmt(my), fmt(paper_speed(i))))
    lines.append("M5")
    lines.append("G65 P115 Q1 A1 W2")
    lines.append("M65 P0")
    lines.append("G65 P115 Q0 A3 W1")
    lines.append("M64 P0")
    lines.append("G53 G1 X-10 Y-436 F3000 (park home)")
    lines.append("M2")

    out = Path(args.out)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("wrote %s (%d lines)" % (out, len(lines)))

    # ---- verification ----
    vmoves, vruns = parse_source(out)
    draw_runs = [r for r in vruns if len(r) > 4]
    print("verification: %d pen-down runs in the output (expect 4)" % len(draw_runs))
    if len(draw_runs) == 4:
        for name, (gen_run, src_run, off) in (
            ("copy1 inner", (draw_runs[0], seq1, t1)),
            ("copy1 outer", (draw_runs[1], seq2, t1)),
            ("copy2 inner", (draw_runs[2], seq1, t2)),
            ("copy2 outer", (draw_runs[3], seq2, t2)),
        ):
            err = 0.0
            for out_i, src_i in zip(gen_run, src_run):
                ex = vmoves[out_i].bed[0] - (pts[src_i][0] + off[0])
                ey = vmoves[out_i].bed[1] - (pts[src_i][1] + off[1])
                err = max(err, math.hypot(ex, ey))
            print("  %s: max shape error vs source %.4f mm" % (name, err))
        a1 = [vmoves[i].a for i in draw_runs[0] + draw_runs[1]]
        flips = sum(
            1
            for k in range(1, len(a1) - 1)
            if (a1[k] - a1[k - 1]) * (a1[k + 1] - a1[k]) < 0
            and abs(a1[k] - a1[k - 1]) > 0.01
            and abs(a1[k + 1] - a1[k]) > 0.01
        )
        a2 = [vmoves[i].a for i in draw_runs[2] + draw_runs[3]]
        print("  A reversals: copy 1 (moving bed) = %d, copy 2 (parked) A range %.3f deg"
              % (flips, max(a2) - min(a2)))


if __name__ == "__main__":
    main()
