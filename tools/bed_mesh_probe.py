"""Automated bed mesh using the toolhead's existing M3 contact seek as a probe.

No new hardware and no rewiring: the toolhead already homes to the GP2 lift
reference, drives the pen down in bounded pulses, and stops when the CS1238
force reading crosses the contact threshold. The travel it used (pulse count
and the learned-travel EMA) is reported over the toolhead service serial; this
tool drives the RP23NC over telnet/serial, runs one M3 per mesh point, captures
that telemetry, and writes a CSV the existing ``tools\bed_tilt_map.py`` reads.

The travel is proportional to how far the pen had to move to touch the surface,
so it maps directly to the bed height: more travel = surface further away.

Measurement resolution (from toolhead_config.h): the actuator moves about
1.75 mm per 100 ms of full-drive, so a 5 ms fine pulse is ~0.0875 mm. The seek
mixes 10 ms coarse and 5 ms fine pulses; the firmware's per-seek travel (in
fine-pulse units) is recovered here from the warm-seek EMA
(``travel = 4*ema_after - 3*ema_before``). Repeat each point 2-3 times and
average; report the spread so a bad point shows up as a bad point.

Calibration: probe once with the pencil at its normal height, then slide a
known shim (e.g. 0.5 mm) under the pencil tip and probe again. The change in
travel divided by the shim thickness gives ``--mm-per-pulse`` directly (mm per
fine-pulse-equivalent unit).

Usage::

    python tools\\bed_mesh_probe.py --simulate --mode polar --out bed_mesh.csv
    python tools\\bed_mesh_probe.py --robot-host 10.10.10.2 --toolhead-serial COM7 ^
        --mode polar --radii 60,120,180 --angles 12 --out bed_mesh.csv
    python tools\\bed_tilt_map.py bed_mesh.csv --mounts-xy="..." --out bed_mesh.png
"""

from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
import sys
import time
from pathlib import Path

RATIO = 12.03324
FINE_PULSE_MM = 0.0875

TELEMETRY_KEYS = (
    "home_seek_pulses",
    "warm_ema",
    "last_seek_travel",
    "probe_travel",
    "force_norm_raw",
    "cs1238_delta",
    "lift_home",
)


class RobotLink:
    """grblHAL line protocol over telnet or serial."""

    def __init__(self, host: str | None, port: int, serial_port: str | None, baud: int = 115200):
        self.sock = None
        self.ser = None
        if serial_port:
            import serial

            self.ser = serial.Serial(serial_port, baud, timeout=0.2)
        else:
            import socket

            self.sock = socket.create_connection((host, port), timeout=5.0)
            self.sock.settimeout(0.2)
        self._buffer = b""

    def _read_lines(self, timeout: float):
        deadline = time.time() + timeout
        while time.time() < deadline:
            chunk = b""
            if self.sock is not None:
                try:
                    chunk = self.sock.recv(4096)
                except OSError:
                    chunk = b""
            else:
                chunk = self.ser.read(4096) or b""
            if chunk:
                self._buffer += chunk
                while b"\n" in self._buffer:
                    line, self._buffer = self._buffer.split(b"\n", 1)
                    yield line.decode("ascii", "replace").strip()
            else:
                time.sleep(0.02)
        if self._buffer:
            line, self._buffer = self._buffer, b""
            yield line.decode("ascii", "replace").strip()

    def send(self, line: str, timeout: float = 10.0) -> str:
        payload = (line + "\n").encode("ascii")
        if self.sock is not None:
            self.sock.sendall(payload)
        else:
            self.ser.write(payload)
        for response in self._read_lines(timeout):
            if response in ("ok", "error", "error:1", "error:2", "error:3") or response.startswith("error:"):
                return response
            if response.startswith("ALARM"):
                return response
        return "timeout"

    def close(self):
        if self.sock is not None:
            self.sock.close()
        if self.ser is not None:
            self.ser.close()


class ToolheadLink:
    """Toolhead service serial: single-char commands, key=value telemetry lines."""

    def __init__(self, port: str, baud: int = 115200):
        import serial

        self.ser = serial.Serial(port, baud, timeout=0.2)
        self._buffer = b""

    def _lines(self, timeout: float):
        deadline = time.time() + timeout
        while time.time() < deadline:
            chunk = self.ser.read(4096) or b""
            if chunk:
                self._buffer += chunk
                while b"\n" in self._buffer:
                    line, self._buffer = self._buffer.split(b"\n", 1)
                    yield line.decode("ascii", "replace").strip()
            else:
                time.sleep(0.02)

    def snapshot(self, timeout: float = 2.0):
        self.ser.write(b"p")
        for line in self._lines(timeout):
            if "event=SNAPSHOT" in line:
                return parse_telemetry(line)
        return None

    def send(self, data: str):
        self.ser.write(data.encode("ascii"))

    def close(self):
        self.ser.close()


