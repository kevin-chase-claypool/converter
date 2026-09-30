# Motif library

Two folders of black-on-white PNGs for the Kaleidoscope Converter's **Motif
folder...** button.

| Folder | What it is | Files |
| --- | --- | --- |
| `nature/` | Real organism silhouettes from [PhyloPic](https://www.phylopic.org): birds, cats, elephants, fish, dolphins, spiders, ants, jellyfish, butterflies, crabs, tortoises, plants and more, traced by scientists and published under CC0 / public domain / CC BY. | 150 |
| `nature-drawn/` | The first, code-drawn set (`tools/make_nature_motifs.py`): schematic leaves, flowers, trees, shells, insects and small animals. Flat and cartoon-like, but tidy and very light to plot. | 110 |

`nature/CREDITS.md` lists the taxon, contributor, licence and source of every
downloaded file, and `nature/manifest.json` carries the same data for tooling.

## Use them

1. Start `kaleidoscope.bat`.
2. Tick **Generate a random pattern**.
3. Press **Motif folder...** and pick `motifs/nature` (this also ticks **Use
   natural motifs in patterns**).
4. Browse `Seed`; set `Intricacy`. In motif mode each shape is drawn at full
   size with two smaller nested copies inside it, rings are separated by thin
   bundles with flower studs and bead rows, and the copies overlap.

Only the motifs a seed actually places get traced, and traced results are
cached, so pointing at 150 files costs nothing until they are used.

## Regenerate, extend or swap

```powershell
python tools\make_nature_motifs.py --out motifs\nature-drawn       # redraw the drawn set
python tools\fetch_phylopic_motifs.py --out motifs\nature --limit 150   # more organisms
python tools\fetch_nature_motifs.py --out motifs\nature --limit 120    # Commons silhouettes
```

- `make_nature_motifs.py` draws every shape from code; add a function plus a
  `CATALOGUE` line to extend it.
- `fetch_phylopic_motifs.py` pulls vector organism silhouettes from PhyloPic,
  rasterises them with Qt and writes the credits files.
- `fetch_nature_motifs.py` pulls from Wikimedia Commons (silhouette categories,
  pressed herbarium leaves). Wikimedia throttles bulk downloads hard, so run it
  in small batches and expect pauses.

Any folder of dark-on-light PNG/JPG artwork works too: hand-drawn scans,
herbarium sheets, your own pen sketches.
