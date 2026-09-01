# ADR-002: Use a Pro Micro RP2350 toolhead controller

- Status: accepted
- Date: 2026-06-06
- Accepted: 2026-08-22

## Context

The toolhead uses a 6 V N20 actuator, DRV8833, HX711/load cell, and TMAG5273.
An earlier plan deferred the choice between placing this work inside RP23CNC
grblHAL and using a separate MCU. The installed toolhead now has a SparkFun Pro
Micro RP2350 with the required local power, sensor, actuator, and isolated
controller interfaces.

Keeping the force-control and magnetic-sensing workload off the RP23CNC avoids
coupling HX711/TMAG sampling or actuator control to motion-planner timing. It
also matches the constructed GP0/GP1, GP4-GP7, Qwiic, and GP27-GP29 harnesses.

## Decision

Use the toolhead-mounted SparkFun Pro Micro RP2350 as the combined controller
for:

- M3/M5-driven pen-clear, seek-contact, and force-hold states, plus local
  LIFT_HOME reference handling.
- HX711 load-cell acquisition.
- DRV8833/N20 actuator control and local fault response.
- TMAG5273 Qwiic magnetic sensing.
- The conditioned GP27 magnetic output through PC817C U3.

RP23CNC/grblHAL remains the exclusive motion controller. GP29 receives the
isolated M3/M5 mode request and GP28 receives the isolated magnetic-arm request.
Whether the existing GP27/U3 return ultimately terminates at `LIMA` or `PRB`
remains a separate F-08/E-18 decision and is not settled by this ADR.

There is no additional RP2040 magnetic adapter and no current plan to move the
toolhead loop into an RP23CNC plugin or second core.

## Consequences

- One Pro Micro RP2350 owns both pressure and magnetic toolhead behavior.
- Toolhead firmware must keep sensor/control work bounded and default to a safe
  lift/off state after reset, fault, or invalid command combinations.
- Version 1 continues to use M3/M5 plus fixed G4 settling delays; dedicated
  `CONTACT_READY` and `TOOL_FAULT` returns remain possible later upgrades.
- Toolhead and RP23CNC grounds remain isolated across the PC817C interface.
- Replacing this controller placement requires a new superseding ADR and new
  wiring, timing, and safety evidence.

## Verification still required

- Complete force-loop calibration and fault tests T-01 through T-06.
- Complete F-05 for the RP23CNC M3/M5 output mapping.
- Complete E-18 for the installed GP27/GP28/GP29 isolated interface.
- Complete F-08 before any `LIMA` to `PRB` retermination.
