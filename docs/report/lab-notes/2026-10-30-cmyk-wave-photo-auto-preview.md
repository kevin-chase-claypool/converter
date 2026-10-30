# Lab Note: 2026-10-30 - CMYK Wave-screen Auto photo comparison

## Objective

Improve the converter's **Auto (photo)** result for the image currently loaded
in the CMYK tab and preserve more of the source photograph's exposure and
color while keeping equidistant Wave-screen rows.

## Input

- Source:
  `C:\Users\jacks\Downloads\PXL_20241218_215026972~2.jpg`, SHA-256
  `0DB593F75E18601BC140EF2625B7266D2AAD6540E8E0675708606063A9E82A77`.
- Style: **Wave screen - equidistant rows**.
- Pen width: `0.8 mm`.
- Effective row pitch: `1.92 mm`.
- Source is a normal-exposure sunset landscape with pale blue sky, warm clouds,
  dark vegetation, and red foreground foliage.

## Old Auto result

The pre-change Auto button selected:

```text
auto levels: on
saturation: 115 %
contrast: 240 %
brightness: 60 %
sharpen: 200 % at 2.0 mm
ink gamma: 0.60
GCR: 85 %
```

The live preview became a dense red/magenta/black screen. The blue sky and pale
cloud field were substantially darker than the photograph.

## New Auto result

The photo-fidelity path for Wave screen selects:

```text
auto levels: on
saturation: 100 %
contrast: 120 %
brightness: 120 %
sharpen: 100 % at 1.5 mm
ink gamma: 1.00
GCR: 55 %
```

These values were compared in the live CMYK preview at the source's current
page and artwork scale. The revised preview exposed a distinct blue-sky region,
kept warm cloud highlights separate from the sky, and preserved the dark
foreground/foliage structure without imposing the old all-over dense tint.

## Interpretation

The previous Auto search optimized grayscale gradient energy for a
tone-varying line-pitch model. That objective is not appropriate for the Wave
screen, whose row pitch is fixed and whose ink presence is binary at each
sample. The new branch uses source exposure percentiles and high-chroma
statistics to preserve image color and dynamic range.

## Boundary and next action

This is a live preview comparison, not a printed color measurement. The Wave
screen still cannot express continuous-tone density as finely as halftone or
stipple modes. Print a small comparison coupon before committing a full page;
if exact photographic density is more important than the wave treatment, use a
dot screen.
