# Lab Note: 2026-09-13 - E-14C DRV8833 label-mapping correction

## Objective

Resolve the installed DRV8833 sleep/fault-label conflict without disassembling
or resoldering the toolhead, then prepare a guarded actuator retest.

## Configuration

- Hardware: installed ACEIRMC-style DRV8833 toolhead module and replacement
  1000 RPM N20.
- Wiring/pin map retained: GP4→IN1, GP5→IN2, GP6→EEP, ULT→GP7.
- Firmware to reflash: `e07b_hx711_actuator_steps` after this correction.
- Supply: 6 V toolhead rail; user observed 6 V at the driver.
- Instruments: Allosun multimeter and bench supply.

## Code, commands, and configuration used

```text
E07B prior service-UART commands: u, d, x, and a
Corrected electrical contract:
GP6 -> EEP / nSLEEP: HIGH enables; LOW sleeps
GP7 <- ULT / nFAULT: INPUT_PULLUP; LOW indicates fault
Pending safe logic-meter command after reflash: v
```

## Procedure

1. The owner confirmed the actual installed-module image: `SLEEP` is pin 1
   labelled `EEP`; `FAULT` is pin 6 labelled `ULT`.
2. Retained the existing GP6→EEP and ULT→GP7 wires.
3. Recorded the unsuccessful pre-correction E07B pulse observations and
   performed passive checks.
4. Corrected firmware mappings; powered retest is pending reflash.

## Results

- E07B reported valid HX711 telemetry and accepted actuator commands, but
  100 ms `u`/`d` pulses produced no observable N20 movement.
- Bench-supply display changed from about 0.024 A idle to 0.023 A during a
  pulse; that display is too slow to characterize a short pulse but did not
  show expected motor loading.
- The N20 ran when connected directly to 6 V. The driver rail measured 6 V.
- With power removed, OUT1-to-OUT2 measured about 31 ohm and continuity
  beeped. GP4→IN1, GP5→IN2, and GP7→ULT continuity were reported.
- The old firmware description was reversed relative to the owner-confirmed
  board labels. No E-14C pass is claimed until the corrected E07B build runs.
- After the corrected E07B reflash, non-motion `v` meter mode reported both
  stages and the owner measured GP4=3.3 V, GP5=0 V, and GP6/EEP=3.3 V, each
  relative to local DRV8833 ground. This passes the controller-side logic
  portion of E-14C; driver-output switching remains unverified.
- With both N20 leads disconnected, E07B `o` mode held each output polarity
  for 30 seconds. The owner reported all four expected readings: OUT1≈VM /
  OUT2≈0 V, then OUT1≈0 V / OUT2≈VM. The driver output stage passes.

## Difficulties and corrective actions

- The existing documentation said `ULT` was sleep and `EEP` was fault. The
  owner-confirmed board image showed the opposite.
- Moving wires was rejected to avoid unnecessary toolhead disassembly.
- Firmware was changed to treat GP6/EEP as sleep and GP7/ULT as fault. The
  next retest must use the reflashed E07B sketch.
- After the corrected E07B build still gave no audible motion from repeated
  100 ms UP pulses, a non-motion `v` meter mode was added. It holds GP4/GP5
  logic while asleep, then GP6/EEP enabled with both direction pins low.
- The isolated output test passed while the N20 previously ran direct from
  6 V. The remaining fault is therefore the physical N20 lead/OUT1/OUT2 path,
  which must be re-terminated or resoldered with power removed.

## Interpretation

The no-motion observation cannot yet qualify or reject the 1000 RPM motor.
The enable pin was driven on the wrong physical endpoint, so a corrected
driver-enable/fault mapping must be verified first.

## Decisions and next action

Temporarily isolate the motor from OUT1/OUT2, then measure a held driver-output
test. Do not hold a potentially stalled motor energized merely to accommodate a
slow multimeter. Related changes:
[`HW-20260913-001`](../../changes/hardware/2026/2026-09-13-correct-drv8833-sleep-fault-mapping.md).
and [`HW-20260913-002`](../../changes/hardware/2026/2026-09-13-add-nonmotion-drv8833-meter-mode.md).
With power removed, repair only the two N20 output connections, reconnect them,
and verify a single short `u` pulse before any automatic force test. The next
E07B build records ULT immediately after enable and during that short loaded
pulse, so retain the complete UART line.

Loaded repeat result: after the N20 was reconnected, a 100 ms UP pulse printed
`fault_during_drive=0 raw=1` and still produced no motion. Therefore ULT was
inactive throughout the actual command; E07B did not cancel the pulse and the
driver did not claim over-current/thermal protection. The next discriminator is
the supply/current capability required by the 1000 RPM motor, not another GPIO
or signal-wire change.

