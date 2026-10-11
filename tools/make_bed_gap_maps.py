"""Generate pen-up bed-gap measurement programs for the rotating-bed plotter.

These programs need no sensors or wiring: the controller only positions the
carriage (and indexes the bed) and pauses, while the operator reads a dial
indicator or feeler gauges at each stop. Feed the readings to
``tools/bed_tilt_map.py`` to get the tilt report and map.

* ``grid_*``    5x5 grid in G54 X/Y with the bed parked: gantry-to-bed distance
                against machine position.
* ``rot_*``     carriage parked at r = 60/120/180 mm, bed indexed in 30 deg
                steps: disc flatness and bearing runout against bed angle.

Every program comes in an ``M0`` variant (pause; resume with Cycle Start) and a
``_dwell`` variant (``G4 P25``) for builds without program pause.

Usage::

    python tools\\make_bed_gap_maps.py --out samples\\gcode
"""

from __future__ import annotations

import argparse
from pathlib import Path

RATIO = 12.03324
GRID = (-100.0, -50.0, 0.0, 50.0, 100.0)
RADII = (60.0, 120.0, 180.0)
STEP_BED_DEG = 30.0
STEP_MOTOR_DEG = STEP_BED_DEG * RATIO


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


def stop(comment: str, pause: bool) -> list[str]:
    if pause:
        return ["M0 (%s)" % comment]
    return ["(stop) %s" % comment, "G4 P25"]


def grid_program(pause: bool) -> list[str]:
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
            lines.extend(stop("G54 X%.1f Y%.1f - read gap, then Cycle Start" % (x, y), pause))
    lines.append("M5")
    lines.append("M2")
    return lines


def rotation_program(pause: bool) -> list[str]:
    lines = header(
        "gap map: bed rotation sweep at r = 60 / 120 / 180 mm",
        "carriage parks at each radius; the bed indexes 30 deg at a time",
    )
    for r in RADII:
        lines.append("(radius %.0f mm)" % r)
        lines.append("G0 X%.3f Y0.000" % r)
        lines.append("G4 P0.5")
        for k in range(int(360 / STEP_BED_DEG)):
            lines.append("M5")
            lines.extend(
                stop("r=%.0f mm, angle %d deg - read gap, then Cycle Start"
                     % (r, k * int(STEP_BED_DEG)), pause)
            )
            if k < int(360 / STEP_BED_DEG) - 1:
                lines.append("G91")
                lines.append("G1 A%.4f F6000" % STEP_MOTOR_DEG)
                lines.append("G90")
                lines.append("G4 P0.5")
    lines.append("M5")
    lines.append("M2")
    return lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=".", help="output directory (default: current)")
    args = parser.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for pause in (True, False):
        suffix = "" if pause else "_dwell"
        for name, program in (("gap_map_grid", grid_program), ("gap_map_rot", rotation_program)):
            path = out / ("%s%s.gcode" % (name, suffix))
            path.write_text("\n".join(program(pause)) + "\n")
            print("wrote %s" % path)


if __name__ == "__main__":
    main()
