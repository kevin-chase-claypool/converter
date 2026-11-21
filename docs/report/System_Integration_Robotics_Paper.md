<!--TITLE: System Integration of a Rotating Bed and Force Controlled Pen Plotter-->
<!--SUBTITLE: Design Commissioning and Verified Performance-->
<!--AUTHOR: Kevin Chase Claypool-->
<!--COURSE: Systems Integration in Robotics-->
<!--DATE: November 21 2026-->
<!--KEYWORDS: system integration, pen plotter, grblHAL, rotating bed, force control, commissioning, verification-->
<!--HERO: docs/report/paper_assets/cover_machine_overview.png-->

# Abstract

This paper documents the design, commissioning, and verification of an XY gantry with a rotating bed and a force-controlled pen toolhead. The project shows how separately developed components can be integrated into a complete plotting pipeline through explicit interface contracts, staged testing, and fault-aware behavior. The host-side configuration pipeline, motion controller, operator application, and toolhead controller are treated as black boxes. The analysis therefore concentrates on the physical and logical boundaries between them rather than on software internals.

The integration method combined bench characterization, interface verification, subsystem commissioning, and end-to-end physical tests. Evidence includes 100 mm X and Y travel checks, three independent measurements of the bed drive ratio at 12.0332 to 1, automated magnetic registration of the bed center and angular index, a known-mass force calibration with a coefficient of determination of 0.999978 and 0.132 g RMS residual, a controller-visible M3 and M5 completion handshake with both success and failure tests, verified emergency-stop behavior, and an independently photographed compensated calibration sheet whose RMS error fell from 1.744 mm to 0.218 mm after a mechanical repair and coordinate correction.

The final system executes complete command-driven plots and several full-sheet calibration artifacts. It also exposes limits that a defensible engineering report must retain. The newest 200 ms pen-clearance value still requires a fresh no-drag test, rare handshake timeouts have not been completely explained, the latest expanded bed-compensation field includes extrapolated coverage, and some loaded electrical and thermal checks remain open. The project establishes a working and traceable integrated machine while distinguishing demonstrated capability from production qualification.

# Introduction

Pen plotters are attractive robotics projects because their purpose is easy to state: transform a digital drawing into physical marks. The implementation is less simple. A plotter combines geometric planning, coordinated electromechanical motion, material handling, tool actuation, sensing, safety, and operator workflow. Failure at any interface can produce a result that looks like a software error, a motion problem, or a mechanical defect. This makes the project well suited to systems integration research and engineering practice.

The machine studied here has an XY gantry above a rotating circular bed. The bed moves under the pen, so a requested line in the drawing can be produced through a combination of X, Y, and bed-angle motion. A separate toolhead controls the pen's contact force. The toolhead receives M3 to seek and hold contact and M5 to release and create clearance. The main controller owns G-code parsing, coordinated motion planning, limit handling, and startup registration. The host application produces the G-code and supplies the operator workflow.

Three constraints shaped the work. First, the physical machine changes faster than a tightly coupled architecture can tolerate. Sensors, wiring, driver settings, toolhead mechanics, and calibration values were revised as evidence accumulated. Second, each subsystem must remain testable on its own. A force-loop failure should not require rewriting motion planning, and a coordinate error should not be hidden inside a motor calibration. Third, a successful motion without a successful mark is not an integration result. The final evidence has to include paper, force behavior, registration, and fault response.

The project treated the software systems as black boxes. The host planning application accepts artwork and settings and returns G-code. The motion controller accepts G-code and produces X, Y, and A motion plus tool-output states. The operator application transports commands and exposes machine status. The toolhead accepts M3 and M5 requests and produces a controlled mechanical response plus readiness information. Their internal algorithms are outside this paper. Their observable contracts, timing, units, fault behavior, and physical effects are central.

This boundary follows established systems engineering practice: interfaces, requirements traceability, verification, and lifecycle evidence are treated as part of the system rather than as after-the-fact paperwork [1], [2].

The work addressed five questions:

- How should coordinate, timing, and tool-state responsibilities be divided among the host, motion controller, and toolhead?
- Which interfaces make subsystem behavior observable and repeatable?
- How can a failure at one boundary be detected before it causes an incorrect or unsafe action?
- What evidence is sufficient to support an integrated-system claim?
- Which limitations remain after the system produces complete plots?

The paper contributes a working integration architecture, a staged commissioning method, a traceable account of representative failures and corrections, and a quantitative result set. It also separates functional success from production readiness so that the same evidence can support both an academic assessment and future engineering work.

# Background and Requirements

## Rotating bed kinematics

The drawing plane is defined relative to a rotating bed. X and Y locate the toolhead in a fixed machine plane, while A rotates the bed. A point in artwork coordinates is achieved by combining a radial position from the bed center with an angular orientation of the bed. The machine does not need to rotate for every point, but a sequence of nearby points can demand a large angular change at a small radius. The motion planner must therefore operate on X, Y, and A together, and the integration must preserve one consistent angular convention.

The parameter A is defined in motor-shaft degrees. The host applies the measured motor-to-bed reduction before emitting G-code. The controller does not apply that mechanical ratio a second time. This single-owner rule is essential: a small convention error becomes a visible angular displacement at the outer edge of the bed and grows again when the bed is returned for later strokes.

