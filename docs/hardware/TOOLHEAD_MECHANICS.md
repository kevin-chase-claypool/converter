# Toolhead Pen Mount and Spring Mechanics

## Purpose

This is the current physical model for the pen mount. It is the authority for
interpreting toolhead travel and spring measurements during T-01 force testing.
It supersedes any inference that a lead-screw position dimension is a spring
length.

## Physical parts and motion

The toolhead has two distinct moving systems:

| Part | Motion and role |
|---|---|
| Outer spring housing | Fixed to the toolhead structure. It provides the stationary upper spring seat. |
| Pen housing/carriage | Slides vertically within the fixed spring housing. It carries the dummy pen or writing tool and makes contact with the lower end of the compression spring. |
| Compression spring | Expanded while the pen is clear of paper. It is compressed only when paper reaction pushes the pen housing upward into the fixed spring housing. |
| N20 lead screw and heat-set nut | Provide actuator/carrier position. Their relative visible gap is an actuator-position datum, not the spring length. |
| GP2 `LIFT_HOME` switch and flag | Provides an absolute retract reference. It is a position switch, not a force sensor and not a spring-compression measurement. |

## Force path

```text
paper / scale reaction (upward)
        -> pen tip
        -> sliding pen housing (upward)
        -> compression spring
        -> fixed spring housing / toolhead structure
```

With no upward reaction at the pen tip, the pen housing is lower in the fixed
spring housing and the spring is unloaded/expanded. Moving the actuator to
retract or lift the pen does not by itself establish spring compression.

When the tip meets paper or a scale, continued controlled down/engage motion
lets the upward reaction move the pen housing upward and compress the spring.
That contact-force condition—not a lead-screw gap—is the relevant condition for
spring rate, writing force, `L_contact`, `L_min`, and coil-bind margin.

## Measurement vocabulary

| Quantity | Meaning | How to measure |
|---|---|---|
| `L_free` | Spring length outside the assembly with no load | Measure the removed spring between its end coils. |
| `L_unloaded` | Installed spring length with pen clear and no upward tip force | Measure directly between the fixed upper spring seat and the sliding pen-housing lower spring seat. |
| `L_contact` | Installed spring length at first paper/scale contact | Use the same two spring seats while the scale first registers force. |
| `L_min` | Smallest approved spring length at the greatest intended force | Determine only from guarded scale-force testing; it must remain above `L_solid`. |
| `L_solid` | Spring length when adjacent coils first fully touch | Measure the removed spring cautiously between flat surfaces. This is a contact-force limit. |
| Lead-screw/nut gap | Visible distance between the lead screw/heat-set-nut reference faces | Use only as a repeatable actuator-position datum. It is not any `L_*` spring value. |

Current measured values are `L_free = 25.00 mm`, `L_solid = 3.75 mm`, and an
initial direct `L_unloaded = 20.29 mm` repeat (the prior record is 20.37 mm).
Treat unloaded spring length as approximately 20.3 mm until a repeat set
establishes measurement tolerance. The observed GP2 switch positions of 7.23
mm asserted and 7.97 mm released are lead-screw/heat-set-nut gaps, not spring
measurements. Do not use the historical 1.95 mm housing-endpoint figure as a
spring length until its physical datum is re-verified.

## Test implications

- GP2 can establish a repeatable lift reference but cannot establish pen force
  or pen clearance by itself.
- E-07/T-01B scale work must use a dummy or real pen in the normal clamp and
  measure force through the actual paper-contact path.
- Any motor replacement requires a fresh actuator characterization, but the
  pen-housing/spring force path remains the model used to interpret it.
- Do not select force limits, pulse bounds, or normal M5 clearance from
  lead-screw travel alone.

## Evidence boundary

This model is based on the project owner's 2026-09-09 physical inspection and
side-view photographs: one with upward force applied to the pen carriage and
one with no upward force. It records the observed mechanism; spring-rate and
force-vs-compression data remain T-01B work.
