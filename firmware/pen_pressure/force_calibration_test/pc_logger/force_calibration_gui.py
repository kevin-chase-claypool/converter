"""Clickable Windows control panel for one supervised force-calibration run."""
from __future__ import annotations

import subprocess
import sys
import threading
import tkinter as tk
import csv
import json
import os
import statistics
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from serial.tools import list_ports


LEAD_MS = 100
STEADY_WINDOW_US = 200_000


def channel_settle_time(rows: list[dict[str, str]], time_key: str, value_key: str,
                        pulse_end_us: int) -> dict[str, float | int | None | str]:
    """Estimate when a raw channel stays at its final value for 200 ms.

    The complete trace stays untouched.  This only produces a repeatable
    analysis reading for the operator and for selecting a suitable capture
    duration; it does not alter the acquisition CSV.
    """
    points = [(int(row[time_key]), float(row[value_key])) for row in rows]
    if len(points) < 3:
        return {"status": "insufficient samples", "settle_ms": None}
    sample_period_us = statistics.median(b - a for (a, _), (b, _) in zip(points, points[1:]))
    final_points = [(time_us, value) for time_us, value in points
                    if time_us >= points[-1][0] - STEADY_WINDOW_US]
    if not final_points or final_points[-1][0] - final_points[0][0] < STEADY_WINDOW_US - sample_period_us:
        return {"status": "insufficient final window", "settle_ms": None}
    final_values = [value for _, value in final_points]
    final_mean = statistics.fmean(final_values)
    final_sigma = statistics.pstdev(final_values) if len(final_values) > 1 else 0.0
    # One raw count prevents a perfectly quantized final window from producing
    # a zero-width acceptance band; the three-sigma term follows observed noise.
    band = 1.0 + 3.0 * final_sigma
    post = [(time_us, value) for time_us, value in points if time_us >= pulse_end_us]
    for index, (start_us, _) in enumerate(post):
        end_us = start_us + STEADY_WINDOW_US
        window = [(time_us, value) for time_us, value in post[index:] if time_us <= end_us]
        if not window or window[-1][0] < end_us - sample_period_us:
            continue
        if all(abs(value - final_mean) <= band for _, value in window):
            return {"status": "settled", "settle_ms": (start_us - pulse_end_us) / 1000.0,
                    "final_mean": final_mean, "noise_sigma": final_sigma, "band": band}
    return {"status": "not settled in capture", "settle_ms": None,
            "final_mean": final_mean, "noise_sigma": final_sigma, "band": band}


def analyze_settling(rows: list[dict[str, str]], pulse_ms: int) -> dict[str, object]:
    """Return independent CS1238 and reference-ADC settling readings."""
    pulse_end_us = (LEAD_MS + pulse_ms) * 1000
    return {
        "method": "final 200 ms mean; first post-pulse 200 ms interval within final mean ± (3 sigma + 1 raw count)",
        "pulse_end_us_from_gate": pulse_end_us,
        "cs1238": channel_settle_time(rows, "toolhead_time_us", "toolhead_cs1238_raw", pulse_end_us),
        "reference_adc": channel_settle_time(rows, "reference_time_us", "reference_adc_raw", pulse_end_us),
    }


def linear_fit(x: list[float], y: list[float]) -> tuple[dict[str, float], list[float]]:
    """Ordinary least-squares fit plus residuals; raises for an unusable span."""
    if len(x) < 2:
        raise ValueError("at least two points are required")
    mean_x, mean_y = statistics.fmean(x), statistics.fmean(y)
    denominator = sum((value - mean_x) ** 2 for value in x)
    if denominator == 0:
        raise ValueError("the calibration input has no measurable span")
    slope = sum((a - mean_x) * (b - mean_y) for a, b in zip(x, y)) / denominator
    intercept = mean_y - slope * mean_x
    residuals = [actual - (slope * raw + intercept) for raw, actual in zip(x, y)]
    ss_total = sum((value - mean_y) ** 2 for value in y)
    return ({"slope": slope, "offset": intercept,
             "rms": (sum(value * value for value in residuals) / len(residuals)) ** 0.5,
             "r_squared": 1.0 - sum(value * value for value in residuals) / ss_total if ss_total else 1.0}, residuals)


class CalibrationApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Force Calibration Test")
        self.resizable(False, False)
        self.base = Path(__file__).parent
        self.pico = tk.StringVar()
        self.toolhead = tk.StringVar()
        self.direction = tk.StringVar(value="down")
        self.pulse = tk.StringVar(value="20")
        self.settle = tk.StringVar(value="1000")
        self.auto_steps = tk.StringVar(value="3")
        self.reference_slope = tk.StringVar(value="")
        self.reference_offset = tk.StringVar(value="")
        self.force_limit = tk.StringVar(value="")
        self.known_mass_g = tk.StringVar(value="50")
        self.reference_capture_ms = tk.StringVar(value="1000")
        self.reference_points = []
        self.data_dir = self.base / "data"
        self.reference_store = self.data_dir / "reference_calibration.json"
        self.latest_result_dir: Path | None = None
        shell = ttk.Frame(self, padding=12); shell.grid()
        tabs = ttk.Notebook(shell); tabs.grid(row=0, column=0, sticky="nsew")
        form = ttk.Frame(tabs, padding=12); reference = ttk.Frame(tabs, padding=12); calibration = ttk.Frame(tabs, padding=12); results = ttk.Frame(tabs, padding=12)
        tabs.add(form, text="Pulse Test"); tabs.add(reference, text="Reference Calibration"); tabs.add(calibration, text="Toolhead Calibration"); tabs.add(results, text="Results")
        ttk.Label(form, text="Pico 2 COM port").grid(row=0, column=0, sticky="w")
        self.pico_box = ttk.Combobox(form, textvariable=self.pico, width=38, state="readonly"); self.pico_box.grid(row=0, column=1, padx=8, pady=4)
        ttk.Label(form, text="Pro Micro COM port").grid(row=1, column=0, sticky="w")
        self.toolhead_box = ttk.Combobox(form, textvariable=self.toolhead, width=38, state="readonly"); self.toolhead_box.grid(row=1, column=1, padx=8, pady=4)
        ttk.Button(form, text="Refresh ports", command=self.refresh_ports).grid(row=0, column=2, rowspan=2, padx=(2, 0))
        ttk.Label(form, text="Direction").grid(row=2, column=0, sticky="w"); ttk.Combobox(form, textvariable=self.direction, values=("down", "up"), width=10, state="readonly").grid(row=2, column=1, sticky="w", padx=8, pady=4)
        ttk.Label(form, text="Pulse ms (10–100)").grid(row=3, column=0, sticky="w"); ttk.Entry(form, textvariable=self.pulse, width=12).grid(row=3, column=1, sticky="w", padx=8, pady=4)
        ttk.Label(form, text="Settle ms (0–10000)").grid(row=4, column=0, sticky="w"); ttk.Entry(form, textvariable=self.settle, width=12).grid(row=4, column=1, sticky="w", padx=8, pady=4)
        self.status = tk.StringVar(value="")
        ttk.Label(form, textvariable=self.status, wraplength=500).grid(row=5, column=0, columnspan=3, sticky="w", pady=(10, 6))
        self.run_button = ttk.Button(form, text="Pulse 1x", command=self.run)
        self.run_button.grid(row=6, column=0, columnspan=3, pady=(2, 0))
        self.settle_reading = tk.StringVar(value="Measured settling: run a pulse to calculate.")
        ttk.Label(form, textvariable=self.settle_reading, wraplength=500).grid(row=7, column=0, columnspan=3, sticky="w", pady=(8, 0))
        ttk.Label(reference, text="Place no load on the strain-gauge ball and record zero. Then place centered known masses and record each one.", wraplength=500).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0,10))
        ttk.Label(reference, text="Known mass (g)").grid(row=1, column=0, sticky="w"); ttk.Entry(reference, textvariable=self.known_mass_g, width=12).grid(row=1, column=1, sticky="w", padx=8)
        ttk.Label(reference, text="Capture ms").grid(row=2, column=0, sticky="w"); ttk.Entry(reference, textvariable=self.reference_capture_ms, width=12).grid(row=2, column=1, sticky="w", padx=8)
        ttk.Button(reference, text="Record Zero", command=lambda: self.record_reference(0.0)).grid(row=3, column=0, pady=8)
        ttk.Button(reference, text="Record Known Weight", command=lambda: self.record_reference(None)).grid(row=3, column=1, pady=8)
        ttk.Button(reference, text="Clear reference points", command=self.clear_reference_points).grid(row=3, column=2, pady=8)
        self.reference_status = tk.StringVar(value="No reference points recorded.")
        ttk.Label(reference, textvariable=self.reference_status, wraplength=500).grid(row=4, column=0, columnspan=3, sticky="w")
        self.reference_table = ttk.Treeview(reference, columns=("mass", "adc"), show="headings", height=5)
        self.reference_table.heading("mass", text="Known mass g"); self.reference_table.column("mass", width=140, anchor="center")
        self.reference_table.heading("adc", text="Reference ADC mean"); self.reference_table.column("adc", width=180, anchor="center")
        self.reference_table.grid(row=5, column=0, columnspan=3, sticky="w", pady=(10, 0))
        ttk.Label(calibration, text="1. Complete Reference Calibration.  2. Choose a conservative pulse and capture duration.  3. Auto Calibrate retains every raw sample but fits only samples after both channels have settled.", wraplength=560).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))
        ttk.Label(calibration, text="Auto steps each direction (1–10)").grid(row=1, column=0, sticky="w"); ttk.Entry(calibration, textvariable=self.auto_steps, width=12).grid(row=1, column=1, sticky="w", padx=8, pady=4)
        ttk.Label(calibration, text="Reference N/count slope").grid(row=2, column=0, sticky="w"); ttk.Entry(calibration, textvariable=self.reference_slope, width=18).grid(row=2, column=1, sticky="w", padx=8, pady=4)
        ttk.Label(calibration, text="Reference-force offset N").grid(row=3, column=0, sticky="w"); ttk.Entry(calibration, textvariable=self.reference_offset, width=18).grid(row=3, column=1, sticky="w", padx=8, pady=4)
        ttk.Label(calibration, text="Absolute force stop limit N").grid(row=4, column=0, sticky="w"); ttk.Entry(calibration, textvariable=self.force_limit, width=18).grid(row=4, column=1, sticky="w", padx=8, pady=4)
        self.auto_button = ttk.Button(calibration, text="Auto Calibrate", command=self.auto_calibrate); self.auto_button.grid(row=5, column=0, columnspan=2, pady=(8, 0))
        self.result_summary = tk.StringVar(value="No calibration analysis has been created yet.")
        ttk.Label(results, text="Calibration outputs", font=("TkDefaultFont", 10, "bold")).grid(row=0, column=0, sticky="w")
        ttk.Label(results, text="Each Auto Calibrate session is retained separately. Select any completed session below to review its raw files and graphs.", wraplength=650).grid(row=1, column=0, sticky="w", pady=(6, 8))
        self.result_table = ttk.Treeview(results, columns=("session", "status", "pulses", "slope", "r2"), show="headings", height=7)
        for column, title, width in (("session", "Session", 200), ("status", "Status", 100), ("pulses", "Pulses", 80), ("slope", "N / CS count", 140), ("r2", "R²", 100)):
            self.result_table.heading(column, text=title); self.result_table.column(column, width=width, anchor="center")
        self.result_table.grid(row=2, column=0, sticky="w")
        self.result_table.bind("<<TreeviewSelect>>", self.select_result)
        ttk.Label(results, textvariable=self.result_summary, wraplength=650).grid(row=3, column=0, sticky="w", pady=(10, 8))
        controls = ttk.Frame(results); controls.grid(row=4, column=0, sticky="w")
        ttk.Button(controls, text="Refresh history", command=self.refresh_results_history).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(controls, text="Open results folder", command=lambda: self.open_result(".")).grid(row=0, column=1, padx=6)
        ttk.Button(controls, text="Open time-trace graph", command=lambda: self.open_result("time_traces.png")).grid(row=0, column=2, padx=6)
        ttk.Button(controls, text="Open transfer graph", command=lambda: self.open_result("transfer_fit.png")).grid(row=0, column=3, padx=6)
        ttk.Button(controls, text="Open residual graph", command=lambda: self.open_result("residuals.png")).grid(row=0, column=4, padx=6)
        monitor = ttk.LabelFrame(shell, text="Live COM monitor", padding=8); monitor.grid(row=1, column=0, sticky="ew", pady=(10,0))
        ttk.Label(monitor, text="Pico 2").grid(row=0, column=0, sticky="w")
        self.pico_monitor = ttk.Treeview(monitor, columns=("event", "toolhead_us", "cs1238_raw", "reference_us", "reference_adc", "cs_settle", "ref_settle"), show="headings", height=1)
        for column, title, width in (("event", "Event", 110), ("toolhead_us", "Toolhead µs", 115), ("cs1238_raw", "CS1238 raw", 115), ("reference_us", "Reference µs", 115), ("reference_adc", "Reference ADC", 115), ("cs_settle", "CS settle ms", 115), ("ref_settle", "Ref settle ms", 115)):
            self.pico_monitor.heading(column, text=title); self.pico_monitor.column(column, width=width, anchor="center")
        self.pico_monitor.insert("", "end", iid="latest", values=("waiting", "", "", "", "", "", "")); self.pico_monitor.grid(row=1, column=0, sticky="ew")
        ttk.Label(monitor, text="Pro Micro UART").grid(row=2, column=0, sticky="w", pady=(8,0))
        self.pro_monitor = ttk.Treeview(monitor, columns=("event", "direction", "pulse_ms", "settle_ms", "trace_settle", "fault"), show="headings", height=1)
        for column, title, width in (("event", "Event", 160), ("direction", "Direction", 100), ("pulse_ms", "Pulse ms", 100), ("settle_ms", "Capture ms", 105), ("trace_settle", "Trace settle ms", 125), ("fault", "Fault", 95)):
            self.pro_monitor.heading(column, text=title); self.pro_monitor.column(column, width=width, anchor="center")
        self.pro_monitor.insert("", "end", iid="latest", values=("waiting", "", "", "", "", "")); self.pro_monitor.grid(row=3, column=0, sticky="ew")
        self.load_reference_store()
        self.refresh_results_history()
        self.refresh_ports()

    def refresh_ports(self) -> None:
        choices = [f"{p.device} — {p.description}" for p in list_ports.comports()]
        self.pico_box["values"] = choices
        self.toolhead_box["values"] = choices
        if choices and not self.pico.get(): self.pico.set(choices[0])
        if len(choices) > 1 and not self.toolhead.get(): self.toolhead.set(choices[1])

    @staticmethod
    def port(value: str) -> str:
        return value.split(" — ", 1)[0]

    def load_reference_store(self) -> None:
        if not self.reference_store.exists():
            return
        try:
            data = json.loads(self.reference_store.read_text(encoding="utf-8"))
            self.reference_points = [(float(point["adc_mean"]), float(point["mass_g"]))
                                     for point in data["points"]]
            self.reference_slope.set(str(data["force_n_per_adc_count"]))
            self.reference_offset.set(str(data["force_offset_n"]))
            self.refresh_reference_table()
            self.reference_status.set(f"Loaded {len(self.reference_points)} saved reference points.")
        except (OSError, ValueError, KeyError, TypeError):
            self.reference_status.set("Saved reference calibration could not be read; record fresh points.")

    def refresh_reference_table(self) -> None:
        self.reference_table.delete(*self.reference_table.get_children())
        for index, (adc, mass) in enumerate(self.reference_points, start=1):
            self.reference_table.insert("", "end", iid=f"reference-{index}", values=(f"{mass:g}", f"{adc:.2f}"))

    def save_reference_store(self) -> None:
        if len(self.reference_points) < 2:
            return
        x, y = zip(*self.reference_points)
        fit, _ = linear_fit(list(x), list(y))
        n_per_count, n_offset = fit["slope"] * 0.00980665, fit["offset"] * 0.00980665
        self.reference_slope.set(f"{n_per_count:.12g}")
        self.reference_offset.set(f"{n_offset:.12g}")
        self.data_dir.mkdir(exist_ok=True)
        data = {
            "method": "ordinary least squares, known mass grams versus raw reference ADC counts",
            "points": [{"adc_mean": adc, "mass_g": mass} for adc, mass in self.reference_points],
            "force_n_per_adc_count": n_per_count, "force_offset_n": n_offset,
            "r_squared": fit["r_squared"], "residual_rms_g": fit["rms"],
        }
        self.reference_store.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        with (self.data_dir / "reference_calibration.csv").open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=("reference_adc_mean", "known_mass_g"))
            writer.writeheader()
            writer.writerows({"reference_adc_mean": adc, "known_mass_g": mass} for adc, mass in self.reference_points)
        self.write_reference_plot(fit)

    def write_reference_plot(self, fit: dict[str, float]) -> None:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        x, y = zip(*self.reference_points)
        figure, axis = plt.subplots(figsize=(7, 4.5), constrained_layout=True)
        axis.scatter(x, y, label="known masses")
        low, high = min(x), max(x)
        axis.plot((low, high), (fit["slope"] * low + fit["offset"], fit["slope"] * high + fit["offset"]), label=f"OLS, R²={fit['r_squared']:.5f}")
        axis.set(xlabel="Reference ADC raw count", ylabel="Known mass (g)", title="Reference strain-gauge calibration")
        axis.grid(True, alpha=0.3); axis.legend()
        figure.savefig(self.data_dir / "reference_calibration.png", dpi=180)
        plt.close(figure)

    def clear_reference_points(self) -> None:
        if not messagebox.askyesno("Clear reference calibration", "Remove the saved reference points and force conversion? The raw capture folders are not deleted."):
            return
        self.reference_points = []
        self.reference_slope.set(""); self.reference_offset.set("")
        self.reference_store.unlink(missing_ok=True)
        self.refresh_reference_table()
        self.reference_status.set("Reference points cleared. Record zero and known masses again.")

    def open_result(self, filename: str) -> None:
        target = self.latest_result_dir if filename == "." else (self.latest_result_dir / filename if self.latest_result_dir else None)
        if target is None or not target.exists():
            messagebox.showinfo("Results", "Select a completed calibration session first.")
            return
        os.startfile(target)  # type: ignore[attr-defined]  # Windows fixture application

    def refresh_results_history(self) -> None:
        self.data_dir.mkdir(exist_ok=True)
        self.result_table.delete(*self.result_table.get_children())
        sessions = sorted(self.data_dir.glob("auto_calibration_*"), reverse=True)
        for session in sessions:
            summary_path = session / "calibration_summary.json"
            try:
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                runs = summary.get("runs", [])
                status = str(summary.get("status", "unknown"))
                slope = summary.get("proposed_force_n_per_cs1238_count")
                r_squared = summary.get("r_squared")
                values = (session.name.removeprefix("auto_calibration_"), status, len(runs),
                          f"{float(slope):.7g}" if slope is not None else "—",
                          f"{float(r_squared):.6f}" if r_squared is not None else "—")
                self.result_table.insert("", "end", iid=str(session), values=values)
            except (OSError, ValueError, TypeError):
                self.result_table.insert("", "end", iid=str(session), values=(session.name, "unreadable", "—", "—", "—"))
        if self.latest_result_dir and self.latest_result_dir.exists():
            self.result_table.selection_set(str(self.latest_result_dir))
            self.result_table.focus(str(self.latest_result_dir))

    def select_result(self, _event=None) -> None:
        selected = self.result_table.selection()
        if not selected:
            return
        self.latest_result_dir = Path(selected[0])
        try:
            summary = json.loads((self.latest_result_dir / "calibration_summary.json").read_text(encoding="utf-8"))
            if summary.get("status") == "completed":
                self.result_summary.set(
                    f"Selected {self.latest_result_dir.name}: Force N = ({float(summary['proposed_force_n_per_cs1238_count']):.8g} × CS1238 raw) + ({float(summary['proposed_force_offset_n']):.8g}); R² = {float(summary['r_squared']):.6f}; RMS = {float(summary['residual_rms_n']):.5g} N.")
            else:
                self.result_summary.set(f"Selected {self.latest_result_dir.name}: session stopped; raw data is retained, but no calibration fit is offered.")
        except (OSError, ValueError, KeyError, TypeError):
            self.result_summary.set("Selected session cannot be summarized; open its folder to inspect the preserved files.")

    def run(self) -> None:
        try:
            pulse, settle = int(self.pulse.get()), int(self.settle.get())
            if not 10 <= pulse <= 100 or not 0 <= settle <= 10000: raise ValueError
            pico, toolhead = self.port(self.pico.get()), self.port(self.toolhead.get())
            if not pico or not toolhead or pico == toolhead: raise ValueError
        except ValueError:
            messagebox.showerror("Check settings", "Choose two different COM ports. Pulse must be 10–100 ms; settle 0–10000 ms.")
            return
        if not messagebox.askyesno("Confirm supervised motion", "The Pro Micro will make one bounded pulse. Confirm the force path is clear and the 6 V cutoff is reachable."):
            return
        self.run_button.configure(state="disabled")
        self.status.set("Running. Do not disconnect either USB cable or leave the test unattended.")
        command = [sys.executable, str(self.base / "run_force_calibration.py"), "--pico", pico, "--toolhead", toolhead, "--direction", self.direction.get(), "--pulse-ms", str(pulse), "--settle-ms", str(settle)]
        threading.Thread(target=self.worker, args=(command,), daemon=True).start()

    def worker(self, command: list[str]) -> None:
        process = subprocess.Popen(command, cwd=self.base, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = []
        assert process.stdout is not None
        for line in process.stdout:
            output.append(line)
            self.after(0, self.monitor_line, line.rstrip())
        self.after(0, self.finished, process.wait(), "".join(output).strip())

    def monitor_line(self, line: str) -> None:
        text = line[5:] if line.startswith("PICO ") else line[10:] if line.startswith("PRO_MICRO ") else line
        fields = text.split(",")
        values = {item.split("=", 1)[0]: item.split("=", 1)[1] for item in fields[1:] if "=" in item}
        if line.startswith("PICO "):
            if fields[0] == "SAMPLE" and len(fields) == 5:
                old = self.pico_monitor.item("latest", "values")
                row = ("SAMPLE", fields[1], fields[2], fields[3], fields[4], old[5], old[6])
            else:
                old = self.pico_monitor.item("latest", "values")
                row = (fields[0], "", "", "", "", old[5], old[6])
            self.pico_monitor.item("latest", values=row)
        else:
            old = self.pro_monitor.item("latest", "values")
            row = (fields[0], values.get("direction", ""), values.get("pulse_ms", ""), values.get("settle_ms", ""), old[4], values.get("fault_during_pulse", values.get("driver_fault", "")))
            self.pro_monitor.item("latest", values=row)

    def finished(self, code: int, output: str) -> None:
        self.run_button.configure(state="normal")
        self.status.set(output or ("Completed" if code == 0 else "Failed"))
        if code == 0:
            self.show_settling_reading(output)
        if code != 0: messagebox.showerror("Run failed", output or "Use the physical cutoff if the toolhead is not safe.")

    def show_settling_reading(self, output: str) -> None:
        try:
            run_dir = Path(output.strip().split("Completed:")[-1].strip())
            with (run_dir / "samples.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            analysis = analyze_settling(rows, int(self.pulse.get()))
            (run_dir / "settling_analysis.json").write_text(json.dumps(analysis, indent=2) + "\n", encoding="utf-8")
            cs = analysis["cs1238"]; ref = analysis["reference_adc"]
            def display(result: dict[str, object]) -> str:
                value = result["settle_ms"]
                return f"{value:.1f} ms" if isinstance(value, float) else str(result["status"])
            self.settle_reading.set(
                f"Measured settling — CS1238: {display(cs)}; reference ADC: {display(ref)}. "
                "Use the slower valid value when choosing Settle ms.")
            self.pico_monitor.item("latest", values=("SETTLED", "", "", "", "", display(cs), display(ref)))
            measurements = [value for value in (cs["settle_ms"], ref["settle_ms"])
                            if isinstance(value, float)]
            trace_settle = f"{max(measurements):.1f}" if measurements else "unavailable"
            old = self.pro_monitor.item("latest", "values")
            self.pro_monitor.item("latest", values=(old[0], old[1], old[2], old[3], trace_settle, old[5]))
        except (OSError, ValueError, KeyError, IndexError) as error:
            self.settle_reading.set(f"Measured settling unavailable: {error}")

    def auto_calibrate(self) -> None:
        try:
            steps = int(self.auto_steps.get())
            slope, offset, limit = float(self.reference_slope.get()), float(self.reference_offset.get()), float(self.force_limit.get())
            pulse, settle = int(self.pulse.get()), int(self.settle.get())
            pico, toolhead = self.port(self.pico.get()), self.port(self.toolhead.get())
            if not 1 <= steps <= 10 or not 10 <= pulse <= 100 or not 0 <= settle <= 10000 or not pico or not toolhead or pico == toolhead or limit <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Auto-Calibrate settings", "Choose two COM ports, 1–10 steps, valid pulse/settle values, and a calibrated reference slope, offset, and positive force limit.")
            return
        warning = ("This executes %d DOWN pulses followed by %d UP pulses. It stops on a run failure or measured reference-force limit.\n\n"
                   "Confirm the reference sensor is calibrated, travel is clear, and the physical 6 V cutoff is reachable.") % (steps, steps)
        if not messagebox.askyesno("Confirm Auto-Calibrate", warning): return
        self.run_button.configure(state="disabled"); self.auto_button.configure(state="disabled")
        self.status.set("Auto-Calibrate running. Keep the hardware cutoff reachable.")
        threading.Thread(target=self.auto_worker, args=(pico, toolhead, steps, pulse, settle, slope, offset, limit), daemon=True).start()

    def auto_worker(self, pico: str, toolhead: str, steps: int, pulse: int, settle: int, slope: float, offset: float, limit: float) -> None:
        results: list[dict[str, object]] = []
        raw_points: list[dict[str, object]] = []
        fit_points: list[dict[str, object]] = []
        error = ""
        for direction in ["down"] * steps + ["up"] * steps:
            command = [sys.executable, str(self.base / "run_force_calibration.py"), "--pico", pico, "--toolhead", toolhead, "--direction", direction, "--pulse-ms", str(pulse), "--settle-ms", str(settle), "--notes", "auto-calibrate"]
            result = subprocess.run(command, cwd=self.base, text=True, capture_output=True)
            if result.returncode:
                error = (result.stdout + result.stderr).strip() or "run failed"; break
            run_dir = Path(result.stdout.strip().split("Completed:")[-1].strip())
            with (run_dir / "samples.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            if not rows:
                error = "empty raw CSV"; break
            settling = analyze_settling(rows, pulse)
            cs_settle = settling["cs1238"]["settle_ms"]
            ref_settle = settling["reference_adc"]["settle_ms"]
            if not isinstance(cs_settle, float) or not isinstance(ref_settle, float):
                error = "one or both channels did not settle within capture; increase Capture ms and repeat"
                break
            fit_from_us = (LEAD_MS + pulse) * 1000 + int(max(cs_settle, ref_settle) * 1000)
            run_forces = []
            for row in rows:
                cs_raw = float(row["toolhead_cs1238_raw"])
                adc_raw = float(row["reference_adc_raw"])
                force_n = slope * adc_raw + offset
                point = {
                    "run_dir": str(run_dir), "direction": direction,
                    "toolhead_time_us": row["toolhead_time_us"],
                    "toolhead_cs1238_raw": cs_raw,
                    "reference_time_us": row["reference_time_us"],
                    "reference_adc_raw": adc_raw,
                    "reference_force_n": force_n,
                    "used_for_steady_fit": int(int(row["toolhead_time_us"]) >= fit_from_us and int(row["reference_time_us"]) >= fit_from_us),
                }
                raw_points.append(point)
                if point["used_for_steady_fit"]:
                    fit_points.append(point)
                run_forces.append(force_n)
            results.append({"run_dir": str(run_dir), "direction": direction,
                            "raw_samples": len(rows), "reference_force_min_n": min(run_forces),
                            "reference_force_max_n": max(run_forces), "settling": settling,
                            "steady_fit_start_us": fit_from_us})
            if max(abs(value) for value in run_forces) >= limit:
                error = f"reference-force limit reached: {max(run_forces, key=abs):.4g} N"; break
        parent = self.base / "data"
        parent.mkdir(exist_ok=True)
        result_dir = parent / ("auto_calibration_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
        result_dir.mkdir()
        summary = result_dir / "calibration_summary.json"
        proposal = {"reference_slope_n_per_count": slope, "reference_offset_n": offset, "force_limit_n": limit, "runs": results, "status": "failed" if error else "completed"}
        if not error and len(fit_points) >= 2:
            x = [float(r["toolhead_cs1238_raw"]) for r in fit_points]; y = [float(r["reference_force_n"]) for r in fit_points]
            try:
                fit, residuals = linear_fit(x, y)
            except ValueError as fit_error:
                error = str(fit_error); proposal["status"] = "failed"
            else:
                proposal.update({"analysis": "ordinary least-squares fit using only synchronized samples after both channels settled; every raw sample is retained separately",
                                 "raw_sample_count": len(raw_points), "steady_fit_sample_count": len(fit_points),
                                 "proposed_force_n_per_cs1238_count": fit["slope"], "proposed_force_offset_n": fit["offset"],
                                 "residual_rms_n": fit["rms"], "r_squared": fit["r_squared"]})
                for point, residual in zip(fit_points, residuals): point["fit_residual_n"] = residual
                self.write_calibration_figures(result_dir, raw_points, fit_points, fit)
        if raw_points:
            combined = result_dir / "combined_raw_samples.csv"
            with combined.open("w", newline="", encoding="utf-8") as stream:
                writer = csv.DictWriter(stream, fieldnames=list(raw_points[0].keys()))
                writer.writeheader(); writer.writerows(raw_points)
            proposal["combined_raw_analysis_csv"] = str(combined)
        summary.write_text(json.dumps(proposal, indent=2) + "\n", encoding="utf-8")
        message = ("Auto-Calibrate stopped: " + error if error else "Auto-Calibrate completed") + f"\nResults: {result_dir}"
        self.after(0, self.auto_finished, bool(error), message, result_dir, proposal)

    def write_calibration_figures(self, result_dir: Path, raw_points: list[dict[str, object]], fit_points: list[dict[str, object]], fit: dict[str, float]) -> None:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        figure, axis = plt.subplots(figsize=(9, 5), constrained_layout=True)
        for direction in ("down", "up"):
            points = [point for point in raw_points if point["direction"] == direction]
            if points:
                axis.plot([float(point["toolhead_time_us"])/1000 for point in points], [float(point["reference_force_n"]) for point in points], label=f"{direction} reference force")
                axis.plot([float(point["toolhead_time_us"])/1000 for point in points], [fit["slope"] * float(point["toolhead_cs1238_raw"]) + fit["offset"] for point in points], "--", label=f"{direction} CS1238 fitted force")
        axis.set(xlabel="Pico time since each capture began (ms)", ylabel="Force (N)", title="Raw force-response traces")
        axis.grid(True, alpha=0.3); axis.legend(); figure.savefig(result_dir / "time_traces.png", dpi=180); plt.close(figure)
        figure, axis = plt.subplots(figsize=(7, 5), constrained_layout=True)
        for direction in ("down", "up"):
            points = [point for point in fit_points if point["direction"] == direction]
            axis.scatter([point["toolhead_cs1238_raw"] for point in points], [point["reference_force_n"] for point in points], s=10, alpha=.55, label=f"{direction}, settled")
        x = [float(point["toolhead_cs1238_raw"]) for point in fit_points]; low, high = min(x), max(x)
        axis.plot((low, high), (fit["slope"]*low+fit["offset"], fit["slope"]*high+fit["offset"]), color="black", label=f"OLS R²={fit['r_squared']:.5f}")
        axis.set(xlabel="CS1238 raw count", ylabel="Reference force (N)", title="Toolhead CS1238 transfer calibration")
        axis.grid(True, alpha=0.3); axis.legend(); figure.savefig(result_dir / "transfer_fit.png", dpi=180); plt.close(figure)
        figure, axis = plt.subplots(figsize=(7, 4.5), constrained_layout=True)
        residuals = [float(point.get("fit_residual_n", 0)) for point in fit_points]
        axis.scatter(x, residuals, s=10, alpha=.6); axis.axhline(0, color="black", linewidth=.8)
        axis.set(xlabel="CS1238 raw count", ylabel="Reference − fitted force (N)", title="Steady-sample fit residuals")
        axis.grid(True, alpha=0.3); figure.savefig(result_dir / "residuals.png", dpi=180); plt.close(figure)

    def auto_finished(self, failed: bool, message: str, result_dir: Path, proposal: dict[str, object]) -> None:
        self.run_button.configure(state="normal"); self.auto_button.configure(state="normal"); self.status.set(message)
        self.latest_result_dir = result_dir
        self.refresh_results_history()
        self.select_result()
        if failed: messagebox.showwarning("Auto-Calibrate stopped", message)

    def record_reference(self, mass_g: float | None) -> None:
        try:
            if mass_g is None: mass_g = float(self.known_mass_g.get())
            capture_ms = int(self.reference_capture_ms.get())
            pico, toolhead = self.port(self.pico.get()), self.port(self.toolhead.get())
            if mass_g < 0 or not 100 <= capture_ms <= 10000 or not pico or not toolhead or pico == toolhead: raise ValueError
        except ValueError:
            messagebox.showerror("Reference calibration", "Select both COM ports, enter a nonnegative known mass, and use a 100–10000 ms capture."); return
        self.reference_status.set("Recording reference sensor; do not touch the loading fixture.")
        command=[sys.executable,str(self.base/"run_force_calibration.py"),"--pico",pico,"--toolhead",toolhead,"--capture-ms",str(capture_ms),"--notes","reference calibration"]
        threading.Thread(target=self.reference_worker,args=(command,mass_g),daemon=True).start()

    def reference_worker(self, command: list[str], mass_g: float) -> None:
        result=subprocess.run(command,cwd=self.base,text=True,capture_output=True)
        if result.returncode: self.after(0,self.reference_failed,(result.stdout+result.stderr).strip()); return
        run_dir=Path(result.stdout.strip().split("Completed:")[-1].strip())
        with (run_dir/"samples.csv").open(newline="",encoding="utf-8") as stream: rows=list(csv.DictReader(stream))
        adc=sum(float(row["reference_adc_raw"]) for row in rows)/len(rows)
        self.reference_points.append((adc,mass_g))
        if len(self.reference_points)>=2:
            self.save_reference_store()
        self.after(0,self.reference_done,adc,mass_g)

    def reference_done(self, adc: float, mass_g: float) -> None:
        self.refresh_reference_table()
        suffix = " Reference force conversion and graph saved." if len(self.reference_points) >= 2 else " Record at least one more mass to create the conversion."
        self.reference_status.set(f"Recorded {mass_g:g} g at ADC {adc:.1f}. Points: {len(self.reference_points)}.{suffix}")

    def reference_failed(self, text: str) -> None:
        self.reference_status.set("Reference capture failed."); messagebox.showerror("Reference calibration", text or "Capture failed")


if __name__ == "__main__":
    CalibrationApp().mainloop()