## Motion control and tool control

The motion controller receives a constrained G-code vocabulary. It owns G-code parsing, lookahead, acceleration, step generation, homing, limits, and work-coordinate registration [3]. The project uses the RP23U5XBB V1.01 controller from the RP23CNC platform [4]. G21 selects millimeters, G90 selects absolute positioning, G94 selects feed-per-minute mode, G17 selects the XY plane, and G54 selects the registered work frame. G0 moves with the pen clear, and G1 draws. M3 requests contact and force hold; M5 requests release and clearance.

The toolhead has a distinct real-time responsibility. It measures pen force, drives a small linear actuator, seeks contact, enters a bounded force-hold state, releases the pen, and reports readiness. Its work is isolated from step generation. Putting the force loop on a separate controller prevents slow sensing and actuation tasks from blocking the motion controller. The interface is not a direct force setpoint. It is a state request with a physical completion condition.

## Integration requirements

The project requirements were derived from the desired plotted result and from the safety consequences of incorrect composition [5]. Table 1 states the main requirements and the evidence used to judge them.

TABLE: Integration requirements and acceptance basis | 0.45,1.55,2.00,2.00
| ID | Requirement | Acceptance basis | Current evidence |
| R1 | Preserve one defensible coordinate frame | A registered G54 frame places the pen at bed center and the outer magnet defines A zero | Automated integrated registration completed; later center correction still requires a repeat registration |
| R2 | Coordinate X, Y, and A without lost motion | Matched travel checks and full-bed angular excursions return to physical references | 100 mm axis checks, coordinated X/Y/A smoke test, and repeated bed rotations |
| R3 | Use one measured angular convention | Independent surveys agree on motor degrees per bed revolution | Three surveys produced a mean of 4331.97 motor degrees and 0.335 degree spread |
| R4 | Produce repeatable pen contact and clearance | Contact and clear states are distinct, bounded, and observable | Known-mass calibration, guarded hold tests, M3/M5 command tests, and no-drag cycling within the tested scope |
| R5 | Prevent stale tool state from authorizing motion | A fresh completion edge is required after each M3 or M5 | Controller handshake passed normal and injected-failure tests |
| R6 | Stop safely on operator stop and internal fault | Physical stop enters Halt; unsafe force or missing contact stops the actuator | Live E-stop test and toolhead fault paths |
| R7 | Demonstrate physical drawing accuracy | Calibration marks are measured against a registered reference | Independent pre/post compensated sheet comparison |
| R8 | Preserve traceability | Tests identify configuration, procedure, result, and residual risk | Dated lab notes, test IDs, photographs, and source fingerprints |

## Black-box system boundary

The black-box model is summarized in Table 2. It defines what each subsystem promises and what the rest of the system is entitled to observe. It intentionally omits internal functions and implementation choices.

TABLE: Black box contracts used in the paper | 1.05,1.55,1.65,1.75
| Black box | Inputs | Observable outputs | Excluded from this paper |
| Host planning application | Artwork, placement, calibration profile, process settings | Ordered G-code with documented units and frame | Parser, geometry algorithms, rendering, UI implementation |
| Operator application | G-code file and controller connection | Streaming, status display, command entry, alarms | Internal UI architecture and transport code |
| Motion controller | G-code and machine inputs | X/Y/A motion, tool-output state, homing and registration, alarms | Planner and step-timing implementation |
| Toolhead controller | M3 or M5 state, load-cell and magnetic signals, safety limits | Contact seek, force hold, pen clear, readiness or fault | Control-loop code and task scheduling |
| Physical machine | Motor, tool, and control commands | Ink on paper, motion, force, wear, thermal response | Detailed software ownership |

The black-box boundary also defines change control. A motion-controller update is allowed to change internal planning code without changing the G-code contract. A toolhead update is allowed to change filtering or pulse scheduling without changing the meaning of M3 and M5. If an observable output changes, the affected subsystem, interface document, and acceptance test must change together [6]. This rule keeps the paper focused on integration while preserving enough rigor to evaluate the machine.

The resulting architecture is shown in Figure 1. The mission path is supported by sensing, power, safety, and structure. These cross-cutting systems are not optional accessories. Registration depends on sensing, safe tool motion depends on power state, and plotting quality depends on cable routing and frame stiffness. The title-page image shows the corresponding physical concept: a bed carrying the artwork beneath an XY gantry, with the force-controlled toolhead mounted on the moving carriage. The comparison between the block and physical views makes the main engineering problem visible. A short logical command path crosses several mechanical, electrical, and control boundaries before it produces a mark.

The boundary also records prohibited actions. The host must not apply the magnet-to-pen offset a second time, the controller must not reinterpret the bed reduction as a second calibration step, the toolhead must not publish ready before its physical completion condition is met, and motion must not continue after a required completion signal is missing. These negative requirements are as important as the positive command formats because they prevent individually correct subsystems from producing a jointly incorrect machine.

FIGURE: docs/report/paper_assets/figure_01_system_architecture.png | Black box architecture of the integrated plotter. Each labeled arrow is an owned interface rather than an implementation dependency. | 6.35

# Integration Method

The integration method followed a deliberate dependency order. A test was allowed to advance only when the inputs needed for that test had already been established. Electrical inspection preceded power. Driver signal behavior preceded full motion. Homing preceded work-coordinate registration. Force sensing and failure behavior preceded normal drawing. Registration and bed compensation preceded accuracy claims.

