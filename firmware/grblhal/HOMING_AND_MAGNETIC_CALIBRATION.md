# Homing and Magnetic Bed Calibration Plan

This plan is not yet verified on hardware. Keep all thresholds, offsets, pin
assignments, and grblHAL `$` settings as `TBD` until measured.

## Responsibility split

grblHAL on RP23CNC remains the motion controller. It homes and jogs X, Y, and A,
executes scan moves, enforces limits, and runs generated plot G-code. It should
see ordinary digital home/limit signals, not raw I2C magnetic data.

A separate RP2040 adapter reads the SparkFun TMAG5273 Qwiic 3D Hall sensor and
reports magnetic measurements to the host. The current adapter candidate is a
SparkFun Pro Micro RP2040 because it provides 3.3 V logic and onboard Qwiic. The
adapter is expected to assert a clean digital `A_HOME` signal to an RP23CNC
limit/home input for normal A homing after the signal conditioning, output
driver, and input polarity are verified.

The host PC coordinates setup and maintenance calibration scans by talking to
both devices:

```text
Host PC
  |-- Ethernet/Telnet/WebSocket or USB --> RP23CNC/grblHAL for X/Y/A motion
  |
  |-- USB serial -----------------------> RP2040 adapter for TMAG5273 readings
```

Use RP23CNC Ethernet after the W5500 bring-up is verified. Keep USB as the
initial recovery and baseline configuration path.

For a detailed normal-startup homing data-flow sheet, including the requirements for
ioSender, grblHAL, the RP2040/TMAG5273 adapter, and the toolhead controller,
see [`../../docs/homing_data_flow.html`](../../docs/homing_data_flow.html).

## Hardware concept

- X and Y use conventional physical home/limit switches wired to RP23CNC
  limit inputs.
- A/theta uses a cylindrical outer bed magnet as an angular index mark.
- A cylindrical center bed magnet provides the geometric bed-center reference.
- The TMAG5273 rides with the gantry/toolhead so the machine can scan over the
  magnets. Its Z height is fixed by the toolhead mount and heat-set inserts;
  calibration must treat that height as non-adjustable unless the mount is
  redesigned.
- The RP2040 adapter reads TMAG5273 `Bx`, `By`, and `Bz`, computes or reports
  field magnitude, exposes diagnostic readings over USB serial, and provides
  the validated switch-like `A_HOME` output used by grblHAL normal A homing.

The two embedded magnets are planned as:

| Magnet | Purpose | Nominal location |
|---|---|---|
| Center magnet | Calibrate actual bed center after X/Y homing | Bed rotation center |
| Outer magnet | Define A/theta angular index | About 8.9 in radially from the center magnet |

Do not use the center magnet as a theta reference. A magnet on the rotation
axis locates center but does not define angular phase.

## Startup and calibration sequence

The pen/toolhead must be up for every homing and magnetic-calibration move.
Before starting, command `M5`, wait for the configured lift dwell, and verify
that the pen is physically clear of the bed. Magnetic calibration uses the
TMAG5273 position, not pen contact.

Normal startup homing should be simple after setup constants are established:
ioSender sends `M5`, waits for the lift dwell, then sends `$H`; grblHAL homes
X/Y from physical switches and A from the RP2040-generated `A_HOME` input. The
steps below describe the setup/maintenance calibration path used to determine
bed center, magnetic thresholds, hysteresis, edge offsets, and repeatability.

1. Command tool lift/retract:

   ```text
   M5
   G4 P<TBD-lift-settle-seconds>
   ```

2. Home X and Y with grblHAL using physical limit switches while the pen remains
   retracted.
3. Move the TMAG5273 to the expected bed-center area.
4. Scan a bounded `4 in x 4 in` square around the expected center.
5. Find the center magnet's saturated or thresholded field footprint.
6. Compute the geometric center from opposing saturated edges:

   ```text
   center_x = (left_edge + right_edge) / 2
   center_y = (front_edge + back_edge) / 2
   ```

7. Move the sensor to the nominal outer radius from that measured center.
8. Rotate A slowly through two full bed revolutions so the outer magnet is
   observed twice from the same scan direction. With the current convention,
   one bed revolution is `4320` A motor degrees because the host applies the
   12:1 bed ratio, so the normal A-homing scan is `8640` A motor degrees. Record
   two valid saturated or thresholded angular entry/exit pairs:

   ```text
   center_1 = (theta_enter_1 + theta_exit_1) / 2
   center_2 = (theta_enter_2 + theta_exit_2) / 2
   theta_center = (center_1 + center_2) / 2
   ```

   The two centers must agree within a measured tolerance before the result is
   accepted. This improves repeatability checking and can reduce random edge
   noise; it does not compensate for a biased threshold, incorrect magnet
   geometry, or backlash from inconsistent approach direction.

9. At `theta_center`, jog radially across the outer magnet and compute:

   ```text
   radius_center = (radius_inner_edge + radius_outer_edge) / 2
   ```

10. Repeat the angular scan at the measured `radius_center` if more precision is
   needed.
11. Use the final angular center as the A/theta index reference.

## Saturated-field handling

For these cylindrical magnets, saturation is acceptable if the scan captures a
repeatable geometric footprint with visible edges. The calibration routine
should find the center of the saturated or thresholded blob, not the maximum
field value.

Minimum requirements for repeatability:

- Sensor height is fixed by the toolhead mount and must remain unchanged during
  all calibration scans.
- The scan plane is parallel to the bed.
- The saturated footprint does not fill the entire search window.
- Each edge is approached consistently to reduce backlash error.
- Multiple TMAG5273 samples are averaged at each scan point.
- Nearby ferromagnetic parts are checked for field distortion before relying on
  the result.

If saturation fills the search window or produces inconsistent edges, do not
assume Z-height adjustment is available. Instead, widen the scan window, reduce
threshold sensitivity, reduce magnet strength, change magnet size/shape/depth,
or redesign the fixed sensor mount before recording calibration constants.

## grblHAL integration

For first bring-up, do not write a custom grblHAL plugin for the TMAG5273. Use
standard grblHAL motion and limit/home behavior:

- grblHAL homes X/Y from the physical limit switches.
- grblHAL homes A from the RP2040 adapter's validated switch-like `A_HOME`
  input during normal startup homing.
- grblHAL moves the machine through scan coordinates sent by a host calibration
  script after `M5` has lifted the pen/toolhead during setup or maintenance
  calibration.
- The RP2040/TMAG5273 adapter provides diagnostic readings to the host script
  and the digital `A_HOME` edge to grblHAL once the electrical interface is
  verified.
- Any inconsistent edge pair, missing edge, sensor fault, grblHAL alarm, or
  unknown toolhead-lift state must abort the current attempt, stop motion or
  enter alarm/hold, keep the pen lifted, preserve diagnostics, and require
  explicit user inspection before retrying.

Custom grblHAL code is justified only after the host-coordinated calibration
proves a specific limitation that cannot be handled by settings, sender macros,
or the RP2040 adapter.

## Open verification items

- Exact fixed TMAG5273 mounting height and orientation.
- Magnet diameter, grade, polarity, and installed depth.
- Confirmed 8.9 in outer-magnet radius after measurement.
- Final RP2040 adapter board selection and output-driver circuit.
- RP23CNC input terminal, polarity, voltage/current requirement, and isolation
  behavior for the adapter's digital `A_HOME` signal.
- Scan step sizes, averaging count, thresholds, and acceptable repeatability.
- Final sender macro or procedure for `M5`, lift dwell, `$H`, status check, and
  abort recovery.
