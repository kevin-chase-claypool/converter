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

## Expected result

The controller remains `Idle`; `P` may briefly assert during READY_ACK. P108
prints `P108 complete: Q5 handshake passed with no axis command` and leaves
Aux0 released. Neither X nor Y must move or enter `Home`.

## Stop condition

If either axis moves or controller status enters `Home`, stop immediately with
Reset and capture the retained P108 messages/status. Do not run Q5 afterward.

## Boundary

P108 does not validate the Q5 raster or centroid. It only isolates the
non-motion readiness-handshake stage that follows P107's now-verified move.
