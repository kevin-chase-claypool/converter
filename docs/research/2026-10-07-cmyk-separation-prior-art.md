# CMYK color separation for pen plotters - open-source prior art from r/plotter and r/plotterart

Date: 2026-10-07

## Answer

Yes. The exact feature - split a PNG/JPG into CMYK and produce one plot file
per ink - already exists in open source, and the reusable parts are small
enough that this converter does not need new motion or G-code work:

1. **`ohnorobo/cmyk-splitter` (MIT, Python)** is the most directly reusable
   code found. It is a small FastAPI service that converts RGB to CMYK with
   gray-component replacement (GCR) in Pillow/NumPy, renders each channel as
   halftone-dot SVG, and combines the four channels into one layered SVG. The
   converter already uses Pillow/NumPy for image-driven fills and already has
   `halftone` and `stipple` fill styles, so porting this is a focused change
   rather than a new engine.
2. **`svenhb/plotterfun-color` (MIT, JavaScript)** is mitxela's Plotterfun
   with a CMYK mode: the selected algorithm runs per channel and the four path
   groups are exported in one SVG. The converter already vendors the base
   Plotterfun app (`software/plotterfun_vendor/`) and hosts it in a
   QtWebEngine tab, so this variant can be added the same way if the artistic
   look fits better than a Python port.
3. **`serycjon/vpype-flow-imager` (GPL-3.0, Python)** has a documented
   `--cmyk` mode ("Split image to CMYK and process each channel", output layer
   numbering) and is the tool r/PlotterArt users describe as "Vpype - Image
   Flow, default CMYK". It is copyleft, so it stays an external CLI helper
   (the rule this repository already applies to GPL tools), not vendored code.

The community's default answer in r/PlotterArt threads is **DrawingBotV3**,
but its own README confirms CMYK separation is a **premium, closed-source**
feature. The free GPL-3.0 download is a workflow reference only.

Nothing relevant was found in **r/plotter** itself: the PullPush archive
returned zero matches for every CMYK/color-separation keyword tried, while a
control query (`pen`) returned data. The survey is therefore reported honestly
as "r/PlotterArt plus GitHub search".

Two further projects are close to the request but cannot be copied:
`KevLars/D2SCMYK` (Processing) is the closest output model - four
pre-separated images in, four G-code files plus PDFs out - but it has no
license file and is a fork/edit of the AGPL-3.0 Death to Sharpie code, so it
is ideas-only. `pywkt/plottter`'s Reddit post claims MIT and its feature list
includes CMYK separation with G-code/SVG/HPGL export, but the repository has
no LICENSE file on 2026-10-07; treat it as unverified until the author adds
one.

## Reuse assessment for this converter

Existing converter pieces that a CMYK feature can reuse unchanged:

- Pillow + NumPy image loading is already an established dependency
  (`generator_tabs/line_draw_tab.py`, `flow_field_tab.py`,
  `converter_core/kaleidoscope.py`).
- Fill styles already include `halftone` (fixed-pitch dots, radius follows
  tone) and `stipple` (blue-noise dots, density follows tone), so each CMYK
  channel can reuse an existing screening style.
- The **Layers** tool already splits artwork by pen color and plots one layer
  at a time, and **Path Prep** already sorts/merges paths.
- The theta cost model (`theta_resolver="rtheta"`, candidate axis cost across
  X, Y and A motor degrees) applies to every generated program without
  change. Cost efficiency for the XY-theta machine therefore carries over:
  each ink becomes one G-code program produced by the same pipeline, with the
  same cost-aware ordering, `M3`/`M5` tool contract and G4 dwell behavior.

New work required in every option is only the image-side separation and
screening: RGB -> CMYK(+GCR), per-channel gamma/threshold, dot pitch/style,
and a per-pen export step. Registration (one shared origin across the four
programs) is mechanical, and r/PlotterArt threads confirm pen micro-alignment
is the community's top failure mode for multicolor plots.

