# Lab Note: 2026-09-08 - T-01A current spring geometry

## Objective

Establish the first measured geometry values for the installed 0.4 mm × 7 mm ×
25 mm replacement compression spring with power off.

## Measurements

| Quantity | Value | Interpretation |
|---|---:|---|
| `L_free` | 25.00 mm | Measured outside the housing. |
| `L_unloaded` | 20.37 mm | Spring length installed in the housing with no external load. |
| `x_unloaded = L_free - L_unloaded` | 4.63 mm | Existing housing compression. |
| `L_housing_full` | 1.95 mm | Measured spring-seat separation at the lower housing endpoint. |
| `ΔL_housing = L_unloaded - L_housing_full` | 18.42 mm | Motor-controlled in-housing compression span. |

## Interpretation

The housing already compresses the spring by 4.63 mm with no external load.
For motor travel, the relevant assembled range is the 18.42 mm reduction from
20.37 mm unloaded to 1.95 mm at the lower housing endpoint. The 25.00 mm free
length is only the reference for captured preload, not the commanded travel
range. The 1.95 mm endpoint is not free-spring `L_solid`; it may represent a
housing hard stop, near coil bind, or both, and is not an approved working
`L_min`.

## Remaining T-01A measurements

With power still off, measure and record the repeatable LIFT length `L_lift`,
first-contact length `L_contact`, chosen minimum working length `L_min`,
compression direction under retract, and positive margin from the 1.95 mm
housing endpoint. Obtain `L_solid` outside the housing (or its manufacturer
specification) before establishing final coil-bind margin or force limits. No
powered preload or force-control conclusion is authorized from these dimensions
alone.
