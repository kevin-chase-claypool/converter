"""Windows UI for raw CS1238 known-mass calibration through one Pro Micro.

This program never commands the DRV8833 or any motor.  It uses the native USB
serial contract of e07d_cs1238_known_mass_calibration.ino only.
"""
from __future__ import annotations

import csv
import json
import os
import statistics
import threading
import time
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import serial
from serial.tools import list_ports


BAUD_RATE = 115200
MIN_CAPTURE_MS = 250
MAX_CAPTURE_MS = 10000
DOWNWARD_WEIGHT_LOAD = "Downward weight on motor mount"
UPWARD_PEN_REACTION = "Opposite: upward pen-tip reaction"
SAME_FORCE_DIRECTION = "Same direction as calibration load"


def linear_fit(raw_values: list[float], grams: list[float]) -> tuple[dict[str, float], list[float]]:
    """Return the ordinary least-squares grams = slope * raw + offset fit."""
    if len(raw_values) < 3 or len(set(raw_values)) < 2:
        raise ValueError("at least three captures with a non-zero raw span are required")
    raw_mean = statistics.fmean(raw_values)
    gram_mean = statistics.fmean(grams)
    denominator = sum((value - raw_mean) ** 2 for value in raw_values)
    if denominator == 0:
        raise ValueError("the CS1238 values have no measurable span")
    slope = sum((raw - raw_mean) * (gram - gram_mean) for raw, gram in zip(raw_values, grams)) / denominator
    offset = gram_mean - slope * raw_mean
    residuals = [gram - (slope * raw + offset) for raw, gram in zip(raw_values, grams)]
    total = sum((gram - gram_mean) ** 2 for gram in grams)
    return {
        "grams_per_raw_count": slope,
        "offset_g": offset,
        "rms_residual_g": (sum(value * value for value in residuals) / len(residuals)) ** 0.5,
        "r_squared": 1.0 - sum(value * value for value in residuals) / total if total else 1.0,
    }, residuals


def project_printing_force_fit(weight_fit: dict[str, float], relationship: str) -> dict[str, float | str]:
    """Project a signed weight fit into an approximate pen-tip force fit.

    A downward weight on the motor mount and an upward paper reaction at the
    pen normally bend the cell in opposite directions. The caller chooses that
    relationship explicitly because the mechanical load path is not assumed to
    be a precision-equivalent fixture.
    """
    multiplier = -1.0 if relationship == UPWARD_PEN_REACTION else 1.0
    slope = multiplier * float(weight_fit["grams_per_raw_count"])
    offset = multiplier * float(weight_fit["offset_g"])
    if slope == 0:
        raise ValueError("the fitted CS1238 slope is zero")
    return {
        "relationship": relationship,
        "force_equation": "estimated_pen_force_g = grams_per_raw_count * cs1238_raw + offset_g",
        "grams_per_raw_count": slope,
        "offset_g": offset,
        "raw_at_40g": (40.0 - offset) / slope,
        "raw_at_60g": (60.0 - offset) / slope,
        "warning": (
            "Approximate projection only: it assumes the installed upward pen-tip reaction "
            "produces the selected same/opposite strain direction relative to the downward "
            "weight fixture. Confirm raw direction with the installed pen before enabling control."
        ),
    }


class KnownMassCalibrationApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("CS1238 Known-Mass Calibration")
        self.minsize(810, 520)
        self.base_dir = Path(__file__).resolve().parent
        self.results_root = self.base_dir / "results"
        self.port_choice = tk.StringVar()
        self.capture_ms = tk.StringVar(value="1000")
        self.total_mass_g = tk.StringVar(value="0")
        self.pass_direction = tk.StringVar(value="Loading")
        self.calibration_load_direction = tk.StringVar(value=DOWNWARD_WEIGHT_LOAD)
        self.printing_force_relationship = tk.StringVar(value=UPWARD_PEN_REACTION)
        self.connection_status = tk.StringVar(value="Not connected")
        self.capture_status = tk.StringVar(value="Enter the total mass currently resting on the load cell.")
        self.fit_status = tk.StringVar(value="Capture at least three distinct total masses before fitting.")
        self.device: serial.Serial | None = None
        self.serial_lock = threading.Lock()
        self.points: list[dict[str, object]] = []
        self.current_run_dir: Path | None = None
        self.capture_number = 0

        shell = ttk.Frame(self, padding=12)
        shell.grid(sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        shell.columnconfigure(0, weight=1)
        shell.rowconfigure(1, weight=1)

        ttk.Label(shell, text="CS1238 Known-Mass Calibration", font=("TkDefaultFont", 12, "bold")).grid(row=0, column=0, sticky="w")
        tabs = ttk.Notebook(shell)
        tabs.grid(row=1, column=0, sticky="nsew", pady=(8, 0))
        setup = ttk.Frame(tabs, padding=14)
        capture = ttk.Frame(tabs, padding=14)
        results = ttk.Frame(tabs, padding=14)
        help_tab = ttk.Frame(tabs, padding=14)
        tabs.add(setup, text="1. Connect")
        tabs.add(capture, text="2. Capture masses")
        tabs.add(results, text="3. Fit and graphs")
        tabs.add(help_tab, text="Help")

        self._build_setup(setup)
        self._build_capture(capture)
        self._build_results(results)
        self._build_help(help_tab)
        self.refresh_ports()
        self.protocol("WM_DELETE_WINDOW", self.close)

    @staticmethod
    def port_name(choice: str) -> str:
        return choice.split(" — ", 1)[0]

    def _build_setup(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Pro Micro USB COM port").grid(row=0, column=0, sticky="w", pady=4)
        self.port_box = ttk.Combobox(frame, textvariable=self.port_choice, width=56, state="readonly")
        self.port_box.grid(row=0, column=1, sticky="ew", padx=8, pady=4)
        ttk.Button(frame, text="Refresh ports", command=self.refresh_ports).grid(row=0, column=2, padx=(0, 6))
        self.connect_button = ttk.Button(frame, text="Connect", command=self.connect)
        self.connect_button.grid(row=0, column=3)
        ttk.Label(frame, text="Connection").grid(row=1, column=0, sticky="nw", pady=(14, 4))
        ttk.Label(frame, textvariable=self.connection_status, wraplength=620).grid(row=1, column=1, columnspan=3, sticky="w", pady=(14, 4))
        ttk.Button(frame, text="Read device status", command=self.request_status).grid(row=2, column=1, sticky="w", pady=8)
        ttk.Button(frame, text="Read unloaded tare", command=self.tare).grid(row=2, column=2, sticky="w", pady=8)
        ttk.Separator(frame).grid(row=3, column=0, columnspan=4, sticky="ew", pady=12)
        ttk.Label(frame, text="Live device message").grid(row=4, column=0, sticky="nw")
        self.live_message = tk.Text(frame, width=82, height=8, wrap="word", state="disabled")
        self.live_message.grid(row=4, column=1, columnspan=3, sticky="ew")

    def _build_capture(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text="Calibration force direction").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Label(frame, textvariable=self.calibration_load_direction).grid(row=0, column=1, columnspan=3, sticky="w", padx=8, pady=4)
        ttk.Label(frame, text="Printing force relationship").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Combobox(
            frame,
            textvariable=self.printing_force_relationship,
            values=(UPWARD_PEN_REACTION, SAME_FORCE_DIRECTION),
            width=34,
            state="readonly",
        ).grid(row=1, column=1, columnspan=3, sticky="w", padx=8, pady=4)
        ttk.Label(frame, text="Total applied mass (g)").grid(row=2, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.total_mass_g, width=16).grid(row=2, column=1, sticky="w", padx=8, pady=4)
        ttk.Label(frame, text="Use the total currently on the cell: 0, 5, 10, …, 70.").grid(row=2, column=2, columnspan=2, sticky="w")
        ttk.Label(frame, text="Pass").grid(row=3, column=0, sticky="w", pady=4)
        ttk.Combobox(frame, textvariable=self.pass_direction, values=("Loading", "Unloading", "Repeat"), width=14, state="readonly").grid(row=3, column=1, sticky="w", padx=8, pady=4)
        ttk.Label(frame, text="Capture duration (ms)").grid(row=4, column=0, sticky="w", pady=4)
        ttk.Entry(frame, textvariable=self.capture_ms, width=16).grid(row=4, column=1, sticky="w", padx=8, pady=4)
        self.capture_button = ttk.Button(frame, text="Capture raw point", command=self.capture_point, state="disabled")
        self.capture_button.grid(row=5, column=1, sticky="w", pady=(10, 8))
        ttk.Button(frame, text="Start a new run", command=self.new_run).grid(row=5, column=2, sticky="w", pady=(10, 8))
        ttk.Label(frame, textvariable=self.capture_status, wraplength=700).grid(row=6, column=0, columnspan=4, sticky="w", pady=(2, 10))
        ttk.Label(frame, text="Captured points", font=("TkDefaultFont", 10, "bold")).grid(row=7, column=0, columnspan=4, sticky="w")
        columns = ("number", "mass", "pass", "samples", "raw_mean", "raw_sigma")
        self.point_table = ttk.Treeview(frame, columns=columns, show="headings", height=11, selectmode="browse")
        for key, title, width in (
            ("number", "#", 45), ("mass", "Total mass g", 100), ("pass", "Pass", 100),
            ("samples", "Raw samples", 100), ("raw_mean", "Final-half mean", 150), ("raw_sigma", "Final-half σ", 135),
        ):
            self.point_table.heading(key, text=title)
            self.point_table.column(key, width=width, anchor="center")
        self.point_table.grid(row=8, column=0, columnspan=4, sticky="nsew", pady=(6, 0))
        ttk.Button(frame, text="Exclude selected point from fit", command=self.exclude_selected).grid(row=9, column=0, columnspan=2, sticky="w", pady=(8, 0))

    def _build_results(self, frame: ttk.Frame) -> None:
        frame.columnconfigure(0, weight=1)
        ttk.Label(frame, text="Calibration result", font=("TkDefaultFont", 10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.fit_status, wraplength=700).grid(row=1, column=0, sticky="w", pady=(6, 10))
        actions = ttk.Frame(frame)
        actions.grid(row=2, column=0, sticky="w")
        self.fit_button = ttk.Button(actions, text="Fit calibration and save graphs", command=self.fit_and_save, state="disabled")
        self.fit_button.grid(row=0, column=0, padx=(0, 8))
        ttk.Button(actions, text="Open current run folder", command=self.open_run_folder).grid(row=0, column=1, padx=8)
        ttk.Separator(frame).grid(row=3, column=0, sticky="ew", pady=14)
        ttk.Label(frame, text="Saved files", font=("TkDefaultFont", 10, "bold")).grid(row=4, column=0, sticky="w")
        files = (
            "raw/point_###_*.csv — every raw CS1238 sample, unmodified",
            "calibration_points.csv — one representative mean for each capture",
            "calibration_summary.json — downward-weight fit plus estimated upward pen-force projection",
            "calibration_curve.png, estimated_pen_force_projection.png, residuals.png, raw_traces.png — figures for review/reporting",
        )
        for index, line in enumerate(files, start=5):
            ttk.Label(frame, text=line).grid(row=index, column=0, sticky="w", pady=2)

    def _build_help(self, frame: ttk.Frame) -> None:
        text = (
            "1. Flash e07d_cs1238_known_mass_calibration.ino. Keep the actuator 6 V rail disconnected.\n\n"
            "2. Connect the Pro Micro by its native USB port. Select that COM port here, then use Read device status.\n\n"
            "3. With the installed load cell unloaded, use Read unloaded tare. Tare is a diagnostic baseline; it does not change raw capture data.\n\n"
            "4. Place the precision weights downward on the motor mount. This characterizes the cell; it may bend opposite to the upward reaction force at the pen tip. Leave Printing force relationship at Opposite unless a simple installed-pen check shows otherwise. Enter the total mass, wait for it to stop moving, then click Capture raw point.\n\n"
            "5. Capture 0, 5, 10, …, 70 g while loading. Repeat the sequence while unloading. Keep at least three complete loading/unloading passes for a defensible calibration.\n\n"
            "6. Click Fit calibration and save graphs. The summary retains both the measured downward-weight fit and an estimated 40–60 g upward pen-force raw window. The latter is an approximate sign projection, not a precision claim. Confirm the raw direction with the installed pen before copying anything into later force-control firmware."
        )
        help_text = tk.Text(frame, width=86, height=23, wrap="word", relief="solid", borderwidth=1, padx=8, pady=8)
        help_text.insert("1.0", text)
        help_text.configure(state="disabled")
        help_text.grid(sticky="nsew")

    def refresh_ports(self) -> None:
        choices = [f"{port.device} — {port.description}" for port in list_ports.comports()]
        self.port_box["values"] = choices
        if choices and not self.port_choice.get():
            self.port_choice.set(choices[0])
        if not choices:
            self.connection_status.set("No COM ports found. Connect the Pro Micro USB cable, then refresh.")

    def append_message(self, message: str) -> None:
        def update() -> None:
            self.live_message.configure(state="normal")
            self.live_message.delete("1.0", "end")
            self.live_message.insert("1.0", message)
            self.live_message.configure(state="disabled")
        self.after(0, update)

    def connect(self) -> None:
        if self.device and self.device.is_open:
            self.disconnect()
            return
        if not self.port_choice.get():
            messagebox.showerror("No COM port", "Select the Pro Micro USB COM port first.")
            return
        self.connect_button.configure(state="disabled")
        self.connection_status.set("Connecting…")
        threading.Thread(target=self._connect_worker, daemon=True).start()

    def _connect_worker(self) -> None:
        try:
            device = serial.Serial(self.port_name(self.port_choice.get()), BAUD_RATE, timeout=0.25, write_timeout=1)
            time.sleep(0.25)
            device.reset_input_buffer()
            device.write(b"STATUS\n")
            device.flush()
            lines = self._read_until_quiet(device, 1.5)
            response = "\n".join(lines) or "No STATUS response received. Confirm the E-07D sketch is flashed."
            self.device = device
            self.after(0, lambda: self._connected(response))
        except (serial.SerialException, OSError) as error:
            self.after(0, lambda: self._connection_failed(str(error)))

    def _connected(self, response: str) -> None:
        self.connection_status.set("Connected at 115200 baud. " + response.replace("\n", " "))
        self.append_message(response)
        self.connect_button.configure(text="Disconnect", state="normal")
        self.capture_button.configure(state="normal")

    def _connection_failed(self, error: str) -> None:
        self.connection_status.set("Connection failed: " + error)
        self.connect_button.configure(state="normal")

    def disconnect(self) -> None:
        if self.device:
            self.device.close()
        self.device = None
        self.connection_status.set("Disconnected")
        self.connect_button.configure(text="Connect", state="normal")
        self.capture_button.configure(state="disabled")

    @staticmethod
    def _read_until_quiet(device: serial.Serial, seconds: float) -> list[str]:
        lines: list[str] = []
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            line = device.readline().decode("utf-8", errors="replace").strip()
            if line:
                lines.append(line)
        return lines

    def _send_simple(self, command: str, label: str) -> None:
        if not self.device or not self.device.is_open:
            messagebox.showerror("Not connected", "Connect to the Pro Micro first.")
            return
        self.connection_status.set(f"Sending {command}…")
        threading.Thread(target=self._simple_worker, args=(command, label), daemon=True).start()

    def request_status(self) -> None:
        self._send_simple("STATUS", "Device status")

    def tare(self) -> None:
        self._send_simple("TARE", "Unloaded tare")

    def _simple_worker(self, command: str, label: str) -> None:
        try:
            assert self.device is not None
            with self.serial_lock:
                self.device.reset_input_buffer()
                self.device.write((command + "\n").encode("ascii"))
                self.device.flush()
                lines = self._read_until_quiet(self.device, 2.5)
            response = "\n".join(lines) or "No response received."
            self.after(0, lambda: self._simple_done(label, response))
        except (serial.SerialException, OSError) as error:
            self.after(0, lambda: self._simple_done(label, f"Communication error: {error}"))

    def _simple_done(self, label: str, response: str) -> None:
        self.connection_status.set(f"{label}: {response.replace(chr(10), ' ')}")
        self.append_message(response)

    def capture_point(self) -> None:
        try:
            mass = float(self.total_mass_g.get())
            duration = int(self.capture_ms.get())
        except ValueError:
            messagebox.showerror("Invalid entry", "Total mass must be a number and capture duration must be whole milliseconds.")
            return
        if mass < 0 or mass > 300:
            messagebox.showerror("Invalid mass", "Enter a total mass from 0 to 300 g.")
            return
        if not MIN_CAPTURE_MS <= duration <= MAX_CAPTURE_MS:
            messagebox.showerror("Invalid capture duration", f"Enter {MIN_CAPTURE_MS} to {MAX_CAPTURE_MS} ms.")
            return
        if self.points and (
            self.points[0]["calibration_load_direction"] != self.calibration_load_direction.get()
            or self.points[0]["printing_force_relationship"] != self.printing_force_relationship.get()
        ):
            messagebox.showerror(
                "Start a new run",
                "Force-direction interpretation cannot change within one calibration run. "
                "Start a new run before changing it.",
            )
            return
        if not self.device or not self.device.is_open:
            messagebox.showerror("Not connected", "Connect to the Pro Micro first.")
            return
        self.capture_button.configure(state="disabled")
        self.capture_status.set(f"Capturing {duration} ms at {mass:g} g…")
        threading.Thread(target=self._capture_worker, args=(mass, duration, self.pass_direction.get()), daemon=True).start()

    def _capture_worker(self, mass: float, duration: int, direction: str) -> None:
        try:
            assert self.device is not None
            lines: list[str] = []
            with self.serial_lock:
                self.device.reset_input_buffer()
                self.device.write(f"CAPTURE {duration}\n".encode("ascii"))
                self.device.flush()
                deadline = time.monotonic() + (duration / 1000.0) + 5.0
                completed = False
                while time.monotonic() < deadline:
                    line = self.device.readline().decode("utf-8", errors="replace").strip()
                    if not line:
                        continue
                    lines.append(line)
                    if line.startswith("CAPTURE_STOP,"):
                        completed = "reason=completed" in line
                        break
            samples: list[tuple[int, int]] = []
            for line in lines:
                pieces = line.split(",")
                if len(pieces) == 3 and pieces[0] == "SAMPLE":
                    samples.append((int(pieces[1]), int(pieces[2])))
            if not completed:
                raise RuntimeError("capture did not complete: " + (lines[-1] if lines else "no device response"))
            if len(samples) < 3:
                raise RuntimeError("capture completed without enough raw samples")
            self.after(0, lambda: self._store_capture(mass, duration, direction, samples, lines))
        except (ValueError, RuntimeError, serial.SerialException, OSError) as error:
            self.after(0, lambda: self._capture_failed(str(error)))

    def _run_dir(self) -> Path:
        if self.current_run_dir is None:
            stamp = datetime.now().strftime("run_%Y-%m-%d_%H-%M-%S")
            self.current_run_dir = self.results_root / stamp
            (self.current_run_dir / "raw").mkdir(parents=True, exist_ok=False)
            (self.current_run_dir / "metadata.json").write_text(json.dumps({
                "created_local": datetime.now().isoformat(timespec="seconds"),
                "method": "Pro Micro RP2350 E-07D raw CS1238 known-mass calibration",
                "calibration_load_direction": self.calibration_load_direction.get(),
                "printing_force_relationship": self.printing_force_relationship.get(),
                "raw_data_policy": "Raw capture files are retained unfiltered. Representative values use the final half of each capture.",
                "firmware_command": "CAPTURE <ms>",
            }, indent=2) + "\n", encoding="utf-8")
        return self.current_run_dir

    def _store_capture(self, mass: float, duration: int, direction: str, samples: list[tuple[int, int]], lines: list[str]) -> None:
        self.capture_number += 1
        run_dir = self._run_dir()
        raw_path = run_dir / "raw" / f"point_{self.capture_number:03d}_{mass:g}g_{direction.lower()}.csv"
        with raw_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(("time_us", "cs1238_raw"))
            writer.writerows(samples)
        with (run_dir / "device_messages.log").open("a", encoding="utf-8") as handle:
            handle.write(f"\n# point {self.capture_number:03d}, mass_g={mass:g}, pass={direction}\n")
            handle.write("\n".join(lines) + "\n")
        final_half = [raw for time_us, raw in samples if time_us >= samples[-1][0] / 2]
        mean = statistics.fmean(final_half)
        sigma = statistics.pstdev(final_half) if len(final_half) > 1 else 0.0
        point = {
            "number": self.capture_number,
            "mass_g": mass,
            "pass": direction,
            "calibration_load_direction": self.calibration_load_direction.get(),
            "printing_force_relationship": self.printing_force_relationship.get(),
            "capture_ms": duration,
            "sample_count": len(samples),
            "final_half_sample_count": len(final_half),
            "raw_mean": mean,
            "raw_sigma": sigma,
            "raw_file": str(raw_path.relative_to(run_dir)),
            "included": True,
        }
        self.points.append(point)
        self._write_points_csv()
        self._refresh_table()
        self.capture_status.set(
            f"Saved point {self.capture_number}: {mass:g} g, {len(samples)} raw samples, final-half mean {mean:.1f}, σ {sigma:.1f}."
        )
        self.append_message(lines[-1])
        self.capture_button.configure(state="normal")
        self._update_fit_button()

    def _capture_failed(self, error: str) -> None:
        self.capture_status.set("Capture failed: " + error)
        self.capture_button.configure(state="normal" if self.device and self.device.is_open else "disabled")

    def _write_points_csv(self) -> None:
        if not self.current_run_dir:
            return
        fields = ("number", "mass_g", "pass", "calibration_load_direction", "printing_force_relationship", "capture_ms", "sample_count", "final_half_sample_count", "raw_mean", "raw_sigma", "raw_file", "included")
        with (self.current_run_dir / "calibration_points.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(self.points)

    def _refresh_table(self) -> None:
        self.point_table.delete(*self.point_table.get_children())
        for point in self.points:
            label = "excluded" if not point["included"] else point["pass"]
            self.point_table.insert("", "end", iid=str(point["number"]), values=(
                point["number"], f"{point['mass_g']:g}", label, point["sample_count"],
                f"{point['raw_mean']:.1f}", f"{point['raw_sigma']:.1f}",
            ))

    def exclude_selected(self) -> None:
        selection = self.point_table.selection()
        if not selection:
            messagebox.showinfo("No selected point", "Select a point in the table first.")
            return
        number = int(selection[0])
        for point in self.points:
            if point["number"] == number:
                point["included"] = False
                break
        self._write_points_csv()
        self._refresh_table()
        self._update_fit_button()

    def _included_points(self) -> list[dict[str, object]]:
        return [point for point in self.points if point["included"]]

    def _update_fit_button(self) -> None:
        included = self._included_points()
        masses = {float(point["mass_g"]) for point in included}
        enabled = len(included) >= 3 and len(masses) >= 3
        self.fit_button.configure(state="normal" if enabled else "disabled")
        if enabled:
            self.fit_status.set(f"{len(included)} included captures at {len(masses)} total masses. Ready to fit and save graphs.")
        else:
            self.fit_status.set("Capture at least three distinct total masses before fitting.")

    def new_run(self) -> None:
        if self.points and not messagebox.askyesno("Start a new run", "Keep the current run on disk and start an empty new run?"):
            return
        self.points.clear()
        self.current_run_dir = None
        self.capture_number = 0
        self._refresh_table()
        self._update_fit_button()
        self.capture_status.set("New run ready. The next capture creates a new timestamped results folder.")

    def fit_and_save(self) -> None:
        included = self._included_points()
        try:
            raw = [float(point["raw_mean"]) for point in included]
            grams = [float(point["mass_g"]) for point in included]
            fit, residuals = linear_fit(raw, grams)
            assert self.current_run_dir is not None
            slope = fit["grams_per_raw_count"]
            fit["raw_at_downward_weight_40g"] = (40.0 - fit["offset_g"]) / slope
            fit["raw_at_downward_weight_60g"] = (60.0 - fit["offset_g"]) / slope
            printing_fit = project_printing_force_fit(fit, self.printing_force_relationship.get())
            summary = {
                "created_local": datetime.now().isoformat(timespec="seconds"),
                "downward_weight_fit_equation": "downward_weight_g = grams_per_raw_count * cs1238_raw + offset_g",
                "downward_weight_fit": fit,
                "estimated_printing_force_fit": printing_fit,
                "included_point_count": len(included),
                "raw_policy": "All raw records are in raw/. Point means use the final half of each capture only.",
                "warning": "This result is not a production motor-control authorization. The estimated printing-force fit is a direction projection from a downward weight fixture; review traces, repeatability, raw direction at the installed pen, and later actuator tests first.",
            }
            (self.current_run_dir / "calibration_summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
            self._make_graphs(included, raw, grams, residuals, fit, printing_fit)
            self.fit_status.set(
                f"Saved downward-weight fit: g = {slope:.9g} × raw + {fit['offset_g']:.5g}; R² = {fit['r_squared']:.6f}. "
                f"Estimated 40–60 g pen-force raw window: {printing_fit['raw_at_40g']:.1f} to {printing_fit['raw_at_60g']:.1f} ({printing_fit['relationship']})."
            )
        except (ValueError, ZeroDivisionError) as error:
            messagebox.showerror("Cannot fit calibration", str(error))

    def _make_graphs(
        self,
        points: list[dict[str, object]],
        raw: list[float],
        grams: list[float],
        residuals: list[float],
        fit: dict[str, float],
        printing_fit: dict[str, float | str],
    ) -> None:
        assert self.current_run_dir is not None
        colors = {"Loading": "#1f77b4", "Unloading": "#d62728", "Repeat": "#2ca02c"}
        figure, axis = plt.subplots(figsize=(8, 5), layout="constrained")
        for direction in colors:
            selected = [(float(point["raw_mean"]), float(point["mass_g"])) for point in points if point["pass"] == direction]
            if selected:
                axis.scatter(*zip(*selected), label=direction, color=colors[direction], s=45)
        lower, upper = min(raw), max(raw)
        span = max(1.0, upper - lower)
        line_x = [lower - 0.05 * span, upper + 0.05 * span]
        line_y = [fit["grams_per_raw_count"] * value + fit["offset_g"] for value in line_x]
        axis.plot(line_x, line_y, color="black", label="OLS fit")
        axis.set(title="CS1238 downward-weight calibration", xlabel="CS1238 raw count (final-half mean)", ylabel="Applied downward mass (g)")
        axis.grid(True, alpha=0.3)
        axis.legend()
        figure.savefig(self.current_run_dir / "calibration_curve.png", dpi=180)
        plt.close(figure)

        pen_slope = float(printing_fit["grams_per_raw_count"])
        pen_offset = float(printing_fit["offset_g"])
        pen_40 = float(printing_fit["raw_at_40g"])
        pen_60 = float(printing_fit["raw_at_60g"])
        lower = min(min(raw), pen_40, pen_60)
        upper = max(max(raw), pen_40, pen_60)
        span = max(1.0, upper - lower)
        line_x = [lower - 0.05 * span, upper + 0.05 * span]
        figure, axis = plt.subplots(figsize=(8, 5), layout="constrained")
        axis.plot(
            line_x,
            [pen_slope * value + pen_offset for value in line_x],
            color="#7c3aed",
            label="Estimated pen-force projection",
        )
        axis.axhspan(40, 60, color="#ffbf00", alpha=0.18, label="Initial 40–60 g target")
        axis.axvline(pen_40, color="#92400e", linestyle="--", linewidth=1, label="40 g candidate raw")
        axis.axvline(pen_60, color="#b45309", linestyle="--", linewidth=1, label="60 g candidate raw")
        axis.set(
            title="Estimated upward pen-force projection",
            xlabel="CS1238 raw count",
            ylabel="Estimated pen force (g)",
        )
        axis.text(
            0.02,
            0.02,
            str(printing_fit["warning"]),
            transform=axis.transAxes,
            fontsize=8,
            va="bottom",
            wrap=True,
        )
        axis.grid(True, alpha=0.3)
        axis.legend(fontsize=8)
        figure.savefig(self.current_run_dir / "estimated_pen_force_projection.png", dpi=180)
        plt.close(figure)

        figure, axis = plt.subplots(figsize=(8, 4), layout="constrained")
        for direction in colors:
            selected = [(float(point["mass_g"]), residual) for point, residual in zip(points, residuals) if point["pass"] == direction]
            if selected:
                axis.scatter(*zip(*selected), label=direction, color=colors[direction], s=45)
        axis.axhline(0, color="black", linewidth=1)
        axis.set(title="Calibration residuals", xlabel="Applied mass (g)", ylabel="Measured − fitted mass (g)")
        axis.grid(True, alpha=0.3)
        axis.legend()
        figure.savefig(self.current_run_dir / "residuals.png", dpi=180)
        plt.close(figure)

        figure, axis = plt.subplots(figsize=(8, 5), layout="constrained")
        for point in points:
            raw_path = self.current_run_dir / str(point["raw_file"])
            with raw_path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.DictReader(handle))
            times = [int(row["time_us"]) / 1000.0 for row in rows]
            values = [int(row["cs1238_raw"]) for row in rows]
            axis.plot(times, values, linewidth=0.8, alpha=0.65, label=f"{point['mass_g']:g} g {point['pass']}")
        axis.set(title="Raw CS1238 traces", xlabel="Time since capture start (ms)", ylabel="CS1238 raw count")
        axis.grid(True, alpha=0.3)
        axis.legend(fontsize=7, ncol=2)
        figure.savefig(self.current_run_dir / "raw_traces.png", dpi=180)
        plt.close(figure)

    def open_run_folder(self) -> None:
        if not self.current_run_dir:
            messagebox.showinfo("No run yet", "Capture a point first. The app will then create a timestamped results folder.")
            return
        os.startfile(self.current_run_dir)  # type: ignore[attr-defined]

    def close(self) -> None:
        self.disconnect()
        self.destroy()


if __name__ == "__main__":
    KnownMassCalibrationApp().mainloop()