The 100 ms manual-pulse cap was then superseded for this replacement motor.
E07B now permits 100–1000 ms in 100 ms adjustments, while retaining a finite
one-second guard because LIFT_HOME remains report-only in this service sketch.

At the owner's request, a verbatim historical E-05 source copy from `03f6c00`
was prepared as an A/B reproduction. It must be treated as two automatic
500 ms motions, not as the guarded current E07B procedure.

To make that comparison controllable without changing the preserved source,
`e05_legacy_manual_steps` now uses the same historical roles with the 3.3 V
GP20/GP21 `Serial2` service adapter. It starts at 100 ms. Send `u` for the
historical first direction or `d` for reverse; send `]` before the next pulse
to increase by 100 ms, up to 1000 ms (`[` decreases). It never automatically
reverses. Clear travel in the selected direction remains mandatory because
LIFT_HOME is not used as a motion stop in this diagnostic. A movement result
still cannot prove GP7 is physical sleep: GP6 `INPUT_PULLUP` can itself leave
the confirmed EEP sleep input high.

## Final root cause and verified repair

The owner found a DRV8833 pin that was not soldered to the board. With power
removed, the joint was reflowed and inspected. No wire, connector, or GPIO
mapping was changed. After the repair, the corrected E07B sketch moved the
installed N20 in both `u` and `d` directions. This closes the loaded
OUT1/OUT2 delivery fault: the prior static-output test was a false assurance
because the bridge could present open-circuit voltage despite the defective
loaded output connection.

## Direction observation

With corrected E07B and the repaired output, the owner observed that the
then-current `u` command physically lowered the motor/carriage and `d` raised
it. E07B was corrected in code only: `u` now uses the observed lift polarity
and `d` the observed lower polarity. The motor wiring remains unchanged.

## Initial blunt-tool force response

With the blunt pen end on the paper-covered scale, two net 100 ms down pulses
produced 43.4 g at `hx_delta=-503592`. One 100 ms up pulse then reduced the
physical scale reading to 0.5 g at `hx_delta=-5984`. This proves the 1000 RPM
N20 can overcome the spring, lift the carriage, and release contact, but it
also proves 100 ms is too coarse for low-force control. E07B now defaults to
20 ms and provides 10 ms increments below 100 ms; its previous 100 ms
increments remain available for longer diagnostic travel.

### Controlled E07B response measurements

All values below used the blunt pen end on the paper-covered scale, with the
repaired DRV8833, corrected `u`/`d` command polarity, and E07B sleep after
every pulse. The physical scale is the force authority.

| Trial | Clear tare raw | Command sequence | Settled HX711 result | Scale result | Result |
|---|---:|---|---:|---:|---|
| 20 ms contact | 233439 | `d` once at 20 ms | `hx_raw=-116095`, `hx_delta=-349534` | 19.6 g | First controlled contact point. |
| 20 ms release | 233439 | `u` once at 20 ms | `hx_raw=225222`, `hx_delta=-8217` | 0.0 g | Released to clear. |
| 10 ms contact | 218958 | `d` twice at 10 ms | `hx_raw=-118526`, `hx_delta=-337484` | 22.8 g | First pulse may have taken up clearance; individual first-pulse force was not read. |
| 10 ms partial release | 218958 | `u` once at 10 ms | `hx_raw=167647`, `hx_delta=-51311` | 11.3 g | Reduced contact by 11.5 g without clearing. |
| 10 ms clear | 218958 | second `u` at 10 ms | `hx_raw=238037`, `hx_delta=19079` | 0.0 g | Released to clear. |
| 10 ms no-contact down | 232452 | `d` once at 10 ms | `hx_raw=-93219`, `hx_delta=-325671` | 0.0 g | Invalid force indication: no scale force despite large HX711 change. |
| 10 ms repeat down | -105646 | `d` once at 10 ms | `hx_raw=-201604`, `hx_delta=-95958` | 53.4 g | Large physical force with comparatively small HX711 delta. |
| 10 ms third down | 240356 | `d` once at 10 ms | `hx_raw=-123865`, `hx_delta=-364221` | 31.1 g | Down-force value differs substantially from preceding repeat. |
| 10 ms third clear | 240356 | `u` once at 10 ms | `hx_raw=222344`, `hx_delta=-18012` | 0.0 g | Released to clear. |
| Post-interference 10 ms down | 226681 | `d` once at 10 ms | `hx_raw=-16713`, `hx_delta=-243394` | 11.8 g | First post-observation verification point; release check pending. |
| Post-interference 10 ms clear | 226681 | `u` once at 10 ms | `hx_raw=232952`, `hx_delta=6271` | 0.0 g | Released to clear; HX711 returned near tare. |
| Post-interference repeat down | 227032 | `d` once at 10 ms | `hx_raw=-106343`, `hx_delta=-333375` | 27.8 g | Same nominal down pulse produced 16.0 g more than preceding cycle. |
| Post-interference repeat clear | 227032 | `u` once at 10 ms | `hx_raw=227674`, `hx_delta=642` | 0.0 g | Released to clear; HX711 returned near tare. |
| Settled-force stability | 53462 | `d` twice at 10 ms | `hx_delta=-186392`, `-185420`, `-184008` over 6 s | 31.5 g | Stable range 2384 counts while stationary. |

