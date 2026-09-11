# Lab Note: 2026-09-11 - P106 Manual Magnetic Survey Plan

## Objective

Provide enough no-motion scan-active time to validate the Q3 candidate
rectangle's clear corners and magnetic center before automatic raster motion.

## Method

P106 uses a five-second inactive baseline, then `M65 -> M64 -> M65` with
0.1-second intervals. This transitions the installed diagnostic firmware from
READY_ACK through WAIT_REARM into SCAN_ACTIVE. It holds that state for 180
seconds and performs no axis motion.

## Expected operator observations

- At the NW, NE, SE, and SW candidate corners: P is blank.
- Over the center magnet: P is red.
- On leaving the center magnet for a corner: P returns blank.

## Boundary

The macro is unverified until copied to the controller and run. It does not
authorize Q3 or change its commissioning lock.
