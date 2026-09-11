# Lab Note: 2026-09-11 - P108 Q5 Readiness-Handshaking Diagnostic

## Objective

Determine whether Q5's Aux0 readiness handshake, rather than its verified
preposition, can provoke the reported unexpected X/Y limit approaches.

## Method

With the toolhead diagnostic firmware connected and the controller Idle,
execute `G65 P108`. P108 performs the same Aux0 sequence and PRB checks as
Q5: released baseline, READY_ACK assertion, release verification, scan-state
assertion, and cleanup. It deliberately contains no G-code axis-motion word
and no `$H`.

## Result

The controller remained `Idle`; P briefly asserted for READY_ACK and returned
to blank on release. P108 printed `P108 complete: Q5 handshake passed with no
axis command`, left Aux0 released, and produced neither X/Y movement nor a
`Home` state.

## Stop condition

If either axis moves or controller status enters `Home`, stop immediately with
Reset and capture the retained P108 messages/status. Do not run Q5 afterward.

## Boundary

P108 does not validate the Q5 raster or centroid. It verifies only the
non-motion readiness-handshake stage that follows P107's now-verified move.
