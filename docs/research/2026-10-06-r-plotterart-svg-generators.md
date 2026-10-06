# r/plotterart SVG generators — open-source shortlist

Date: 2026-10-06

## Answer

r/plotterart has produced or repeatedly recommended a large family of
SVG-generating tools. Filtering the survey down to code that can legally be
reused in this converter leaves **35 projects under permissive licenses**
(MIT, Unlicense, CC0, and one public-domain-style JS tool) — these are safe to
copy, port, vendor, or adapt with attribution. Another **14 open-source
projects are GPL/AGPL**, so they can only be used as separate command-line
programs (at arm's length) or after a deliberate licensing decision for this
repository. Everything else found either has **no license** (ideas only, no
code reuse) or is **closed-source** (usable only as a separate application).

The single most valuable families for this converter are:

1. **Image → line/shade fills** — SquiggleCam (MIT), Plotterfun (MIT),
   linedraw (MIT), SquiggleDraw (Unlicense), contour-drawing / ContourTool
   (CC0), FastMarchingTopoPlot (Unlicense), and the vpype plugin family
   (mostly MIT).
2. **Path preparation and cleanup** — vpype (MIT), occult (MIT),
   deduplicate (MIT), vpype-vectrace (MIT), vpype-pixelart (MIT), and
   Svg-Layer-Painter (MIT).
3. **Generators and 3D** — substitution-system (MIT), cadin's Unlicense
   Processing tools, Viewport.js (MIT), fogleman/ln (MIT), and the Blender
   screen-space hatch add-on (MIT).
4. **Maps and terrain** — plotting-maps (MIT, already vendored as the Maps
   tab), anvaka/city-roads (MIT), peak-map (MIT), and axismaps/contours (MIT).

**UI decision: do not create `converter2.bat`.** The current converter is a
single window with a scrollable sidebar of collapsible settings groups, a live
OpenGL preview with playback and fit/clip controls, and a G-code command list;
the Kaleidoscope app already hosts a `QTabWidget` with a vendored web app in
its Maps tab. The weight is in the engine modules, not the UI layout, and the
settings are built from one data-driven source (`TEXT_FIELD_GROUPS` /
`CHECKBOX_FIELDS`), so new generator features can be added as new fill
patterns or as a new tab using the existing pattern. A second application
would duplicate the GUI and split maintenance. See "UI assessment" below for
the evidence.

## License rule used for the filter

This repository has no root `LICENSE` file (the only license file is the
vendored MIT `software/plotting_maps/LICENSE`), so the converter defaults to
all rights reserved. Therefore:

- **Permissive** (MIT, Unlicense, CC0, BSD, Apache): code may be copied,
  ported, vendored, or adapted, preserving the license text and attribution.
- **Copyleft** (GPL, AGPL): do not import or copy modules into the app.
  Invoke them as separate installed programs (subprocess / CLI) or accept the
  license for the whole work before linking code.
- **No license**: read the algorithm for ideas only; do not copy code.
- **Closed source**: feature reference only.

Every repository below was checked live on 2026-10-06: GitHub API metadata
(HTTP 200), or for repositories discovered late, `raw.githubusercontent.com`
license files plus the GitHub page. The full search log and limits are at the
end.

## Table A — permissive licenses, usable in the converter

Tab-separated so rows can be pasted into a spreadsheet. Columns:
`project | author | license | what it generates | feature to bring | source |
r/plotterart mention`.

```text
SquiggleCam	u/msurguy (Maks Surguy)	MIT	image to squiggle/scribble SVG in the browser	squiggle image fill	https://github.com/msurguy/SquiggleCam	https://reddit.com/r/PlotterArt/comments/l9go0y/plowing_powder_glass_using_squigglecam/
Plotterfun	mitxela	MIT	image to vector art: squiggle, linedraw, halftone, scan, weave	fill algorithm family	https://github.com/mitxela/plotterfun	https://reddit.com/r/PlotterArt/comments/15ctxs5/photo_plot/jtyxofj/
linedraw	LingDong-	MIT	image to contour/hatch/Perlin line drawings	linedraw fill	https://github.com/LingDong-/linedraw	https://reddit.com/r/PlotterArt/comments/1nkmeym/pen_plot_from_photo_hibiscus_flower/
flow-lines	u/msurguy	MIT	flow-field SVG polylines	flow-field fill	https://github.com/msurguy/flow-lines	https://reddit.com/r/PlotterArt/comments/1uunada/me_in_the_flow/ox4msx0/
SquiggleDraw	gwygonik	Unlicense	image brightness to sine-wave SVG lines	sine-wave fill	https://github.com/gwygonik/SquiggleDraw	https://reddit.com/r/PlotterArt/comments/heicg5/chief/fvt6ovj/
vpype	abey79	MIT	SVG CLI: merge, sort, reloop, squiggle, hatch, crop; plugin host	path prep engine	https://github.com/abey79/vpype	https://reddit.com/r/PlotterArt/comments/1hog742/a_single_line_plotted_with_a_bic_cristal_pen/m4dngmq/
vsketch	abey79	MIT	Python generative plotter-art environment	generator authoring surface	https://github.com/abey79/vsketch	https://reddit.com/r/PlotterArt/comments/1k0wgyo/luminets_black_hole/mnhf1ee/
vpype-pixelart	abey79	MIT	pixel-art plotting fill	pixel fill	https://github.com/abey79/vpype-pixelart	https://reddit.com/r/PlotterArt/comments/1aocrvc/hi_all_does_anyone_use_vpype_can_anyone_please/kq1cmx2/
vpype-vectrace	tatarize	MIT	bitmap vector tracing plugin	vector trace fill	https://github.com/tatarize/vpype-vectrace	https://reddit.com/r/PlotterArt/comments/1mbl2b6/seeking_source_to_convert_sketch_to_vector_paths/n5t35w4/
occult	LoicGoulefert	MIT	hidden-line removal for SVG	occlusion cleanup	https://github.com/LoicGoulefert/occult	https://reddit.com/r/PlotterArt/comments/1iklga3/joining_the_club/mbn9v17/
deduplicate	LoicGoulefert	MIT	remove overlapping/duplicate SVG lines	overdraw cleanup	https://github.com/LoicGoulefert/deduplicate	https://reddit.com/r/PlotterArt/comments/1fkk0fd/paper_problem/lo3ci08/
contour-drawing	krummrey	CC0	image to contour drawings	terrain fill	https://github.com/krummrey/contour-drawing	https://reddit.com/r/PlotterArt/comments/1sgoj6r/question_for_the_plotter_community/ofc0sp5/
ContourTool	JRButler	CC0	C-accelerated geodesic contour extraction	terrain fill speed/smoothing	https://github.com/JRButler/ContourTool	https://reddit.com/r/PlotterArt/comments/1ook3yz/affection/nt3773e/
FastMarchingTopoPlot	u/rolandinoman (Roland Blok)	Unlicense	photo to topographic contours (Fast Marching, browser)	terrain fill upgrade	https://github.com/rolandblok/FastMarchingTopoPlot	https://reddit.com/r/PlotterArt/comments/1ubsahp/ffm_contour_algo_online_webbased_version_for_play/
plotting-maps	u/piebroo	MIT	OpenStreetMap to SVG maps	maps tab (already vendored)	https://github.com/piebro/plotting-maps	https://reddit.com/r/PlotterArt/comments/18fzild/a_tool_to_easily_create_openstreetmap_svg_maps_to/
substitution-system	u/piebroo	MIT	substitution-system generative art	generator motifs	https://github.com/piebro/substitution-system	https://reddit.com/r/PlotterArt/comments/1ag9prf/generative_art_using_a_substitution_system/
factorio-blueprint-visualizer	u/piebroo	MIT	Factorio blueprints to artful SVG	niche import/generator	https://github.com/piebro/factorio-blueprint-visualizer	https://reddit.com/r/PlotterArt/comments/1f0mn4m/plotting_factorio_maps/ljz922q/
generative-noodles	u/cadinb	Unlicense	Processing generative noodle sketch	organic generator	https://github.com/cadin/generative-noodles	https://reddit.com/r/PlotterArt/comments/18f9ozu/video_how_i_create_generative_art_for_the_axidraw/kct7woy/
line-wobbler	u/cadinb	Unlicense	hand-drawn wobble for vector lines	pen realism	https://github.com/cadin/line-wobbler	https://reddit.com/r/PlotterArt/comments/1tmewdb/multilayer_moire_stenography/onmp0g9/
plotter-text	u/cadinb	Unlicense	monoline SVG text system	single-stroke text	https://github.com/cadin/plotter-text	https://reddit.com/r/PlotterArt/comments/18w8xol/video_creating_a_system_for_dynamic_plottable/
plotter-canvas	u/cadinb	Unlicense	Processing canvas with SVG/PNG save	sketch template	https://github.com/cadin/plotter-canvas	https://reddit.com/r/PlotterArt/comments/1b5s9c7/video_a_flexible_canvas_for_plotter_art_projects/
plotter-postcard	u/cadinb	Unlicense	plottable PTPX postcard layouts	layout generator	https://github.com/cadin/plotter-postcard	https://reddit.com/r/PlotterArt/comments/1hgfhip/processing_project_generate_plottable_layouts_for/
snowflake	vishnubob	MIT	snowflake generator	seasonal generator	https://github.com/vishnubob/snowflake	https://reddit.com/r/PlotterArt/comments/kh719p/plotted_some_christmas_gift_wrap_decoration/ggqgmg5/
p5.js-svg	zenozeng	MIT	SVG runtime for p5.js	JS generator bridge	https://github.com/zenozeng/p5.js-svg	https://reddit.com/r/PlotterArt/comments/13qh4h5/which_version_of_processing_should_i_learn_if_i/jlfuj5y/
Viewport.js	u/mastaginger	MIT	3D scenes to SVG vector renderer	3D import/fill	https://github.com/RobMakesThings/Viewport.js	https://reddit.com/r/PlotterArt/comments/1rni21y/two_pieces_and_a_new_plotter_art_library/
ln	fogleman	MIT	3D line-art engine (Go)	3D reference engine	https://github.com/fogleman/ln	https://reddit.com/r/PlotterArt/comments/1rni21y/two_pieces_and_a_new_plotter_art_library/
blender-screen-space-hatch-lines	a-johanson	MIT	Blender hatch/stipple/scribble shading	shading styles	https://github.com/a-johanson/blender-screen-space-hatch-lines	https://reddit.com/r/PlotterArt/comments/1r1qnzw/update_on_3d_2d_mesh_projection/
cnc-text-tool	u/msurguy	MIT	single-stroke text inserted into SVG	text tool	https://github.com/msurguy/cnc-text-tool	https://reddit.com/r/PlotterArt/comments/1bj55rz/uuna_tek_iauto_pen_plotter/lrpax1d/
harmonograph	ttencate	MIT	harmonograph curves to SVG	spiro/harmonograph generator	https://github.com/ttencate/harmonograph	https://reddit.com/r/PlotterArt/comments/q22toc/cats/hfkuu4r/
city-roads	anvaka	MIT	city road networks to SVG	maps	https://github.com/anvaka/city-roads	https://reddit.com/r/PlotterArt/comments/1tje6gu/babys_first_plot/on1vs93/
peak-map	anvaka	MIT	elevation ridgeline art	terrain	https://github.com/anvaka/peak-map	https://reddit.com/r/PlotterArt/comments/1i7o97x/the_emerald_isle_a3/m97sz0m/
contours	axismaps	MIT	contour maps from terrain tiles	terrain	https://github.com/axismaps/contours	https://reddit.com/r/PlotterArt/comments/1ff64po/milford_sound/lnh2ktp/
Svg-Layer-Painter	jdbrande	MIT	split/recolor SVG layers	for multi-pen prep	https://github.com/jdbrande/Svg-Layer-Painter	https://reddit.com/r/PlotterArt/comments/1taovwv/adding_color_to_a_single_color_svg_file/
forsaken-ideas	nclslbrn	MIT	brightness-banded hatching (fillShape.js)	hatch fill	https://github.com/nclslbrn/forsaken-ideas	https://reddit.com/r/PlotterArt/comments/1lakywh/mixed_and_diluted_inks/mxydfw5/
PlotterArt	Sunil2198	MIT	Processing plotter/laser art sketches	generator sketches	https://github.com/Sunil2198/PlotterArt	https://reddit.com/r/PlotterArt/comments/1lpruuv/grab_the_code_for_this_one/
```

Notable feature coverage: the app already owns terrain, sine-gradient,
halftone/stipple, and hatch fills plus a kaleidoscope generator, so the
highest-value gaps Table A closes are **SquiggleCam/SquiggleDraw squiggles**,
**linedraw/Plotterfun image-to-line styles**, **flow fields** (port
`flow-lines` or invoke the GPL `vpype-flow-imager` externally), **vpype path
preparation**, **3D-to-SVG**, and **monoline text**.

## Table B — open source but copyleft (separate tool or license decision)

```text
vpype-flow-imager	serycjon	GPL-3.0	image to flow-field SVG plugin for vpype
DrawingBotV3	SonarSonic	GPL-3.0	image to vector art, many sketch algorithms
Drawbot_image_to_svg	anadi-mitra	GPL-3.0	PFM spiral, crosshatch, iron filing, flow contours
plotter-hacks	maxf	GPL-3.0	Textorizer, boids, celtic knots and other web generators
urpflanze core	urpflanze-org	GPL-3.0	recursive 2D shapes with browser/Node SVG output
GRBL-Plotter	svenhb	GPL-3.0	plotterfun-color image to SVG plus GRBL control
StippleGen	evil-mad / Shornone	GPL-2.0	stipple and TSP art from images
HalftonePAL	ehufsted	GPL	Java halftoning program that saves SVG
Drawbot_image_to_gcode_v2	Scott-Cooper	AGPL-3.0	DrawBot image to G-code variants
factorio-cli	drawscape-labs	GPL	Factorio data to SVG CLI
Makelangelo-software	MarginallyClever	GPL-3.0	plotter control with built-in art generators
py5	py5coding	GPL	Processing for Python (generator authoring)
inkscape-centerline-trace	fablabnbg	GPL	stroke centerline tracing (avoids double outlines)
Python-Pillow-Scripts	itsMohammedThaier	AGPL-3.0	dotter, liner, fractal image filters
```

These are still useful: vpype as a CLI already installed by the user, DrawingBot
as a separate converter, `vpype-flow-imager` as an optional external command,
and the rest as feature references. None should be imported into this
unlicensed application without a licensing decision.

## Table C — no license found (ideas only, do not copy code)

SquiggleCam-adjacent and image tools: `msurguy/plotterfun-extended`,
`mikeemoo/plotted` (Waves / Photo Spirals), `blnkhz/plotter-tools` (ordered
dithering + 3D slicer), `laserpilot/SongPlotter`,
`laserpilot/font-ozempic`, `laserpilot/Pen-Plotter-Calibration`,
`pywkt/plottter`, `malvarezcastillo/txt2plotter`, `somebox/plotter`,
`bbaudry/swart-studio`, `piebro/plotting-ribbons`,
`piebro/plotting-architecture`, `eshatkeinensinn/Truchet-Hexagon`,
`mkarliner/BelshazzarClock`, `Moishe/pyplot`, `vishnubob/pontiff`,
`hapiel/Genuary-2022`, `joshwcomeau/tinkersynth`, and
`The-Nils/LineMaker` (GPL-3.0, so Table B rules apply).

Standalone sites without a reusable license: Curveforge, Serpentine
(Jawhar Kodadi Labs), andysdesigns.github.io/art, mikeemoo `plotted`,
jeromegautier.info/lab, and Paragraphic.

## Table D — closed-source generators mentioned in the sub

Contour-V / VEX Engine (u/Left-Excitement3829; sold via ko-fi), Continuo
(u/rafzan; free app, no source found), GD Studio (u/freddievn / Synendo; paid
macOS app; its Plotter Hub server is separately open source), Grimstache's
Harmonograph Maker / Sacred Geometry Maker / Trochoid Maker (App Store),
Drawscape (commercial map/QR SVG service), Turtletoy (closed web IDE), and
Volume/Form (a request thread, not a released tool).

## UI assessment — why `converter2.bat` is not justified

Evidence from the current code:

- `converter.bat` is a three-line launcher; a second `.bat` would only select a
  second GUI script.
- `software/qt_svg_to_gcode.pyw` is one `QMainWindow` with a three-pane
  splitter: a scrollable sidebar of collapsible settings groups (Geometry,
  Fill, Motion, Machine, Theta kinematics, Pen, Preview settings), the
  OpenGL preview with playback and fit/fill controls, and the G-code command
  list. Only Geometry/Fill/Motion start expanded; every field has a tooltip,
  and stale-preview and clip warnings are already handled next to the preview.
- Settings are data-driven from `TEXT_FIELD_GROUPS` and `CHECKBOX_FIELDS` in
  the core, so a new "Generators" group does not need a new window or a new
  layout.
- `software/qt_kaleidoscope.pyw` already has a `QTabWidget` with a Maps tab
  embedding a vendored web app, which is the proven pattern for adding
  browser-based generators without touching the converter layout.
- The heaviness is in the engine modules (`geometry.py` 93 KB,
  `kinematics.py` 48 KB, `generative.py` 46 KB, GUI 3.1k lines), not in UI
  clutter. A second app would duplicate the GUI and split maintenance, which
  the repository working agreement explicitly discourages.

Recommended integration order (no new app):

1. Add one permissive Python-portable algorithm as a new Fill pattern
   (recommended first: `linedraw` or `SquiggleDraw`), with tests.
2. Add a "Generators" tab to the Kaleidoscope app that vendors one MIT web
   tool (recommended first: SquiggleCam) using the existing Maps-tab pattern,
   plus an "Export SVG then open in converter" action.
3. Add optional external-CLI support for vpype (MIT) for path preparation;
   keep GPL tools (DrawingBotV3, vpype-flow-imager) as separate installs the
   user runs outside the app.

This is recorded as a roadmap task; the proof integration should be one tool
end-to-end before more are added.

## Search log

- Reddit's own JSON/search endpoints are blocked from this network (HTTP 403,
  as in the 2026-10-04 terrain survey). Discovery therefore used the PullPush
  Reddit archive API.