Figure 2 summarizes the sequence. The sequence is a verification dependency graph, not a calendar. Some activities repeated when new evidence invalidated an earlier assumption.

Each test was treated as a record rather than a recollection. The project test plan defines acceptance criteria, and the lab notes capture configuration, commands, measurements, photographs, and disposition [7]. For significant tests, the record includes the exact firmware or controller configuration when available. A test that could not be reproduced was kept as a limitation rather than rounded up to a pass.

The main evidence categories were:

- electrical inspection and signal tests before connection or power;
- no-load or pen-free motion tests before force-loaded plotting;
- coordinate and ratio checks using physical references;
- command-level tests that exercised normal, stale, and missing-status cases;
- calibrated force measurements against known masses;
- independent drawings used to compare baseline and corrected geometry;
- photographs and measured images that preserve what the machine actually produced.

FIGURE: docs/report/paper_assets/figure_02_commissioning_sequence.png | Staged commissioning sequence used to expose interface failures before they reached a complete plot. | 6.35

The integration process rejected three kinds of false confidence. A connection was not accepted merely because it was electrically continuous. A sensor was not accepted merely because it produced stable numbers. A drawing was not accepted merely because it looked acceptable at normal viewing size. Each had to demonstrate the behavior required by the next subsystem.

# Integration Difficulties and Corrective Actions

## Coordinate scale and the measured drive ratio

The rotating bed was initially treated as a nominal 12 to 1 drive, which would make 4320 motor degrees equal one bed revolution. Three independent magnetic surveys measured 4331.818, 4331.930, and 4332.153 motor degrees [12]. Their mean was 4331.97 motor degrees, or 12.0332 motor degrees per bed degree, with a total spread of 0.335 degrees. The deviation was small per revolution but consequential across many rotations.

At a radius of 150 mm, the uncorrected ratio produced about 2.5 mm of accumulated displacement; at 185 mm, it produced about 3.0 mm. Earlier artwork showed ghosting that was consistent with this magnitude. The correction established 4331.97 motor degrees per revolution as the single host-side constant and changed the registration acceptance band to 4332 plus or minus 10 motor degrees. A repeatability program then drove the bed out and back at two radii at the reduced command limit. The radial ticks returned on their original lines, providing physical evidence that the angular scale and rate could be held over repeated revolutions.

The lesson is not simply that the gear ratio was not exactly 12 to 1. The important integration result is that a nominal mechanical parameter must be measured through the complete assembled chain, then assigned to one owner. Applying the ratio in both the host and controller would have produced a different error that looked equally plausible.

## Motion calibration and the danger of a precise but invalid measurement

The first calibration sequence also revealed how easily a measurement can mislead. A short Y test was run while the controller was still in absolute mode and produced an unexpectedly long move. The mode was corrected, and a 100 mm relative move then measured exactly 100 mm and returned to its reference. The X calibration encountered a different issue. A first 10 mm observation suggested a large correction, but a 100 mm caliper check produced 100.36 mm and led to a proportionally calculated adjustment. A later operator recheck restored the 80 steps per millimeter baseline. The final accepted setting therefore rested on the longer, repeated check, not on the short observation.

This episode changed the verification method. Motion tests now record modal state, use travel long enough to reduce relative measurement error, and require a matched reverse move. A numerical result is not accepted without a statement of what was measured and how the setting was obtained.

## Homing, magnetic registration, and reference ownership

The X and Y limit switches establish physical machine coordinates. They do not establish where the center of the rotating bed lies under the pen. A center magnet and an outer magnet were therefore used for automated registration. The motion controller performs a serpentine raster over the center magnet, records entry and exit positions from a magnetic threshold, computes a weighted centroid, and applies the measured sensor-to-pen offset before writing G54 [8]. It then scans the outer magnet twice, validates their angular spacing, and establishes G54 A zero. The TMAG5273 provides the magnetic measurement through the toolhead interface [15].

The production integrated-toolhead path completed this sequence without an alarm. The center centroid was recorded at machine coordinates X -232.138 mm and Y -219.475 mm, and the resulting G54 frame placed the pen at the center magnet. The two outer-magnet centers were separated by 4331.930 motor degrees, consistent with the independently measured ratio. The center coordinate repeated within 0.013 mm between runs, and the angular spacing repeated within 0.112 motor degrees.

An earlier attempt faulted at exactly the 300 s magnetic-arm watchdog because the raster approached the magnet more slowly than expected. That was not a registration calculation failure; it was a mismatch between the watchdog budget and the integrated scan duration. The acceptance workflow now treats timeout margin as a system parameter and requires a successful standard path, not a diagnostic pass, before registration is accepted.

The ownership rule is important. The magnetic sensor does not directly set the pen position. The controller records all coordinates, computes the centroid, validates the outer index, and applies the fixed sensor-to-pen transformation. The host uses G54 as already registered. This prevents the same offset from being introduced twice.

## Force sensing, contact uncertainty, and actuator control

The toolhead's original HX711 force path did not provide a reliable force authority [16]. The sensor communicated and produced stable bench readings, but actuator tests showed contact-like responses before physical contact and a large delayed response after release. The installed design was rejected for production force control rather than tuned around the ambiguity.

