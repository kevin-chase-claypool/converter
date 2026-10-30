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
brightness: 150 %
sharpen: 100 % at 1.5 mm
ink gamma: 1.40
GCR: 35 %
dot pitch: 1.20 mm before scale (2.76 mm on paper)
```

These values were compared in the live CMYK preview at the source's current
page and artwork scale. The revised preview exposed a distinct blue-sky region,
kept warm cloud highlights separate from the sky, and separated the dark
foreground/foliage colors without imposing the old all-over dense tint. The
wider pitch was necessary because the Wave screen is a binary mark mask; at the
previous pitch, all three CMY plates covered most dark-red flower pixels.

Using the same binary row-mask approximation for before/after comparison, the
modelled average print RGB changed as follows:

| Settings | Mean RGB | Mean absolute error vs source |
|---|---:|---:|
| Old Auto | `(0.383, 0.298, 0.293)` | `0.2362` |
| New Auto | `(0.540, 0.469, 0.467)` | `0.2105` |

The source mean is `(0.543, 0.457, 0.380)`. The new result is much closer in
overall lightness and red/green balance while retaining the dark foreground.

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