- Full submission crawl: `api.pullpush.io/reddit/search/submission/` with
  `subreddit=plotterart`, 100 per page, newest → oldest: 5,745 rows,
  5,570 unique submissions, coverage 2018-01-26 → 2026-10-03.
- Comment keyword queries (each paginated): `svg` (988 unique),
  `github.com` (404), `my code` (373), `source code` (86),
  `svg generator` (23). The `github` query and later queries hit sustained
  HTTP 429/400 rate limits and were stopped; comment coverage is therefore
  partial. This is the main limitation.
- Candidate tools were cross-checked against every outbound URL in the
  crawled submissions and the successful comment queries (603 unique comment
  URLs, 474 unique submission URLs).
- Live verification: 49 repositories through the GitHub API (all HTTP 200),
  28 + 18 additional repositories through raw LICENSE files and GitHub pages,
  and 40 standalone sites fetched (all 200 except `svgstud.io` and
  `ejkaplan.com`, which failed to connect, and several JavaScript-only pages
  whose titles are rendered client-side).
- License classification used the repository LICENSE file first; "no license
  found" means no LICENSE/COPYING file at the repository root on 2026-10-06.

## Limits and gaps

- Reddit content could not be fetched live; mention permalinks are canonical
  archive URLs, not re-verified page contents.
- Comment coverage is partial because PullPush rate-limited the remaining
  keyword queries; a tool mentioned only in an unqueried comment thread could
  be missing.
- The no-license list is a legal default, not a statement that the author
  refuses reuse; asking the author for a license is a valid follow-up.
- GPL/AGPL classification is based on the LICENSE file, not a legal review of
  subprocess/aggregation boundaries.

## Next step

Pick the first proof integration from Table A. The smallest end-to-end win is
**linedraw as a new Fill pattern** (Python, MIT, image-to-line family already
familiar to this converter), or **SquiggleCam as a vendored Generators tab**
(MIT, browser tool, matches the existing Maps-tab pattern). Do not fork the
UI into `converter2.bat`.