The two 10 ms lift pulses reduced 22.8 g to 11.3 g then clear. A subsequent
no-contact 10 ms down pulse produced a similar-magnitude negative HX711 delta
while the scale remained 0.0 g. Therefore the HX711 currently responds to
actuator/mechanical state or a motion-related artifact, not yet a validated
pen-force signal. No target force, pulse bound, or automatic approach is
approved. Pause contact-force mapping until this force-path discrepancy is
isolated. Two later nominally identical 10 ms down trials reached 53.4 g and
31.1 g with incompatible HX711 deltas; the following 10 ms up pulse cleared
31.1 g to 0.0 g. The safe release behavior does not make the down-force
response suitable for closed-loop control.

### Mechanical observation after variable-force trials

The owner observed that the leadscrew briefly hung up on the spring inside its
housing, then appeared to release. This is a plausible direct cause of the
large trial-to-trial force variation and HX711 state offsets: a snagged spring
or screw can store/release force suddenly and impose side load unrelated to
paper contact. The observation is not a repair verification. Pause powered
force trials until, with power removed, the screw-to-spring/housing clearance,
spring seating, centering, and full guarded travel are inspected for rubbing,
binding, or witness marks.

After the owner reported the observed screw/spring hang-up resolved, one
post-observation 10 ms down verification from a clear tare of 226681 reached
11.8 g at `hx_delta=-243394`. The matching 10 ms up pulse released to 0.0 g
and returned HX711 near tare (`hx_delta=6271`). One paired cycle does not prove
that the interference is eliminated or that the force/HX711 relationship is
repeatable. The next paired cycle reached 27.8 g from the same nominal 10 ms
down command, then cleared to 0.0 g at `hx_delta=642` with one 10 ms up
command. Release is repeatable, but down-force response remains variable.
Gearbox friction, backlash, and clearance take-up make that expected for an
open-loop pulse; it does not by itself prove an unresolved screw/spring fault.
The closed-loop controller must measure settled force after each bounded pulse,
use a deadband and dwell, and never assume a fixed grams-per-pulse value.

At a later stationary 31.5 g point reached after two 10 ms down pulses from a
clear tare of 53462, three HX711 samples over roughly six seconds spanned only
2384 counts (`-186392` through `-184008`). This supports using a settle dwell
and filtered feedback after a bounded pulse; it does not establish a transfer
curve or final force settings.

### Failed post-release zero-reference check

After the settled 31.5 g point was released and the physical scale read 0.0 g,
the immediate HX711 value was `hx_delta=166043`. With no actuator motion and
the scale remaining 0.0 g, three further samples over 16 seconds were
`168245`, `164697`, and `163794`. This is a persistent history-dependent
zero-force offset, not ordinary settling noise. Open-loop gearbox friction can
explain variable force from a pulse, but it cannot authorize using this
state-dependent HX711 value as an absolute force reference. Pause closed-loop
force implementation until the mechanical load-cell force path is isolated.

### Lubrication retest

The owner greased the moving toolhead mechanism before another guarded trial.
From tare raw 215937, one 10 ms down pulse reached 33.7 g. Three stationary
samples over about five seconds were `hx_delta=-323079`, `-322781`, and
`-322551`, a 528-count span. This is better stationary stability than the
earlier 31.5 g point, but it does not yet resolve the failed post-release
zero-reference condition. Release and zero-reference checks remain pending.

One 10 ms up pulse released the 33.7 g point. The scale read 0.4 g at
`hx_delta=-21011`, then 1.2 g at `hx_delta=-26409`; the intermediate sample
was `hx_delta=-22650`. Compared with the earlier persistent approximately
+166k zero-force offset, this is a substantial improvement after lubrication.
The low residual scale reading and small raw offset are not yet an approved
PEN_CLEAR threshold or a repeatability result.

A second 10 ms up pulse produced `hx_delta=10956` while the scale remained at
0.4 g. This does not justify continued retraction toward the unverified
mechanical endpoint solely to eliminate a sub-gram scale indication. Verify a
visible pen-to-paper gap and establish a bounded clearance reserve instead.

Physical clearance observation after the second bounded 10 ms up pulse: one
sheet of paper could just barely slide beneath the blunt pen end. This confirms
the pen was not pressing the scale, but it is only a minimal air gap and not a
qualified production `PEN_CLEAR` reserve. Bracket the gap with additional
sheets before choosing a clearance pulse.
