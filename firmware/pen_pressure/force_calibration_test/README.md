# Supervised force-calibration test package

This is the one package for the installed toolhead-load-cell calibration test.
It is separate from production force-control firmware.

```text
Pro Micro GP0 --(3.3 V DAQ gate)--> Pico 2 GP15
Pro Micro TOOL_GND ----------------> Pico 2 GND

Toolhead bridge -> CS1238 #1 -> Pico 2 GP2/GP3
Reference INA101 OUT -------------> Pico 2 GP26/ADC0
Pico USB --------------------------> PC raw-data logger
Pro Micro UART1 via USB-to-TTL ----> PC test command logger
```

## Contents

| Folder | Board / host | Purpose |
|---|---|---|
| [`pico2_daq/`](pico2_daq/) | Raspberry Pi Pico 2 | Arduino-Pico sketch for raw CS1238 + ADC0 acquisition over USB CDC. |
| [`pro_micro_actuator/`](pro_micro_actuator/) | SparkFun Pro Micro RP2350 | Arduino-Pico sketch for one bounded actuator pulse and GP0 capture gate. |
| [`pc_logger/`](pc_logger/) | Windows PC | Python logger and double-clickable batch launcher. |

## Guided app workflow

1. Complete the power-off wiring and INA101 output-span checks in
   [`docs/hardware/PICO2_DUAL_SENSOR_DAQ.md`](../../../docs/hardware/PICO2_DUAL_SENSOR_DAQ.md).
   Do not connect ADC0 until INA101 `OUT` has been measured within 0-3.3 V.
2. Flash `pico2_daq` as `PICO_BOARD=pico2`. Flash the Pro Micro fixture sketch
   only after its CS1238/HX711 bridge wires are disconnected; GP0 is temporary
   DAQ-gate output and GP1 is unused.
3. Wire only `GP0 -> GP15` and `TOOL_GND -> Pico GND` between boards. No GP1
   or Pico GP14 wire is used.
4. Connect both PC COM ports and double-click
   [`run_force_calibration.bat`](pc_logger/run_force_calibration.bat).
5. In **Reference Calibration**, record an unloaded zero and several known
   masses. The app retains each raw capture, saves `reference_calibration.csv`
   and `.json`, and produces `reference_calibration.png`. Its saved conversion
   maps raw reference ADC counts into force.
6. Use **Pulse Test** for one conservative trial. Its live tables show the raw
   CS1238/reference readings, command state, and post-run settling estimate.
   Increase capture duration when either channel reports it did not settle.
7. In **Toolhead Calibration**, run **Auto Calibrate** only after the reference
   fit is available and an appropriate force-stop limit is set. It retains all
   samples but uses only samples after both channels settled for its transfer
   fit. The **Results** tab retains a selectable history of every timestamped
   session, each with its own folder, time-trace overlay,
   CS1238-to-reference transfer graph, and residual plot.

GP0 defaults HIGH on reset and after every outcome. Pico GP15 treats HIGH as
stopped and LOW as logging. The Pro Micro asserts LOW, waits 100 ms before
motion, performs the one requested 10-100 ms pulse, preserves the requested
0-10,000 ms settle interval, then sleeps the driver and returns HIGH.

This fixture does not replace the physical toolhead 6 V cutoff or E-stop.
Never leave a powered test unattended; use the smallest pulse first.
