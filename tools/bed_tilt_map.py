"""Bed tilt and gap map for the rotating-bed plotter (Klipper-style report).

Measure the gap between a reference at the pen's working height and the bed
surface at a set of points (see the generated ``gap_map_*.gcode`` programs),
write the readings into the CSV template this tool emits, and it will:

* fit the best plane (and optionally a radial bowl term) to the readings,
* print a per-mount "raise by X mm / N turns" report like Klipper's
  ``screws_tilt_adjust``,
* save a 3D surface, a top-down map, the residual-after-plane map, and the
  per-radius profiles to one PNG so the same map can be compared across
  iterations,
* flag whether the residual looks like a rigid tilt (fixable by shimming) or
  like warp/bearing runout (not fixable by shimming alone).

Two measurement types share one CSV:

``grid``  machine G54 X/Y with the bed parked (column ``x``/``y``, mm)
``ring``  bed indexed under a parked carriage (``radius_mm`` and ``angle_deg``,
          bed-frame degrees)

Usage::

    python tools\\bed_tilt_map.py --template bed_map.csv
    python tools\\bed_tilt_map.py bed_map.csv --mounts "90,200;210,200;330,200"
"""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import numpy as np

FIELDS = ("type", "x", "y", "radius_mm", "angle_deg", "gap_mm")

GRID = (-100.0, -50.0, 0.0, 50.0, 100.0)
RADII = (60.0, 120.0, 180.0)
RING_STEP_DEG = 30.0


def template_rows() -> list[dict[str, str]]:
    rows = []
    for iy, y in enumerate(GRID):
        xs = GRID if iy % 2 == 0 else tuple(reversed(GRID))
        for x in xs:
            rows.append(
                {
                    "type": "grid",
                    "x": "%.1f" % x,
                    "y": "%.1f" % y,
                    "radius_mm": "",
                    "angle_deg": "",
                    "gap_mm": "",
                }
            )
    for r in RADII:
        for k in range(int(360 / RING_STEP_DEG)):
            rows.append(
                {
                    "type": "ring",
                    "x": "",
                    "y": "",
                    "radius_mm": "%.1f" % r,
                    "angle_deg": "%.1f" % (k * RING_STEP_DEG),
                    "gap_mm": "",
                }
            )
    return rows


def write_template(path: Path) -> None:
    with path.open("w", newline="") as handle:
        handle.write("# fill gap_mm with the dial/feeler reading at each stop\n")
        handle.write("# gap is positive when the surface is further from the reference\n")
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(template_rows())
    print("wrote template %s (%d rows)" % (path, len(template_rows())))


def load_points(path: Path, bed_angle_deg: float):
    rows = []
    with path.open() as handle:
        lines = [line for line in handle if not line.lstrip().startswith("#")]
    reader = csv.DictReader(lines)
    for row in reader:
        if not row.get("gap_mm"):
            continue
        kind = (row.get("type") or "grid").strip().lower()
        gap = float(row["gap_mm"])
        if kind == "grid":
            x, y = float(row["x"]), float(row["y"])
            if bed_angle_deg:
                t = math.radians(-bed_angle_deg)
                x, y = x * math.cos(t) - y * math.sin(t), x * math.sin(t) + y * math.cos(t)
        elif kind == "ring":
            r = float(row["radius_mm"])
            a = math.radians(float(row["angle_deg"]))
            x, y = r * math.cos(a), r * math.sin(a)
        else:
            raise SystemExit("unknown row type %r" % kind)
        rows.append((x, y, gap, kind, float(row.get("radius_mm") or 0.0)))
    if len(rows) < 6:
        raise SystemExit("need at least 6 readings, found %d" % len(rows))
    return rows