The replacement CS1238 path was calibrated with known masses under a strict sensor-only procedure [10]. A cap-free loading and unloading sequence from 0 to 90 g produced a linear fit of 5038.77 raw counts per gram, R squared equal to 0.999978, and 0.132 g RMS residual. The raw traces, fit, and residuals were retained. This result established a credible conversion from sensor input to mass force, but it did not by itself prove that the installed pen could approach paper safely or settle reliably.

FIGURE: docs/report/paper_assets/figure_04_force_calibration.png | Known-mass CS1238 calibration. The linear fit establishes a measurement scale; the guarded actuator tests separately establish whether the integrated pen can use that scale safely. | 5.65

The corrected actuator workflow separated three conditions: the mechanism is clear, the tip has made contact, and the contact force is stable enough to publish as ready. A guarded test reached 40.0 g and 40.4 g in two cycles and held for five seconds. A separate clear sequence released the tip and produced an approximately 1.75 mm visible air gap. Later review found that one nominally successful trace had started from a loaded tare and ended through pulse-budget safeguards, so that trace was not accepted as repeatability evidence.

This distinction is a central result of the project. Sensor calibration, mechanical behavior, and control qualification are separate claims. The system now uses bounded pulses, driver sleep between corrections, a hard-force limit, stale-sensor rejection, and a safe-lift path. It still treats the tool profile as supervised until the required repeated clear and per-tool checks are complete.

## M3 and M5 as physical contracts

M3 and M5 initially appeared to be simple digital commands. Their integrated meaning is more demanding. M3 means seek contact and enter force hold. M5 means release from paper and create clearance. M5 is not a command to travel to the distant full-retract switch, which is reserved for boot, recovery, or service.

The first controller-to-toolhead test exposed a polarity error. The controller's spindle-enable output was active-high by default, while the toolhead interface expected the asserted state to pull low. At power-up the toolhead saw a permanent M3 request and exhausted its contact-seek pulse budget. Inverting the controller output restored M3 down and M5 up, and disconnecting the command wire left the toolhead in the lifted fail-safe state.

The next weakness was timing. The toolhead's ready signal chattered during force hold because the ready flag released faster than the control loop could correct an excursion. A fresh completion edge could therefore be missed or falsely acknowledged. The toolhead now holds the ready level through bounded excursions and releases it only after a sustained out-of-band condition. The controller waits for an inactive-to-active completion edge after each transition.

The strict handshake test then produced three successful acknowledgements in one program and no error. Two injected failures were also tested: a stale held-ready state and a signal that never asserted. Both raised controller error 39 before later motion could execute [9]. This is stronger evidence than a successful normal command because it demonstrates that the boundary fails closed when the completion condition is absent.

Residual risk remains. A rare handshake timeout has been observed in long printing sessions and has not been reproduced with a complete diagnostic capture. The recover path lifts the pen and continues instead of issuing an unchecked motion command, but the root cause remains open.

## Mechanical interaction and rotating bed motion

The Y drag chain originally climbed a stepped transition on a northeast frame pillar. The added friction varied with position and was consistent with striations that changed with feed rate. Replacing the stepped pillar with a straight section allowed the chain to follow the extrusion through the full Y stroke. The operator then reported a visually clean XY-only version of the affected print [13].

This result is intentionally limited. It strongly supports a mechanical cause, but it does not complete the rotating-bed motion test. The machine has several coupled sources of visible error: bed runout, carriage and belt dynamics, cable drag, angular rate, and host-side geometric correction. The integration method treats the physical observation as evidence for one causal branch and leaves the simultaneous X/Y/A discriminator as follow-up work.

The A-axis command rate was also reduced from 80,000 to 20,000 motor degrees per minute after analysis showed the former value asked the bed for an implausibly high surface speed at the outer radius. The lower setting survived a power cycle, and repeated full-bed rotations at two radii returned the reference marks without lost motion. This is a system-level correction: a controller setting, host assumption, and physical capability were brought back into one defensible range.

## Registration residual and geometric compensation

Physical registration gives the machine a valid origin, but it cannot remove all repeatable bed-to-tool geometry error. A dense set of calibration marks was printed at multiple bed angles. Images were processed to assign station marks and fiducials, then measured errors were compared with a baseline. An early compensation attempt applied the correction in the wrong frame and increased error. The coordinate transformation was corrected by rotating measured bed-frame corrections into machine coordinates before interpolation and application.

After a mechanical repair, an independent compensated verification sheet reduced overall RMS from 1.744 mm to 0.218 mm, an 87.5 percent improvement. Maximum error fell from 2.965 mm to 0.591 mm, an 80.1 percent reduction [11]. All measured angle stages improved, and the result remained within the acceptance gates when the image extraction threshold was varied.

Figure 4 shows the physical calibration sheet and Figure 5 shows the pre/post comparison. The improvement is a system result: the map included measured registration error, the correction preserved the angular frame, and the second sheet was an independent check rather than a refit of the first.

The image processing was treated as part of the measurement system. A photograph can be distorted by perspective, glare, tape, ink bleed, or a paper sheet that moved during the run. The acceptance process therefore required complete fiducial and station recognition, repeated extraction at different thresholds, and an unchanged assignment of station identity. A result that depended on a single image-processing setting was not accepted. This makes the reported error reduction stronger than a visual before-and-after comparison, while still limiting the result to the measured bed and camera setup.