def parse_telemetry(line: str) -> dict:
    data: dict = {"raw": line}
    for key in TELEMETRY_KEYS:
        match = re.search(key + r"=(\d+)(?:/(\d+))?", line)
        if match:
            data[key] = int(match.group(1))
            if match.group(2):
                data[key + "_max"] = int(match.group(2))
    contact = re.search(r"contact:(\d)", line)
    if contact:
        data["contact"] = int(contact.group(1))
    return data


def travel_fine(before: dict, after: dict, mm_per_pulse: float):
    """Per-seek travel in fine-pulse units.

    Preferred: ``probe_travel`` - total travel since the full retract, which
    includes the hold-correction pulses that finish an early-stopped seek.
    Then the per-seek ``last_seek_travel`` export; then the EMA step (quantized,
    so average more probes); then the raw pulse count.
    """
    if after.get("probe_travel"):
        return after["probe_travel"]
    if after.get("last_seek_travel"):
        return after["last_seek_travel"]
    ema_before = before.get("warm_ema", 0)
    ema_after = after.get("warm_ema", 0)
    if ema_before and ema_after and ema_after != ema_before:
        return 4 * ema_after - 3 * ema_before
    # fall back to the raw pulse count (coarse and fine both count as one)
    return after.get("home_seek_pulses", 0)


class FakeRobot:
    def __init__(self, *_, **__):
        self.log = []
        self.toolhead = None

    def send(self, line: str, timeout: float = 10.0) -> str:
        self.log.append(line)
        if self.toolhead is not None:
            self.toolhead._note_move(line)
        return "ok"

    def close(self):
        pass


class FakeToolhead:
    """Synthetic bed: 0.5 mm tilt + 0.12 mm two-lobe warp, with 0.5 mm baseline clearance."""

    def __init__(self, *_, **__):
        self.pos = (0.0, 0.0)
        self.engaged = False
        self.lift_home = 1          # power-on state: pen at the GP2 home switch
        self.cold = False
        self.probe_travel = 0.0
        self.rng = __import__("random").Random(7)
        self.ema = None

    def _note_move(self, line: str):
        m = re.search(r"X(-?[\d.]+)(?: Y(-?[\d.]+))?", line)
        if m and line.startswith("G0"):
            x = float(m.group(1))
            y = float(m.group(2)) if m.group(2) else 0.0
            self.pos = (x, y)
        if line.strip() == "M3":
            self.cold = self.lift_home == 1
            self.engaged = True
            self.lift_home = 0
        if line.strip() == "M5":
            self.engaged = False
            self.lift_home = 0
        if line.strip() == "M65 P0":
            self.lift_home = 1
            self.probe_travel = 0.0
        if line.strip() == "h":
            self.lift_home = 1
            self.probe_travel = 0.0

    def send(self, data: str):
        self._note_move(data)

    def snapshot(self, timeout: float = 2.0):
        x, y = self.pos
        r = math.hypot(x, y)
        height = -0.0025 * x - 0.0012 * y + 0.06 * math.cos(2 * math.atan2(y, x))
        gap = 1.2 + height  # mm from clearance to surface
        if self.engaged:
            base = gap + (2.0 if self.cold else 0.0)
            travel_mm = max(0.0, base + self.rng.gauss(0.0, 0.02))
            travel = travel_mm / FINE_PULSE_MM
            self.probe_travel = travel
            self.ema = travel if self.ema is None else (self.ema * 3 + travel) / 4
            return {
                "home_seek_pulses": int(round(travel)),
                "warm_ema": int(round(self.ema)),
                "last_seek_travel": int(round(travel)),
                "probe_travel": int(round(self.probe_travel)),
                "force_norm_raw": 40000,
                "cs1238_delta": 40000,
            "lift_home": self.lift_home,
                "contact": 1,
            }
        return {
            "home_seek_pulses": 0,
            "warm_ema": int(round(self.ema)) if self.ema else 0,
            "last_seek_travel": 0,
            "force_norm_raw": 0,
            "cs1238_delta": 0,
            "lift_home": self.lift_home,
            "contact": 0,
        }

    def close(self):
        pass


