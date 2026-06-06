# Theta Pen Plotter — System Integration Project

A polar (XY + rotating-bed) pen-plotting system. SVG artwork is converted on a
host PC into G-code for a machine whose **bed rotates under an XY gantry**, with a
force-controlled pen. This repository is split into independent components so each
can be edited and iterated on its own.

## Components

| Folder | What it is | Language / target |
|---|---|---|
| [`software/`](software/) | Host desktop app: SVG → G-code converter with a live Qt/OpenGL preview | Python 3 + PySide6 |
| [`firmware/`](firmware/) | Machine controller (motion via grblHAL) + the pen-pressure control system | grblHAL on RP23CNC; toolhead placement pending tests |
| [`docs/`](docs/) | Design/handoff notes and the System Integration in Robotics report | Markdown |
| [`samples/`](samples/) | Example SVG inputs and generated G-code outputs | assets |

New contributors and AI sessions should begin with
[`docs/START_HERE.md`](docs/START_HERE.md). It links the hardware inventory,
architecture, interface contracts, roadmap, and test plan.

## Run the converter

Double-click **`converter.bat`** (launches the Qt/OpenGL app and logs to
`software/qt_debug.log`), or:

```powershell
python software\qt_svg_to_gcode.pyw
```

See [`software/README.md`](software/README.md) for full usage and settings.

## System overview

```
   SVG  ──►  software/ (host)  ──►  .gcode  ──►  firmware/ (Pico 2 + grblHAL)  ──►  machine
                                                        │
                                                        └─ M3/M5 pen signal ──►  pen-pressure MCU (load-cell force loop)
```

- The host converter maps SVG artwork (bed-local coordinates) into machine
  `X/Y/A` moves for the rotating bed, and emits pen up/down as `M3`/`M5`.
- grblHAL on the Pico 2 parses that G-code and drives the X/Y/A steppers.
- The pen-pressure system is an independent closed loop that treats `M3`/`M5` as a
  **mode override** (engage / lift) and otherwise holds a target contact force.

Full architecture, decisions, and open items live in
[`docs/HANDOFF.md`](docs/HANDOFF.md).
