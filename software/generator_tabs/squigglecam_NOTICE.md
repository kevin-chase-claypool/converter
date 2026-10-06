# SquiggleCam tab - third-party notice

The SquiggleCam tab ports the MIT-licensed msurguy/SquiggleCam
(https://github.com/msurguy/SquiggleCam). All of its settings are exposed:
line count, frequency, amplitude, brightness, contrast, min/max brightness,
pixel spacing, and the black-background inversion.

The algorithm (one continuous squiggle per row; brightness drives an
accumulated phase and the local wave amplitude) was rewritten in Python for
this repository from the upstream Vue source. The Convert tab's
`sine_gradient` fill is the related SquiggleDraw idea applied as a region
fill; this tab is the full-page SquiggleCam generator.
