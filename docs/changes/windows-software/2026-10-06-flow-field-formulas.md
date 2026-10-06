---
id: WSW-20261006-023
date: 2026-10-06
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/flow_field_tab.py
tags:
  - generators
  - flow-field
  - fidelity
related:
  - WSW-20261006-002
  - docs/research/2026-10-06-generator-tab-fidelity-audit.md
---

# Flow Field formula source

## Summary

Flow Field gained the upstream-style formula source: a safe `f(x, y)`
expression for the field angle, or two expressions for the vector components
`dx`/`dy`, with presets (Swirl, Radial, Vortex, Waves, Sheets) and custom
entry. This closes the audit's top Flow Field gap.

## Reason

The 2026-10-06 fidelity audit found the upstream `msurguy/flow-lines` tool is
formula-driven while this tab only offered procedural noise and image
gradients.

## Implementation

- `compile_formula()` parses the expression with `ast`, allows only numbers,
  `x`/`y`, the listed math functions, and arithmetic operators, then evaluates
  with empty builtins. Unsafe syntax (`__import__`, attributes, lambdas)
  raises `ValueError`.
- `flow_field_polylines(..., field_angle=...)` uses the callable when present;
  coordinates are page-centre millimetres so formulas read naturally.
- The tab's Source combo gained **Formula**, with preset/mode/formula fields.

## Verification

- `python -m unittest discover -s software\tests -p "test_flow_field_tab.py" -v`
  -> 7 tests pass, including evaluator safety, a formula-driven streamline
  field, and the tab's formula-mode SVG build.

## Struggles and rejected approaches

- A general `eval` was rejected; the AST whitelist keeps formulas to
  arithmetic and math functions.

## Risks and follow-up

- Formula evaluation is per sample point in Python; very dense fields with
  heavy expressions are slower than the noise field.

## Files

- `software/generator_tabs/flow_field_tab.py`: evaluator, presets, UI, field.
- `software/tests/test_flow_field_tab.py`: formula coverage.
