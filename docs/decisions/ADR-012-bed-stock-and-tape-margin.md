# ADR-012: Model the bed, stock, and tape margin separately

- Status: accepted for physical geometry; converter implementation deferred
  after the 2026-11-26 rollback
- Date: 2026-11-26
- Supersedes: numeric bed/stock defaults in ADR-009

## Context

The converter previously used one `Bed dia mm` value for both the physical
rotating bed and the paper stock. It modeled 15-inch stock as a 15-inch bed,
then treated the 14.5-inch rim-clear circle as the stock boundary while a
180 mm gantry cap reduced the actual drawing circle to 14.173 inches. That
misrepresented the installed machine and made the tape border impossible to
reason about in Preview.

The project owner confirmed the installed geometry:

- physical rotating bed: 18 inches;
- round paper stock: 15 inches;
- requested drawing diameter: 14.5 inches;
- remaining 0.5-inch diameter reduction: 0.25-inch margin on each stock edge
  for tape.

## Decision

Represent the three diameters independently:

```text
bed_diameter_mm    = 457.2  # 18 in physical rotating bed
stock_diameter_mm  = 381.0  # 15 in round paper stock
bed_margin_mm      = 6.35   # 0.25 in inward from every stock edge
drawing_diameter   = 368.3  # 14.5 in
gantry_reach_radius = 184.15 # 7.25 in
```

The artboard clip uses `stock_diameter_mm / 2 - bed_margin_mm`. The physical
bed diameter controls the outer Preview circle, machine geometry, and safe
parking distance; it does not define the paper edge.

The default gantry planning radius becomes the owner-specified `184.15 mm`.
That replaces the prior conservative `180.0 mm` default. Compensation profile
`745e3d264cc5` retains the centered dense-v3 measured samples through
`165.1 mm` and extends the local-affine correction field to `184.15 mm`.

## Consequences

- The 2026-11-26 rollback (`WSW-20261126-005`) restored the converter to its
  earlier single-diameter stock model. The physical 18-inch bed, 15-inch stock,
  6.35 mm tape margin, and need for a fresh HOME + REGISTER remain project
  facts; only the converter-side three-circle implementation is deferred.
- Preview can show distinct 18-inch bed, 15-inch stock, and 14.5-inch drawing
  circles, including the tape band.
- Saved programs clip against the paper-stock margin unless the gantry cap is
  lower.
- The outer `19.05 mm` compensation annulus remains extrapolated until an
  edge-band sheet verifies it.
- The owner-selected 14.5-inch disc exceeds the prior conservative 180 mm
  planning default. Each HOME + REGISTER cycle must verify the current +Y
  soft-limit envelope and physical stock/tape clearance before a full-disc
  production run.
- The current profile reserves `1.142 mm` for its maximum outward correction,
  so nominal artwork clipping is `183.008 mm`. The final corrected envelope
  may not exceed `184.15 mm`.
- Older settings or scripts that supplied only `bed_diameter_mm` must also
  supply `stock_diameter_mm` when they intend a custom stock size.

## References

- [`settings.py`](../../software/converter_core/settings.py)
- [`INTERFACES.md`](../integration/INTERFACES.md)
- [`software/README.md`](../../software/README.md)
