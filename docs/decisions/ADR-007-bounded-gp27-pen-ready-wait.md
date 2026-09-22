# ADR-007: Use a bounded GP27 acknowledgement for commissioned pen transitions

- Status: accepted for source; commissioning gated
- Date: 2026-09-21

## Context

The current M3/M5 pen contract uses fixed G4 delays. Those delays are a useful
safe default but cannot prove that the toolhead actually completed a requested
contact or pen-clear transition. The existing isolated GP27/U3 path already
reaches the RP23CNC `PRB` input, but it is also reserved for the two-phase
GP28/P100 magnetic protocol. The source repository does not include an
RP23CNC/grblHAL plugin source tree in which to intercept M3/M5 invisibly.

## Decision

- Keep M3/M5 unchanged as the toolhead command interface and keep fixed G4
  delays as the default generated-program behavior.
- Add controller-filesystem macro `P115`. `G65 P115 Q0` waits for a verified
  initial clear indication. `G65 P115 Q1`, emitted immediately after each
  normal M3/M5 transition, first requires PRB to become inactive and then
  requires a new active assertion.
- Bound the release and ready waits at 0.50 s and 5.00 s respectively. A
  failed wait raises grblHAL `error[39]` before the next drawing-motion block.
- P115 observes only `#<_probe_state>` and dwell time. It must not issue
  motion, M3/M5, Aux0, or actuator commands.
- GP27 normal-print status is permitted only while the magnetic state is
  fully `DISARMED`; P100 owns GP27 in every other magnetic state.
- The Windows converter exposes this behavior as an unchecked, commissioned
  option. It validates that the active pen contract remains M3/M5.

## Consequences

- A new completion edge prevents an old contact/clear indication from being
  mistaken for acknowledgement of the next command.
- P115 must be installed on the controller filesystem and passed through the
  F-05A dry-contact and integrated tests before either firmware gate or
  converter option is enabled.
- Controller macro-loop semantics are a candidate-build assumption until
  F-05A validates them on the installed firmware. The G4 default remains
  available if that test fails.
- No new wire, USB/UART synchronization mechanism, or PC-timestamp dependency
  is introduced.

## Verification still required

- F-05A: PRB polarity, Q0/Q1 fresh-edge behavior, finite timeout, and no
  unintended motion/output on the installed controller.
- E-09C and later actuator response: establish truthful CS1238 contact force.
- T-01H: establish truthful M5 pen clearance before `CLEAR_READY` is used.