FIGURE: docs/report/paper_assets/figure_03_registration_artifact.jpg | Measured bed calibration artifact used to evaluate registration and compensation across the plotting field. The image is retained as physical evidence rather than reconstructed from commanded coordinates. | 5.15

FIGURE: docs/report/paper_assets/figure_05_error_improvement.png | Independent post-repair comparison for overall RMS and maximum bed error before and after compensated plotting. | 5.85

Later work expanded the correction field and produced a denser candidate. The project owner selected one candidate for continued use even though it missed some formal promotion gates, and the current expanded coverage includes an extrapolated outer annulus. Those decisions are disclosed here because they affect the interpretation of the result. The verified post-repair comparison demonstrates that the method can reduce error. It does not prove that every later default is fully qualified over the expanded field.

## Verification validity and rejected results

The project records several failures that are important to the academic result. One calibration sheet was invalidated when the paper was re-taped after printing began. A later dense layout crossed its own station labels and was rejected. A compensation candidate reduced average error modestly but failed maximum-error and improvement criteria. These results were not removed from the record.

The integration method now preserves failed tests and rejected candidates alongside successful tests. That practice prevents a later author from repeating a rejected path and makes the final result auditable. It also supports the professional responsibility expected in an engineering program: a measured improvement is reported with its acceptance gate, and an exception is identified as an exception.

# Results

## Integrated plotting capability

The machine now performs the complete black-box path: artwork and settings produce ordered G-code, the operator application streams that program, the motion controller coordinates X, Y, and A, M3 and M5 request tool states, and the toolhead produces contact or clearance. Complete command-driven and converter-generated plots have been produced. Several physical artifacts use the full rotating-bed field rather than a short motion demonstration.

FIGURE: docs/report/paper_assets/figure_06_completed_plot.jpg | Completed full-sheet wave matrix produced by the integrated plotting path. The artifact is used as evidence of end-to-end operation and as a source of visual failure modes. | 3.85

The wave matrix in Figure 6 is an example of a completed artwork-scale output. It also exposes why visual inspection alone is insufficient. A sheet can look deliberate while containing invisible registration error, a narrow-row defect, or a pen-clearance trace. That is why the results combine completed plots, measured calibration artifacts, and interface tests.

## Measured performance

Table 3 summarizes the principal quantitative evidence and its qualification. The table distinguishes a result from the broader claim that may be tempting to make from it.

TABLE: Principal integration results | 0.75,1.25,1.55,1.80
| Area | Result | Evidence | Qualification |
| X travel | 100 mm commanded and measured after calibration; matched reverse returned to reference | M-03, 2026-09-06 | Unloaded scope; final active baseline was rechecked by the operator |
| Y travel | 100 mm commanded and measured; matched reverse returned to reference | M-03, 2026-09-05 | Pen-free travel check |
| Bed ratio | 4331.97 motor degrees per bed revolution; 12.0332 to 1 | Three magnetic surveys | Mean of three surveys with 0.335 degree spread |
| Registration | Integrated magnetic center and A-index sequence completed without alarm | P113 production-toolhead run, 2026-09-24 | Later center correction requires a repeat registration |
| Force calibration | 5038.77 raw per gram; R squared 0.999978; 0.132 g RMS residual | E-09C cap-free known-mass run | Downward weight fixture; upward pen response is an opposite-direction projection |
| Handshake | Three M3/M5 acknowledgements passed; stale and missing signals raised error 39 | F-05A, 2026-09-29 | Rare long-run timeout remains unresolved |
| E-stop | Physical switch entered controller Halt; release required Reset and Unlock; no automatic motion | E-19, 2026-09-08 | E-stop does not remove motor or tool power |
| Bed accuracy | RMS reduced 1.744 to 0.218 mm; maximum reduced 2.965 to 0.591 mm | Independent post-repair verification | Applies to the tested field and configuration |

The coordinate and ratio results support the current motion convention. The registration result supports automated startup within the tested configuration. The force result supports a calibrated sensor and bounded tool behavior, but not unrestricted production use with any writing tool. The handshake result demonstrates fail-closed command behavior, with one unexplained long-run risk. The accuracy result is the strongest system-level outcome because it includes registration, motion, tool behavior, a mechanical correction, and independent physical measurement.

## Requirement attainment

Table 4 evaluates the project at the system level. A requirement is marked verified only within the evidence scope. Partial status is not treated as a failed subsystem; it identifies where further work is required before a broader operational claim can be defended.

TABLE: Requirement attainment as of November 21 2026 | 1.05,3.45,2.05
| Requirement | Evidence based disposition | Status |
| R1 Coordinate frame | Automated P113 registration works on the integrated build; later center correction still needs a repeat registration | Verified in prior frame; partial for current deployment |
| R2 X/Y/A motion | 100 mm travel checks, coordinated smoke test, and full-bed repeated rotations | Verified for tested unloaded motion |
| R3 Angular convention | Three independent ratio surveys and one-owner host convention | Verified |
| R4 Tool force and clearance | Known-mass calibration and guarded holds; current 200 ms clearance still requires a fresh no-drag run | Partial |
| R5 Completion handshake | Normal and injected-failure tests pass; rare timeout unexplained | Verified for tested cases; operational risk remains |
| R6 Safety response | Command-wire fail-safe, E-stop Halt, force and pulse bounds | Verified for tested states |
| R7 Physical accuracy | Independent compensated sheet improves RMS and maximum error | Verified for tested field and configuration |
| R8 Traceability | Named tests, dated notes, photographs, source fingerprints, and rejected results | Verified |

