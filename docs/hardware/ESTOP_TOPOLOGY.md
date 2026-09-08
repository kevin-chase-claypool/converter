# Emergency-stop topology

This document is the current design authority for the plotter's emergency-stop
and Halt arrangement. It supplements the individual connection rows in
[`WIRING_TABLE.md`](WIRING_TABLE.md).

Status: NC-A has been reported landed across the RP23CNC's dedicated
opto-isolated Halt input; E-19 has not yet been performed, so the connection
is wired but unverified. A relay energy-removal branch is not part of this
project. The physical terminal is identified (see "Identified terminal" below).

## Purpose and boundary

For the initial implementation, SW1 must do one thing when pressed:

1. Assert the RP23CNC E-stop/Halt input so grblHAL enters Halt and requires a
   deliberate Reset/Unlock recovery.

The RP23CNC manual specifically supports this 12 V opto-isolated control-input
approach. The controller remains powered during an E-stop, preserving the Halt
state and avoiding a power restoration being treated as permission to move.
This is a **controller-signal stop**, not an energy-isolation circuit: it does
not remove 12 V from the TB6600s or toolhead. Use the main power switch (and
disconnect mains before wiring) for power isolation.

SW1's unused second NC contact is not part of this project. Insulate both of
its terminals individually.

## Components

| Ref | Component | Status | Role |
|---|---|---|---|
| SW1 | mxuteuk `HB2-BS544`, 22 mm latching mushroom, 2 NC | purchased | NC-A is the initial controller Halt circuit; NC-B remains unused and insulated |
| FMAIN | DC main fuse/carrier | TBD selection | Protects the external positive feed from the 10 A supply; fuse must not exceed 10 A |
| FCTRL | HD064RT `OUT1` branch fuse | planned | Protects the RP23CNC and isolated-input supply; 2 A selected, fitted marking/current still require verification |
| PD1 | HCDC `HD064RT`, 5-32 V, eight-channel fused distribution | received/installed | `OUT1` RP23CNC, `OUT4` D36V50F6, `OUT6` X, `OUT7` Y, `OUT8` A; `OUT2`, `OUT3`, and `OUT5` unused |

## Initial net topology

```text
              upper NC contact block in the supplied switch photo
                 (released: 1--2 closed; pressed: 1--2 open)

 RP23CNC ESTOP SIG o------[ terminal 1   NC   terminal 2 ]------o RP23CNC ESTOP GND
                         \_____________ SW1 NC-A _____________/

 lower NC contact block (SW1 NC-B): use neither terminal; insulate each

 RP23CNC ISO 12 V input -> powers the isolated control-input section
                            separately from this two-wire switch loop
```

The E-stop's NC terminals have no polarity: terminal 1 may go to `SIG` and
terminal 2 to `GND`, as shown, or the two wires may be swapped. Do not use one
terminal from each contact block. The upper block in the supplied rear-switch
photo is designated NC-A only to make the diagram unambiguous; the lower,
independent `1`/`NC`/`2` block is NC-B and remains unused. Do not skip the E-19
continuity/live checks just because the terminal name is known.

## Identified terminal

The RP23CNC user manual's "Key Features" board diagram (`docs/hardware/references/RP23CNC-user-manual.pdf`,
p.6, board rev RP23U5XBB V1.0) labels a dedicated 2-pin `ESTOP` screw
terminal (`SIG` / `GND`) as the rightmost terminal in the "Grbl Control
Inputs" group, immediately after `DOOR`, `CY/ST`, and `FD HOLD`. This was
cross-checked against a photo of the owner's installed board, which reads
`RP23U5XBB V1.01` on the silkscreen and shows the same
`... DOOR CY/ST FD HOLD ESTOP` terminal row with matching `SIG`/`GND`
labels. See
`docs/report/lab-notes/2026-09-08-rp23cnc-estop-terminal-identification.md`
for the evidence photos and reasoning.

This is a simple 2-wire switch loop, not a powered feed: SW1 NC-A bridges the
`ESTOP` terminal's `SIG` and `GND` pins when the switch is released (open when
pressed). The board's isolated 12 V input must still be powered for the
control-input opto section to be live at all; that is separate from this
2-wire connection and carries no polarity requirement of its own here.

Because SW1 is NC, its E-stop inversion bit must be **clear**. The manual's
first-run `$14=70` value assumes an NO E-stop. With the current Feed Hold and
Cycle Start choices unchanged, the target after SW1 is wired is `$14=6`
(bit 6 removed); make that change only as part of E-19 while verifying the
actual input state.

## HD064RT allocation and limits

The module is not the E-stop itself. It is the downstream fused distribution
point on the protected 12 V bus. It is compatible with the 12 V source because its
specified 5-32 V operating range covers 12 V and its 20 A aggregate rating is
above the source's 10 A maximum.

Do not assume the pre-installed 3 A fuses are the values currently fitted.
The initial planned values are 2 A on `OUT1`, `OUT6`, `OUT7`, and `OUT8`, and
3 A intended on `OUT4`. With power removed, verify each physical fuse marking;
then verify steady and start/stall current before retaining or changing a value.
Do not fit a fuse above the terminal/module limit or the source/wire protection
basis.

## Required E-19 verification: controller Halt

Perform with the pen removed, axes clear, and motion set to a safe test state:

1. With all power removed, meter NC-A terminal `1` to `2`: continuous when
   released and open when pressed. Verify NC-B is isolated from NC-A and leave
   both NC-B terminals individually insulated.
2. With isolated 12 V present, wire only NC-A to the RP23CNC `ESTOP` terminal's
   `SIG`/`GND` pins (identified above; confirm once more against the physical
   board before landing wire). The `SIG`/`GND` assignment at the NC contact is
   interchangeable.
3. Set the E-stop control-input inversion for NC operation as part of this
   live test (current planned `$14=6`, subject to ioSender state verification).
4. Power only the controller/control branch. Press SW1 and verify that ioSender
   reports E-stop/Halt; release SW1 and verify that Reset/Unlock is still a
   deliberate separate action.
5. Confirm no automatic motion restart occurs after twist-release, reset, and
   unlock. Record the final terminal pair, `$14` value, state transitions, and
   photographs in a dated lab note before changing the row to `verified`.

## Non-negotiable rules

- Do not connect the unused NC-B pair to any conductor.
- Do not connect PE/chassis earth to `12V -V` merely because both are called
  ground.
- Do not use a 30 A fuse simply because a holder or relay is rated 30-40 A.
- Do not treat this planned arrangement as safety-certified machinery control.
