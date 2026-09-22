# Lab Note: 2026-09-22 - T-02 home-origin seek setup

## Objective

Record the initial full-retract-to-paper condition that exposed why the
integrated M3 short move was insufficient, and capture the user-observed
starting state before running the new supervised seek.

## Configuration

- Hardware revisions: SparkFun Pro Micro RP2350 toolhead; installed N20/DRV8833,
  CS1238 load cell, GP2 lift-home switch, installed pen.
- Wiring/pin map: integrated toolhead harness; GP2 is active-low at the switch.
- Firmware commit/build: prior checked-in `pro_micro_rp2350_toolhead` build;
  the new home-origin seek source had not been flashed at the time of the
  observation.
- grblHAL settings: not involved; service UART used.
- Converter settings/sample: not involved.
- Instruments: one-shot serial status snapshot; physical gap estimated by user.

## Code, commands, and configuration used

No motor command was issued in this setup observation. The user supplied the
following serial snapshot and estimated the tip-to-paper separation at about
12 mm:

```text
14:22:35.275 -> event=SNAPSHOT pressure=LIFTED cmd=M5 fault=none cs1238_raw=254197 cs1238_filtered=254761 cs1238_tare=279348 tare_valid=1 cs1238_delta=-24587 force_norm_raw=24587 hard_limit_raw=302326 lift_home=1 mag=DISARMED mT=[0.156,0.166,0.136] delta=0.036 mag_samples=109947 status=0x0000046f ready=[contact:0 clear:0 gp27:0] commission=[dir:1 pressure:1 lift:0 mag:0]
```

## Procedure

1. Read the current device snapshot over the Pro Micro service UART.
2. Report the approximate tip-to-paper gap at the full retract position.
3. Do not issue M3/e while determining whether the currently flashed firmware
   has enough travel to reach the paper.

## Results

- Snapshot reports `pressure=LIFTED`, `cmd=M5`, `fault=none`,
  `tare_valid=1`, and `lift_home=1`.
- The user estimates the pen is about 12 mm from paper while at GP2 full retract.
- No motor movement or contact attempt was reported in this observation.
- This is far beyond the previously staged 100 ms M3 move, which was based on
  the roughly 1.75 mm ordinary M5 clearance gap, not the cold-start distance.

### First bounded seek result

After flashing the first home-origin candidate, the user issued `e`. It ended
safely at its 160-pulse budget rather than contacting paper:

```text
15:00:00.789 -> event=FAULT_EVENT pressure=FAULT cmd=M3 fault=M3 home contact seek pulse budget exhausted cs1238_raw=169277 cs1238_filtered=169004 cs1238_tare=249630 tare_valid=1 cs1238_delta=-80626 force_norm_raw=80626 hard_limit_raw=302326 lift_home=0 home_seek_pulses=160/160 mag=DISARMED mT=[0.136,0.146,0.146] delta=0.020 mag_samples=40465 status=0x00000473 ready=[contact:0 clear:0 gp27:0] commission=[dir:1 pressure:1 lift:0 mag:0]
```

The pen was still physically about 4.5 mm above paper. The normalized force
was 80,626 raw, or approximately 16 g using the cap-free precision-weight
profile: below the 176,357 raw (35 g) contact threshold and far below the
302,326 raw (60 g) hard limit. This is a safe pulse-budget result, not a
contact-seek pass.

### Fast-seek contact result

The next 25 ms/50 ms candidate reached the intended contact threshold after
three completed pulses:

```text
STATE_EVENT pressure=HOME_SEEK_CONTACT cmd=M3 lift_home=1 tare_valid=1 force_norm_raw=38281
STATE_EVENT pressure=HOLD_FORCE cmd=M3 lift_home=1 tare_valid=1 force_norm_raw=177470
event=FAULT_EVENT pressure=FAULT cmd=M3 fault=hard force limit exceeded cs1238_raw=-53945 cs1238_filtered=-4204 cs1238_tare=301607 tare_valid=1 cs1238_delta=-305811 force_norm_raw=305811 hard_limit_raw=302326 lift_home=0 home_seek_pulses=3/80
```

The operator reported that the pen appeared to make contact and stop at the
desired physical force. The force state entered `HOLD_FORCE` at 177,470 raw,
just above the 176,357 raw (35 g) target. The next filtered value was 305,811
raw: only 3,485 raw, or about 0.7 g, above the 60 g hard limit. The controller
therefore faulted and stopped as designed. This is a contact pass with an
unacceptable transient hard-limit fault, not a qualified force-hold pass.

The run also exposed a tare-lifecycle defect. The earlier clear snapshot used
`cs1238_tare=249630`; the fast-seek fault contained `cs1238_tare=301607` and
started the seek at `force_norm_raw=38281` despite `lift_home=1`. The prior
firmware began the 64-sample tare before boot retraction completed, so a
startup contact/load transient could become the live zero reference.

## Difficulties and corrective actions

