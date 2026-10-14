"""Generate pen-up bed-gap measurement programs for the rotating-bed plotter.

These programs need no sensors or wiring: the controller only positions the
carriage (and indexes the bed) and pauses, while the operator reads a dial
indicator or feeler gauges at each stop. Feed the readings to
``tools/bed_tilt_map.py`` to get the tilt report and map.

* ``grid_*``    5x5 grid in G54 X/Y with the bed parked: gantry-to-bed distance
                against machine position.
* ``rot_*``     carriage parked at the ``--radii`` distances (default
                60/120/180 mm), bed indexed in ``--bed-step`` degrees: disc
                flatness and bearing runout against bed angle. A matching
                ``gap_map_rot.csv`` template is written for the readings.

Every program comes in an ``M0`` variant (pause; resume with Cycle Start) and a
``_dwell`` variant (``G4 P<--dwell>``, default 25 s) for builds without
program pause.

Usage::

    python tools\\make_bed_gap_maps.py --out samples\\gcode
    python tools\\make_bed_gap_maps.py --out samples\\gcode --radii 60,90
"""

from __future__ import annotations

import argparse
from pathlib import Path

RATIO = 12.03324
GRID = (-100.0, -50.0, 0.0, 50.0, 100.0)


def header(title: str, note: str) -> list[str]:
    return [
        "(%s)" % title,
        "(pen-up measurement program: no wiring, read the gauge at each stop)",
        "(requires HOME + bed registration, so G54 X0 Y0 is the bed centre)",
        "(keep the toolhead clear of the bed at the working height)",
        "(%s)" % note,
        "G21",
        "G90",
        "G94",
        "G17",
        "G54",
        "G0 F3000",
        "M5",
        "G4 P1.0",
    ]


def stop(comment: str, pause: bool, dwell: float) -> list[str]:
    if pause:
        return ["M0 (%s)" % comment]
    return ["(stop) %s" % comment, "G4 P%g" % dwell]


def grid_program(pause: bool, dwell: float) -> list[str]:
    lines = header(
        "gap map: 5x5 grid over the used area, bed parked",
        "record the gap at every stop; the bed does not move in this program",
    )
    for iy, y in enumerate(GRID):
        xs = GRID if iy % 2 == 0 else tuple(reversed(GRID))
        for x in xs:
            lines.append("G0 X%.3f Y%.3f" % (x, y))
            lines.append("G4 P0.3")
            lines.append("M5")
            lines.extend(
                stop("G54 X%.1f Y%.1f - read gap, then Cycle Start" % (x, y), pause, dwell)
            )
    lines.append("M5")
    lines.append("M2")
    return lines


def rotation_program(
    pause: bool, radii: list[float], bed_step: float, dwell: float
) -> list[str]:
    steps = int(round(360.0 / bed_step))
    motor_step = bed_step * RATIO
    lines = header(
        "gap map: bed rotation sweep at r = %s mm"
        % " / ".join("%g" % r for r in radii),
        "carriage parks at each radius; the bed indexes %g deg at a time"
        % bed_step,
    )
    for r in radii:
        lines.append("(radius %g mm)" % r)
        lines.append("G0 X%.3f Y0.000" % r)
        lines.append("G4 P0.5")
        for k in range(steps):
            lines.append("M5")
            lines.extend(
                stop(
                    "r=%g mm, angle %g deg - read gap, then Cycle Start"
                    % (r, k * bed_step),
                    pause,
                    dwell,
                )
            )
            if k < steps - 1:
                lines.append("G91")
                lines.append("G1 A%.4f F6000" % motor_step)
                lines.append("G90")
                lines.append("G4 P0.5")
    lines.append("M5")
    lines.append("M2")
    return lines


def rotation_csv(radii: list[float], bed_step: float) -> list[str]:
    steps = int(round(360.0 / bed_step))
    rows = [
        "# fill gap_mm with the dial/feeler reading at each stop",
        "# gap is positive when the surface is further from the reference",
        "type,x,y,radius_mm,angle_deg,gap_mm",
    ]
    for r in radii:
        for k in range(steps):
            rows.append("ring,,,%g,%g," % (r, k * bed_step))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=".", help="output directory (default: current)")
    parser.add_argument(
        "--radii", default="60,120,180",
        help="ring radii in mm, comma separated (default 60,120,180)",
    )
    parser.add_argument(
        "--bed-step", type=float, default=30.0, dest="bed_step",
        help="bed index step in degrees (default 30)",
    )
    parser.add_argument(
        "--dwell", type=float, default=25.0,
        help="dwell seconds per stop in the _dwell variants (default 25)",
    )
    args = parser.parse_args()

    radii = [float(part) for part in args.radii.split(",") if part.strip()]
    if not radii or any(r <= 0.0 for r in radii):
        raise SystemExit("--radii must be a comma list of positive mm distances")
    if args.bed_step <= 0.0:
        raise SystemExit("--bed-step must be positive")
    count = 360.0 / args.bed_step
    if abs(count - round(count)) > 1e-6 or count < 3:
        raise SystemExit("--bed-step must divide 360 into at least three steps")
    if args.dwell <= 0.0:
        raise SystemExit("--dwell must be positive")

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for pause in (True, False):
        suffix = "" if pause else "_dwell"
        for name, program in (("gap_map_grid", grid_program), ("gap_map_rot", rotation_program)):
            path = out / ("%s%s.gcode" % (name, suffix))
            if name == "gap_map_grid":
                content = program(pause, args.dwell)
            else:
                content = program(pause, radii, args.bed_step, args.dwell)
            path.write_text("\n".join(content) + "\n")
            print("wrote %s" % path)
    csv_path = out / "gap_map_rot.csv"
    csv_path.write_text("\n".join(rotation_csv(radii, args.bed_step)) + "\n")
    print("wrote %s" % csv_path)


if __name__ == "__main__":
    main()
