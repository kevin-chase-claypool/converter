# Struggles and Rejected Approaches

This register exists alongside the chronological
[`ENGINEERING_LOG.md`](ENGINEERING_LOG.md). The engineering log records events
in time order; this document groups failures, difficult bugs, misleading data,
and rejected approaches by topic so they can be found before work is repeated.

## Update rules

1. Add an item when an approach fails, a difficult bug is resolved, a source is
   shown to be unreliable, or a component/design is rejected.
2. Link to the dated engineering-log entry, commit, test, lab note, or other evidence.
3. State why it failed rather than only stating what replaced it.
4. Include retry conditions. `Do not retry` is valid when supported by evidence.
5. Update the existing item instead of creating duplicates for repeated symptoms.
6. Keep unresolved struggles here even when no successful replacement exists yet.

## Software and preview

| Topic | What happened | Cause/evidence | Resolution/status | Retry conditions |
|---|---|---|---|---|
| OpenGL preview colors | `paintGL` repeatedly threw exceptions | `color_tuple()` returned `QVector4D` while callers unpacked a tuple | Return a plain tuple | Do not restore mixed return types |
| Bed preview transform | Artwork rotated opposite the converter model and the pen did not track | Bed rotation sign was reversed | Use positive bed theta around preview center | Change only with a regression test covering converter/preview agreement |
| Theta shader uniform | Theta appeared fixed at zero | PySide6 selected an integer overload for scalar `setUniformValue` | Use `setUniformValue1f` | Retry generic overload only if binding behavior is proven by a focused test |
| OpenGL VBO binding | Attribute binding was brittle through PySide6 | Raw `glVertexAttribPointer(..., 0)` offset path | Use `QOpenGLShaderProgram.setAttributeBuffer` | Do not return to the raw path without a demonstrated requirement |
| Sparse fill boundaries | Early patterns crossed boundaries or disappeared near edges | Pattern generation and clipping were handled too locally | Clip full pattern layers against compound regions and preserve boundary points | Replace only with regression tests for concave, compound, and edge-crossing cases |
| Sparse fill identity | Different pattern choices produced overly similar geometry | Initial generators did not preserve distinct lattice structures | Shared lattice/cell implementations | Rework only if physical output demonstrates a repeatable defect |

## Kinematics and planning

| Topic | What happened | Cause/evidence | Resolution/status | Retry conditions |
|---|---|---|---|---|
| Theta DP winding reference | Low-winding solutions disappeared from the candidate window | Candidate winding was anchored to a tangent-following reference that itself accumulated winding | Use principal angles and nearest-wrap edge costs | Do not retry reference anchoring |
| Hold-steady theta grid | Planning became about six times faster, but the bed stayed still for roughly 94% of segments | Uniform orientation anchors dominated cost | Grid disabled by default | Retry only when throughput is explicitly more important than visible theta participation |
| Monotonic theta | Reduced direction reversals but increased peak net winding | Continuing rotation trades oscillation for cable wrap | Available with documented tradeoff; no hard winding cap yet | Use only with suitable cable management or after adding a winding bound |
| Full vector timing for travel preview | Theta-heavy travels appeared to crawl | Preview treated motor degrees as feed-distance units during travel | Travel preview uses XY distance at fixed expected travel speed | Revisit after measuring actual combined-axis machine timing |

## Hardware and source data

| Topic | What happened | Cause/evidence | Resolution/status | Retry conditions |
|---|---|---|---|---|
| Power-supply reseller specifications | Ubuy mixed 30 A / 360 W data into a 12 V / 10 A product page | Listing contamination from another model | Reject contradictory fields; prefer physical markings and manufacturer evidence | Accept only if confirmed on the received unit or manufacturer documentation |
| Power-supply model | Secondary listing reported `SE-1500-12`; received unit is `S-120-12` | Reseller metadata did not match physical hardware | Physical label controls | Never override a verified unit marking with reseller metadata |
| QR-linked power-supply PDF | Text extraction returned the captured viewer shell, not useful manual content; first extraction also hit a console encoding error | PDF is a web-viewer capture with limited text layer | Archive PDF and use physical label/visual inspection | OCR/render only when a specific unreadable detail is needed |
| Fixed 5 V buck for actuator | Existing module was below the 6 V motor rating and had marginal unverified current capacity | Fixed 5 V output; listing about 1.5 A continuous/1.8 A maximum | Replaced by adjustable B085T73CSD; fixed modules retained as spares | Use for actuator only if measured demand and 5 V performance are acceptable |
| Conceptual wiring diagram | Diagram originally stated unverified TB6600 polarity and power routing as facts | Hardware revisions and received driver inputs had not been inspected | Master wiring table is authoritative; diagram carries a warning | Promote diagram details only after wiring-table evidence exists |

## Process and documentation

| Topic | What happened | Cause/evidence | Resolution/status | Retry conditions |
|---|---|---|---|---|
| History spread across files | Important difficulties were buried in Git history and the handoff | No dedicated chronology or failure register | Engineering log plus this topic-based register | Keep both documents current after substantial work |
| Markdown wiring table looked unformatted | Raw Markdown was opened in a plain-text editor | Markdown tables require a renderer | Use GitHub or Markdown Preview | Not a file-format defect |

