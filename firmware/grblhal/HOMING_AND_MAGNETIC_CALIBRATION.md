# Homing and Magnetic Registration

This is the implemented, commissioning-gated design. Source code exists, but
the magnetic motion modes remain locked until the named electrical and motion
tests provide measured constants. Do not set either commissioning lock to true
merely to make the macro run.

## Ownership and references

- RP23CNC/grblHAL owns X/Y/A motion, physical X/Y homing, probe-coordinate
  capture, centroid arithmetic, work-coordinate registration, and aborts.
- The toolhead SparkFun Pro Micro RP2350 owns pen lift/pressure control and the
  TMAG5273. There is no separate RP2040 adapter.
- X/Y limit switches establish machine coordinates only. The center magnet
  establishes the bed's actual G54 X0/Y0 after physical homing.
- The outer magnet establishes G54 A0. A commands remain motor-shaft degrees;
  one bed revolution is 4320 A degrees with the 12:1 drive.

The controller macro is [`macros/P100.macro`](macros/P100.macro). It is invoked
from ioSender with `G65 P100 Q<mode>` after the file is copied to the RP23CNC
filesystem and the candidate build passes F-08.

| Mode | Purpose | Current availability |
|---:|---|---|
| `Q0` | Full startup: lift, X/Y home, center raster, A index, return to G54 zero | Locked until commissioning |
| `Q1` | Toolhead readiness handshake only | Source ready; requires commissioned toolhead firmware and E-18 |
| `Q2` | Physical X/Y `$H` only | Candidate for parser/motorless testing; homing configuration must omit A/Z |
| `Q3` | Center raster and G54 X/Y registration | Locked until commissioning |
| `Q4` | Outer-magnet A scan and G54 A registration | Locked until commissioning |

The eventual single ioSender button sends `G65 P100 Q0`. Separate modes exist
so each stage can be commissioned without bypassing the others.

### Planned interchangeable-tool preflight

Before a tool change can be considered automatically safe, the P100 `Q0`
sequence needs a commissioning-gated toolhead preflight: `LIFT_HOME`, a
RAM-only no-contact load-cell baseline, limited-force seek to the actual paper,
normal M5 `PEN_CLEAR`, and stable clear-band verification. This is deliberately
not implemented in the present macro: the existing M3/M5 signal plus fixed
dwell does not yet provide an acknowledgement that lets grblHAL safely wait
for the local force result. Until that interface is implemented and T-01J
passes, the operator must run the equivalent guarded tool check and must not
assume a shared pen-tip height.

## Intended P100 Q0 data movement

This is the target commissioning-gated order. It records which controller owns
each decision and which existing signal carries the result. The present macro
does not yet implement the GP2-verified home wait or the per-run touch check.
The interactive companion is [`../../docs/p100-data-movement.html`](../../docs/p100-data-movement.html).

### 1. Start command: host to motion controller

```text
ioSender -- G65 P100 Q0 --> RP23CNC/grblHAL
```

P100 begins locally on RP23CNC. Pen-force samples do not travel to the host.

### 2. Toolhead home: motion controller and Pro Micro

```text
RP23CNC GP28 -- home/ready request --> Pro Micro
Pro Micro GP2 <-- upper LIFT_HOME switch
Pro Micro GP27 -- LIFT_HOME verified --> RP23CNC
```

P100 first requests a safe M5 state and then requests the toolhead-ready
phase. The Pro Micro owns N20 motion, waits for GP2 (including the guarded
release/retrigger branch if already pressed), captures its RAM-only no-contact
baseline, and asserts GP27 only after successful `LIFT_HOME`. P100 waits for
that reply with a timeout; it does not substitute a fixed dwell for the switch
result.

### 3. Machine home: RP23CNC only

```text
RP23CNC -- $H --> X/Y motors and X/Y physical switches
```

The grblHAL homing cycle establishes gantry coordinates. The Pro Micro does
not participate in X/Y homing.