def fit(rows, bowl: bool):
    pts = np.array([[r[0], r[1]] for r in rows])
    gaps = np.array([r[2] for r in rows])
    cols = [np.ones(len(pts)), pts[:, 0], pts[:, 1]]
    names = ["c", "x", "y"]
    if bowl:
        cols.append(pts[:, 0] ** 2 + pts[:, 1] ** 2)
        names.append("r2")
    a = np.stack(cols, axis=1)
    coef, *_ = np.linalg.lstsq(a, gaps, rcond=None)
    pred = a @ coef
    residual = gaps - pred
    return coef, names, pred, residual


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", nargs="?", help="measurement CSV")
    parser.add_argument("--template", metavar="PATH", help="write an empty CSV template and exit")
    parser.add_argument("--mounts", default="90,200;210,200;330,200",
                        help='mount points as "angle_deg:radius_mm" pairs separated by ; (default: 3 mounts at r=200)')
    parser.add_argument("--mounts-xy", default=None,
                        help='mount points as "x,y;x,y;..." in G54 machine mm; overrides --mounts')
    parser.add_argument("--bed-angle", type=float, default=0.0,
                        help="bed angle in degrees during the grid sweep (default 0)")
    parser.add_argument("--pitch", type=float, default=0.7,
                        help="thread pitch of the mount screws, mm per revolution (default 0.7, M4)")
    parser.add_argument("--bowl", action="store_true", help="also fit a radial r^2 term")
    parser.add_argument("--rail-mounts", action="store_true",
                        help="the mount points move the RAIL ends rather than the bed: "
                             "'raise' then means move the rail end away from the bed (up), "
                             "and the reported sign is flipped accordingly")
    parser.add_argument("--out", default=None, help="output PNG (default: beside the CSV)")
    args = parser.parse_args()

    if args.template:
        write_template(Path(args.template))
        return
    if not args.csv:
        parser.error("give a CSV (or --template PATH)")

    csv_path = Path(args.csv)
    rows = load_points(csv_path, args.bed_angle)
    coef, names, pred, residual = fit(rows, args.bowl)
    c, bx, by = coef[0], coef[1], coef[2]

    tilt_deg = math.degrees(math.atan(math.hypot(bx, by)))
    tilt_dir = math.degrees(math.atan2(by, bx))
    print("readings: %d" % len(rows))
    print("plane fit: gap = %.4f %+.5f x %+.5f y%s (mm, mm)"
          % (c, bx, by, (" %+.6f r^2" % coef[3]) if args.bowl else ""))
    print("tilt: %.3f mm across 100 mm  (%.3f deg, high side toward %.0f deg in bed frame)"
          % (math.hypot(bx, by) * 100.0, tilt_deg, tilt_dir))
    print("residual after fit: rms %.3f mm, max %.3f mm" % (
        float(np.sqrt((residual ** 2).mean())), float(np.abs(residual).max())))

    mounts = []
    if args.mounts_xy:
        for item in args.mounts_xy.split(";"):
            item = item.strip()
            if not item:
                continue
            x, y = (float(v) for v in item.split(","))
            mounts.append((math.degrees(math.atan2(y, x)), math.hypot(x, y), x, y))
    else:
        for item in args.mounts.split(";"):
            item = item.strip()
            if not item:
                continue
            angle, radius = (float(v) for v in item.split(","))
            mounts.append((angle, radius,
                           radius * math.cos(math.radians(angle)),
                           radius * math.sin(math.radians(angle))))

    def predict(x, y):
        value = c + bx * x + by * y
        if args.bowl:
            value += coef[3] * (x * x + y * y)
        return value

    ref = float(np.mean([predict(mx, my) for _, _, mx, my in mounts])) if mounts else c
    print("\nmount report (reference = mean of mount heights):")
    what = "rail end" if args.rail_mounts else "surface"
    print("  %-22s %9s %14s %10s" % ("mount (x, y) mm", "gap mm", "%s move mm" % what, "M4 turns"))
    for angle, radius, mx, my in mounts:
        gap = predict(mx, my)
        delta = gap - ref
        if args.rail_mounts:
            # Moving a rail end moves the pen reference, not the surface: a
            # mount whose gap reads high needs its rail end brought DOWN.
            delta = -delta
        action = "raise" if delta > 0 else "lower"
        print("  %-22s %9.3f %14s %10s" % (
            "(%.1f, %.1f)" % (mx, my), gap,
            "%+.3f (%s)" % (delta, action), "%+.2f" % (delta / args.pitch)))
    if args.rail_mounts:
        print("  ('raise' = move the rail end up, away from the bed; 'lower' = toward the bed)")
    else:
        print("  (positive shim = add that thickness under the mount / raise the surface there)")

    ring_rows = [(math.degrees(math.atan2(r[1], r[0])) % 360.0, r[4], r[2]) for r in rows if r[3] == "ring"]
    if ring_rows:
        laps = np.array([a for a, _, _ in ring_rows])
        print("\nring coverage: %d points over %d radii" % (len(ring_rows), len(set(r[4] for r in rows if r[3] == "ring"))))
        # systematic deviation per ring radius after removing the plane
        for radius in sorted(set(r[4] for r in rows if r[3] == "ring")):
            sel = [i for i, r in enumerate(rows) if r[3] == "ring" and r[4] == radius]
            rms = float(np.sqrt((residual[sel] ** 2).mean()))
            print("  r=%.0f mm: residual rms %.3f mm (ring vs gantry plane)" % (radius, rms))

    verdict = []
    rms = float(np.sqrt((residual ** 2).mean()))
    if rms <= 0.05:
        verdict.append("residual is small: the surface is flat to within 0.05 mm once tilted - shim to level and you are done")
    elif rms <= 0.15:
        verdict.append("residual 0.05-0.15 mm: level the tilt, expect a small remaining lump/warp")
    else:
        verdict.append("residual > 0.15 mm: this is not a rigid tilt - leveling alone will not fix it; expect warp/bearing runout")
    print("\nverdict: " + " ".join(verdict))

    _plot(rows, pred, residual, mounts, Path(args.out) if args.out else csv_path.with_suffix(".png"))


