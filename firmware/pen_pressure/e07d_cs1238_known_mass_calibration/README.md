# E-07D Pro Micro-only known-mass calibration

This sensor-only sketch replaces the temporary Pico 2/INA101 dual-sensor
fixture. The Pro Micro is the sole ADC owner of the installed 300 g load cell:
`3V3/GND` to CS1238 `VCC/GND`, `GP0` to `DT/DRDY`, and `GP1` to `SCK`.

Keep the actuator 6 V rail disconnected. For the current practical fixture,
place known masses downward on the motor mount without side-loading or bending
the cell. The pen normally receives an upward paper reaction, so the Windows
application retains the measured downward-weight fit separately and produces a
clearly labelled approximate opposite-direction pen-force projection. This is
appropriate for the initial non-precision 40–60 g setup, but it is not proof
that the two mechanical load paths are identical.

For the recommended PC workflow, double-click
[`pc_logger/run_known_mass_calibration.bat`](pc_logger/run_known_mass_calibration.bat).
The separate Windows application connects to the **one** Pro Micro native-USB
COM port, retains every raw `SAMPLE,time_us,cs1238_raw` record, and writes a
timestamped result folder containing raw CSV files, per-capture summary CSV,
a raw-to-grams fit, and calibration/residual/raw-trace PNG graphs.

At each total mass (recommended 0, 5, 10, …, 70 g), enter the total mass,
wait for the fixture to stop moving, and click **Capture raw point**. Make at
least three increasing and three decreasing passes. The application uses the
final half of a capture only as a representative point for the proposed fit;
it never filters, averages over, or overwrites the raw CSV trace. Fit raw count
versus known mass only after reviewing raw noise and load/unload hysteresis.
Choose **Opposite: upward pen-tip reaction** unless a simple installed-pen
check proves the raw direction is the same. The resulting `calibration_summary`
retains both fits and the separate projection graph identifies the approximate
40–60 g upward-force raw window. The 40–60 g desired operating band is
0.392–0.588 N, but it is not a production force-control setting until this test
and later actuator response tests pass.

If a constant item was on the cell for every capture (for example, a 2.5 g pen
cap), it is physical fixture load. In the application use **Open saved run…**,
then **Add fixture mass to labels…** before fitting again: `0, 5, …` becomes
`2.5, 7.5, …`. The raw trace files remain untouched and
`mass_label_corrections.csv` records the adjustment. Do not subtract such a
fixture mass from the labels.

After fitting, **4. Pen-scale check** can directly verify the selected force
direction at the installed pen: select the saved `calibration_summary.json`,
put a kitchen scale under the pen, establish a steady reading near 50 g, and
capture a raw trace. This records only; it does not command the N20. It writes
`raw/pen_scale_check_*.csv` and `pen_scale_checks.csv` alongside that run.