def probe_point(robot, toolhead, args, x: float | None, y: float | None):
    values = []
    units_seen = []

    def one_touch():
        robot.send("M5")
        time.sleep(args.lift_settle)
        if args.retract_each:
            # The M5 clearance is relative to the last contact, so a warm M3
            # only re-traverses a fixed gap. The absolute measurement is a cold
            # seek from the GP2 lift-home switch: retract fully first.
            # Preferred: the toolhead's own 'h' service command. The GP28/Aux0
            # arm line is dual-purpose (magnetic readiness handshake vs
            # end-of-print retract) and is not used unless asked.
            if args.retract_via_arm:
                robot.send("M65 P0")
            else:
                toolhead.send("h")
            deadline = time.time() + args.retract_timeout
            at_home = False
            snap = None
            while time.time() < deadline:
                snap = toolhead.snapshot()
                if snap and snap.get("lift_home") == 1:
                    at_home = True
                    break
                time.sleep(args.poll_sleep)
            if args.retract_via_arm:
                robot.send("M64 P0")
            if not at_home:
                raise RuntimeError(
                    "toolhead never reported the GP2 home switch during retract; last snapshot: %s"
                    % (snap.get("raw") if snap else "no reply")
                )
            # Let the mechanism settle on the switch before the seek: the hard
            # retract stop preloads the thread, and probing immediately after
            # arrival adds a few pulses of scatter between cycles.
            time.sleep(args.home_settle)
        if x is not None:
            robot.send("G0 X%.3f Y%.3f" % (x, y))
            time.sleep(args.move_settle)
        robot.send("M3")
        after = None
        snap = None
        deadline = time.time() + args.probe_timeout
        while time.time() < deadline:
            snap = toolhead.snapshot()
            if snap and snap.get("contact"):
                after = snap
                break
            time.sleep(args.poll_sleep)
        robot.send("M5")
        time.sleep(args.lift_settle)
        if after is None:
            raise RuntimeError(
                "probe timed out at X=%s Y=%s; last snapshot: %s"
                % (x, y, snap.get("raw") if snap else "no reply")
            )
        return travel_fine({}, after, args.mm_per_pulse)

    # The first touch is a conditioning pass like a two-touch probe: it seats
    # the tip and mechanism before the measured touches, and its reading is
    # discarded. The measured touches each start from a fresh GP2 retract, so
    # their travel stays an absolute, switch-referenced distance.
    for _ in range(args.condition_touches):
        conditioning = one_touch()
        print("    conditioning touch: %.1f units (not measured)" % conditioning)

    for _ in range(args.probes_per_point):
        units = one_touch()
        units_seen.append(units)
        values.append(units * args.mm_per_pulse)
        print("    probe %d/%d: %.1f units (%.3f mm)"
              % (len(values), args.probes_per_point, units, units * args.mm_per_pulse))
    spread = (max(values) - min(values)) if len(values) > 1 else 0.0
    # The probe can land in two states ~1.5 mm apart (see the bimodal series in
    # the 2026-10-11 calibration runs). A trimmed mean absorbs both a single
    # outlier and a 50/50 split, where a median would snap to one mode.
    agg = aggregate(units_seen)
    return agg * args.mm_per_pulse, spread, agg