def _plot(rows, pred, residual, mounts, out_path: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.tri as mtri
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401

    xs = np.array([r[0] for r in rows])
    ys = np.array([r[1] for r in rows])
    gaps = np.array([r[2] for r in rows])
    # Display convention: positive = surface closer to the pen (higher), which is
    # the sign Klipper's Bed Mesh panel uses. Our gap grows when the surface is
    # further away, so the plotted height is mean(gap) - gap.
    height = float(gaps.mean()) - gaps

    def label_directions(ax):
        """Mark which way +X and +Y run on a 2-D panel."""
        box = dict(facecolor="#151515", edgecolor="none", alpha=0.75, pad=1.5)
        ax.annotate("+X \u2192", xy=(0.99, 0.02), xycoords="axes fraction",
                    ha="right", va="bottom", fontsize=14, fontweight="bold",
                    color="#7fd4ff", bbox=box)
        ax.annotate("\u2191 +Y", xy=(0.01, 0.99), xycoords="axes fraction",
                    ha="left", va="top", fontsize=14, fontweight="bold",
                    color="#ffd27f", bbox=box)
        ax.plot([0.0], [0.0], marker="+", color="#cccccc", markersize=10)
        ax.annotate("0,0 bed centre", (0.0, 0.0), textcoords="offset points",
                    xytext=(6, -12), fontsize=9, color="#cccccc")

    dark = {
        "figure.facecolor": "#151515",
        "axes.facecolor": "#151515",
        "savefig.facecolor": "#151515",
        "text.color": "#e8e8e8",
        "axes.labelcolor": "#e8e8e8",
        "axes.edgecolor": "#5a5a5a",
        "xtick.color": "#c8c8c8",
        "ytick.color": "#c8c8c8",
        "grid.color": "#3a3a3a",
    }
    with plt.rc_context(dark):
        fig = plt.figure(figsize=(13, 10))
        ax3d = fig.add_subplot(2, 2, 1, projection="3d")
        ux = np.unique(xs)
        uy = np.unique(ys)
        # Klipper-style sheet: the measured lattice as a surface with grid
        # lines. Missing lattice points (a grid clipped to the reach radius)
        # become NaN holes instead of dropping the surface entirely.
        lookup = {(round(float(x), 3), round(float(y), 3)): h
                  for x, y, h in zip(xs, ys, height)}
        gx, gy = np.meshgrid(ux, uy)
        gz = np.full(gx.shape, np.nan)
        for yi, yv in enumerate(uy):
            for xi, xv in enumerate(ux):
                gz[yi, xi] = lookup.get((round(float(xv), 3), round(float(yv), 3)), np.nan)
        present = int(np.isfinite(gz).sum())
        if present >= max(0.6 * len(xs), 6):
            surf = ax3d.plot_surface(
                gx, gy, gz, cmap="RdYlBu_r", edgecolor="#6a6a6a",
                linewidth=0.5, antialiased=True, rstride=1, cstride=1,
            )
        else:
            tri = mtri.Triangulation(xs, ys)
            surf = ax3d.plot_trisurf(
                tri, height, cmap="RdYlBu_r", edgecolor="#6a6a6a", linewidth=0.3,
            )
        ax3d.set_title("bed mesh (mm, + = higher)")
        # Direction is carried in the axis labels: the tick numbers already
        # increase along each arrow, so the label states the positive end.
        ax3d.set_xlabel("X (mm), +X \u2192", color="#7fd4ff")
        ax3d.set_ylabel("Y (mm), +Y \u2192", color="#ffd27f")
        try:
            ax3d.set_box_aspect((1.0, 1.0, 0.32))
        except AttributeError:
            pass
        for axis in (ax3d.xaxis, ax3d.yaxis, ax3d.zaxis):
            axis.pane.set_facecolor((0.10, 0.10, 0.10, 1.0))
            axis.pane.set_edgecolor("#5a5a5a")
            axis._axinfo["grid"]["color"] = (0.35, 0.35, 0.35, 0.6)
        ax3d.view_init(elev=26, azim=-58)
        ax3d.set_zticks(np.round(np.linspace(height.min(), height.max(), 5), 2))
        cb = fig.colorbar(surf, ax=ax3d, shrink=0.6, pad=0.13, fraction=0.05)
        cb.set_label("mm")

        ax = fig.add_subplot(2, 2, 2)
        sc = ax.scatter(xs, ys, c=height, cmap="RdYlBu_r", s=70, edgecolors="#101010")
        for angle, radius, mx, my in mounts:
            ax.plot([mx], [my], marker="X", color="#ffffff", markersize=13)
            ax.annotate("mount", (mx, my), textcoords="offset points", xytext=(6, 6))
        fig.colorbar(sc, ax=ax, label="mm")
        ax.set_aspect("equal")
        ax.set_title("top-down map")
        ax.set_xlabel("bed x (mm)")
        ax.set_ylabel("bed y (mm)")
        label_directions(ax)
        ax.grid(True, alpha=0.25)

        ax = fig.add_subplot(2, 2, 3)
        sc = ax.scatter(xs, ys, c=residual, cmap="coolwarm", s=70, edgecolors="#101010")
        fig.colorbar(sc, ax=ax, label="residual (mm)")
        ax.set_aspect("equal")
        ax.set_title("residual after plane fit")
        ax.set_xlabel("bed x (mm)")
        ax.set_ylabel("bed y (mm)")
        label_directions(ax)
        ax.grid(True, alpha=0.25)

        ax = fig.add_subplot(2, 2, 4)
        rads = sorted(set(r[4] for r in rows if r[3] == "ring"))
        for radius in rads:
            sel = [i for i, r in enumerate(rows) if r[3] == "ring" and r[4] == radius]
            angs = np.array([math.degrees(math.atan2(rows[i][1], rows[i][0])) % 360.0 for i in sel])
            ax.plot(angs, gaps[sel], "o-", label="r=%.0f mm" % radius)
        if rads:
            ax.set_xlabel("bed angle (deg)")
            ax.set_ylabel("gap (mm)")
            ax.set_title("ring profiles (disc + bearing runout)")
            ax.legend()
        else:
            ax.text(0.5, 0.5,
                    "no ring data\n(run a polar mesh for disc / bearing runout)",
                    ha="center", va="center", transform=ax.transAxes)
            ax.set_axis_off()
        ax.grid(True, alpha=0.25)

        fig.tight_layout()
        fig.savefig(out_path, dpi=130)
    print("wrote %s" % out_path)


if __name__ == "__main__":
    main()
