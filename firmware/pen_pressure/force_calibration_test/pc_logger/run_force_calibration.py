"""Supervised Windows logger for the Pico 2 / Pro Micro force-calibration fixture."""

from __future__ import annotations

import argparse
import csv
import json
import queue
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import serial
from serial.tools import list_ports


@dataclass(frozen=True)
class ReceivedLine:
    source: str
    received_utc: str
    text: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def reader_worker(source: str, port: serial.Serial, lines: queue.Queue[ReceivedLine], stop: threading.Event) -> None:
    while not stop.is_set():
        try:
            raw = port.readline()
        except serial.SerialException as error:
            lines.put(ReceivedLine(source, utc_now(), f"SERIAL_ERROR,{error}"))
            return
        if raw:
            lines.put(ReceivedLine(source, utc_now(), raw.decode("utf-8", errors="replace").strip()))


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pico", help="Pico 2 USB CDC COM port, for example COM5")
    parser.add_argument("--toolhead", help="Pro Micro USB-to-TTL COM port, for example COM6")
    parser.add_argument("--direction", choices=("down", "up"), default="down")
    parser.add_argument("--pulse-ms", type=int, default=20, help="One bounded actuator pulse: 10..100 ms")
    parser.add_argument("--settle-ms", type=int, default=1000, help="Post-pulse capture interval: 0..10000 ms")
    parser.add_argument("--output-dir", type=Path, default=Path("data"), help="Parent directory for dated runs")
    parser.add_argument("--notes", default="", help="Optional operator notes saved as metadata")
    parser.add_argument("--capture-ms", type=int, help="Record reference ADC only: 100..10000 ms; no motor motion")
    parser.add_argument("--list-ports", action="store_true", help="List COM ports and exit")
    return parser.parse_args()


def wait_for(lines: queue.Queue[ReceivedLine], source: str, prefix: str, timeout_s: float, record) -> ReceivedLine:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            line = lines.get(timeout=0.1)
        except queue.Empty:
            continue
        record(line)
        if line.source == source and line.text.startswith(prefix):
            return line
        if line.text.startswith("SERIAL_ERROR,"):
            raise RuntimeError(line.text)
    raise TimeoutError(f"Timed out waiting for {source} record {prefix!r}")