The result is therefore a verified integrated system with a clear qualification boundary. The strongest end-to-end evidence is the measured improvement in printed geometry. The motion chain, pen command path, registration, and compensation each contribute to that outcome and each have independent tests. The partial requirements are not hidden engineering failures; they mark the remaining steps between the demonstrated system and a release-ready instrument.

# Discussion

## Explicit black boxes make integration possible

Treating software as a black box did not remove the need for precision. It increased the importance of the contract. Each subsystem needed a documented input vocabulary, output vocabulary, unit convention, timeout, failure state, and acceptance test. The system became easier to reason about because the interfaces were stable even while implementations changed.

This approach also protected subsystem debugging. A coordinate error could be assigned to the conversion or controller contract. A pen that failed to clear could be assigned to M5 semantics, force release, mechanical clearance, or power polarity. Once the symptom was observed at the boundary, the next test could isolate the owner instead of reopening the whole architecture.

## Physical semantics outrank connectivity

Several failures passed simple connectivity checks and still violated the integrated contract. The spindle-enable wire was electrically connected but asserted the wrong state at power-up. The load cell produced valid samples but was not a reliable force authority. A ready signal changed state but did not remain stable long enough after contact. The completion handshake observed an edge but could miss it if the edge occurred before polling.

The correct validation therefore tested the physical semantics of the interface. M3 had to move the pen down and hold force. M5 had to release and create clearance. The ready signal had to remain valid through a force correction. A failure injection had to produce an alarm rather than permit the next motion. This is the difference between interface presence and interface correctness.

## Staged evidence supports better design decisions

The project repeatedly changed direction when measurements contradicted assumptions. The nominal gear ratio was replaced by the measured ratio. The HX711 path was rejected after actuator traces showed ambiguous contact. A bed correction was rejected when it was applied in the wrong frame. The drag-chain pillar was changed after a feed-dependent visual defect pointed to a mechanical source.

Those changes did not indicate an undisciplined design. They came from tests that made the assumption falsifiable. The design became stronger because each subsystem had a test that could reject it. The resulting record is useful beyond the final artifact because it shows how the team reached the current configuration.

## Tradeoffs

Separating the force controller from the motion controller reduced real-time coupling but increased the number of wires, electrical domains, and handshake states. That tradeoff was justified because blocking motion timing to service a load cell or actuator would violate the safety requirement. The cost appears in the need for careful opto-isolation, polarity, timeout, and fault management.

Pulse-based force correction is slower than a continuously energized controller, but it limits heat and unintended force when a sensor or actuator is in an uncertain state. The design uses a bounded pulse cadence, driver sleep between corrections, and a separate retract-only relief path. This is appropriate for a plotter, where the pen should remain stable for long periods and an occasional small correction is preferable to a continuous holding current.

Bed compensation improves geometric accuracy but introduces a new dependency on a measured profile, coordinate transformation, and configuration identity. The correction cannot compensate for sheet distortion, arbitrary re-taping, or a new mechanical fault. It can only represent repeatable machine error within its measured field. The paper therefore reports the improvement with the field and configuration that produced it.

## Threats to validity

The results come from one machine and a small number of primary operators. Some tests were performed before every configuration value was captured, and the hardware changed during the project. Physical measurements used calipers, photographic extraction, visual reference marks, and a kitchen-scale cross-check where precision-mass sensing was not practical. These methods are adequate for the reported engineering decisions but limit statistical generalization.

Image-based calibration has a particular selection risk: the best-looking threshold or fit can be chosen after examining the result. The project reduced that risk by repeating extraction thresholds, using independent verification sheets, preserving rejected candidates, and not refitting a verification sheet as a new calibration profile. Yet some later profiles were selected despite missing formal gates. The report identifies those cases rather than treating owner selection as equivalent to automatic qualification.

The open verification items are material. Current pen-clearance behavior, full interchangeable-tool validation, loaded power and thermal characterization, and some simultaneous X/Y/A tests remain incomplete. The results should be read as evidence of a functioning integrated machine with a defined qualification path, not as a claim that every operating state is production-ready.

# Limitations and Future Work

The next engineering priority is to close the toolhead state qualification. The current M5 clearance is 200 ms, raised after earlier clearance proved insufficient. That value requires a fresh measured air gap, repeated no-drag cycles, and a first-contact check. The same work should establish a strict, per-tool startup preflight for interchangeable pens or pencils.

The controller handshake needs a diagnostic capture of the rare long-run timeout. The present recover behavior keeps the pen lifted and allows a long job to continue, which is safer than unchecked motion, but the underlying cause remains unknown. A future run should record the controller input state, toolhead state, force trace, and command timestamp around the event.

