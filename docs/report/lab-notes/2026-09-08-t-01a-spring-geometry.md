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
| `L_housing_full` | 1.95 mm | Owner-reported full-compression endpoint within the housing. |
| `x_housing_full = L_free - L_housing_full` | 23.05 mm | Compression at that housing endpoint. |

## Interpretation

The housing already compresses the spring by 4.63 mm with no external load.
The 1.95 mm reading is the housing endpoint, not the free spring's `L_solid`.
It cannot establish coil-bind clearance and may represent a housing hard stop,
near coil bind, or both. It is not an approved working `L_min`.

## Remaining T-01A measurements

With power still off, measure and record the repeatable LIFT length
`L_solid` outside the housing (or obtain the manufacturer specification),
repeatable LIFT length `L_lift`, first-contact length `L_contact`, chosen
minimum working length `L_min`, compression direction under retract, and
positive margins from both `L_solid` and the 1.95 mm housing endpoint. No
powered preload or force-control conclusion is authorized from these dimensions
alone.