def aggregate(values):
    if len(values) >= 4:
        ordered = sorted(values)
        return statistics.fmean(ordered[1:-1])
    return statistics.fmean(values)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--simulate", action="store_true", help="run the whole pipeline against a synthetic bed")
    parser.add_argument("--robot-host", default="10.10.10.2")
    parser.add_argument("--robot-port", type=int, default=23)
    parser.add_argument("--robot-serial", default=None, help="use USB serial instead of telnet, e.g. COM4")
    parser.add_argument("--toolhead-serial", default=None, help="toolhead USB/service serial port, e.g. COM7")
    parser.add_argument("--mode", choices=("polar", "grid"), default="polar")
    parser.add_argument("--radii", default="60,120,180")
    parser.add_argument("--angles", type=int, default=12, help="number of bed angles per radius (default 12 = 30 deg)")
    parser.add_argument("--grid", default="100,50,0", help="grid half-pitch values; 3 values gives a 5x5 grid")
    parser.add_argument("--probes-per-point", type=int, default=2)
    parser.add_argument("--condition-touches", type=int, default=1, dest="condition_touches",
                        help="unmeasured seating touches before the measured probes (default 1, "
                             "double-touch style: rough approach first, then measure)")
    parser.add_argument("--retract-each", action=argparse.BooleanOptionalAction, default=True,
                        help="full-retract to the GP2 home switch before every probe, so the "
                             "travel is an absolute bed-height measurement (default: on)")
    parser.add_argument("--retract-via-arm", action="store_true",
                        help="retract with the RP23NC M65 P0 arm line instead of the toolhead's "
                             "'h' service command (the arm line is shared with the magnetic "
                             "readiness handshake; leave this off)")
    parser.add_argument("--retract-timeout", type=float, default=15.0)
    parser.add_argument("--home-settle", type=float, default=0.6, dest="home_settle",
                        help="settle time on the GP2 switch before each seek (default 0.6 s)")
    parser.add_argument("--mm-per-pulse", type=float, default=FINE_PULSE_MM,
                        help="calibrated mm per fine-pulse travel unit (default %.4f from 1.75 mm/100 ms)" % FINE_PULSE_MM)
    parser.add_argument("--probe-timeout", type=float, default=30.0)
    parser.add_argument("--lift-settle", type=float, default=0.9)
    parser.add_argument("--move-settle", type=float, default=0.4)
    parser.add_argument("--out", default="bed_mesh.csv")
    parser.add_argument("--poll-sleep", type=float, default=0.2, dest="poll_sleep")
    args = parser.parse_args()

    if args.simulate:
        robot = FakeRobot()
        toolhead = FakeToolhead()
        robot.toolhead = toolhead
        args.lift_settle = 0.01
        args.move_settle = 0.01
        args.poll_sleep = 0.005
    else:
        if not args.toolhead_serial:
            parser.error("--toolhead-serial is required unless --simulate")
        robot = RobotLink(args.robot_host, args.robot_port, args.robot_serial)
        toolhead = ToolheadLink(args.toolhead_serial)

    rows = []
    try:
        if args.mode == "polar":
            radii = [float(v) for v in args.radii.split(",")]
            step_deg = 360.0 / args.angles
            for radius in radii:
                robot.send("G0 X%.3f Y0.000" % radius)
                time.sleep(args.move_settle)
                for k in range(args.angles):
                    angle = k * step_deg
                    gap, spread, units = probe_point(robot, toolhead, args, None, None)
                    print("r=%6.1f mm  angle=%5.1f deg  gap=%.3f mm (%.1f units)  spread=%.3f"
                          % (radius, angle, gap, units, spread))
                    rows.append({"type": "ring", "x": "", "y": "",
                                 "radius_mm": "%.1f" % radius, "angle_deg": "%.1f" % angle,
                                 "gap_mm": "%.3f" % gap})
                    if k < args.angles - 1:
                        robot.send("G91")
                        robot.send("G1 A%.4f F6000" % (step_deg * RATIO))
                        robot.send("G90")
                        time.sleep(args.move_settle)
        else:
            half = [float(v) for v in args.grid.split(",")]
            values = sorted(set([-v for v in half] + [0.0] + list(half)))
            for iy, y in enumerate(values):
                xs = values if iy % 2 == 0 else list(reversed(values))
                for x in xs:
                    gap, spread, units = probe_point(robot, toolhead, args, x, y)
                    print("X=%7.1f  Y=%7.1f  gap=%.3f mm (%.1f units)  spread=%.3f"
                          % (x, y, gap, units, spread))
                    rows.append({"type": "grid", "x": "%.1f" % x, "y": "%.1f" % y,
                                 "radius_mm": "", "angle_deg": "", "gap_mm": "%.3f" % gap})
    finally:
        robot.close()
        toolhead.close()

    out = Path(args.out)
    with out.open("w", newline="") as handle:
        handle.write("# toolhead contact-seek bed mesh; gap = travel from M5 clearance to contact\n")
        writer = csv.DictWriter(handle, fieldnames=("type", "x", "y", "radius_mm", "angle_deg", "gap_mm"))
        writer.writeheader()
        writer.writerows(rows)
    print("\nwrote %s (%d points)" % (out, len(rows)))
    print("next: python tools\\bed_tilt_map.py %s --mounts-xy=\"x1,y1;x2,y2;x3,y3;x4,y4\"" % out)


if __name__ == "__main__":
    main()
