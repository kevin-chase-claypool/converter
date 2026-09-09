# Lab Note: 2026-09-08 - T-01G LIFT_HOME switch installation

## Objective

Install and safely expose the toolhead's fully-retracted-carriage reference
switch before any automatic retract behavior is enabled.

## Evidence

With power removed, the selected normally-open microswitch contact read open
(no continuity beep) when released and closed (continuity beep) when pressed.
The owner then installed the dry contact between the Pro Micro RP2350 `GP2`
pin and its adjacent local `TOOL_GND` pin.

## Firmware boundary

The integrated toolhead firmware configures GP2 as `INPUT_PULLUP` and reports
the active-low switch state as `lift_home` in both native-USB and GP20/GP21
service-UART telemetry. It does not yet use this input to start, stop, or
otherwise control the DRV8833/motor. This keeps the initial post-installation
check motor-safe.

## Unpowered input/UART result

The motor-safe UART1 diagnostic was flashed through USB-C/UF2. With the
toolhead powered from its known-good 5 V service supply and the FTDI adapter on
COM8 at 115200 baud, it repeatedly reported `T01G lift_home=0` released and
`T01G lift_home=1` while the microswitch was pressed, then returned to `0` on
release. This verifies the switch contact, GP2 active-low pull-up, GP20 UART1
TX path, local ground, adapter, and monitor configuration. It does not verify
motor direction, retract stopping, debounce under motion, or a mechanical
backstop.

## Remaining T-01G verification

The unpowered input test passed. Next, restore the integrated firmware, then
run ten guarded slow retract cycles and document repeatability, release
position, debounce behavior, and timeout/fault behavior. The switch is a
position reference, not a mechanical hard stop and not a spring-force sensor.

If the integrated sketch does not produce readable service telemetry, first
flash the motor-safe `t01g_lift_home_uart` sketch. It prints only
`T01G lift_home=0` or `T01G lift_home=1` through GP20/GP21 at 115200 baud,
making the switch/UART hardware path independently testable.

**Correction:** GP20/GP21 are hardware UART1 pins in Arduino-Pico. The first
diagnostic and integrated service implementation used `Serial1` (UART0), whose
pin assignment to GP20/GP21 is invalid and is silently refused by the core.
Both now use `Serial2` (UART1).

## Integrated-telemetry correction

The clean T-01G diagnostic output isolated a later integrated-sketch failure to
its UART telemetry writer rather than to the switch, Pro Micro, FTDI adapter,
or wiring. The integrated writer had required the entire formatted telemetry
record to fit in `Serial2.availableForWrite()` before issuing a write. A UART
FIFO may be smaller than that record, so that condition suppressed every line.
The writer now writes the valid completed record directly, and startup emits
`Theta toolhead service UART ready` before pressure and magnetic
initialization. This correction does not change motor behavior: actuator
commissioning remains locked and T-01G powered retract testing is still open.

## Integrated service-UART result

With the corrected integrated firmware flashed through USB-C/UF2, the same
externally powered FTDI COM8 monitor at 115200 reported `Theta toolhead service
UART ready` followed by recurring complete telemetry records. The reported
`pressure=FAULT` with `fault=T-01 actuator direction is not commissioned` is
the expected compile-time safety lock; it keeps the DRV8833 disabled. The
reported `lift_home=0` is the expected released-switch state. The separate
`mag=FAULT`, zero magnetic samples, and zero HX711 values are not UART failures
and remain sensor bring-up items outside this input/UART check.

## Integrated LIFT_HOME transition result

While the integrated firmware continued to report its intentional actuator
commissioning fault, manually pressing and releasing the installed switch
produced repeated `lift_home=0` released, `lift_home=1` pressed, and
`lift_home=0` released telemetry. This completes the input/UART portion of
T-01G end-to-end. It does not authorize powered retracts: the next T-01G scope
is separately guarded motor direction, slow travel, switch repeatability,
release position, and timeout/backstop evidence.
