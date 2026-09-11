# Lab Note: 2026-09-11 - P109 Q5 Combined Preposition/Handshake Diagnostic

## Objective

Test Q5's preposition and readiness handshake in their actual order, while
excluding every G38 raster move.

## Preconditions

- A fresh `G65 P100 Q2` completed after the X/Y shaft-adapter adjustment.
- X/Y path to G53 `X=-280`, `Y=-266` is clear.
- P107 and P108 separately passed.

## Method

Execute `G65 P109`. It reproduces Q5's `M5`, released baseline, southwest
G53 preposition, READY_ACK/release/re-arm handshake, and cleanup. It then
returns before its first G38 command.

## Result

P109 made one continuous move from X/Y home to `MPos:-280,-266`, briefly
asserted/released P for the handshake, stayed out of `Home`, and printed its
completion message. No raster row, probe move, G54 write, or A move occurred.

## Stop condition

No stop condition occurred. The remaining untested Q5 operation is its first
G38 raster command.
