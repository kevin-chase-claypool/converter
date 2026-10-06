# Substitution tab - third-party notice

The Substitution tab re-implements the algorithm of
**piebro/substitution-system** (https://github.com/piebro/substitution-system),
which is licensed under the MIT License; its license text ships in that
repository's `LICENSE` file.

The algorithm: each colour in a palette receives a random 2x2 replacement
rule, the grid starts at 2x2, and each iteration replaces every cell with its
rule, doubling the grid. The Python implementation in `substitution_tab.py`
was written for this repository; the plotting adaptation (colour boundaries or
cell diagonals for a single pen) is local to this project.
