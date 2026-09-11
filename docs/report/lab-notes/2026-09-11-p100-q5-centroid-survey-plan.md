# Lab Note: 2026-09-11 - P100 Q5 Automatic Centroid Survey Plan

## Objective

Run the first automatic center-magnet raster only within the measured 100 mm
square, then stop at the calculated TMAG centroid without changing G54 or A.

## Preconditions

- P111 X/Y homing has passed immediately before Q5.
- Candidate G53 rectangle: X `-280..-180`, Y `-266..-166`.
- Active Q5 pitch/feed: 5 mm / requested 2000 mm/min. The 100 mm square now
  has 21 rows; this doubles the requested line speed and sample density while
  retaining approximately the former total crossing time.
- X/Y travel is clear and the operator watches the motion.

## Result

Q5 entered the P100 magnetic protocol, ran the chord-validating raster,
approached the calculated G53 centroid, released Aux0, and printed its Q5
completion message. After the queued approach fully completed, final position
was `MPos:-232.325,-217.950,0.000,0.000`. A magnet placed under that final
TMAG position appeared visually centered.

The original SD P100 also executed three unintended `$H` cycles during Q5,
before the raster. `$H` is a grblHAL system command and was processed despite
the false O-word branches surrounding its three literal instances. The full
raster and centroid result are still valid, but this P100 revision must not be
reused; P111 now owns the one intentional physical X/Y home. G54 and A
remained unchanged.

P111 was then installed and successfully performed exactly one X/Y home.
The first corrected-P100 execution stopped before motion with `error:71`:
the new explanatory parenthesized comment had been split across two physical
lines. That has been corrected to one line and is now rejected by static
validation if reintroduced.

The corrected P100 Q5 then completed without any `Home` state after the Q5
command. Its final position was `MPos:-232.013,-218.775,0.000,0.000`; a
magnet placed under the TMAG at that endpoint was visually centered.

After the A-axis fuse was reinstalled, the low-speed incremental `G1 A10 F120`
then `G1 A-10 F120` check returned controller MPos A to `0.000` and returned
the physical bed reference mark exactly. P112 is the pending two-observation
outer-index survey; it preserves G54 for this first M-09 evidence pass.
Its two A searches run at 10,000 motor-degrees/min (2.31 bed RPM), with a
short reverse trim to the second observed index center rather than a third
forward rotation. The direct measured +X radius is 1.776 mm beyond the X
`-10` mm home pull-off bound, so P112 instead uses G53 X `-10.5` mm: about
2.2 mm inboard on the same radial line.

The installed P112 outer-index survey then captured two complete A magnetic
footprints at `11234.037..11340.462` and `15566.192..15671.942` motor degrees.
Their widths were `106.425` and `105.750` motor degrees; their centers were
`11287.250` and `15619.067`, separated by `4331.818` motor degrees. The
provisional `4320 +/- 10` gate rejected this repeatable 11.818-degree deviation.
P112 now uses a bounded `4320 +/- 15` gate; it still makes no G54 write and Q4
remains locked pending a successful installed survey.

With the revised gate installed, P112 completed successfully. Its second-pass
footprint was captured at `A8557.209..8662.959`; P112 trimmed backward to the
computed midpoint and stopped at `MPos:-10.500,-218.363,A8610.084`. It printed
its survey-complete message, released the probe state, and did not alter G54.
The operator then visually confirmed that the stopped TMAG chip is centered
over the physical index magnet. P112 is therefore M-09 verified as a
survey-only stage; no registration mode has been enabled.

Before any further movement, the operator issued `G10 L20 P1 A0` at the P112
stop. The controller returned `ok` without motion; `$#` then reported
`[G54:-232.900,-191.200,0.000,17281.142]`. This preserves the physical index
as G54 A0. It does not validate or replace the temporary XY work offset.

The operator then ran another successful Q5. It returned TMAG to the calculated
center at `MPos:-232.125,-218.325,A17281.142`. While stationary, the operator
issued `G10 L20 P1 X0 Y-29.4892`; `$#` reported
`[G54:-232.126,-188.835,0.000,17281.142]`. Finally, `G54 G0 X0 Y0` moved the
pen north by the measured offset. The operator visually confirmed that the pen
tip was perfectly centered over the physical center magnet. This is a complete
manual magnetic G54 registration: pen center is X0/Y0 and outer index is A0.

## Boundary

Q5 is hardware-verified as a center-magnet survey. The manual registration
sequence is now verified, but Q5 itself remains non-registering. Do not unlock
Q0/Q3/Q4: their combined body has not yet been updated to use the verified
P111/Q5/P112 workflow.

## Follow-up implementation

After the complete manual frame was verified, P100 Q0 was rewritten to use the
same P111/Q5/P112 measurements. Q0 still contains no `$H`; the ioSender routine
must issue `G65 P111` before `G65 P100 Q0`. Q0 keeps the old G54 frame until
both the center raster and two-pass A survey have passed, then writes A0 at the
second observed index center, returns TMAG to the calculated center, writes the
verified `X0 Y-29.4892` sensor-to-pen offset, and parks the pen at G54 X0/Y0.
Q3/Q4 remain locked. The first combined Q0 run completed without alarm and
visually parked the pen tip at center. A second run verified the long
index-to-center return at `FS:1500`; it completed without alarm at
`MPos:-232.800,-190.063,A8664.309` with WCO
`-232.799,-190.058,A8664.197`.

The installed `$110/$111=1500` mm/min axis limits have not been changed as
part of this raster retune. A requested `F2000` may therefore be rate-limited
by grblHAL; a loaded X/Y rate test must precede any claim that the physical
crossing speed doubled.