def main() -> int:
    args = parse_arguments()
    if args.list_ports:
        for port in list_ports.comports():
            print(f"{port.device}  {port.description}")
        return 0
    if not args.pico or not args.toolhead:
        raise SystemExit("--pico and --toolhead are required unless --list-ports is used")
    if not 10 <= args.pulse_ms <= 100:
        raise SystemExit("--pulse-ms must be 10 through 100")
    if not 0 <= args.settle_ms <= 10_000 or (args.capture_ms is not None and not 100 <= args.capture_ms <= 10_000):
        raise SystemExit("--settle-ms must be 0 through 10000")

    run_id = datetime.now().strftime("force_calibration_%Y%m%d_%H%M%S")
    run_dir = args.output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    metadata_path = run_dir / "metadata.json"
    metadata = {
        "run_id": run_id,
        "pc_started_utc": utc_now(),
        "pico_port": args.pico,
        "toolhead_port": args.toolhead,
        "direction": args.direction,
        "pulse_ms": args.pulse_ms,
        "settle_ms": args.settle_ms,
        "notes": args.notes,
        "status": "started",
        "timebase": "Pico monotonic microseconds relative to TEST_START",
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    pico = toolhead = None
    stop_readers = threading.Event()
    lines: queue.Queue[ReceivedLine] = queue.Queue()
    threads: list[threading.Thread] = []
    run_complete = False
    pico_stopped = False

    try:
        pico = serial.Serial(args.pico, 115200, timeout=0.1)
        toolhead = serial.Serial(args.toolhead, 115200, timeout=0.1)
        pico.reset_input_buffer()
        toolhead.reset_input_buffer()
        for source, port in (("pico", pico), ("toolhead", toolhead)):
            thread = threading.Thread(target=reader_worker, args=(source, port, lines, stop_readers), daemon=True)
            thread.start()
            threads.append(thread)

        with (run_dir / "samples.csv").open("w", newline="", encoding="utf-8") as samples_file, \
             (run_dir / "events.csv").open("w", newline="", encoding="utf-8") as pico_events_file, \
             (run_dir / "promicro.log").open("w", encoding="utf-8") as toolhead_log:
            samples_writer = csv.writer(samples_file)
            samples_writer.writerow(["toolhead_time_us", "toolhead_cs1238_raw", "reference_time_us", "reference_adc_raw"])
            events_writer = csv.writer(pico_events_file)
            events_writer.writerow(["pc_received_utc", "record"])

            def record(line: ReceivedLine) -> None:
                nonlocal run_complete, pico_stopped
                if line.source == "pico":
                    if line.text.startswith("SAMPLE,"):
                        fields = line.text.split(",")
                        if len(fields) != 5:
                            raise RuntimeError(f"Malformed Pico sample: {line.text}")
                        samples_writer.writerow(fields[1:])
                        # Preview one of every 64 raw records for the GUI; all
                        # records still go unchanged into samples.csv.
                        if g_sample_preview_count[0] % 64 == 0:
                            print(f"PICO {line.text}", flush=True)
                        g_sample_preview_count[0] += 1
                    else:
                        events_writer.writerow([line.received_utc, line.text])
                        print(f"PICO {line.text}", flush=True)
                    if line.text.startswith("TEST_STOP,"):
                        pico_stopped = True
                else:
                    toolhead_log.write(f"{line.received_utc},{line.text}\n")
                    toolhead_log.flush()
                    print(f"PRO_MICRO {line.text}", flush=True)
                    if line.text.startswith("RUN_COMPLETE,"):
                        run_complete = True
                if line.text.startswith("SERIAL_ERROR,"):
                    raise RuntimeError(line.text)

            g_sample_preview_count = [0]
            pico.write(b"STATUS\n")
            pico.flush()
            pico_status = wait_for(lines, "pico", "STATUS,", 5.0, record)
            if "configured=1" not in pico_status.text:
                raise RuntimeError(f"Pico CS1238 is not configured: {pico_status.text}")

            # READY can have been emitted before the serial port was opened;
            # STATUS positively proves the Pro Micro fixture is responsive.
            toolhead.write(b"STATUS\n")
            toolhead.flush()
            wait_for(lines, "toolhead", "STATUS,", 5.0, record)

            command_text = f"CAPTURE {args.capture_ms}" if args.capture_ms is not None else f"RUN {args.direction.upper()} {args.pulse_ms} {args.settle_ms}"
            toolhead.write((command_text + "\n").encode("ascii"))
            toolhead.flush()
            complete_prefix = "CAPTURE_COMPLETE," if args.capture_ms is not None else "RUN_COMPLETE,"
            deadline = time.monotonic() + ((args.capture_ms or args.pulse_ms + args.settle_ms) / 1000.0) + 12.0
            while time.monotonic() < deadline and not (run_complete and pico_stopped):
                try:
                    line = lines.get(timeout=0.1); record(line)
                    if line.source == "toolhead" and line.text.startswith("CAPTURE_COMPLETE"):
                        run_complete = True
                except queue.Empty:
                    continue
            if not run_complete or not pico_stopped:
                raise TimeoutError("Run did not receive both RUN_COMPLETE and Pico TEST_STOP")

        metadata["status"] = "completed"
        metadata["pc_finished_utc"] = utc_now()
        print(f"Completed: {run_dir}")
        return 0
    except Exception as error:
        metadata["status"] = "failed"
        metadata["failure"] = str(error)
        metadata["pc_finished_utc"] = utc_now()
        print(f"FAILED: {error}", file=sys.stderr)
        # STOP makes the Pro Micro sleep and releases GP0 HIGH when the port is alive.
        if toolhead is not None and toolhead.is_open:
            try:
                toolhead.write(b"STOP\n")
                toolhead.flush()
            except serial.SerialException:
                pass
        return 1
    finally:
        metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
        stop_readers.set()
        for port in (pico, toolhead):
            if port is not None:
                port.close()
        for thread in threads:
            thread.join(timeout=0.5)


if __name__ == "__main__":
    raise SystemExit(main())
