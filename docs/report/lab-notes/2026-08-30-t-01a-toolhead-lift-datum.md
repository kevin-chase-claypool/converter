# Lab Note: 2026-08-30 - T-01A Toolhead Lift Datum

## Objective

Establish a proposed repeatable LIFT geometry for the spring-loaded pen
toolhead.

## Configuration

- Spring free length, measured with calipers: 1.190 in.
- Spring nominal dimensions: 0.027 in wire diameter x 0.295 in outside
  diameter x 1.19 in free length.
- Proposed LIFT spring compression: 0.535 in.
- Resulting installed spring length: `1.190 - 0.535 = 0.655 in`.
- Measured pen-tip-to-bed clearance at the proposed LIFT datum: 0.1885 in.
- Planned mechanical feature: a pen stop integrated into the pen mount to set
  a repeatable pen insertion height.

## Code, commands, and configuration used

```text
Unpowered mechanical measurement; no firmware or motion command used.
```

## Procedure

1. Measured the unloaded spring length with calipers.
2. Positioned the toolhead at the selected LIFT geometry.
3. Measured spring compression and pen-tip clearance from the bed.
4. Selected an integrated pen stop as the mechanical datum for future pen
   insertion.

## Results

- The proposed LIFT compression is 0.535 in.
- The corresponding installed spring length is 0.655 in.
- Pen-tip clearance is 0.1885 in, which is the proposed safe-travel clearance.
- The pen stop should make the relationship between pen insertion, carriage
  position, and spring compression repeatable.

## Difficulties and corrective actions

Spring solid height was not measured. The selected 0.655 in installed length
is therefore not yet a verified maximum-safe compression. Do not use it as a
firmware hard limit until the solid-height margin is recorded.

## Decisions and next action

Use this as the proposed LIFT datum, then measure or obtain `L_solid` and
verify the margin at 0.655 in. Build the pen stop, verify repeatable insertion,
and repeat the LIFT-clearance measurement before completing T-01A.
