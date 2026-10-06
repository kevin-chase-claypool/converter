# Path Prep tab - third-party notice

The Path Prep tab implements a subset of the MIT-licensed
**vpype** command set (https://github.com/abey79/vpype): `linemerge`
(collinear point merge), `deduplicate` (repeated segments), `reloop` (join
ends within a gap tolerance), and `linesort` (nearest-neighbour ordering).

The Python implementation in `path_prep_tab.py` was written for this
repository. The full vpype CLI remains the external tool of record for the
commands not implemented here.