### 4. Magnetic registration: motion controller and Pro Micro

```text
RP23CNC GP28 -- magnetic-scan request --> Pro Micro
TMAG5273 ------ magnetic field samples --> Pro Micro
Pro Micro GP27 -- magnetic active/inactive --> RP23CNC
```

The second GP28 phase changes GP27 from the home-ready reply into the one-bit
magnetic state. RP23CNC performs the center raster and outer-A scans, captures
their edge coordinates, validates the geometry, and sets G54 `X0 Y0 A0`.

### 5. Per-run pen touch check: motion controller and Pro Micro

```text
RP23CNC M3 -- GP29 --> Pro Micro       request guarded contact seek
HX711/load cell --------> Pro Micro    contact/release force samples
RP23CNC M5 -- GP29 --> Pro Micro       request normal PEN_CLEAR
```

For every P100 run, the Pro Micro will seek the current paper at limited force,
reject overforce or missing contact, then run normal M5 release plus the
clearance pulse. The toolhead must return a pass/fail result through the
existing GP28/GP27 request/reply path before P100 proceeds. The exact third
request/reply phase is TBD; it is a protocol definition, not a new wire or
RP23CNC pin.

### 6. Ready state

```text
P100 --> G54 X0 Y0 A0
toolhead --> PEN_CLEAR
RP23CNC --> ready to stream drawing G-code
```

Any missing home-ready acknowledgement, failed touch check, force fault,
magnetic-handshake failure, invalid magnetic footprint, or invalid A spacing
aborts P100 and leaves plotting disabled.

## Existing three-signal interface

No additional moving-harness conductor is required.

| Controller path | Pro Micro pin | Meaning during this sequence |
|---|---:|---|
| Spindle ENA through U1 | GP29 | `M5` requests lift; `M3` is forbidden during a magnetic scan |
| Aux0 through U2 | GP28 | Two-phase magnetic arm/readiness command |
| GP27 through U3 to candidate `PRB` | GP27 | Readiness acknowledgement first, then thresholded magnetic state |

The two-phase handshake prevents the first threshold crossing from being
mistaken for a computed center:

1. RP23CNC issues `M64 P0` while the toolhead is safe and lifted.
2. GP27 asserts only as a readiness acknowledgement.
3. RP23CNC verifies it, issues `M65 P0`, and verifies GP27 releases.
4. RP23CNC issues `M64 P0` a second time. GP27 now represents only the
   thresholded TMAG footprint during G38 moves.
5. RP23CNC issues `M65 P0` on success or any handled abort.

The current physical endpoint remains `LIMA` until F-08 passes. Moving the
existing GP27/U3 return to `PRB` is a controller-end retermination, not a new
drag-chain wire.

## Toolhead dual-core behavior

The integrated Arduino-Pico firmware uses the RP2350's two cores:

| Core | Responsibility |
|---|---|
| Core 0 | GP29 command, HX711 acquisition, lift/seek/force states, DRV8833 control, faults, USB diagnostics, and watchdog feed |
| Core 1 | TMAG5273 sampling, baseline and hysteresis, GP28 handshake, GP27 output, and magnetic timeout |

Shared status is fixed-size atomic data. During magnetic readiness and scan,
Core 0 requires a verified lifted state and powers down/suspends the HX711;
pen-pressure measurement is unnecessary while the pen is up. Core 0 feeds the
hardware watchdog only while Core 1's heartbeat is fresh. A reset, stale core,
sensor failure, unsafe pressure state, M3 request during scan, or timeout
suppresses GP27 and leaves the actuator in its safe path.

The compile-time gates in
[`../pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h`](../pen_pressure/pro_micro_rp2350_toolhead/toolhead_config.h)
remain false until T-01/T-02, E-07/E-08, and E-18/M-08 establish installed
direction, lift reference, force values, and magnetic thresholds.

## Center raster and centroid

