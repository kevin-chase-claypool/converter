# Pen pressure control

Independent closed-loop control of pen contact force, on its own MCU. Driven by
the grblHAL spindle-enable line as a **mode override**, not a position command.

## Behavior

- **LIFT** (input = M5): drive the pen actuator open-loop to a safe retract
  height; force loop paused. Report `pen_is_lifted` when there.
- **ENGAGE** (input = M3): release the override; seek down slowly until the load
  cell crosses the contact threshold, then hold target force, tracking paper/bed
  unevenness while drawing. Report `pen_in_contact` once settled.

The host's `G4` dwell after M3/M5 gives this loop time to reach the LIFT/ENGAGE
state before motion resumes (open-loop handshake). A later upgrade: feed-hold
grblHAL until `pen_in_contact` is asserted (true closed-loop handshake, e.g., via
a grblHAL plugin reading a contact input).

## Safety (build into ENGAGE)

- approach rate-limit (don't slam the pen down)
- max-seek / stall guard → abort to LIFT if no contact (paper missing / bed too low)
- force clamp on PID output
- force LIFT on any fault / E-stop

## Open decisions

- load-cell interface: HX711 vs ADC + instrumentation amp
- actuator type for pen height (geared DC + encoder, stepper, voice coil…)
- separate MCU now vs. fold into a grblHAL plugin later
