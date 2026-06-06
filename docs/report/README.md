# System Integration in Robotics — report

Working area for the end-of-semester report on this project. Drop drafts, figures,
and exports here.

Use [`LAB_NOTE_TEMPLATE.md`](LAB_NOTE_TEMPLATE.md) for bench work. Keep dated
notes under `lab-notes/` so measurements and design changes can be cited later.
The project-wide chronology is maintained in
[`../project/ENGINEERING_LOG.md`](../project/ENGINEERING_LOG.md); use it to build
the report timeline and locate supporting commits or lab evidence.

The report is about **integrating the subsystems** into one working pipeline:
host conversion software → motion controller → force-controlled pen. The repo is
organized along those subsystem lines so each maps to a report section.

## Suggested outline

1. **Introduction / goal** — polar pen plotter: SVG in, drawn artwork out.
2. **System architecture** — the block diagram in the root `README.md`; how the
   three subsystems interface (G-code, the M3/M5 pen signal, the load-cell loop).
3. **Host software** (`software/`) — use the `converter_core/` split to explain
   settings, SVG geometry, XY+theta kinematics, planning, G-code emission, and the
   OpenGL preview as separate integration responsibilities.
4. **Motion control** (`firmware/grblhal/`) — why grblHAL, axis configuration, the
   motor-degree `A` convention and the 12:1 pulley ratio.
5. **Pen pressure subsystem** (`firmware/pen_pressure/`) — the force loop and the
   LIFT/ENGAGE override contract; the settle handshake.
6. **Integration decisions & trade-offs** — pull from `../HANDOFF.md`
   ("Debugging history", "Known soft spots", "Goals / roadmap").
7. **Results** — calibration, sample prints, runtime-estimate vs actual.
8. **Future work** — items still open in the roadmap.

`../HANDOFF.md` is the running record of design decisions and is the best single
source when drafting sections 3–6. `../SIMPLIFICATION_PLAN.md` captures the
before/after code footprint and is useful evidence for the host-software section.