## Table A - permissive licenses, reusable in this converter

Tab-separated so rows can be pasted into a spreadsheet. Columns:
`project | author | license | what it produces | what to reuse | source | Reddit mention`.

```text
ohnorobo/cmyk-splitter	ohnorobo	MIT	RGB->CMYK with GCR + per-channel halftone-dot SVG, layered SVG export	separation math + dot screening to port into converter_core (Pillow/NumPy already used)	https://github.com/ohnorobo/cmyk-splitter	none found (GitHub search)
svenhb/plotterfun-color	svenhb (fork of mitxela/plotterfun)	MIT	Plotterfun algorithms run per CMYK channel; four path groups exported in one SVG	vendor as a CMYK variant of the existing Plotterfun tab	https://github.com/svenhb/plotterfun-color	https://www.reddit.com/r/PlotterArt/comments/1lhl3v6/help_regarding_cmyk_plots/ (comment mz88vve); https://www.reddit.com/r/PlotterArt/comments/k22vbp/ (comment gdrrmbl)
ClayFlannigan/halftone	ClayFlannigan	Apache-2.0	Python CLI: four CMYK raster images + combined image, halftone screen angles, GCR percentage	screen-angle/GCR parameter reference; feed per-channel rasters into existing halftone/stipple fills	https://github.com/ClayFlannigan/halftone	none found (GitHub search)
aacd164/HalftoneLab	Aaron Dey	MIT	Browser CMYK halftone artwork with misregistration/grain simulation	preview/registration idea reference (no vector export verified)	https://github.com/aacd164/HalftoneLab	none found (GitHub search)
danielpetho/cmyk-halftone-emulator	danielpetho	MIT	CMYK halftone visual emulator	visual reference only (emulation, not plot output)	https://github.com/danielpetho/cmyk-halftone-emulator	none found (GitHub search)
FelixHuber08/PenFlow	FelixHuber08	MIT	Tauri/Rust GRBL plotter app; 12-pen color separation from SVG stroke/fill colors; auto pick/drop G-code	multi-pen G-code and pen-slot sequencing reference (not raster CMYK)	https://github.com/FelixHuber08/PenFlow	none found (GitHub search)
```

## Table B - open source but copyleft (separate tool or license decision)

```text
serycjon/vpype-flow-imager	serycjon	GPL-3.0	vpype plugin; `--cmyk` splits the image into four consecutively numbered layers	run as external CLI to produce a 4-layer CMYK SVG feeding the Layers tool	https://github.com/serycjon/vpype-flow-imager	https://www.reddit.com/r/PlotterArt/comments/xfhmjv/12x18_cmyk_arteza_rollerballs_lion/ (comment iopwt0f)
ehufsted/HalftoneWebPAL	ehufsted	GPL-3.0	Browser halftoning app, 24 methods, "CMYK - 4 layers" option, Export SVG	external tool or a deliberate licensing decision; full source available	https://github.com/ehufsted/HalftoneWebPAL	https://www.reddit.com/r/PlotterArt/comments/1wmgaj1/penplotter_halftoning_25_styles_blackwhite_and/
drc-art/drc_halftone_cmyk	drc-art	GPL-3.0	Python printmaker CMYK separations with angle/frequency/dot-shape control	screening parameter reference (print, not plotter, output)	https://github.com/drc-art/drc_halftone_cmyk	none found (GitHub search)
The-Nils/LineMaker	The-Nils	GPL-3.0 LICENSE file (README claims MIT - conflict)	Web tools; HatchMaker CMYK channel separation for CNC pen plotting	external tool only until the license conflict is resolved; 100% AI-generated per repo description	https://github.com/The-Nils/LineMaker	https://www.reddit.com/r/PlotterArt/comments/1n6w4nd/just_finished_my_linemaker_project_for_cnc_pen/
SonarSonic/DrawingBotV3	Ollie Lansdell	GPL-3.0 free / CMYK premium closed	Image to vector art; CMYK separation documented but premium-gated	free app does not include CMYK; workflow reference only	https://github.com/SonarSonic/DrawingBotV3	https://www.reddit.com/r/PlotterArt/comments/16asp7t/cmyk_color_separation_inquiry_drawingbotv3/ ; https://www.reddit.com/r/PlotterArt/comments/10otonq/help_looking_for_resourcestools/ (comment j6kltaa)
```

