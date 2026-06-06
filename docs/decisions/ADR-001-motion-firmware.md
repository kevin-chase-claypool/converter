# ADR-001: Use grblHAL for motion control

- Status: accepted
- Date: 2026-06-06

## Context

The controller must interpret G-code and coordinate X, Y, and rotating-bed A
motion with acceleration, limits, homing, and real-time stop behavior.

## Decision

Use grblHAL and its RP2040/RP2350 driver on RP23CNC. Keep custom code limited to
configuration and a toolhead plugin unless a demonstrated requirement cannot be
met upstream.

## Consequences

- The project avoids maintaining a custom parser, lookahead planner, and pulse generator.
- Firmware work starts with board configuration and hardware tests.
- Dual-core use must respect the upstream driver's architecture.
- Toolhead control may use a plugin, a supported core-1 service, or a separate MCU.
- The exact grblHAL source revision and build options become reportable configuration items.
