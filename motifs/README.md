# Nature motif library

`nature/` holds 110 black-on-white PNG silhouettes for the Kaleidoscope
Converter's **Motif folder...** button: leaves, flowers, trees, sea life, birds,
insects, small animals, shells, mushrooms, acorns, mountains, sun, moon,
snowflake and water.

Every image is drawn from code in `../tools/make_nature_motifs.py`, supersampled
and thresholded, so the result is pure black on pure white with crisp edges and
nothing for the tracer to guess at. The files are 1-bit, about 1 KB each.

## Use them

1. Start `kaleidoscope.bat`.
2. Tick **Generate a random pattern**.
3. Press **Motif folder...** and pick `motifs/nature` (this also ticks **Use
   natural motifs in patterns**).
4. Browse `Seed`; set `Intricacy` and, if the shapes vanish, lower the trace
   threshold or raise `Trace detail`.

Motif mode keeps fewer, thicker rings so the shapes stay recognisable, mixes one
to three motifs per ring, and lets the copies overlap.

## Regenerate or extend

```powershell
python tools\make_nature_motifs.py                 # rewrite motifs/nature
python tools\make_nature_motifs.py --out D:\shapes # somewhere else
python tools\make_nature_motifs.py --limit 12      # quick preview
```

Add a new shape by writing a `draw(draw, size, variant)` function in
`tools/make_nature_motifs.py` that draws in 0..1 coordinates and adding it to
`CATALOGUE`. Point the app at any folder of PNG/JPG files - a hand-drawn or
scanned set works too, as long as the shapes are dark on a light background.
