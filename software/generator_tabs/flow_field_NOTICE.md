# Flow Field tab - third-party notice

The Flow Field tab uses the evenly-spaced streamline placement concept of
**msurguy/flow-lines** (https://github.com/msurguy/flow-lines), which follows
the Jobard & Lefer streamline algorithm. The upstream project is licensed under
the MIT License; its license text ships in that repository's `LICENSE` file.
The upstream tool drives the vector field from user-entered formulas; this
tab's procedural-noise and image-gradient field sources were written for this
repository, so this is an adaptation of the placement method rather than a
full port of the upstream interface.

The Python implementation in `flow_field_tab.py` was written for this
repository; no upstream source code was copied. Attribution is kept here
because the algorithm and parameterization come from the upstream work.
