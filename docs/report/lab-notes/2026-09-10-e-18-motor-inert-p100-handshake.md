# Lab Note: 2026-09-10 - E-18 / F-08 staged motor-inert P100 handshake

## Objective

Exercise the installed RP23CNC `Aux0` to Pro Micro `GP28` two-phase arm path
and the local TMAG5273 magnetic threshold state without using any actuator pin
or machine motion. Observe the U3 `A_HOME` sink at its temporary `LIMA` endpoint
where physically accessible.

## Configuration

- Toolhead controller: SparkFun Pro Micro RP2350; service UART on COM8 at
  115200 baud.
- Toolhead: pen removed; normal 6 V toolhead supply; USB-C disconnected after
  upload; no motor command issued by the diagnostic.
- Controller path: yellow `ENA`, green `AUX0`, and blue `A_HOME` routed to the
  RP23CNC; during this session blue `A_HOME` was connected to `LIMA SIG`.
- Magnetic sensor: installed TMAG5273, initially held away from the bed
  magnets for its baseline.
- Instrument: digital multimeter. Controller-side reference was J1.5
  `CTRL_GND`.
- Controller motion: no `$H`, `G38`, P100 macro, or axis-movement command was
  used.

## Code, commands, and configuration used

```text
Source: firmware/pen_pressure/p100_handshake_test/p100_handshake_test.ino
Source SHA-256: D925AD897C498C646D85F21EB9BFDB0C2270E5AB6D668E7E5CDFD034A714AC74
Repository commit before bench run: b3812f8acd3875d7462c022f2513fd32456391fe

M64 P0
M65 P0
M64 P0
M65 P0
```

The first `M64 P0` requested readiness, `M65 P0` released it, and the second
`M64 P0` was issued within the diagnostic's three-second re-arm window. The
final `M65 P0` disarmed it.

## Procedure

1. Flashed the motor-inert handshake diagnostic and confirmed a far-field
   `baseline=1`, `detected=0`, and `DISARMED` state on COM8.
2. Measured J1.4 `AUX0` relative to J1.5 `CTRL_GND` while issuing `M65 P0`,
   `M64 P0`, then `M65 P0`.
3. Issued the first arm/release cycle and recorded the service-UART state
   transitions.
4. Connected blue J1.6 `A_HOME` to RP23CNC `LIMA SIG`; during `READY_ACK`,
   measured J1.6 relative to J1.5.
5. Issued the re-arm sequence, entered `SCAN_ACTIVE`, and brought the center
   magnet near then away from the TMAG sensor.
6. Issued the final `M65 P0` and confirmed return through `WAIT_REARM` to
   `DISARMED`.

## Results

- Controller `AUX0` was 9.33 V released and 0.15 mV asserted relative to
  `CTRL_GND`.
- The installed command/input path repeatedly produced:

  ```text
  DISARMED baseline=1 detected=0 arm=0
  READY_ACK baseline=1 detected=0 arm=1
  WAIT_REARM baseline=1 detected=0 arm=0
  SCAN_ACTIVE baseline=1 detected=0 arm=1
  ```

- In `SCAN_ACTIVE`, bringing the center magnet near changed `detected` from
  `0` to `1`; moving it away returned `detected` to `0`.
- During `READY_ACK`, J1.6 `A_HOME` measured 0 V relative to J1.5
  `CTRL_GND`, demonstrating that GP27/U3 sank the temporary LIMA return.
- Final `M65 P0` showed `WAIT_REARM` and then `DISARMED`; no motor or axis
  movement was observed or commanded.

## Difficulties and corrective actions

- An early GP28 voltage observation appeared inverted while the perfboard was
  disconnected for inspection. Power-off continuity checks confirmed the
  v2-minwire U2 nets and D2 orientation. After reassembly, the expected
  active-low command behavior and all diagnostic transitions passed. No
  firmware polarity was changed; the exact cause of the earlier observation is
  not established.
- The installed perfboard does not provide practical meter clips, and the
  ioSender verbose console did not expose a real-time `Pn:`/`LIMA` input state.
  Therefore the controller's interpretation of the U3 sink and the released
  LIMA voltage were not observed.

## Interpretation

This passes the motor-inert installed path from RP23CNC `M64`/`M65` through
`AUX0`, U2, GP28, and the diagnostic's two-phase state machine. It also passes
the local TMAG scan-state response and proves U3 can sink the connected
`A_HOME`/LIMA conductor during readiness. It does not prove that RP23CNC reads
that LIMA state, does not establish PRB polarity or G38 capture, and does not
authorize P100 motion modes or production firmware.

## Decisions and next action

Keep the blue return at `LIMA`; do not reterminate it to `PRB`. Run the direct
motorless PRB/G38 stage of F-08 next, then repeat it through GP27/U3 with a
controller-visible probe input. See [the test plan](../../testing/TEST_PLAN.md),
[the wiring table](../../hardware/WIRING_TABLE.md), and
[RPSW-20260910-001](../../changes/rp23cnc-software/2026/2026-09-10-record-motor-inert-p100-handshake.md).

## Addendum: F-08 PRB/G38 completion stage

The earlier stage was superseded by a controller-visible follow-up on the same
date. With power off, the blue J1.6 `A_HOME` conductor was moved from `LIMA
SIG` to `PROBE SIG`; `LIMA GND` and `PROBE GND` were meter-confirmed common, so
J1.5 `CTRL_GND` remained unchanged. This is the installed endpoint now.

The candidate grblHAL build enabled `PRB`; its installed report included
`[SIGNALS:HSEP]`, `EXPR`, `PRB` on pin 7, and `Aux out 0,P0` on pin 36. The
candidate artifact was 889,856 bytes with SHA-256
`892799841E6262556D380594CF909FE8A40284BC6FA52E798102BFEC36276DC9`.

The three TB6600 branch fuses were removed. This left drivers/motors without
power while G38 updated only controller coordinates; it did not authorize or
produce physical axis movement. Direct `PRB SIG`/`GND` dry-contact checks
established `$6=1`: open was `P` blank and closed was `P` red. Direct X and A
`G38.3`/`G38.5` captures each returned `[PRB:...:1]`.

The actual toolhead path then passed as follows:

- On this installed active-low Aux0 interface, `M65 P0` requests `READY_ACK`
  and makes `P` red; `M64 P0` produces `WAIT_REARM` and makes `P` blank.
- `M65 P0` -> `M64 P0` -> `M65 P0`, with the second arm inside three seconds,
  entered `SCAN_ACTIVE`. The center magnet produced `detected=0 -> 1 -> 0`
  and `P` blank -> red -> blank in sync.
- With `$20=0`, `G21`, and `G91`, the real-magnet A entry test
  `G38.3 A30 F60` returned `[PRB:0.000,0.000,0.000,11.475:1]`.
- The real-magnet release test `G38.5 A30 F60` returned
  `[PRB:0.000,0.000,0.000,13.275:1]`.

One first A probe attempt returned `:0` because the diagnostic had exceeded
its five-minute `SCAN_ACTIVE` timeout and deliberately entered `FAULT`.
Lowering Aux0 reset it to `DISARMED`, it reacquired a far-field baseline, and
the repeated entry/release tests passed. At completion, `M64 P0`, `$20=1`,
`G90`, and an ioSender reset restored `DISARMED`, `P` blank, soft limits, and
absolute distance mode. The three TB6600 fuses remain out.

This closes the direct and actual GP27/U3 PRB transition stages of F-08, but
not filesystem `G65 P100 Q1`, `#5064`, G53/G54/G10 semantics, the 20 ms
normal-status interval, or any Q3/Q4/production motion authorization.
