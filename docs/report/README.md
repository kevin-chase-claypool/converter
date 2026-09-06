# System Integration in Robotics — report

Working area for the end-of-semester report on this project. Drop drafts, figures,
and exports here.

Use [`LAB_NOTE_TEMPLATE.md`](LAB_NOTE_TEMPLATE.md) for bench work. Keep dated
notes under `lab-notes/` so measurements and design changes can be cited later.
The project-wide chronology is maintained in
[`../project/ENGINEERING_LOG.md`](../project/ENGINEERING_LOG.md); use it to build
the report timeline, locate supporting commits or lab evidence, and discuss
setbacks, troubleshooting, rejected designs, and lessons learned in sequence.

The report is about **integrating the subsystems** into one working pipeline:
host conversion software → motion controller → force-controlled pen. The repo is
organized along those subsystem lines so each maps to a report section.

## Progress presentation

[`Theta_Pen_Plotter_Summer_Progress_Update.pptx`](Theta_Pen_Plotter_Summer_Progress_Update.pptx)
is the professor-facing summer-progress update. It gives the high-level machine
architecture, homing and P100 sequence, force-controlled M3/M5 print cycle,
and remaining commissioning gates. Its P100 map supports hover or click on any
of the six process cards during Slide Show; a matching detail view opens, with
a **Back to overview** control.

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

Use `../HANDOFF.md` for converter history and tradeoffs, current subsystem
documents for present behavior, and the dated change notes for the original
code-refactor evidence. `../SIMPLIFICATION_PLAN.md` is an archived snapshot,
not a current design source.