## Table C - no license / unverifiable (ideas only, do not copy code)

```text
fcor/nib	fcor	no LICENSE file (checked 2026-10-07)	Browser image->lines app; mono / CMYK / Riso separation; layered SVG export	per-plate interleaving and free ink-color UX ideas	https://github.com/fcor/nib	none found (GitHub search)
KevLars/D2SCMYK	KevLars	no license (fork of AGPL Death to Sharpie)	Processing sketch: four pre-separated images -> four G-code files + four PDFs + preview	closest output model to this request; ideas only	https://github.com/KevLars/D2SCMYK	none found (GitHub search)
pywkt/plottter	pywkt	README says MIT; no LICENSE file at HEAD	Python desktop app; 33 generators; K-Means/Luminance/RGB/CMYK separation; SVG/HPGL/G-code export	strong feature overlap; verify license with the author before reuse	https://github.com/pywkt/plottter	https://www.reddit.com/r/PlotterArt/comments/1sodl3x/plottter_because_why_not/
schultek/CNC-Halftone-CMYK-Generator	schultek	no license, no README	Processing CMYK halftone generator for CNC	unverified; ideas only	https://github.com/schultek/CNC-Halftone-CMYK-Generator	none found (GitHub search)
leo-levin/halftones	leo-levin	no license	Image to CMYK halftone separations, raster/vector plates	unverified; ideas only	https://github.com/leo-levin/halftones	none found (GitHub search)
```

## Table D - closed source or commercial references

```text
DrawingBotV3 Premium	Ollie Lansdell	closed (premium tier)	The r/PlotterArt default CMYK workflow; exports separated layers	no code reuse; explains the community baseline and expected quality	https://drawingbotv3.com/ ; https://drawingbotv3.readthedocs.io/en/latest/cmyk.html	16asp7t, 1c9enbj, 1bvqsp0, 10otonq and many more
Adobe Photoshop CMYK separation + Inkscape	Adobe + community	commercial	Manual CMYK channel split, then vector/hatch per channel	workflow reference only	https://www.dirtalleydesign.com/blogs/news/cmyk-all-the-pens	https://www.reddit.com/r/PlotterArt/comments/16asp7t/cmyk_color_separation_inquiry_drawingbotv3/ (comment jz9llmz); 1lz3lqy (comment n33aut8)
rgb2cmyk.org	unknown	closed website	Upload image, download separated channel images	workflow reference only	https://www.rgb2cmyk.org/	https://www.reddit.com/r/PlotterArt/comments/iyfj94/ (comment g6cbdjn)
```

Also mentioned in the color-splitting thread but not a raster-CMYK tool: the
Inkscape `svgparts` extension (splits an existing SVG by color; the converter's
Layers tool already covers this) and `vpypeline.ayrep.fr` (web vpype with
`read --attribute stroke` layer separation).

## Why the reusable options are low-lift

`ohnorobo/cmyk-splitter` backend (read 2026-10-07):

- `backend/services/cmyk_splitter.py` - RGB -> CMY -> extract K as the pixel
  minimum, recompute CMY with GCR, return four `L`-mode images. Pure
  Pillow/NumPy; the docstring states it mimics ImageMagick's CMYK conversion.
- `backend/services/halftone_dots.py` - samples dark pixels and emits SVG
  circles (`divisor`, `dot_size`, `max_dots`). This maps directly onto the
  converter's existing `stipple`/`halftone` fills, which are already faster and
  tone-accurate.
