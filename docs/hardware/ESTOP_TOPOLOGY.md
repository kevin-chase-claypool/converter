# Emergency-stop topology

This document is the current design authority for the plotter's emergency-stop
and Halt arrangement. It supplements the individual connection rows in
[`WIRING_TABLE.md`](WIRING_TABLE.md).

Status: planned as the RP23CNC's dedicated opto-isolated Halt input only; no
final conductor has been landed and E-19 has not yet been performed. A relay
energy-removal branch is not part of this project.

## Purpose and boundary

For the initial implementation, SW1 must do one thing when pressed:

1. Assert the RP23CNC E-stop/Halt input so grblHAL enters Halt and requires a
   deliberate Reset/Unlock recovery.

The RP23CNC manual specifically supports this 12 V opto-isolated control-input
approach. The controller remains powered during an E-stop, preserving the Halt
state and avoiding a power restoration being treated as permission to move.

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
RP23CNC Iso 12 V input -> powers the isolated control-input section

SW1 NC-A terminal 1 -> RP23CNC dedicated E-stop/Halt terminal 1
SW1 NC-A terminal 2 -> RP23CNC dedicated E-stop/Halt terminal 2

SW1 NC-B -> unused: insulate both terminals individually
```

The E-stop's NC terminals have no polarity. The exact RP23CNC E-stop terminal
pair is intentionally not filled in until the installed board silkscreen and
E-19 checks agree. Never infer it from the mushroom-switch drawing alone.

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

1. With all power removed, verify NC-A is continuous when released and open
   when pressed. Verify NC-B is isolated from NC-A and leave NC-B insulated.
2. With isolated 12 V present, wire only NC-A to the RP23CNC E-stop/Halt input
   pair after identifying its terminal labels.
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
