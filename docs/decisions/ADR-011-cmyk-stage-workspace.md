# ADR-011: Expose adaptive CMYK as a staged workspace

- Status: superseded by the 2026-11-26 converter rollback
- Date: 2026-11-25
- Superseded by: `WSW-20261126-005`

## Context

The native CMYK renderer already performs composition, image preparation,
process-ink separation, structure-tensor guidance, streamline placement, ink
assignment, path joining, machine planning, and coordinated export. Those
behaviors were exposed as one long Advanced form and shared one cache key.

The adaptive-flow requirement needs operators to understand which stage owns a
setting, which input and output contract it changes, what validation applies,
and which automatic adjustments may overwrite a manual decision. It also needs
diagnostic evidence for direction fields without creating a second primary
print preview.

## Decision

Use nine persistent operator stages over the existing converter:

1. Composition and placement
2. Color-managed image preparation
3. Calibrated CMYK separation
4. Structure-tensor direction field
5. Adaptive streamline placement
6. Ink assignment and local coverage
7. Path simplification, chaining, and order
8. Machine motion and alignment
9. Review, validation, and export

Each stage declares:

- an ordered set of existing settings groups;
- its input and output data contracts;
- the validation applied to its controls or results;
- the dependencies represented in its settings hash; and
- an optional diagnostic action.

The rail filters existing controls rather than duplicating them. Guided CMYK
remains the one-action default. Stage locks preserve manual values when Auto,
recommended defaults, quick guided defaults, or complete comparison recipes
run. Explicit Reset stage can still restore a locked stage.

The selected stage and locks are part of the artwork recipe. Every print-set
manifest records each stage's current settings hash and the locked-stage list.

An auxiliary direction-field image uses the actual multichannel structure
tensor. Hue repeats every 180 degrees so eigenvector sign ambiguity cannot
change the displayed orientation; brightness is confidence; keyline confidence
adds a white overlay. The primary simulated CMYK paper preview remains the
single shared OpenGL preview.

## Consequences

- Operators can isolate one part of the pipeline without learning the entire
  tuner at once.
- Stage contracts and manifest hashes create stable review points for later
  cache and pipeline decomposition.
- Hidden stage groups must not shrink the preferred advanced tool-pane width;
  the full pre-filter width is retained.
- Stage locks affect automatic adjustments only. They do not prevent explicit
  reset, G-code planning, or export.
- The existing renderer and output geometry remain unchanged for fixed
  settings and seeds.
- The renderer still rebuilds from one combined cache key. Per-stage
  materialized caches and intermediate graphical previews are future work and
  must preserve byte-equivalent fixed-seed geometry before replacing the
  current path.

## Verification

- Stage navigation, lock signals, and deterministic widget-state restore are
  unit-tested.
- Clicking a stage from Guided mode opens the corresponding advanced filter.
- Reset restores that stage only; locked stages survive complete recipe
  application.
- Selected stage and locks round-trip through the artwork recipe.
- All settings groups map to exactly one or more declared stage contracts.
- The opposite-direction diagnostic image is identical, and a flat field is
  darker than structured input.
- Complete converter discovery passes `734` tests with one expected
  OpenGL-context skip.

This decision is UI/architecture and software-diagnostic behavior. It does not
validate paper density, registration, pen spread, or a production recipe.