- `backend/services/svg_combiner.py` - merges the four channel SVGs into one
  layered SVG, the same shape the Layers tool already consumes.

`svenhb/plotterfun-color` (`main.htm`, read 2026-10-07):

- Has an `...and K` checkbox (`id="cmyk"`, `modeK`) and converts the loaded
  image per channel (`applyFilter(0..3)`), then appends four path groups
  (`mainpath_c/m/y/k`) to one SVG and offers `Download SVG`.
- LICENSE is MIT (Copyright 2020 Tim Alex Jacobs / mitxela), so vendoring or
  porting keeps the existing Plotterfun attribution pattern.
- Live app: https://grbl-plotter.de/plotterfun-color/ (HTTP 200 on
  2026-10-07).

`serycjon/vpype-flow-imager` README documents `--cmyk` and the layer-numbering
scheme, including an example that writes a single `cmyk.svg` with four layers;
it is GPL-3.0 and last pushed 2022-12-04, so it is a stable external tool.

## Search log

Reddit live access:

- `https://www.reddit.com/r/plotter/search.json?q=cmyk&restrict_sr=1` ->
  HTTP 403; `https://old.reddit.com/r/plotter/search?q=cmyk` -> HTTP 302
  (redirect to the blocked endpoint). `api.pullpush.io` -> HTTP 200.

PullPush submission queries, `subreddit=plotterart`, `size=100` (unique
results returned):

- `cmyk` 85; `color separation` 7; `colour separation` 1; `four color` 7;
  `4 color` 29; `cyan magenta` 8; `multicolor` 11; `multiple pens` 16;
  `pen change` 54; `halftone` 13; `source code` 25; `github` blocked
  (HTTP 429 on all retries).

PullPush submission queries, `subreddit=plotter`, same keyword list: zero
results for every query. Control query `q=pen` returned data, so the index
exists; the archived r/plotter records carry implausible subscriber counts
(6-10), so this subreddit identity in PullPush appears tiny or partially
indexed. Direct live verification was impossible (403).

PullPush comment queries, `subreddit=plotterart`: `cmyk` 89;
`color separation` 26; `halftone` 23; `github` blocked (HTTP 429 on all
retries). Per-thread comment pulls (`link_id=t3_...`): 16asp7t 7 comments;
1hzrewv 16; 15trckx 3; 1lhl3v6 7; 10otonq 2; 15ctxs5 9; 1ff5bgt 5; 1duphl0
14; 102zxnm 4; 1sodl3x 5; 1n6w4nd and 1wmgaj1 returned none.

GitHub repository search (HTTP 200 unless noted):

- `cmyk plotter` total 3: ohnorobo/cmyk-splitter (MIT), fcor/nib (no
  license), nominmar/colspace (irrelevant).
- `cmyk gcode` total 1: KevLars/D2SCMYK (no license).
- `color separation plotter` total 1: FelixHuber08/PenFlow (MIT).
- `pen plotter cmyk` total 2: ohnorobo/cmyk-splitter, fcor/nib.
- `cmyk halftone` total 39 (permissive highlights: ClayFlannigan/halftone
  Apache-2.0; danielpetho/cmyk-halftone-emulator MIT; aacd164/HalftoneLab
  MIT).
- Later searches (`plotter color separation`, `cmyk svg separation`,
  `image cmyk plotter`, `cmyk inkscape`, `cmyk separation python`) were
  rate-limited (HTTP 403).

Repository metadata verified through the GitHub API and raw LICENSE/README
files on 2026-10-07 (license | language | last push):