Loaded electrical and thermal characterization is also incomplete. The supply, branch protection, regulator behavior, driver current, cable routing, and enclosure cooling must be measured under representative simultaneous motion and force control. The E-stop proves a controller Halt and no automatic restart. It does not remove motor or tool power, so the broader power-removal story requires an explicit operator procedure and additional evidence for a complete risk assessment.

The current expanded bed-compensation field should be tested at its outer coverage and repeated on the installed configuration. The maximum error and promotion gates should remain the basis for accepting a profile unless an exception is documented with its reason, owner, and follow-up. The owner-selected exceptions in the project record provide useful engineering experience, but they are not the same as a passed qualification.

Finally, end-to-end verification should be repeated as a controlled release test. The release should freeze the firmware build, controller settings, mechanical configuration, converter profile, and pen identity; run a standard registration sequence; plot a geometric test and a calibration sheet; and publish the measured result. That package would convert the current project record into a reproducible final validation milestone.

# Conclusion

The project produced an integrated XY and rotating-bed plotter in which host planning, motion control, and force-controlled pen behavior could be tested as separate black boxes and then composed into a complete drawing pipeline. The main engineering achievement is the contract and commissioning structure that made those black boxes observable. The machine can register its bed automatically, coordinate three axes, request and verify pen states, stop on defined faults, and produce measured artwork.

The evidence also shows where the boundary of the claim lies. The ratio, registration, command handshake, safety response, and post-repair geometric correction have strong physical evidence. The newest clearance setting, rare handshake behavior, current expanded compensation field, and loaded electrical and thermal behavior remain open. Those limitations are part of the result because they identify the remaining work required before the machine is treated as production-qualified.

For systems integration practice, this project demonstrates that integrating subsystems is not a final packaging step. It is a continuous process of defining ownership, testing the physical meaning of interfaces, preserving failure evidence, and deciding when a result is strong enough to support the next claim. That process produced the working plotter and the documentation needed to continue improving it.

# References

REF: [1] INCOSE. Systems Engineering Handbook. 5th ed. Wiley, 2023.
REF: [2] NASA. NASA Systems Engineering Handbook. Rev. 2, 2016.
REF: [3] grblHAL. Open source CNC motion control firmware. https://github.com/grblHAL.
REF: [4] Phil Barrett. RP23CNC hardware and RP2350 controller platform. https://github.com/phil-barrett/RP23CNC.
REF: [5] K. C. Claypool. System Architecture. docs/architecture/SYSTEM_ARCHITECTURE.md, Theta Pen Plotter repository, 2026.
REF: [6] K. C. Claypool. Integration Interfaces. docs/integration/INTERFACES.md, Theta Pen Plotter repository, 2026.
REF: [7] K. C. Claypool. Test Plan. docs/testing/TEST_PLAN.md, Theta Pen Plotter repository, 2026.
REF: [8] K. C. Claypool. First integrated firmware P113 magnetic registration. docs/report/lab-notes/2026-09-24-e-18-m-08-p113-integrated-registration.md, 2026.
REF: [9] K. C. Claypool. F-05A GP27 and PRB pen-transition acknowledgement. docs/report/lab-notes/2026-09-29-f-05a-gp27-prb-acknowledgement-pass.md, 2026.
REF: [10] K. C. Claypool. E-09C cap-free CS1238 repeat and force calibration. docs/report/lab-notes/2026-09-22-e-09c-cap-free-repeat.md, 2026.
REF: [11] K. C. Claypool. M-12 post-repair compensated verification. docs/report/lab-notes/2026-10-26-m-12-post-repair-compensated-verification.md, 2026.
REF: [12] K. C. Claypool. P112 outer A-index spacing repeat. docs/report/lab-notes/2026-09-30-p112-a-index-spacing-repeat.md, 2026.
REF: [13] K. C. Claypool. M-13 drag-chain pillar and striation result. docs/report/lab-notes/2026-10-25-m-13-drag-chain-pillar.md, 2026.
REF: [14] K. C. Claypool. Theta Pen Plotter system integration repository. https://github.com/kevin-chase-claypool/converter, accessed November 21, 2026.
REF: [15] Texas Instruments. TMAG5273 low-power 3D Hall-effect sensor datasheet, 2024.
REF: [16] Avia Semiconductor. HX711 24-bit ADC datasheet, accessed from project references, 2026.
REF: [17] ABET. Criteria for Accrediting Engineering Programs, 2025-2026. https://www.abet.org/accreditation/accreditation-criteria/.

# Appendix A Evidence Register

The evidence register points to the project records that support the main claims. Lab notes are the primary source for bench measurements. The test plan identifies acceptance conditions and current dispositions. Change notes and the engineering log preserve design changes and rejected approaches.

TABLE: Primary evidence used in the paper | 1.05,2.65,2.85
| Evidence | Record | Use in this paper |
| E-17 and F-01 | Board inspection and firmware identification | Establishes controller hardware and baseline |
| E-03 and F-03 | Driver signal and unpowered step/dir tests | Establishes controller-to-driver electrical behavior |
| M-03 | X and Y 100 mm calibration notes | Supports axis scale and reverse-travel checks |
| M-05 and P112 | Bed ratio and outer-index surveys | Establishes 12.0332 to 1 angular ratio |
| M-07 and P113 | Homing, center-magnet registration, and A-index integration | Establishes startup coordinate frame |
| E-09C and E-09F | Known-mass calibration and guarded force hold | Establishes force conversion and bounded behavior |
| F-05 and F-05A | M3/M5 polarity and completion handshake | Establishes command semantics and fail-closed behavior |
| E-19 | Emergency-stop configuration and live press test | Establishes controller Halt and reset behavior |
| M-12 | Calibration map and independent compensated verification | Establishes measured geometric improvement |
| M-13 | Drag-chain repair observation | Supports mechanical cause and residual test need |

