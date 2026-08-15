---
id: HW-20260802-003
date: 2026-08-02
category: hardware
affected_categories:
  - hardware
status: implemented
components:
  - tools/onshape/onshape_client.py
  - tools/onshape/set_onshape_env.ps1
  - docs/hardware/cad/README.md
tags:
  - cad
  - onshape
  - api
  - documentation
related:
  - docs/hardware/cad/README.md
---

# Onshape API CAD Workflow

## Summary

Added local Onshape API tooling so project CAD metadata and exports can be
pulled into the repository for course documentation.

## Reason

The project will eventually need complete documentation of CAD models, wiring,
parts, and build evidence. Manual Onshape exports are still useful, but API
tooling gives the project a repeatable path for model snapshots, document
metadata, element lists, and export files.

## Implementation

`tools/onshape/onshape_client.py` implements Onshape API-key request signing
using environment variables and supports URL parsing, document listing,
document metadata, workspace element listing, and a Part Studio STEP export
request. `tools/onshape/set_onshape_env.ps1` prompts for the Onshape access key
and secret key and stores them in Windows user environment variables. The CAD
README now documents the workflow and example commands.

## Verification

- Ran `python -m py_compile tools\onshape\onshape_client.py`.
- Ran `python tools\onshape\onshape_client.py parse-url` against a sample
  Onshape URL and confirmed expected `did`, `w`, and `e` extraction.
- Ran documentation index generation and validation after the update.

## Struggles and rejected approaches

The API secret was supplied in a screenshot, but it was not copied into the
repository. The workflow keeps credentials in environment variables so the same
tooling can be committed and reused without credential churn.

## Risks and follow-up

Live Onshape access has not been tested from this workspace yet because the
environment variables still need to be entered locally. STEP export endpoints
can return asynchronous translation metadata instead of a file; when that
happens, a follow-up download command may be needed after the translation
finishes.

## Files

- `tools/onshape/onshape_client.py`: added the signed Onshape API helper.
- `tools/onshape/set_onshape_env.ps1`: added a local credential setup helper.
- `docs/hardware/cad/README.md`: documented the Onshape API workflow for CAD evidence.
