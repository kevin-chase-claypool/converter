# E-07D Pro Micro-only known-mass calibration

This sensor-only sketch replaces the temporary Pico 2/INA101 dual-sensor
fixture. The Pro Micro is the sole ADC owner of the installed 300 g load cell:
`3V3/GND` to CS1238 `VCC/GND`, `GP0` to `DT/DRDY`, and `GP1` to `SCK`.

Keep the actuator 6 V rail disconnected. Place known masses through the same
vertical force path used by the pen; do not side-load or bend the cell.

At each total mass (recommended 0, 5, 10, …, 70 g), issue `CAPTURE 1000` and
save every `SAMPLE,time_us,cs1238_raw` line. Make at least three increasing and
three decreasing passes. Fit raw count versus known mass only after reviewing
the raw noise and load/unload hysteresis. The 40–60 g desired operating band is
0.392–0.588 N, but it is not a production force-control setting until this test
and the later actuator response tests pass.