After physical X/Y homing, P100 scans equal-pitch X chords in a bounded
serpentine raster. Each row records an inactive-to-active entry with `G38.3`
and an active-to-inactive exit with `G38.5`. The footprint width and midpoint
are:

```text
width_i = abs(exit_i - entry_i)
mid_x_i = (entry_i + exit_i) / 2
```

For equal Y pitch, the area-centroid approximation is:

```text
Xc = sum(mid_x_i * width_i) / sum(width_i)
Yc = sum(row_y_i * width_i) / sum(width_i)
```

The macro rejects too few hit rows, zero area, implausible chord widths,
multiple chords on one row, missing releases, and a centroid outside the scan
bounds. It then performs the deliberately named **Centroid Approach and
Registration Pass**: approach from a fixed direction, move slowly to the
computed centroid, and set G54 X0/Y0 with `G10 L20`.

### Mandatory TMAG-to-pen XY compensation

The TMAG sensing point and pen tip are not coincident. Before Q0 or Q3 can run,
P100 requires a separate `sensor_to_pen_offset_valid` gate in addition to the
general commissioning gate. Record the installed vector in the macro as:

```text
sensor_to_pen_x = pen_X - TMAG_X
sensor_to_pen_y = pen_Y - TMAG_Y
```

At the TMAG centroid P100 assigns those values to the current G54 coordinate.
Its later `G54 G0 X0 Y0` move therefore brings the **pen**, not the TMAG, to bed
center. This correction belongs in P100; do not apply it again in the converter.

This is why GP27 never claims that one threshold edge is the center. It carries
only a one-bit sensor state; grblHAL records all coordinates and computes the
centroid after the full raster.

## Outer-magnet registration

At the commissioned outer radius, P100 rotates A in one direction and records
two entry/exit pairs. It validates each footprint width and requires the two
centers to be separated by approximately 4320 A motor degrees. It averages the
equivalent index observations, approaches from the same direction, and sets
G54 A0 with `G10 L20`.

The center raster must run before the A scan because the sensor is positioned
at the outer radius relative to the newly registered bed center.

## Required controller candidate

The unchanged baseline build has probe support disabled. The candidate recipe
[`config/homing-candidate.md`](config/homing-candidate.md) enables probe support,
NGC parameters, and expressions. It does not certify this use case and no
candidate UF2 has been flashed.

F-08 must prove, on the exact build:

- `PRB` idle/asserted polarity and reporting;
- `G38.3` entry and `G38.5` release capture on X;
- the probe parameter/coordinate values used by the macro;
- filesystem `G65 P100` execution and `$H` behavior inside the macro;
- A-axis G38 acceptance and `#5064` reporting;
- G53/G54 and `G10 L20` semantics for XYZA;
- safe handling of a probe state that remains active between entry and exit.

Run the direct-input motorless stage first, then the GP27/U3 isolated path.
Only after both pass may the existing return be reterminated from `LIMA` to
`PRB` and documented as installed wiring.

## Commissioning sequence

1. Complete toolhead direction, lift, HX711, and magnetic calibration tests.
2. Complete F-08 with TB6600 signal leads and motors disconnected.
3. Build and archive the accepted candidate; do not overwrite the known-good
   baseline UF2.
4. Prove `Q1`, then `Q2`, then bounded low-speed `Q3`, then `Q4`.
5. Install measured scan bounds, pitch, feeds, threshold, hysteresis,
   **sensor-to-pen XY offset**, outer radius, tolerances, and timeouts with
   dated evidence.
6. Set both firmware and macro commissioning gates only after their respective
   acceptance tests pass.
7. Run `Q0` repeatedly without a pen before creating the ioSender button.

Any missing edge, extra footprint, spacing error, sensor fault, unsafe lift
state, grblHAL alarm, or timeout invalidates that run. Keep the pen lifted,
preserve the diagnostic output, and require operator inspection before retry.
