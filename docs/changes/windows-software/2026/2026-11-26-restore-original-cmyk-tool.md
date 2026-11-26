---
id: WSW-20261126-001
date: 2026-11-26
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/generator_tabs/cmyk_tab.py
  - software/generator_tabs/cmyk_photo_tab.py
  - software/tests/test_generator_tabs.py
  - software/README.md
  - software/generator_tabs/README.md
tags:
  - cmyk
  - navigation
  - tools-menu
  - guided-ui
  - regression
related:
  - WSW-20261125-008
---

# Restore the original CMYK tool entry

## Summary

The original **CMYK** tab is available again in the Photo-based Tools list. It
opens the complete CMYK tuner directly, with Ctrl+3 as its shortcut. The guided
**CMYK Photo** workflow remains a separate entry immediately after it.

## Reason

The guided color workflow replaced the original tab registration. The full
tuner still existed, but owners could only reach it after opening **CMYK
Photo** and then **Advanced settings**. That hid the earlier, familiar workflow
from the tool list and reassigned Ctrl+3 to the new guided page.

## Implementation

- `cmyk_tab.py` now registers the original `CmykTab` as **CMYK**.
- The guided `CmykPhotoTab` is registered by `cmyk_photo_tab.py` as **CMYK
  Photo**.
- The two pages use distinct recipe namespaces, `cmyk` and `cmyk_photo`, so
  saving settings in one does not overwrite the other.
- Both pages continue to share the same conversion, preview, program analysis,
  four-file export, and manifest implementation.

## Verification

- `python -m unittest -q software.tests.test_cmyk_tab
  software.tests.test_cmyk_photo_tab software.tests.test_generator_tabs`
  passed `134` tests with the expected OpenGL-context skip.
- Generator-shell tests verify that **CMYK** and **CMYK Photo** are both
  present, use distinct implementations and recipe names, switch to the
  correct stacked page, and assign Ctrl+3 to the restored tuner.

## Struggles and rejected approaches

Keeping the guided page as the only registration and documenting the Advanced
settings route was rejected because it preserved the navigation regression the
owner reported.

The first focused run retained the guided-workflow assertion that every
generator starts at 100% scale. The restored tuner intentionally uses its
previous owner-tuned 280% default, so that assertion was corrected before the
passing run.

## Risks and follow-up

Adding the restored entry shifts the later Photo-based tool shortcuts by one.
Artwork recipes saved under the `cmyk` key while only the guided page was
registered will restore into the original tuner; new guided-page recipes use
`cmyk_photo`.

## Files

- `software/generator_tabs/cmyk_tab.py`: restores the original tab title and
  registration and separates the guided recipe namespace.
- `software/generator_tabs/cmyk_photo_tab.py`: registers the guided page.
- `software/tests/test_generator_tabs.py`: verifies both entries, their distinct
  implementations, page switching, and Ctrl+3.
- `software/README.md`: documents both CMYK entry points.
- `software/generator_tabs/README.md`: updates the tab architecture contract.