# Appendix B Relationship to ABET Student Outcomes

ABET Criterion 3 defines seven student outcomes for engineering programs [17]. This paper can serve as evidence for several of those outcomes because it shows engineering work through requirements, design decisions, physical measurements, failures, corrective actions, and explicit conclusions. The mapping below identifies where that evidence appears and where the report alone is not sufficient.

TABLE: ABET Criterion 3 evidence map | 0.70,2.05,3.70
| Outcome | Student outcome | Evidence in this paper |
| 1 | Identify, formulate, and solve complex engineering problems by applying engineering, science, and mathematics | The project decomposes a three-axis rotating-bed plotter into bounded systems, derives the X/Y/A units and ownership rules, and resolves coupled coordinate, timing, force, and safety problems. Sections on system boundaries, motion calibration, force control, and geometric compensation provide the primary evidence. |
| 2 | Apply engineering design to produce a solution that meets specified needs while considering public health, safety, welfare, and other constraints | Requirements R1-R8, the black-box contracts, fail-safe M5 behavior, E-stop evidence, mechanical drag-chain correction, and stated qualification limits show design against safety and performance constraints. The paper also documents rejected alternatives rather than presenting the first design as complete. |
| 3 | Communicate effectively with a range of audiences | The report uses a technical narrative, requirements tables, architecture and sequence figures, measured plots, an evidence register, and a separate ABET mapping. All major claims identify evidence and scope. This result supports written engineering communication; oral communication is outside the report. |
| 4 | Recognize ethical and professional responsibilities and make informed judgments considering the impact of engineering solutions | The paper distinguishes demonstrated capability from production readiness, discloses owner-selected exceptions, preserves failed tests, and identifies hazards such as over-force, stale tool state, incomplete clearance, E-stop power limitations, and extrapolated compensation coverage. |
| 5 | Function effectively on a team that establishes goals, plans tasks, and meets objectives | This is not independently demonstrated by a solo-authored report. The project record shows explicit subsystem ownership, operator decisions, and coordinated interface changes, but a complete teamwork assessment would require separate evidence of team roles, collaboration, and shared decision-making. |
| 6 | Develop and conduct appropriate experimentation, analyze and interpret data, and use engineering judgment to draw conclusions | The staged test sequence, axis calibration, three ratio surveys, known-mass force calibration, injected handshake failures, independent compensated verification, rejected runs, and qualification boundary are direct evidence of experimentation and data interpretation. |
| 7 | Acquire and apply new knowledge as needed using appropriate learning strategies | The project record shows the team measuring instead of assuming the bed ratio, replacing an unsuitable HX711 path with a calibrated CS1238 path, using controller and sensor documentation, reworking a frame transition after physical evidence contradicted the initial design, and converting failures into new acceptance tests. |

The strongest accreditation evidence in this report is for Outcomes 1, 2, 4, 6, and 7. Outcome 3 is supported by the report and its figures but not by a presentation or other audience-specific communication artifact. Outcome 5 should not be inferred from technical coordination alone; it requires the course's own team-process evidence.

# Appendix C Reproducibility and Configuration Boundary

The strongest claims in the paper are tied to dated records rather than to an undifferentiated final machine state. The following configuration facts are relevant when repeating a test:

- RP23CNC RP23U5XBB V1.01 controller;
- grblHAL build and setting dump recorded in the relevant lab note;
- SparkFun Pro Micro RP2350 toolhead with the PC817C interface;
- measured bed ratio of 4331.97 motor degrees per revolution;
- G54 work frame established by the P113 registration path;
- bed compensation profile and file fingerprint recorded with the physical sheet;
- pen type and test program recorded where a visible plot is used as evidence.

The repository contains source records, scripts, and generated files [14]. A future release should add a single manifest that binds the paper revision to the exact firmware, settings, converter profile, pen, and calibration files used for the final approved plot. That manifest would make the final result easier to reproduce and support future review.

The proposed release run would use the following minimum evidence set:

TABLE: Minimum evidence for a final release run | 1.15,2.65,2.60
| Gate | Evidence required | Release condition |
| Configuration | Frozen build identity, controller settings, converter profile, mechanics, and pen | Every item is uniquely identified |
| Startup | Full P113 registration plus a repeat center check in the installed frame | Registration completes without alarm and the pen remains centered |
| Tool behavior | Current 200 ms clear, 30-cycle no-drag run, first-touch check, force trace, and per-tool preflight | Contact and clear states repeat without ambiguous force or residual marks |
| Motion | Coordinated X/Y/A tracking test and loaded dimensional check | Geometry and return marks remain within the stated tolerance |
| Fault handling | E-stop, missing handshake, over-force, sensor-loss, and timeout cases | Every case stops or lifts safely and is logged |
| Output | Standard geometric drawing and calibration sheet with raw measurement record | Results meet the acceptance criteria or an exception is documented |