- ohnorobo/cmyk-splitter: MIT | Python | 2026-02-26.
- svenhb/plotterfun-color: MIT | JavaScript | (fork of mitxela/plotterfun).
- ClayFlannigan/halftone: Apache-2.0 | Python | 2023-05-18.
- aacd164/HalftoneLab: MIT | HTML | 2026-06-03.
- danielpetho/cmyk-halftone-emulator: MIT | TypeScript | 2026-02-08.
- FelixHuber08/PenFlow: MIT | TypeScript/Rust | 2026-06-16.
- serycjon/vpype-flow-imager: GPL-3.0 | Python | 2022-12-04.
- ehufsted/HalftoneWebPAL: GPL-3.0 | JavaScript | 2026-09-13;
  ehufsted/HalftonePAL (predecessor): LGPL-2.1 | Processing | 2021-05-25.
- drc-art/drc_halftone_cmyk: GPL-3.0 | Python | 2026-02-23.
- The-Nils/LineMaker: GPL-3.0 LICENSE, README claims MIT | JavaScript |
  2026-03-20.
- SonarSonic/DrawingBotV3: GPL-3.0 free / premium closed | Java | 2025-10-08.
- fcor/nib: no LICENSE/LICENSE.md at HEAD; package.json has no license field |
  JavaScript | 2026-08-16.
- KevLars/D2SCMYK: no license file | Processing | 2021-02-16.
- pywkt/plottter: README says MIT; LICENSE, LICENSE.md and COPYING all 404 |
  Python | 2026-06-19.
- schultek/CNC-Halftone-CMYK-Generator: no license file, no README |
  Processing | 2016-07-11.
- leo-levin/halftones: no license file.

Source reads used for the capability claims: cmyk-splitter
`backend/services/cmyk_splitter.py` and `halftone_dots.py`;
plotterfun-color `main.htm` and `LICENSE`; DrawingBotV3 `README.md` (premium
feature list) and `docs/source/cmyk.rst`; HalftoneWebPAL `index.html`
(`CMYK - 4 layers` option); vpype-flow-imager `README.md`; nib `package.json`
and README; plottter README.

## Limits and gaps

- Reddit content could not be fetched live; permalinks are canonical archive
  URLs, not re-verified page contents.
- The `github` keyword queries for both subreddits were rate-limited (HTTP
  429), so a tool mentioned only in a comment that contains "github" but none
  of the other keywords may be missing. Thread comment pulls mitigate this
  for the CMYK-separation threads but do not close it.
- r/plotter produced no CMYK/multicolor content in the archive at all, and its
  archived subscriber counts look wrong; do not read that as proof the live
  subreddit has none.
- License classification is a 2026-10-07 snapshot; the LineMaker (GPL vs MIT)
  and plottter (README MIT vs no LICENSE file) conflicts need author contact
  before any reuse.
- No tool was executed or benchmarked; capabilities were verified by reading
  source and README files only. plotterfun-color's CMYK path is verified in
  source but not in a live plot; cmyk-splitter has no test suite in the tree.
- GitHub API rate limits cut off five repository searches after the queries
  listed above.

## Next step

Recommended build direction (needs the project owner's go-ahead before
implementation):

1. **Port the MIT separation core** from `ohnorobo/cmyk-splitter`
   (`cmyk_splitter.py` GCR math) into the converter's image pipeline, run the
   existing `halftone`/`stipple` fill per channel, and export one G-code
   program per ink through the existing Layers + theta-cost pipeline. This
   gives one G-code file per CMYK pen, keeps the XY-theta axis-cost
   requirement intact, and adds no new motion code.
2. **Optional artistic variant:** vendor `svenhb/plotterfun-color` (MIT) as a
   CMYK tab using the existing Plotterfun/QtWebEngine vendoring pattern.
3. **Optional external tool:** document `vpype-flow-imager --cmyk` as a
   GPL-safe CLI path that produces a 4-layer SVG the Layers tool can import.

Before building, confirm option 1 is the intended feature behavior (per-pen
G-code files, manual pen swaps, one shared origin) so the implementation and
its tests can be scoped in the same working session.