The implementation assumed M3 would normally begin after M5 from a small
clearance gap, but the device currently starts at GP2 full retract. The first
5 ms / 250 ms candidate was also much too slow and short for the measured
distance: 800 ms total drive time covered only about 7.5 mm. Revise only the
home-seek pacing to 25 ms pulses and 50 ms sensing settles, with 80 pulses and
an 8-second ceiling. That candidate then reached contact in three pulses but
overshot the hard limit by about 0.7 g after entering the target band. Revise
the home seek to use its 25 ms pulse only while force is below one-fifth of
the contact threshold, then use 5 ms pulses. The CS1238 35 g target, 60 g hard
limit, and post-contact force-control cadence do not change.

Move the automatic tare to the first confirmed GP2-home position after boot
and after `c` recovery. Reject M3 until that fresh clear-home tare is complete.

## Interpretation

The reported position explains why a fixed 100 ms M3 move can fail to reach
paper from this state. The first pulse-budget fault gives a direct installed
mechanism result: approximately 7.5 mm per 800 ms of full-drive seek motion.
The revised two-stage candidate retains fast empty travel but reduces the
final contact step to 5 ms. It has 100 pulses and an 8-second ceiling. It still
stops on the calibrated contact threshold, a GP2-stuck guard, budget, timeout,
sensor loss, or hard-force limit. A valid clear-home tare is now a prerequisite
to M3. The revised behavior must be checked on the real toolhead.

### Two-stage result and hold-loop correction

After the clear-home-tare update, the next T-02 attempt began correctly at
`force_norm_raw=-369`, released GP2, and entered `HOLD_FORCE` at `177,917 raw`
after 50 home-seek pulses, effectively the configured 35 g target. The later
filtered value reached `302,620 raw`, only 294 raw above the 60 g guard, and
correctly faulted. The operator reported physically appropriate paper contact
at the hold transition.

This isolated the remaining defect to `HOLD_FORCE`, not tare or home seeking:
the former proportional implementation could leave a motor PWM output applied
until the next 250 ms correction decision. Replace it with the validated 5 ms
full-drive pulse as the sole correction unit. Hold sleeps inside the 30–40 g
filtered band, relieves above-band force immediately with UP, and adds
below-band force no more often than every 250 ms. The 60 g guard is retained.
This new bounded hold behavior is source-compiled but remains unqualified until
the next supervised stationary T-02/T-03 attempt.

### Two-touch home approach

The first two-stage post-home attempt proves the current setup can traverse the
home-to-paper distance and reach an appropriate physical drawing force, but it
also shows that a single approach should not be asked both to find paper and
to land at drawing force. The revised source therefore uses two separate
touches: it first detects paper at approximately 5 g, retracts UP for a
bounded 10 ms, then makes a second all-5-ms-pulse approach to the lower 30 g
edge of the 30–40 g hold band. Surface finding and drawing preload are now
separate decisions with their own time/pulse bounds. This follows the intended
printer-style probe-then-approach workflow and is pending supervised hardware
verification.

### GP2-release tare correction

The first flashed two-touch attempt reported `lift_home=1` but began at
`force_norm_raw=59,561` (about 12 g), above the 5 g first-touch threshold. It
therefore immediately entered the back-off/tune stages and then exhausted the
30-pulse tune budget at 85,713 raw without reaching the 30 g threshold. This
shows GP2's pressed position changes the installed load-cell preload and is
not an acceptable tare location.

The controller now ignores force until GP2 first changes from `1` to `0` during
the M3 approach. It stops, waits one second, collects a 64-sample tare at that
released clear position, and only then begins the light 5 g surface touch.
This is the active candidate for the next supervised run.

### Fine-tune travel result

The first valid release-transition tare was `117 raw`, and the surface phase
identified approximately 5 g at `25,589 raw`, confirming both stages work.
After the 10 ms back-off, the original 30 fine 5 ms pulses reached only
`48,185 raw` (about 9.6 g) and safely exhausted its budget. The tune phase is
therefore extended to 100 unchanged 5 ms pulses with a 7-second bound. It does
not increase a single motion step, target force, or the 60 g hard limit.

### Trend-confirmed contact correction

The extended tune run reached `HOLD_FORCE` at `151,654 raw`, near the former
absolute 30 g lower band, while the pen remained physically about 0.5 mm above
paper. This proves that a raw threshold alone represents released-mechanism
preload/friction as well as paper reaction. The next candidate accepts first
touch only after a stopped pulse produces a persistent approximately 10,000 raw
(about 2 g) change from its pre-pulse value across three 25 ms-separated
filtered windows. That accepted response becomes the zero for subsequent
drawing-preload target and hard-force calculations. Single spikes or values
that relax before the three windows do not change state.

## Decisions and next action

Flash and supervise the updated integrated toolhead firmware. First verify a
one-shot `p` snapshot shows `pressure=LIFTED`, `lift_home=1`, and no fault;
`tare_valid=0` at hard home is expected. Then issue one `e` and observe the
GP2 release, `HOME_RELEASE_TARE_SETTLING`, and the later touch states. Keep the
physical power cutoff reachable, and do not clear any fault until its cause
and pen position are checked. See T-02 and T-01J in
[`../../testing/TEST_PLAN.md`](../../testing/TEST_PLAN.md).
