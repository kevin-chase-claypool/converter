---
id: WSW-20261001-003
date: 2026-10-01
category: windows-software
affected_categories:
  - windows-software
status: implemented
components:
  - software/converter_core/generative.py
tags:
  - kaleidoscope
  - generative
  - style
related:
  - WSW-20261001-002
  - software/README.md
---

# Sparse ornaments: the bead, stud and dot rows stop carpeting the design

## Summary

Generated patterns no longer carpet every band with beads, stud flowers and
dotted rings. Those layers are ornaments, not structure, so they are now placed
at twice the pitch of the engraved hatching: the same seed draws roughly half
as many of them, and a band reads as a scatter with rhythm instead of printed
wallpaper. Nothing else about the design changed - the ring count, the shaded
shape families, the separators, the rim and the seed-to-structure mapping are
all as they were.

## Reason

Operator, with a crop of the bead and stud rows: "in the context of
kaleidoscope.bat i want to make this wallpaper-like imagery much more sparse.
right now it appears everywhere". The crop is a piece of a band whose nearest
neighbours are all beads and stud flowers, so the complaint is about the
*scatter* layers, not about the shaded leaf, lace, feather or mesh bands.

## Implementation

- `converter_core/generative.py`:
  - New module constant `ORNAMENT_PITCH = 2.0`, with a comment saying what it
    is for: a pitch multiplier for the ornament layers, 1.0 being the old busy
    spacing. It is the single sparsity knob for this look.
  - `_studs()` and `_dots()`, the two helpers that lay beads, stud flowers and
    dotted rings along an arc, divide their spacing by `ORNAMENT_PITCH`. Every
    caller inherits it: the decoration rows `random_pattern` puts between the
    shape rings, the stud and dot rows in `_rim()`, and the dot ring inside
    `_rosette()`.
  - `_beadrow()` - the shape family made of beads and stud flowers - uses the
    same pitch for its row pitch and its bead pitch, and caps its rows at
    `1 + level // 4` instead of `2 + level // 3`.
  - `_beadrow()` was already in the working tree uncapped from the branch head:
    its rows were lowered from one every 3.4 mm to one every 4.6 mm and each row
    was staggered and rotated off the previous one so the beads stop lining up
    into a printed grid. That edit is part of the same push against the
    wallpaper look, it is verified by the same checks below, and it is carried
    in this change rather than left dangling.
- `software/README.md`: the random-pattern section names the ornaments, the
  doubled pitch and the constant to turn if the operator wants a different
  density.

## Verification

- `python -m unittest` over all thirteen `software/tests` modules: 133 tests
  pass, including `test_generative.py` (determinism, wedge and radius
  contracts, every family still drawing inside its band at intricacy 1, 6 and
  10, and `test_top_intricacy_is_dense`) and `test_kaleidoscope.py`.
- Contour counts for the operator's own design (`kaleidoscope_settings.json`:
  seed 83382, intricacy 10, 4 divisions, no motifs): the wedge drops from 1,570
  to 906 contours across the 8 mirrored copies, i.e. 12,560 to 7,248 contours.
  Seed 7 at the same settings drops from 1,285 to 621 wedge contours; seed 42 at
  intricacy 5 drops from 419 to 299. The removed contours are the ornaments -
  path length falls only 11 % on the operator's seed (150,626 mm to 133,929 mm)
  because the shaded bands are untouched.
- Render check: the same band crop at pitch 1.0, 1.5, 1.8 and 2.0. 1.0 is the
  reported wallpaper; 2.0 leaves clear paper between the beads while the stud
  rows still read as a deliberate band, and the dotted rim border stays
  legible. Before and after at seed 7, intricacy 10 are kept as the local
  evidence `samples\preview\gen_ornament_pitch_before.png` and
  `samples\preview\gen_ornament_pitch_after.png`.
- `python tools\docs_index.py --write` and `--check` pass.

## Struggles and rejected approaches

- Changing `_density()` instead was rejected: it is the packing multiplier for
  the whole composition, so it also thins the contour hatching *inside* the
  leaves, scallops and feathers. That is a different look, and it is not what
  was reported.
- A pitch of 1.5 or 1.8 keeps the bands tidier but still leaves the beads
  reading as rows; 2.0 is the setting that answers "much more sparse".
- The earlier attempt at this look capped and staggered `_beadrow()` only, which
  left the stud and dot rows that `random_pattern` draws between *every* pair of
  shape rings untouched - they are why the imagery still "appeared everywhere".
  The shared pitch is what closes that gap.

## Risks and follow-up

- This is a taste knob, not an accuracy one. `ORNAMENT_PITCH` is the single
  number to move if the default is wrong in either direction.
- The ornaments that belong to a shape rather than to a band - lace scale eyes,
  the bead at the end of a starburst ray, and the two bead rings in `_tulip()` -
  are deliberately left at their drawn pitch.
- No UI control was added. If the density needs to be adjusted per design
  rather than for the project, the next step is a spin box next to `Region
  overlay`; that is a larger interface change than the report asked for.

## Files

- `software/converter_core/generative.py`: `ORNAMENT_PITCH`, `_studs()`,
  `_dots()`, `_beadrow()`.
- `software/README.md`: the random-pattern section describes the ornament
  pitch and the sparsity knob.
- `docs/project/ENGINEERING_LOG.md`: this session's entry.
