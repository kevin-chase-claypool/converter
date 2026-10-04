# r/plotterart terrain-shading projects — survey

Date: 2026-10-04

## Answer

Yes. r/plotterart has repeatedly surfaced open-source GitHub projects for
terrain-like shading, in two families:

1. **Literal terrain/contour tools** that turn an image (or elevation data)
   into topographic isolines. The closest to this project's "image tone is
   elevation" terrain fill are
   [rolandblok/FastMarchingTopoPlot](https://github.com/rolandblok/FastMarchingTopoPlot)
   (photo to topographic contours via the Fast Marching Method),
   [krummrey/contour-drawing](https://github.com/krummrey/contour-drawing)
   and its faster fork
   [JRButler/ContourTool](https://github.com/JRButler/ContourTool)
   (isolines from image-derived distance fields), and
   [pywkt/plottter](https://github.com/pywkt/plottter) (a desktop app whose
   image pipeline includes FMM "topographic & Edge Hug" contours). True
   elevation-data tools are also present:
   [anvaka/peak-map](https://github.com/anvaka/peak-map) and
   [axismaps/contours](https://github.com/axismaps/contours).
2. **Field/streamline/hatch tools** that solve the same tone-to-line problem
   without literal contours, e.g.
   [mitxela/plotterfun](https://github.com/mitxela/plotterfun),
   [msurguy/plotterfun-extended](https://github.com/msurguy/plotterfun-extended),
   [serycjon/vpype-flow-imager](https://github.com/serycjon/vpype-flow-imager),
   [anadi-mitra/Drawbot_image_to_svg](https://github.com/anadi-mitra/Drawbot_image_to_svg),
   [a-johanson/blender-screen-space-hatch-lines](https://github.com/a-johanson/blender-screen-space-hatch-lines),
   [SonarSonic/DrawingBotV3](https://github.com/SonarSonic/DrawingBotV3), and
   [LingDong-/linedraw](https://github.com/LingDong-/linedraw).

The single most relevant prior art for the Theta converter's current terrain
mode is FastMarchingTopoPlot: it uses exactly the brightness-as-elevation
idea, but solves it as an eikonal wave-speed problem and slices the travel-time
field into contours ("bright areas spread contours wide, dark areas compress
them"). Community threads also document the same dark-area overdraw problem
that this project hit, which is useful confirmation that the thinning pass is
addressing a known failure mode rather than a local quirk.

## Confidence and limits

- Reddit's own search endpoints returned **HTTP 403** from this network
  (`www.reddit.com/r/plotterart/search.json`, `api.reddit.com/...`), and the
  `r.jina.ai` proxy of the subreddit wiki also returned 403. Mentions were
  therefore enumerated through the **PullPush Reddit archive API**
  (`api.pullpush.io/reddit/search/{submission,comment}/?subreddit=plotterart&q=...`,
  HTTP 200 for the queries listed below). Permalinks are the canonical
  `reddit.com` URLs carried by the archived objects; their content could not
  be re-fetched live from this network on 2026-10-04.
- Every GitHub repository below was verified live with the GitHub API and its
  README read from `raw.githubusercontent.com` on 2026-10-04 (HTTP 200),
  except `sierramancia/marching-waves`, whose GitHub Pages demo exists but
  whose repository returns HTTP 404 (private, renamed, or deleted).
- PullPush archive coverage is not guaranteed complete, and the `q=github`
  submission and comment queries were rate-limited (HTTP 429). Comments that
  name a repository without linking it can therefore be missed; all links
  found in the successful searches are included.
- Star counts and push dates are the GitHub API values on 2026-10-04.

## Table A — terrain/contour projects mentioned in r/plotterart

| Project | What it does | r/plotterart mention | Verified |
|---|---|---|---|
| [rolandblok/FastMarchingTopoPlot](https://github.com/rolandblok/FastMarchingTopoPlot) | README: "Converts a photo to topographic contour lines using the Fast Marching Method — bright areas spread contours wide, dark areas compress them". Browser JS, Unlicense, 6 stars, pushed 2026-07-03. | ["ffm contour algo" post](https://reddit.com/r/PlotterArt/comments/1ubsahp/ffm_contour_algo_online_webbased_version_for_play/): "I ... created a web based contour plot generator ... [github code]". Also [comment](https://reddit.com/r/PlotterArt/comments/1w5sowm/moir%C3%A9_eel/p7imeu8/): "There are at least 3 web accessible implementations that I know of at this point (example: https://github.com/rolandblok/FastMarchingTopoPlot)". | API + README fetched; description matches the thread exactly. |
| [krummrey/contour-drawing](https://github.com/krummrey/contour-drawing) | README: "creates contour drawings from an image". Python, CC0-1.0, 2 stars, pushed 2025-11-05. | [Comment](https://reddit.com/r/PlotterArt/comments/1sgoj6r/question_for_the_plotter_community/ofc0sp5/): "i had my try at vibe coding it ... not polished in any way. but a start." Also [comment](https://reddit.com/r/PlotterArt/comments/1ook3yz/affection/nnb4kh0/): "it works OK, but has some artifacts in dark areas or where the distance fields collide". | API + README fetched. |
| [JRButler/ContourTool](https://github.com/JRButler/ContourTool) | README: "Geodesic contour extraction using fast marching method. Computes distance maps from source points and extracts isolines." C-accelerated fork of `krummrey/contour-drawing`. CC0-1.0, 1 star, pushed 2025-12-09. | [Comment](https://reddit.com/r/PlotterArt/comments/1ook3yz/affection/nt3773e/): "Has a C-accelerated Fast Marching library now for speed - 20-50x faster. Added a `smooth` flag and some other bits and pieces." | API + README fetched; README credits the original project. |
| [anvaka/peak-map](https://github.com/anvaka/peak-map) | README: "visualize elevation of any area on the map with filled area charts (also known as a ridgeline)", using MapBox elevation data. JS, MIT, 643 stars, pushed 2025-12-27. | [Comment](https://reddit.com/r/PlotterArt/comments/1i7o97x/the_emerald_isle_a3/m97sz0m/): "It seems like the same tool from the recent post about Washington state terrain maps: peak-map". Also [comment](https://reddit.com/r/PlotterArt/comments/1ff64po/milford_sound/lnh2ktp/): "Contour Generator or Peak Map are some basic terrain tools that can do similar stuff." | API + README fetched. |
| [axismaps/contours](https://github.com/axismaps/contours) | README: "Draws contour maps from terrain tiles, using d3-contour". MIT, 46 stars. | Mentioned by name ("Contour Generator") in the same [Milford Sound comment](https://reddit.com/r/PlotterArt/comments/1ff64po/milford_sound/lnh2ktp/); the linked [drawingbots.net tools page](https://drawingbots.net/knowledge/tools) identifies Contour Generator as contours.axismaps.com. Repo identified from that tool's owner/description. | API + README fetched; the Reddit comment names the tool but links the index, not the repo (inference noted). |
| [pywkt/plottter](https://github.com/pywkt/plottter) | README lists "contour lines", Fast Marching Method "topographic & Edge Hug contours", "Flow Field", and "3D Scene — Wireframe, hatched/shaded ... hidden line removal" from OBJ/STL meshes. Python, no license file, 27 stars, pushed 2026-06-19. | ["plottter - because why not" post](https://reddit.com/r/PlotterArt/comments/1sodl3x/plottter_because_why_not/): "i made this app for plotting and figured i'd share it ... [github link]". Also [comment](https://reddit.com/r/PlotterArt/comments/1t76xcp/volumeform_svg_generator/oknh69x/): "i have a plotter app (plottter) where you can import stl/obj files and then slice them". | API + README fetched. No license file means no reuse permission by default. |
| [piebro/plotting-maps](https://github.com/piebro/plotting-maps) | README: "create OpenStreetMap SVG maps to plot them with a pen plotter". MIT, 109 stars. | [Comment](https://reddit.com/r/PlotterArt/comments/t1u5p8/first_plot_of_my_hometown_with_a_diy_plotter/nakrfhp/): "here is a tool that can create svg line art of the maps from openstreetmap.org". | API + README fetched. Street maps only — no elevation/contours. |

## Table B — tone/field/streamline shading mentioned in r/plotterart

These do not draw literal terrain contours, but they solve the same
tone-to-line-density/shape problem and are the community's common answers when
someone asks how to shade a photo.

| Project | What it does | r/plotterart mention | Verified |
|---|---|---|---|
| [mitxela/plotterfun](https://github.com/mitxela/plotterfun) | README: "A collection of algorithms for turning images into vector art" (squiggle, stipple, linedraw, halftone, scan/weave families). MIT, 384 stars. | [Comment](https://reddit.com/r/PlotterArt/comments/1uunada/me_in_the_flow/ox4msx0/): "Github user msurguy crafted an 'extended version' of the well-known tool Plotterfun by mitxela. Here I've used the 'Flow Field' algorithm." Also [comment](https://reddit.com/r/PlotterArt/comments/1pz5fi1/ilona_marchv_contour_portrait_on_cricut_explore_4/nwrdna8/): "Plotterfun and DrawingBotV3 are two of the more popular ones." | API + README fetched. |
| [msurguy/plotterfun-extended](https://github.com/msurguy/plotterfun-extended) | README: "Plotterfun Extended turns images into SVG line art designed for pen plotters", 40 worker algorithms including **Flow Field** and **Contours**. 8 stars, pushed 2026-02-12. | The "Me in the Flow" [comment](https://reddit.com/r/PlotterArt/comments/1uunada/me_in_the_flow/ox4msx0/) links the author's GitHub profile (`github.com/msurguy`) and describes an "extended version" of Plotterfun with a Flow Field algorithm; the profile contains this repo, whose description matches. Indirect: the repo itself was not linked in the comment. | API + README fetched; provenance is the linked profile, so treat as high-probability identification rather than a direct link. |
| [serycjon/vpype-flow-imager](https://github.com/serycjon/vpype-flow-imager) | README: "vpype plug-in to convert images to flow field line art", Jobard–Lefer evenly spaced streamlines. GPL-3.0, 214 stars. | [Comment](https://reddit.com/r/PlotterArt/comments/1vjwxo9/trying_some_flow_streamline_rendering_techniques/p2p0ow7/): "Check out vpype flow imager". | API + README fetched. |
| [anadi-mitra/Drawbot_image_to_svg](https://github.com/anadi-mitra/Drawbot_image_to_svg) | Processing sketches with PFM_spiral, PFM_CrossHatch, PFM_IronFiling (non-overlapping flow fields) and PFM_FlowContours (Sobel-derived flow field). GPL-3.0, 2 stars. | [Comment](https://reddit.com/r/PlotterArt/comments/1r7xqhv/did_some_postcard_size_plots/o63c3h7/): "here is my code, I have been working so much with the 'Flow Field PFM'"; also recommended in [comment](https://reddit.com/r/PlotterArt/comments/1r4jslf/my_diy_plotter_completed_now_what/o7utqr0/). | API + README fetched. |
| [a-johanson/blender-screen-space-hatch-lines](https://github.com/a-johanson/blender-screen-space-hatch-lines) | README: "draws different screen-space shading effects of the scene as Grease Pencil v3 strokes ... evenly spaced hatch lines, stipples ... and scribbling", luminance-driven; Jobard–Lefer 1997 streamlines and Poisson-disk stippling. MIT, 26 stars. | ["Update on 3D -> 2D mesh projection" post](https://reddit.com/r/PlotterArt/comments/1r1qnzw/update_on_3d_2d_mesh_projection/): "Thanks to u/mediocre-mind2 ... Please check out their blender add-on". | API + README fetched. |
| [nclslbrn/forsaken-ideas](https://github.com/nclslbrn/forsaken-ideas) | JavaScript sketchbook; the linked `fillShape.js` walks vectors and keeps points whose gray value falls in a band (threshold hatching). MIT, 6 stars. | [Comment](https://reddit.com/r/PlotterArt/comments/1lakywh/mixed_and_diluted_inks/mxydfw5/): "I have a source image with different shades of gray ... only keep the points when the gray value is between 0 and 10. Here is the JavaScript function". | API + README fetched; the cited behavior is in the linked source file. |
| [somebox/plotter](https://github.com/somebox/plotter) | README: "Fill/shading support for closed paths (hatch, crosshatch, dots) with brightness-based density"; tools include Perlin landscapes and map conversion. 1 star. | [Comment](https://reddit.com/r/PlotterArt/comments/1sajip6/messing_with_images_lines_and_shapes/odwr7e5/): "source is open ... tools/drawbot_squiggle.py". | API + README fetched. |
| [SonarSonic/DrawingBotV3](https://github.com/SonarSonic/DrawingBotV3) | README: image-to-vector art with "Sketch Flow Field", "Streamlines Edge Field", "Streamlines Flow Field", plus hatch/sawtooth/circular-scribble pens. GPL-3.0, 523 stars. | [Comment](https://reddit.com/r/PlotterArt/comments/1ukfu3l/portrait/ouwuwrv/): "Check out drawingbot"; also [comment](https://reddit.com/r/PlotterArt/comments/1ks7jwl/how_can_i_draw_this_image_exactly_exactly_like/mtj7xd7/). | API + README fetched. |
| [LingDong-/linedraw](https://github.com/LingDong-/linedraw) | README: "Convert images to vectorized line drawings for plotters ... Contour-only or hatch-only modes", sketchy style via Perlin noise. MIT, 865 stars. | [Comment](https://reddit.com/r/PlotterArt/comments/1so34zu/just_plottet_my_first_portraits/ogq8nkg/): "The base was that one: https://github.com/LingDong-/linedraw". | API + README fetched. |
| [will-r-chase/aRt](https://github.com/will-r-chase/aRt) | R generative-art repository; months dedicated to procedural noise and flow fields with curl noise and particles. 213 stars. | [Comment](https://reddit.com/r/PlotterArt/comments/wja2fq/eggstacular_perlin_flow_fields_wip_3n/itek071/): "I used R to generate the fields based off of Will R Chase's tutorial". | API + README fetched. |
| [korovyev/quaranteen](https://github.com/korovyev/quaranteen) | Swift "Vector Flow Field generator, applying Perlin Noise", outputs plotter path text. 4 stars. | [Comment](https://reddit.com/r/PlotterArt/comments/fv0dkr/amusing_myself_during_quarantine/fmi31vt/): "I threw my code up here too if you want a look (swift)". | API + README fetched. |
| [msurguy/flow-lines](https://github.com/msurguy/flow-lines) | SVG flow-line/streamline generator (now hosted on drawingbots.com). 169 stars. | Indirect: author profile linked in the "Me in the Flow" [comment](https://reddit.com/r/PlotterArt/comments/1uunada/me_in_the_flow/ox4msx0/), and the tool is listed in awesome-plotters, which is linked in the subreddit. | API + README fetched. |
| [fogleman/ln](https://github.com/fogleman/ln) and [RobMakesThings/Viewport.js](https://github.com/RobMakesThings/Viewport.js) | 3D line-art engines with hidden-line removal (Go / JS) used to render relief-like 3D scenes as SVG. MIT; 3,445 and 19 stars. | ["Announcing Viewport.js" post](https://reddit.com/r/PlotterArt/comments/1rni21y/two_pieces_and_a_new_plotter_art_library/): "I ported an old Go library called ln"; also [comment](https://reddit.com/r/PlotterArt/comments/1rz3ckd/plotting_stereoscopic_images_from_procedural_3d/obizk22/) and [comment](https://reddit.com/r/PlotterArt/comments/1t0jn2g/3d_renderer_finally_works/ojf4hhw/). | API + README fetched. |
| [beardicus/awesome-plotters](https://github.com/beardicus/awesome-plotters) | Curated index of plotter tools; its map/terrain entries include Peak Map and Flow Lines. CC0, 1,462 stars. | [Comment](https://reddit.com/r/PlotterArt/comments/1rheaj8/trying_to_get_into_plotter_art_what_are_some_must/o7z19cp/): the whole comment is the link; also recommended repeatedly. | API + README fetched. |

## Mentioned but not GitHub (or not verifiable)

- **Contour-V STUDIO / VEX Engine** — the closed-source tool behind many of the
  subreddit's contour portraits; distributed via ko-fi, not GitHub. See the
  ["A few people here asked..." post](https://reddit.com/r/PlotterArt/comments/1snzzck/a_few_people_here_asked_what_i_use_for_these/)
  and [Volume/Form post](https://reddit.com/r/PlotterArt/comments/1t76xcp/volumeform_svg_generator/).
- **AxidrawControl V2** (Grasshopper plugin) — food4rhino, not GitHub; used in
  the ["some random terrain" post](https://reddit.com/r/PlotterArt/comments/1eq69np/some_random_terrain_i_generated_and_plotted_while/).
- **Anaglyph isobands terrain** — an Observable notebook by Tony Chu, cited as
  the source for perspective/3D-obscured contour terrain in
  [comment](https://reddit.com/r/PlotterArt/comments/1fz4l6h/topographic_map_with_pen_and_paintbrushes/lqzyha0/)
  and [comment](https://reddit.com/r/PlotterArt/comments/1ff64po/milford_sound/lmzmyiz/).
  Observable is not GitHub.
- **Marching Waves** — the [GitHub Pages demo](https://sierramancia.github.io/marching-waves/)
  is cited in the ["Interference" post](https://reddit.com/r/PlotterArt/comments/1qfd27h/interference/),
  but the corresponding repository returns HTTP 404 as of 2026-10-04.
- **carriebennette** — the artist links their GitHub profile in
  [comment](https://reddit.com/r/PlotterArt/comments/1fz4l6h/topographic_map_with_pen_and_paintbrushes/lqzyha0/)
  but states the terrain code is not published.
- **DEM/Blender/Maya workflows** — USGS DEM plus Blender Freestyle or custom
  Maya scripts are described in several terrain threads (e.g.
  [comment](https://reddit.com/r/PlotterArt/comments/n3yyt7/perspective_contours_easter_island/gwte1n3/),
  [comment](https://reddit.com/r/PlotterArt/comments/1fbonf3/stowe_vt_contours/lm3o8vd/)),
  but no repository is published there.

## Implications for this project's terrain fill

1. **FastMarchingTopoPlot is the closest published analogue of the current
   image-tone terrain mode.** Its parameterization (wave seed, gamma, number of
   contour lines, skip-transparent) is worth comparing against our
   `Fill spacing` / `Terrain size` / separation pass. Reading its source is a
   cheap way to sanity-check our dark-region behavior.
2. **The dark-area overdraw is a known community artifact.** The
   `contour-drawing` author explicitly reports "artifacts in dark areas or
   where the distance fields collide"; our minimum-gap separation pass and
   ContourTool's smoothing flag are two answers to the same failure.
3. **Two different input families exist.** Peak Map and axismaps/contours
   contour *real elevation data*; FastMarchingTopoPlot, contour-drawing, and
   linedraw contour *image luminance*. Our current mode is in the second
   family; a "proper terrain" look from actual DEM data would be a new input
   path, not a tweak to the existing filter.
4. **Flat-area alternatives** the subreddit recommends when contours alone
   look empty: stippling (Plotterfun/StippleGen), brightness-banded hatching
   (forsaken-ideas `fillShape`, linedraw hatch mode), and streamline shading
   (vpype-flow-imager, DrawingBotV3, the Blender hatch add-on).
5. **Licensing:** FastMarchingTopoPlot is Unlicense, contour-drawing and
   ContourTool are CC0, peak-map/axismaps/contours/plotterfun/linedraw are MIT.
   `pywkt/plottter` has no license file, so its code should be treated as
   all-rights-reserved reference material, not a source to copy.

## Search log

Reddit access:

- `https://www.reddit.com/r/plotterart/search.json?q=terrain&restrict_sr=on...`
  → HTTP 403 (network block page).
- `https://api.reddit.com/r/plotterart/search?q=terrain...` → HTTP 403.
- `https://old.reddit.com/r/plotterart/search.json?...` → HTTP 302, empty body.
- `https://r.jina.ai/https://www.reddit.com/r/plotterart/wiki/index` → HTTP
  200 wrapper containing Reddit's 403 block page.
- PullPush archive, submissions (`api.pullpush.io/reddit/search/submission/?subreddit=plotterart&q=<term>&size=100`):
  `terrain`, `topographic`, `topography`, `contour`, `contours`, `elevation`,
  `heightmap`, `hillshade`, `shading`, `hatch`, `hatching`, `flow field`,
  `perlin`, `dem`, `srtm` → HTTP 200; `noise`, `map`, `github` → HTTP 429
  (rate limit, not retried successfully).
- PullPush archive, comments
  (`api.pullpush.io/reddit/search/comment/?subreddit=plotterart&q=<term>&size=100`):
  `github.com`, `terrain`, `topographic`, `heightmap`, `contour`, `shading`,
  `hatch`, `perlin`, `plotterfun` → HTTP 200; `github` → HTTP 429.
- Additional page fetches: `https://drawingbots.net/knowledge/tools` (HTTP
  200; used to resolve the Contour Generator name to contours.axismaps.com).

GitHub verification:

- Repository metadata and READMEs fetched via `api.github.com/repos/...` and
  `raw.githubusercontent.com/<owner>/<repo>/HEAD/README.md` on 2026-10-04.
  All repositories in the tables returned HTTP 200; `sierramancia/marching-waves`
  returned HTTP 404.
- Search queries used for follow-up identification:
  `https://api.github.com/search/repositories?q=contour+generator+plotter`
  and `?q=contour-generator+in:name` (both HTTP 200).

## Not found / gaps

- No r/plotterart post or comment was found that links a dedicated
  *fractal-noise terrain shading* library beyond the flow-field/Perlin tools
  above; most Perlin discussion is about flow fields, not contour relief.
- The `q=github` searches that would catch repository names without URLs were
  rate-limited, so a comment that only says "my repo is <name>" without a URL
  could have been missed. The `github.com` comment search (HTTP 200) captured
  every comment containing a GitHub URL.
- Live Reddit content could not be re-fetched from this network; permalinks
  are canonical but were verified through the archive API only.
