# Ontoly Investigation Prompt — Theta Pen Plotter

Use this prompt at the beginning of any architecture, dependency, impact, or
cross-subsystem investigation in this repository. Replace `<TASK>` with the
question or change being considered.

```text
You are investigating the Theta Pen Plotter repository. Your task is:

<TASK>

This is an XY gantry plus a rotating-bed pen plotter. Its major ownership
boundaries are:

- `software/`: Python/PySide6 SVG-to-G-code converter and preview.
- ioSender: host-side G-code sender and operator console.
- `firmware/grblhal/`: RP23CNC/grblHAL motion control, homing, limits, and
  macros.
- `firmware/pen_pressure/`: Pro Micro RP2350 toolhead force/lift controller.
- `hardware/`: physical wiring, parts, electrical ratings, and mechanical
  evidence.

Start with evidence, not assumptions.

1. Read `AGENTS.md`, every root Markdown file, and `docs/START_HERE.md`.
   Then use `docs/README.md` to select only the authoritative subsystem
   documents needed for this task. Always read `docs/integration/INTERFACES.md`
   for a cross-subsystem question; read `docs/hardware/WIRING_TABLE.md` before
   asserting terminals, conductors, voltage domains, or pin assignments.
2. Check for `.ontoly/cache/compiler/SoftwareGraph.json`. If it exists, query
   it before broad source search. On this Windows repository, use the local
   command when available:

   `node_modules\\.bin\\ontoly.CMD stats .`
   `node_modules\\.bin\\ontoly.CMD architecture --json`
   `node_modules\\.bin\\ontoly.CMD trace <node-id-or-name>`
   `node_modules\\.bin\\ontoly.CMD query impact <node-id>`

   If the graph is missing or stale, do not install packages or rebuild it
   without asking first. Report the limitation and use the authoritative docs
   plus scoped source inspection instead.
3. Treat Ontoly as code-topology evidence, not as evidence of hardware or
   runtime behavior. The graph observed on 2026-09-11 has 512 nodes and 540
   edges, with only `CONTAINS`, `DECORATES`, `EXTENDS`, and `IMPORTS`
   relationships. Its quality report is 67% coverage/confidence. It cannot by
   itself prove call flow, grblHAL behavior, wiring, commissioning state, or
   bench results. State this limitation whenever it affects the conclusion.
4. For source fallback, search only the affected subsystem after recording why
   graph evidence was insufficient. Consult `docs/project/ROADMAP.md`, relevant
   change notes, and the engineering log when current verification status or a
   prior decision matters.

Preserve these non-negotiable system contracts unless the task explicitly asks
to change them and the corresponding authorities are updated together:

- grblHAL owns G-code parsing, motion planning, acceleration, step generation,
  homing, and limits. Do not introduce a competing parser or planner.
- G-code `X` and `Y` are millimetres; `A` is motor-shaft degrees. The 12:1
  bed ratio is applied by the converter, not again by grblHAL.
- `M3` means toolhead ENGAGE (seek then hold force); `M5` means PEN_CLEAR,
  not `LIFT_HOME`. `LIFT_HOME` is boot, recovery, or explicit service only.
- P100 owns normal physical homing and magnetic G54 registration. The
  converter must not apply the TMAG-to-pen offset a second time.
- Any reset, watchdog expiry, invalid calibration, or unsafe state must leave
  the toolhead lifted/off. Toolhead work must never block motion real-time
  handling.
- Do not claim a controller setting, electrical pin level, wiring path, or
  physical test result without its documented evidence.

Report the result in this order:

1. Conclusion and confidence.
2. Evidence: Ontoly graph hash/node IDs/relationships when available, followed
   by the authoritative documents and exact source spans inspected.
3. Ownership and impacted subsystems, including interfaces crossed.
4. Constraints, safety risks, open assumptions, and verification status.
5. A minimal next step. For a proposed change, name the implementation,
   documentation, and test/lab evidence required; do not make the change until
   asked.

When implementation is requested, follow `AGENTS.md`: make scoped changes,
update the current-state documentation and any needed change note/log, run
`python tools\\docs_index.py --write` and `python tools\\docs_index.py --check`,
then inspect the scoped diff before committing and pushing only the milestone
files.
```

The prompt deliberately names the graph's current limits so an investigation
does not mistake static Python-import evidence for an integrated-machine fact.
