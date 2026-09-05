# Engineering Log

This is the rolling chronological record of project work. It answers: what
changed, when it changed, why it changed, what evidence exists, and what should
happen next.

This log must include unsuccessful work as well as successful work. Record:

- Failed experiments and approaches that were abandoned.
- Bugs that were difficult to diagnose.
- Incorrect assumptions and misleading source data.
- Tooling failures, blockers, and workarounds.
- Rejected components or architectures.
- Conditions that would justify retrying a rejected approach.

Do not rewrite a failed attempt as if the successful result was reached
directly. The struggle, evidence, and recovery are part of the engineering
record and are useful report material.

## Visual status

VS Code Markdown Preview renders these markers consistently:

- 🟩 **SUCCESS** - completed implementation or verified result.
- 🟥 **STRUGGLE** - failed attempt, bug, blocker, or rejected approach.
- 🟨 **MIXED/OPEN** - useful progress with unresolved risk or required testing.

Every event belongs in this one chronology. A struggle and its later resolution
should normally be separate entries at their actual times. If the exact time of
an older struggle is unknown, use `Time not recorded` and place it before the
first event known to have occurred afterward. Never invent a timestamp.

Use Central Time and include the UTC offset in every timestamp:

```text
YYYY-MM-DD HH:MM:SS -0500
```

Git commit timestamps are authoritative for repository events. Bench events
should use the time the work was performed or recorded and link to a lab note,
photo, measurement, test ID, or source document.

## Browse by topic

<!-- BEGIN GENERATED TOPIC INDEX -->
The links below are alternate views of the single chronological log.
Entry details remain only in the chronology.

### Windows software
- [2026-06-07 14:02:21 -0500 - SUCCESS - Animated pen-up preview travel](#elog-20260607140221)
- [2026-06-07 13:16:27 -0500 - SUCCESS - Added cooperative preview cancellation](#elog-20260607131627)
- [2026-06-07 11:51:28 -0500 - SUCCESS - Added categorized change documentation and preview progress](#elog-20260607115128)
- [2026-06-06 15:46:05 -0500 - SUCCESS - Organized hardware integration and expanded converter behavior](#elog-20260606154605)
- [2026-06-05 10:56:12 -0500 - SUCCESS - Updated sparse-infill handoff notes](#elog-20260605105612)
- [2026-06-05 09:23:07 -0500 through 10:50:32 -0500 - MIXED/OPEN - Developed sparse fill patterns](#elog-20260605092307)
- [2026-06-05 09:09:40 -0500 through 09:15:25 -0500 - SUCCESS - Added preview navigation](#elog-20260605090940)
- [2026-06-05 08:28:30 -0500 - SUCCESS - Established project repository](#elog-20260605082830)
- [Before 2026-06-05 - Time not recorded - STRUGGLE - OpenGL preview type and binding bugs](#elog-20260605-opengl-preview-type-and-binding-bugs)
- [Before 2026-06-05 - Time not recorded - STRUGGLE - Theta DP winding reference failed](#elog-20260605-theta-dp-winding-reference-failed)
- [Before 2026-06-05 - Time not recorded - MIXED/OPEN - Hold-steady theta grid tradeoff](#elog-20260605-hold-steady-theta-grid-tradeoff)
- [2026-09-04 15:22:39 -0500 - MIXED/OPEN - Moved pen/TMAG XY offset ownership to P100](#elog-20260904152239)

### RP23CNC and machine software
- [2026-08-06 12:30:00 -0500 - MIXED/OPEN - Corrected PC817 active-low contract and PCB review file](#elog-20260806123000)
- [2026-07-31 11:03:49 -0500 - SUCCESS - Added RP2350 toolhead prototype firmware](#elog-20260731110349)
- [2026-07-04 12:30:00 -0500 - MIXED/OPEN - Added electronics layout wiring HTML](#elog-20260704123000)
- [2026-07-04 12:00:00 -0500 - MIXED/OPEN - Planned magnetic homing calibration](#elog-20260704120000)
- [2026-06-09 13:03:34 -0500 - MIXED/OPEN - Planned RP23U5XBB Ethernet bring-up](#elog-20260609130334)
- [2026-06-06 21:09:16 -0500 - MIXED/OPEN - Identified exact purchased RP23CNC kit](#elog-20260606210916)
- [2026-06-06 18:54:01 -0500 - SUCCESS - Promoted RP23CNC upstream reference](#elog-20260606185401)
- [2026-06-05 09:04:15 -0500 - SUCCESS - Chose RP23CNC and grblHAL](#elog-20260605090415)
- [2026-09-04 15:22:39 -0500 - MIXED/OPEN - Moved pen/TMAG XY offset ownership to P100](#elog-20260904152239)

### Hardware and wiring
- [2026-08-06 13:42:00 -0500 - MIXED/OPEN - Recovered KiCad 10 routing into a KiCad 9 review board](#elog-20260806134200)
- [2026-08-06 13:37:00 -0500 - MIXED/OPEN - Added KiCad 9-native perfboard schematic](#elog-20260806133700)
- [2026-08-06 13:30:00 -0500 - MIXED/OPEN - Selected six-position perfboard screw terminals](#elog-20260806133000)
- [2026-08-06 13:00:00 -0500 - MIXED/OPEN - Released all-through-hole perfboard build map](#elog-20260806130000)
- [2026-08-06 12:30:00 -0500 - MIXED/OPEN - Corrected PC817 active-low contract and PCB review file](#elog-20260806123000)
- [2026-08-06 11:54:00 -0500 - MIXED/OPEN - Created PC817C perfboard KiCad schematic](#elog-20260806115400)
- [2026-08-06 10:26:41 -0500 - MIXED/OPEN - Proposed compact three-channel PC817C interface module](#elog-20260806102641)
- [2026-08-03 08:20:00 -0500 - MIXED/OPEN - Added B07WFGTNQC optocoupler to schematic](#elog-20260803082000)
- [2026-08-03 07:15:56 -0500 - MIXED/OPEN - Added power-distribution document and schematic](#elog-20260803071556)
- [2026-08-03 06:14:31 -0500 - MIXED/OPEN - Added RP23CNC interface schematic](#elog-20260803061431)
- [2026-08-02 21:36:20 -0500 - MIXED/OPEN - Added Onshape API CAD workflow](#elog-20260802213620)
- [2026-08-02 17:26:26 -0500 - MIXED/OPEN - Selected shielded stepper cable](#elog-20260802172626)
- [2026-08-02 11:58:36 -0500 - MIXED/OPEN - Added local 5 V toolhead regulator](#elog-20260802115836)
- [2026-07-31 11:03:49 -0500 - SUCCESS - Added RP2350 toolhead prototype firmware](#elog-20260731110349)
- [2026-07-31 10:41:17 -0500 - MIXED/OPEN - Added toolhead wiring diagram](#elog-20260731104117)
- [2026-07-04 12:30:00 -0500 - MIXED/OPEN - Added electronics layout wiring HTML](#elog-20260704123000)
- [2026-07-04 12:00:00 -0500 - MIXED/OPEN - Planned magnetic homing calibration](#elog-20260704120000)
- [2026-06-15 09:57:11 -0500 - MIXED/OPEN - Created reference CAD for Tecmojo sliding shelf](#elog-20260615095711)
- [2026-06-09 13:03:34 -0500 - MIXED/OPEN - Planned RP23U5XBB Ethernet bring-up](#elog-20260609130334)
- [2026-06-06 21:09:16 -0500 - MIXED/OPEN - Identified exact purchased RP23CNC kit](#elog-20260606210916)
- [2026-06-06 18:16:52 -0500 - MIXED/OPEN - Selected adjustable toolhead buck converter](#elog-20260606181652)
- [2026-06-06 18:04:05 -0500 - STRUGGLE - Fixed 5 V buck was marginal](#elog-20260606180405)
- [2026-06-06 17:38:43 -0500 - MIXED/OPEN - Documented received S-120-12 terminal layout](#elog-20260606173843)
- [2026-06-06 17:24:07 -0500 - STRUGGLE - Reseller power data was contaminated](#elog-20260606172407)
- [2026-06-06 16:05:10 -0500 - MIXED/OPEN - Selected 12 V main power supply](#elog-20260606160510)
- [2026-06-06 15:55:07 -0500 - SUCCESS - Created authoritative wiring table](#elog-20260606155507)
- [2026-06-06 15:46:05 -0500 - SUCCESS - Organized hardware integration and expanded converter behavior](#elog-20260606154605)
- [2026-08-06 - SUCCESS - Added viewable PC817 wiring diagram](#elog-20260806-added-viewable-pc817-wiring-diagram)
- [2026-08-06 - SUCCESS - Added annotated perfboard build map](#elog-20260806-added-annotated-perfboard-build-map)
- [2026-08-06 - SUCCESS - Added translucent interconnection overlay](#elog-20260806-added-translucent-interconnection-overlay)
- [2026-08-08 - SUCCESS - Added no-overlap PC817 schematic](#elog-20260808-added-no-overlap-pc817-schematic)
- [2026-08-09 - MIXED/OPEN - Verified RP23CNC A-home electrical requirement](#elog-20260809-verified-rp23cnc-a-home-electrical-requirement)
- [2026-08-10 - SUCCESS - Minimized and verified PC817 layout](#elog-20260810-minimized-and-verified-pc817-layout)
- [2026-08-10 - SUCCESS - Passed all PC817 bench channels](#elog-20260810-passed-all-pc817-bench-channels)
- [2026-08-10 - SUCCESS - Recorded recommended system test sequence](#elog-20260810-recorded-recommended-system-test-sequence)
- [2026-08-10 - SUCCESS - Adopted direct-header toolhead harness](#elog-20260810-adopted-direct-header-toolhead-harness)
- [2026-08-11 - HARDWARE/PLANNED - Reconciled E-stop and HD064RT topology](#elog-20260811-reconciled-e-stop-and-hd064rt-topology)
- [2026-08-11 - SUCCESS - Reassigned HX711 to adjacent GP0/GP1 pins](#elog-20260811-reassigned-hx711-to-adjacent-gp0-gp1-pins)
- [2026-08-12 - SUCCESS - Recorded load-cell wire mapping](#elog-20260812-recorded-load-cell-wire-mapping)
- [2026-08-12 20:16:39 -0500 - MIXED/OPEN - Advanced toolhead perfboard wiring](#elog-20260812201639)
- [2026-08-12 20:22:03 -0500 - SUCCESS - Powered toolhead local branches from a 6 V bench supply](#elog-20260812202203)
- [2026-08-12 20:26:25 -0500 - SUCCESS - Confirmed Pro Micro logic-harness continuity](#elog-20260812202625)
- [2026-08-12 20:35:00 -0500 - STRUGGLE - Exact DRV8833 module corrected generic sleep/fault labels](#elog-20260812203500)
- [2026-08-13 - SUCCESS - Corrected DRV8833 firmware mapping without harness rework](#elog-20260813-corrected-drv8833-firmware-mapping-without-harness-rework)
- [2026-08-13 - SUCCESS - Made E-05 a one-shot boot test](#elog-20260813-made-e-05-a-one-shot-boot-test)
- [2026-08-13 - MIXED/OPEN - Verified N20 bidirectional motion at the toolhead](#elog-20260813-verified-n20-bidirectional-motion-at-the-toolhead)
- [2026-08-14 - SUCCESS - Repaired intermittent DRV8833 output solder joint](#elog-20260814-repaired-intermittent-drv8833-output-solder-joint)
- [2026-08-14 - SUCCESS - Passed E-05 N20 no-load current test](#elog-20260814-passed-e-05-n20-no-load-current-test)
- [2026-08-14 - SUCCESS - Passed E-15A toolhead rails during N20 motion](#elog-20260814-passed-e-15a-toolhead-rails-during-n20-motion)
- [2026-08-14 - SUCCESS - Required complete records for every E-series test](#elog-20260814-required-complete-records-for-every-e-series-test)
- [2026-08-14 - MIXED/OPEN - Started E-07 HX711 calibration](#elog-20260814-started-e-07-hx711-calibration)
- [2026-08-14 - MIXED/OPEN - HX711 first raw-reading attempt passed communication](#elog-20260814-hx711-first-raw-reading-attempt-passed-communication)
- [2026-08-14 - MIXED/OPEN - Prepared E-07B UART toolhead service test](#elog-20260814-prepared-e-07b-uart-toolhead-service-test)
- [2026-08-14 - MIXED/OPEN - Corrected E-07B UART1 serial instance](#elog-20260814-corrected-e-07b-uart1-serial-instance)
- [2026-08-14 - SUCCESS - Passed E-07B UART service bring-up](#elog-20260814-passed-e-07b-uart-service-bring-up)
- [2026-08-14 - PARTIAL - First E-07B automated pen-tip contact](#elog-20260814-first-e-07b-automated-pen-tip-contact)
- [2026-08-14 - SUCCESS - Passed E-08 HX711 rate and noise measurement](#elog-20260814-passed-e-08-hx711-rate-and-noise-measurement)
- [2026-08-14 - BLOCKED - E-09 Qwiic I2C startup](#elog-20260814-e-09-qwiic-i2c-startup)
- [2026-08-14 - SUCCESS - Passed E-09 TMAG5273 intended-wiring test](#elog-20260814-passed-e-09-tmag5273-intended-wiring-test)
- [2026-08-14 - PARTIAL - E-18 repinned PC817 harness pre-check](#elog-20260814-e-18-repinned-pc817-harness-pre-check)
- [2026-08-14 - SUCCESS - Passed E-17 RP23CNC pre-power inspection](#elog-20260814-passed-e-17-rp23cnc-pre-power-inspection)
- [2026-08-14 - SUCCESS - Passed F-01 RP23CNC grblHAL baseline boot](#elog-20260814-passed-f-01-rp23cnc-grblhal-baseline-boot)
- [2026-08-14 - PARTIAL - F-01 first-run control-input alarm](#elog-20260814-f-01-first-run-control-input-alarm)
- [2026-08-14 15:59:36 -0500 - SUCCESS - Cleared RP23CNC first-run control alarm](#elog-20260814155936)
- [2026-08-14 16:30:00 -0500 - SUCCESS - Passed F-03 RP23CNC X/Y/A bare-output test](#elog-20260814163000)
- [2026-08-14 16:45:00 -0500 - MIXED/OPEN - Selected X/Y SPDT roller limit switches](#elog-20260814164500)
- [2026-08-14 17:00:00 -0500 - MIXED/OPEN - Staged temporary X/Y limit-switch harness before drag-chain routing](#elog-20260814170000)
- [2026-08-14 17:30:00 -0500 - HARDWARE/OPEN - Initial E-stop uses RP23CNC Halt input](#elog-20260814173000)
- [2026-08-15 09:00:00 -0500 - HARDWARE/PARTIAL - Recorded TB6600 factory switch state](#elog-20260815090000)
- [2026-08-15 10:00:00 -0500 - HARDWARE/PLANNED - Selected A-axis TB6600 baseline from measured 12:1 reduction](#elog-20260815100000)
- [2026-08-15 10:15:00 -0500 - HARDWARE/PLANNED - Set X/Y initial calibration from confirmed 20-tooth pulleys](#elog-20260815101500)
- [2026-08-19 14:32:03 -0500 - HARDWARE/PARTIAL - Confirmed 17HS15 coil pairs and recorded Y cable exception](#elog-20260819143203)
- [2026-08-19 15:00:00 -0500 - HARDWARE/CORRECTED - Corrected B0FQ5GBNZ1 TB6600 DIP mapping](#elog-20260819150000)
- [2026-08-19 15:22:27 -0500 - HARDWARE/CORRECTED - Limited installed motor shielding to Y](#elog-20260819152227)
- [2026-08-19 16:06:38 -0500 - HARDWARE/PLANNED - Recorded actual HD064RT output allocation](#elog-20260819160638)
- [2026-08-20 15:41:52 -0500 - HARDWARE/PARTIAL - Verified main-supply no-load path through HD064RT](#elog-20260820154152)
- [2026-08-21 - HARDWARE - Segregated mains-input and DC-output routes](#elog-20260821-segregated-mains-input-and-dc-output-routes)
- [2026-08-22 - HARDWARE/PARTIAL - Verified X/Y limit live-input reporting](#elog-20260822-verified-x-y-limit-live-input-reporting)
- [2026-08-22 - HARDWARE - Routed toolhead PC817 harness through drag chains](#elog-20260822-routed-toolhead-pc817-harness-through-drag-chains)
- [2026-08-22 - RP23CNC-SOFTWARE/PLANNED - Added motorless PRB/G38 feasibility gate](#elog-20260822-added-motorless-prb-g38-feasibility-gate)
- [2026-08-22 - RP23CNC-SOFTWARE/CORRECTED - Corrected RP2350 toolhead ownership](#elog-20260822-corrected-rp2350-toolhead-ownership)
- [2026-08-22 - RP23CNC-SOFTWARE/IMPLEMENTED - Implemented gated magnetic registration](#elog-20260822-implemented-gated-magnetic-registration)
- [2026-08-23 - HARDWARE/PARTIAL - Partially terminated toolhead-control harness](#elog-20260823-partially-terminated-toolhead-control-harness)
- [2026-08-23 - HARDWARE/PLANNED - Set X-axis motor shielding plan](#elog-20260823-set-x-axis-motor-shielding-plan)
- [2026-08-23 - HARDWARE/CORRECTED - Corrected X-axis Phase B cable color](#elog-20260823-corrected-x-axis-phase-b-cable-color)
- [2026-08-23 - HARDWARE/PARTIAL - Recorded X sheath protective-earth bond](#elog-20260823-recorded-x-sheath-protective-earth-bond)
- [2026-08-23 - HARDWARE/VERIFIED - Verified mains terminals and X sheath landing](#elog-20260823-verified-mains-terminals-and-x-sheath-landing)
- [2026-08-23 - HARDWARE/VERIFIED - Verified X sheath DC-negative isolation](#elog-20260823-verified-x-sheath-dc-negative-isolation)
- [2026-08-23 - HARDWARE/VERIFIED - Verified supply protective-earth chassis path](#elog-20260823-verified-supply-protective-earth-chassis-path)
- [2026-08-23 - HARDWARE/VERIFIED - Verified X sheath motor-phase isolation](#elog-20260823-verified-x-sheath-motor-phase-isolation)
- [2026-08-23 - HARDWARE/PLANNED - Plan motor-harness strain-relief CAD](#elog-20260823-plan-motor-harness-strain-relief-cad)
- [2026-08-25 - RP23CNC-SOFTWARE/PLANNED - Plan slow PI toolhead force control](#elog-20260825-plan-slow-pi-toolhead-force-control)
- [2026-08-30 - HARDWARE/PLANNED - Plan toolhead motor/preload physical-envelope test](#elog-20260830-plan-toolhead-motor-preload-physical-envelope-test)
- [2026-08-30 - HARDWARE/PLANNED - Add toolhead test stop/go rules](#elog-20260830-add-toolhead-test-stop-go-rules)
- [2026-08-30 - HARDWARE/PARTIAL - Record preliminary toolhead preload current](#elog-20260830-record-preliminary-toolhead-preload-current)
- [2026-08-30 - HARDWARE/PARTIAL - Set proposed toolhead LIFT datum](#elog-20260830-set-proposed-toolhead-lift-datum)
- [2026-08-30 - HARDWARE/PLANNED - Plan toolhead LIFT-home switch](#elog-20260830-plan-toolhead-lift-home-switch)
- [2026-09-01 - MIXED/PLANNED - Separate normal pen clear from LIFT home](#elog-20260901-separate-normal-pen-clear-from-lift-home)
- [2026-09-01 - MIXED/PLANNED - Persist toolhead force profile separately from boot baseline](#elog-20260901-persist-toolhead-force-profile-separately-from-boot-baseline)
- [2026-09-02 08:05:50 -05:00 - SUCCESS - Added current system data-flow chart](#elog-20260902080550)
- [2026-09-02 08:17:43 -05:00 - SUCCESS - Corrected mobile data-flow layout](#elog-20260902081743)
- [2026-09-02 08:24:06 -05:00 - SUCCESS - Made data-flow visual a controlled record](#elog-20260902082406)
- [2026-09-02 - MIXED/PLANNED - Plan interchangeable-tool force preflight](#elog-20260902-plan-interchangeable-tool-force-preflight)
- [2026-09-02 - SUCCESS - Recorded intended P100 data movement](#elog-20260902-recorded-intended-p100-data-movement)
- [2026-09-02 - SUCCESS - Added interactive P100 data-movement map](#elog-20260902-added-interactive-p100-data-movement-map)
- [2026-09-02 - SUCCESS - Added summer progress presentation](#elog-20260902-added-summer-progress-presentation)
- [2026-09-02 - SUCCESS - Added native P100 presentation interaction](#elog-20260902-added-native-p100-presentation-interaction)
- [2026-09-02 - SUCCESS - Aligned P100 presentation detail states](#elog-20260902-aligned-p100-presentation-detail-states)
- [2026-09-02 - SUCCESS - Expanded P100 presentation views to full slide](#elog-20260902-expanded-p100-presentation-views-to-full-slide)
- [2026-09-02 - SUCCESS - Refreshed summer presentation opening render](#elog-20260902-refreshed-summer-presentation-opening-render)
- [2026-09-03 - IMPLEMENTED - Added mobile wiring-table view](#elog-20260903-added-mobile-wiring-table-view)
- [2026-09-03 - IMPLEMENTED - Landed TB6600 power branches](#elog-20260903-landed-tb6600-power-branches)
- [2026-09-03 - IMPLEMENTED - Recorded TB6600 signal and A-axis commissioning baseline](#elog-20260903-recorded-tb6600-signal-and-a-axis-commissioning-baseline)
- [2026-09-03 - SUCCESS - Added opto-isolation presentation slide](#elog-20260903-added-opto-isolation-presentation-slide)
- [2026-09-02 - SUCCESS - Set opening slide to full-bleed machine render](#elog-20260902-set-opening-slide-to-full-bleed-machine-render)
- [2026-09-04 - IMPLEMENTED - Corrected axis-specific motor cable colors in diagrams](#elog-20260904-corrected-axis-specific-motor-cable-colors-in-diagrams)
- [2026-09-04 12:47:26 -0500 - IMPLEMENTED - Rerouted top-down wiring schematic into clean lanes](#elog-20260904124726)
- [2026-09-04 14:43:51 -0500 - MIXED/OPEN - Recorded completed TB6600 signal harness wiring](#elog-20260904144351)
- [2026-09-04 14:48:01 -0500 - MIXED/OPEN - Verified TB6600 signal-harness continuity](#elog-20260904144801)
- [2026-09-04 - HARDWARE/PARTIAL - Clarified N20 endpoint stall current](#elog-20260904-clarified-n20-endpoint-stall-current)
- [2026-09-04 - HARDWARE/PARTIAL - Corrected N20 unloaded current after alignment](#elog-20260904-corrected-n20-unloaded-current-after-alignment)
- [2026-09-04 - HARDWARE/PARTIAL - Passed bounded N20 endpoint-stall test](#elog-20260904-passed-bounded-n20-endpoint-stall-test)
- [2026-09-04 - HARDWARE/IMPLEMENTED - Made pulse response per-tool during preflight](#elog-20260904-made-pulse-response-per-tool-during-preflight)
- [2026-09-04 - HARDWARE/OPEN - Replaced toolhead preload spring](#elog-20260904-replaced-toolhead-preload-spring)
- [2026-09-05 - HARDWARE/VERIFIED - Recovered RP23CNC USB recognition](#elog-20260905-recovered-rp23cnc-usb-recognition)
- [2026-09-05 - HARDWARE/SUCCESS - Passed installed TB6600 signal response test](#elog-20260905-passed-installed-tb6600-signal-response-test)
- [2026-09-05 - HARDWARE/PARTIAL - Passed initial A-axis direction jog](#elog-20260905-passed-initial-a-axis-direction-jog)
- [2026-09-05 - HARDWARE/SUCCESS - Completed M-01 low-speed jog test](#elog-20260905-completed-m-01-low-speed-jog-test)
- [2026-09-05 - HARDWARE/IN PROGRESS - M-02 A-axis rate ramp through F600](#elog-20260905-m-02-a-axis-rate-ramp-through-f600)

### Testing and verification
- [2026-08-06 13:42:00 -0500 - MIXED/OPEN - Recovered KiCad 10 routing into a KiCad 9 review board](#elog-20260806134200)
- [2026-08-06 13:37:00 -0500 - MIXED/OPEN - Added KiCad 9-native perfboard schematic](#elog-20260806133700)
- [2026-07-04 12:00:00 -0500 - MIXED/OPEN - Planned magnetic homing calibration](#elog-20260704120000)
- [2026-08-14 15:59:36 -0500 - SUCCESS - Cleared RP23CNC first-run control alarm](#elog-20260814155936)
- [2026-08-14 16:03:00 -0500 - MIXED/OPEN - Isolated missing grblHAL settings-list response](#elog-20260814160300)
- [2026-08-14 16:10:00 -0500 - SUCCESS - Passed F-02 RP23CNC converter-command parser dry run](#elog-20260814161000)
- [2026-08-14 16:30:00 -0500 - SUCCESS - Passed F-03 RP23CNC X/Y/A bare-output test](#elog-20260814163000)
- [2026-08-14 16:45:00 -0500 - MIXED/OPEN - Selected X/Y SPDT roller limit switches](#elog-20260814164500)
- [2026-08-15 09:00:00 -0500 - HARDWARE/PARTIAL - Recorded TB6600 factory switch state](#elog-20260815090000)
- [2026-08-19 14:32:03 -0500 - HARDWARE/PARTIAL - Confirmed 17HS15 coil pairs and recorded Y cable exception](#elog-20260819143203)
- [2026-08-19 15:00:00 -0500 - HARDWARE/CORRECTED - Corrected B0FQ5GBNZ1 TB6600 DIP mapping](#elog-20260819150000)
- [2026-08-20 15:41:52 -0500 - HARDWARE/PARTIAL - Verified main-supply no-load path through HD064RT](#elog-20260820154152)
- [2026-08-22 - HARDWARE/PARTIAL - Verified X/Y limit live-input reporting](#elog-20260822-verified-x-y-limit-live-input-reporting)
- [2026-09-04 15:22:39 -0500 - MIXED/OPEN - Moved pen/TMAG XY offset ownership to P100](#elog-20260904152239)

### Decisions and architecture
- [2026-06-07 11:57:39 -0500 - SUCCESS - Made continuous maintainability a repository requirement](#elog-20260607115739)
- [2026-06-05 09:04:15 -0500 - SUCCESS - Chose RP23CNC and grblHAL](#elog-20260605090415)
- [Before 2026-06-05 - Time not recorded - MIXED/OPEN - Hold-steady theta grid tradeoff](#elog-20260605-hold-steady-theta-grid-tradeoff)

### Documentation and project organization
- [2026-08-06 13:42:00 -0500 - MIXED/OPEN - Recovered KiCad 10 routing into a KiCad 9 review board](#elog-20260806134200)
- [2026-08-06 13:37:00 -0500 - MIXED/OPEN - Added KiCad 9-native perfboard schematic](#elog-20260806133700)
- [2026-08-06 13:30:00 -0500 - MIXED/OPEN - Selected six-position perfboard screw terminals](#elog-20260806133000)
- [2026-08-06 13:00:00 -0500 - MIXED/OPEN - Released all-through-hole perfboard build map](#elog-20260806130000)
- [2026-08-06 12:30:00 -0500 - MIXED/OPEN - Corrected PC817 active-low contract and PCB review file](#elog-20260806123000)
- [2026-08-06 11:54:00 -0500 - MIXED/OPEN - Created PC817C perfboard KiCad schematic](#elog-20260806115400)
- [2026-08-06 10:26:41 -0500 - MIXED/OPEN - Proposed compact three-channel PC817C interface module](#elog-20260806102641)
- [2026-08-03 08:20:00 -0500 - MIXED/OPEN - Added B07WFGTNQC optocoupler to schematic](#elog-20260803082000)
- [2026-08-03 07:15:56 -0500 - MIXED/OPEN - Added power-distribution document and schematic](#elog-20260803071556)
- [2026-08-03 06:14:31 -0500 - MIXED/OPEN - Added RP23CNC interface schematic](#elog-20260803061431)
- [2026-08-02 21:36:20 -0500 - MIXED/OPEN - Added Onshape API CAD workflow](#elog-20260802213620)
- [2026-08-02 17:26:26 -0500 - MIXED/OPEN - Selected shielded stepper cable](#elog-20260802172626)
- [2026-08-02 11:58:36 -0500 - MIXED/OPEN - Added local 5 V toolhead regulator](#elog-20260802115836)
- [2026-07-31 11:03:49 -0500 - SUCCESS - Added RP2350 toolhead prototype firmware](#elog-20260731110349)
- [2026-07-31 10:41:17 -0500 - MIXED/OPEN - Added toolhead wiring diagram](#elog-20260731104117)
- [2026-07-04 17:41:19 -0500 - SUCCESS - Added project management overview HTML](#elog-20260704174119)
- [2026-07-04 12:30:00 -0500 - MIXED/OPEN - Added electronics layout wiring HTML](#elog-20260704123000)
- [2026-07-04 12:00:00 -0500 - MIXED/OPEN - Planned magnetic homing calibration](#elog-20260704120000)
- [2026-06-15 09:57:11 -0500 - MIXED/OPEN - Created reference CAD for Tecmojo sliding shelf](#elog-20260615095711)
- [2026-06-09 13:03:34 -0500 - MIXED/OPEN - Planned RP23U5XBB Ethernet bring-up](#elog-20260609130334)
- [2026-06-07 12:21:44 -0500 - SUCCESS - Added single-file engineering-log topic navigation](#elog-20260607122144)
- [2026-06-07 12:02:21 -0500 - SUCCESS - Reduced documentation navigation and indexing friction](#elog-20260607120221)
- [2026-06-07 11:57:39 -0500 - SUCCESS - Made continuous maintainability a repository requirement](#elog-20260607115739)
- [2026-06-07 11:51:28 -0500 - SUCCESS - Added categorized change documentation and preview progress](#elog-20260607115128)
- [2026-06-06 21:09:16 -0500 - MIXED/OPEN - Identified exact purchased RP23CNC kit](#elog-20260606210916)
- [2026-06-06 18:58:24 -0500 - SUCCESS - Added roadmap completion checkboxes](#elog-20260606185824)
- [2026-06-06 18:54:01 -0500 - SUCCESS - Promoted RP23CNC upstream reference](#elog-20260606185401)
- [2026-06-06 18:45:28 -0500 - STRUGGLE - Misinterpreted requested log structure](#elog-20260606184528)
- [2026-06-06 18:41:06 -0500 - STRUGGLE - Separated struggles from chronology](#elog-20260606184106)
- [2026-06-06 18:37:31 -0500 - SUCCESS - Required failure details in log](#elog-20260606183731)
- [2026-06-06 18:34:25 -0500 - SUCCESS - Established rolling engineering chronology](#elog-20260606183425)
- [2026-06-06 17:38:43 -0500 - MIXED/OPEN - Documented received S-120-12 terminal layout](#elog-20260606173843)
- [2026-06-06 17:24:07 -0500 - STRUGGLE - Reseller power data was contaminated](#elog-20260606172407)
- [2026-06-06 15:55:07 -0500 - SUCCESS - Created authoritative wiring table](#elog-20260606155507)
- [2026-06-06 15:46:05 -0500 - SUCCESS - Organized hardware integration and expanded converter behavior](#elog-20260606154605)
- [2026-06-05 10:56:12 -0500 - SUCCESS - Updated sparse-infill handoff notes](#elog-20260605105612)
- [2026-06-05 08:28:30 -0500 - SUCCESS - Established project repository](#elog-20260605082830)
- [2026-08-06 - SUCCESS - Added viewable PC817 wiring diagram](#elog-20260806-added-viewable-pc817-wiring-diagram)
- [2026-08-06 - SUCCESS - Added annotated perfboard build map](#elog-20260806-added-annotated-perfboard-build-map)
- [2026-08-06 - SUCCESS - Added translucent interconnection overlay](#elog-20260806-added-translucent-interconnection-overlay)
- [2026-08-08 - SUCCESS - Added no-overlap PC817 schematic](#elog-20260808-added-no-overlap-pc817-schematic)
- [2026-08-14 - SUCCESS - Required complete records for every E-series test](#elog-20260814-required-complete-records-for-every-e-series-test)
- [2026-08-22 - RP23CNC-SOFTWARE/CORRECTED - Corrected RP2350 toolhead ownership](#elog-20260822-corrected-rp2350-toolhead-ownership)
- [2026-08-27 - SUCCESS - Adjusted presentation slide deck and added power schematic](#elog-20260827-adjusted-presentation-slide-deck-and-added-power-schematic)
- [2026-08-28 08:37:05 -0500 - SUCCESS - Established sequential agent execution policy](#elog-20260828083705)
- [2026-09-02 08:05:50 -05:00 - SUCCESS - Added current system data-flow chart](#elog-20260902080550)
- [2026-09-02 08:17:43 -05:00 - SUCCESS - Corrected mobile data-flow layout](#elog-20260902081743)
- [2026-09-02 08:24:06 -05:00 - SUCCESS - Made data-flow visual a controlled record](#elog-20260902082406)
- [2026-09-02 - SUCCESS - Recorded intended P100 data movement](#elog-20260902-recorded-intended-p100-data-movement)
- [2026-09-02 - SUCCESS - Added interactive P100 data-movement map](#elog-20260902-added-interactive-p100-data-movement-map)
- [2026-09-03 - IMPLEMENTED - Added mobile wiring-table view](#elog-20260903-added-mobile-wiring-table-view)
<!-- END GENERATED TOPIC INDEX -->

## Entry format

```markdown
### 🟩 YYYY-MM-DD HH:MM:SS -0500 - SUCCESS - Short title

- Status: success | struggle | mixed/open
- Category: software | firmware | hardware | wiring | test | decision | documentation
- Summary:
- Reason:
- Struggle/failure:
- Evidence:
- Files/commit:
- Result:
- Retry conditions:
- Next action:
```

Add new entries at the top of the log below this line.

---

<a id="elog-20260806134200"></a>
### 🟨 2026-08-06 13:42:00 -0500 - MIXED/OPEN - Recovered KiCad 10 routing into a KiCad 9 review board

- Status: mixed/open
- Category: hardware, test, documentation
- Summary: Recovered 110 manually routed segments and 3 vias from a mistakenly named KiCad 10 board into a cleanly named KiCad 10 review-file pair, with a separate KiCad 9-compatible fallback.
- Reason: The user appeared to lose their manual routing after reopening the intentionally unrouted KiCad 9 perfboard assembly view.
- Struggle/failure: The recovered track geometry is preserved, but DRC found shorts between `TOOL_GND` and GP8/GP10 around C1/C2 plus four open pad-to-track joins. The routing therefore does not yet validate the circuit and must not be used as a fabrication or perfboard wiring output.
- Evidence: `pc817-perfboard-v1.2-routed.kicad_pcb` retains the original KiCad 10 routing and has a matching same-basename schematic. `tools/recover_pc817_routing.py` also transferred the same 110 segments and 3 vias to `pc817-perfboard-v1.2-routed-kicad9.kicad_pcb`, which KiCad 9 opened and checked with `pc817-perfboard-v1.2-routed-kicad9-drc.rpt`.
- Files/commit: `tools/recover_pc817_routing.py`, `hardware/pc817-interface/pc817-perfboard-v1.2-routed.kicad_pcb`, `hardware/pc817-interface/pc817-perfboard-v1.2-routed.kicad_sch`, `hardware/pc817-interface/pc817-perfboard-v1.2-routed-kicad9.kicad_pcb`, `hardware/pc817-interface/pc817-perfboard-v1.2-routed-kicad9.kicad_sch`, `hardware/pc817-interface/pc817-perfboard-v1.2-routed-kicad9-drc.rpt`, and `hardware/pc817-interface/README.md`; commit not yet created.
- Result: The user's routing is recoverable and editable under KiCad 10, with a KiCad 9 fallback; it needs localized correction rather than a complete reroute.
- Retry conditions: Re-run KiCad 9 DRC after correcting C1/C2 and any other conflicting tracks. Retain the original KiCad 10 source file unchanged until the recovered board is verified.
- Next action: Correct the C1/C2 GP8, GP10, and `TOOL_GND` tracks, then rerun DRC before using the routing as a connectivity check.

---

<a id="elog-20260806133700"></a>
### 🟨 2026-08-06 13:37:00 -0500 - MIXED/OPEN - Added KiCad 9-native perfboard schematic

- Status: mixed/open
- Category: hardware, documentation, test
- Summary: Converted the PC817 interface legacy schematic to KiCad 9 native syntax and added the same-basename companion schematic required by the current perfboard PCB Editor view.
- Reason: The PCB's Open Schematic command reported a missing `pc817-perfboard-v1.2.kicad_sch` file; an earlier KiCad 10-only board artifact was also incompatible with the workstation's KiCad 9 installation.
- Struggle/failure: Initial ERC exposed three diode connections ending 1.27 mm short of their intended LED-anode nodes. The PCB netlist was already correct, but the schematic could not be treated as a verified source until those gaps were closed.
- Evidence: `kicad-cli sch erc hardware/pc817-interface/pc817-perfboard-v1.2.kicad_sch` reports zero violations after D1–D3 wire repair. The KiCad 9-native PCB remains `pc817-perfboard-v1.2.kicad_pcb`.
- Files/commit: `hardware/pc817-interface/pc817-interface.kicad_sch`, `hardware/pc817-interface/pc817-perfboard-v1.2.kicad_sch`, `hardware/pc817-interface/README.md`, `hardware/pc817-interface/PERFBOARD_BUILD.md`, and change note `HW-20260806-002`; commit not yet created.
- Result: The current perfboard PCB and schematic now open together under KiCad 9, and the three-channel circuit passes schematic ERC.
- Retry conditions: Re-run ERC after any circuit or connector change. Keep `R6` unpopulated until E-18 verifies the controller A-home interface.
- Next action: Open the schematic from the perfboard PCB, then perform F-05 and E-18 bench tests before connecting the controller harness.

---

<a id="elog-20260806133000"></a>
### 🟨 2026-08-06 13:30:00 -0500 - MIXED/OPEN - Selected six-position perfboard screw terminals

- Status: mixed/open
- Category: hardware, wiring, documentation
- Summary: Replaced the 1×5 header concept with one 1×6, 2.54 mm through-hole screw terminal on each short side of the PC817C perfboard.
- Reason: The project owner selected screw terminals for the two harness interfaces.
- Struggle/failure: The current circuit has only five unique conductors on each isolated side. Adding a sixth active connection without a verified requirement would be unsafe, so terminal 6 is explicitly NC/spare on both blocks.
- Evidence: `pc817-perfboard-v1.2.kicad_pcb` places the two six-position blocks on A1–A6 and N1–N6; `PERFBOARD_BUILD.md` records both pin orders and the unconnected pin-6 rule. U1/U2/U3 use one unrotated footprint definition: notch toward the top edge, pin 1 upper-left, pin 2 lower-left, pin 4 upper-right, and pin 3 lower-right.
- Files/commit: `hardware/pc817-interface/pc817-perfboard-v1.2.kicad_pcb`, `hardware/pc817-interface/PERFBOARD_BUILD.md`, `tools/generate_pc817_perfboard_kicad.py`, `docs/hardware/BOM.md`, and `docs/hardware/WIRING_TABLE.md`; commit not yet created.
- Result: The physical terminal choice and PC817 orientation are explicit without changing the circuit or breaching ground isolation.
- Retry conditions: Revise terminal 6 only after a specific, verified sixth conductor is required. Use a larger board if the selected terminal block body or wire-entry direction blocks the mounting holes.
- Next action: Dry-fit the actual 2.54 mm screw blocks, then confirm F-05 and E-18 before connecting the controller harness.

---

<a id="elog-20260806130000"></a>
### 🟨 2026-08-06 13:00:00 -0500 - MIXED/OPEN - Released all-through-hole perfboard build map

- Status: mixed/open
- Category: hardware, wiring, documentation
- Summary: Replaced the SMD/unrouted PCB direction with a compact all-through-hole PC817C perfboard construction plan matched to the photographed 14 × 6, 2.54 mm pad field.
- Reason: The project owner chose hand-soldered perfboard construction and requested no SMD parts.
- Struggle/failure: An SMD PCB placement review had been created before the final construction choice. It is now retained only as superseded history; it is neither routed nor a fabrication output.
- Evidence: `PERFBOARD_BUILD.md` names exact component holes, DIP and diode orientation, all underside-wire nets, and the DNP R6 safety boundary. `pc817-perfboard-layout-v1.png` renders the component side and wiring list; `pc817-perfboard-v1.1.kicad_pcb` presents the same all-THT layout in KiCad PCB Editor.
- Files/commit: `hardware/pc817-interface/PERFBOARD_BUILD.md`, `hardware/pc817-interface/pc817-perfboard-layout-v1.png`, `hardware/pc817-interface/pc817-perfboard-v1.1.kicad_pcb`, `tools/render_pc817_perfboard.py`, `tools/generate_pc817_perfboard_kicad.py`, `docs/hardware/BOM.md`, `docs/hardware/WIRING_TABLE.md`, and change note `HW-20260806-002`; commit not yet created.
- Result: The build contains only DIP, axial, radial, and 2.54 mm through-hole parts. Controller and toolhead grounds remain isolated; R6 remains unfitted.
- Retry conditions: Use a larger perfboard or a fabricated PCB if the selected headers conflict with the two mounting holes, if wire density prevents a clean insulated underside build, or if F-05/E-18 changes the electrical circuit.
- Next action: Dry-fit the headers, assemble U1/U2 first, power the Pro Micro side only, then complete F-05 before controller connection.

---

<a id="elog-20260806123000"></a>
### 🟨 2026-08-06 12:30:00 -0500 - MIXED/OPEN - Corrected PC817 active-low contract and PCB review file

- Status: mixed/open
- Category: hardware, wiring, firmware, documentation
- Summary: Audited the three PC817 nets, corrected the toolhead firmware to interpret U1/U2 as active-low GP8/GP10 inputs, and produced a separately named `v0.2` PCB placement/net-assignment review file.
- Reason: Review found that the circuit's common-emitter U1/U2 outputs pull GP8/GP10 low when illuminated while the firmware had used active-high reading plus internal pull-downs.
- Struggle/failure: A prior script-based routing attempt created invalid crossings. It was not retained as a manufactured-board candidate; the replacement is explicitly marked unrouted and not for fabrication.
- Evidence: PC817 pin assignment was checked as LED anode/cathode on pins 1/2 and phototransistor emitter/collector on pins 3/4. U1/U2 collector nets are GP8/GP10 with emitters at toolhead ground and R3/R4 pullups to local 3.3 V, so asserted optocouplers pull their inputs LOW.
- Files/commit: `hardware/pc817-interface/pc817-interface-v0.2.kicad_pcb`, `tools/generate_pc817_pcb.py`, `firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`, `docs/hardware/WIRING_TABLE.md`, `docs/integration/INTERFACES.md`, and change note `HW-20260806-002`; commit not yet created.
- Result: The logical circuit and firmware now agree. Controller and toolhead grounds remain isolated, R6 remains DNP, and idle GP8/GP10 are externally pulled HIGH.
- Retry conditions: Revise U1/U2 if F-05 demonstrates ENA does not provide the expected low-side M3/M5 behavior, or revise U2 if E-18 demonstrates a different Aux0/homing-arm behavior.
- Next action: Open the rev 0.2 PCB review file, bench-test F-05 and E-18, then route and DRC-check only after confirmed controller behavior.

---

<a id="elog-20260806115400"></a>
### 🟨 2026-08-06 11:54:00 -0500 - MIXED/OPEN - Created PC817C perfboard KiCad schematic

- Status: mixed/open
- Category: hardware, wiring, documentation
- Summary: Created a three-channel PC817C perfboard schematic for `ENA` to GP8, `AUX0` to GP10, and GP9 to the reverse `A_HOME` path.
- Reason: The project owner selected perfboard construction, making the earlier 1.25 mm JST-GH compact PCB connector concept mechanically unsuitable. The received B07WFGTNQC board's 3.6 V minimum output specification also does not establish safe direct use with RP2350 3.3 V GPIO.
- Struggle/failure: KiCad 10 CLI `sch upgrade` rejects legacy `.sch` import syntax and accepts only native files; the legacy source must be opened and saved once in the KiCad editor before command-line ERC. The earlier JST-GH PCB concept is superseded, not silently reused.
- Evidence: `hardware/pc817-interface/pc817-interface.sch` contains U1/U2/U3, all resistors, reverse clamp diodes, filters, generic 2.54 mm headers, net labels, and build notes. BOM and master wiring table now identify it as the current proposed interface.
- Files/commit: `hardware/pc817-interface/pc817-interface.sch`, `hardware/pc817-interface/README.md`, `docs/hardware/BOM.md`, `docs/hardware/WIRING_TABLE.md`, and change note `HW-20260806-002`; commit not yet created.
- Result: A KiCad schematic is available for a through-hole perfboard build. `R6` remains DNP and controller/toolhead grounds remain isolated.
- Retry conditions: Revise if measured ENA/Aux0 behavior differs from low-side sinking, if the selected header/perfboard will not fit, or if E-18 shows a different A-home input requirement.
- Next action: Open and save the schematic in KiCad to create native `.kicad_sch`, then bench-test U1/U2 and complete E-18 before fitting R6.

---

<a id="elog-20260806102641"></a>
### 🟨 2026-08-06 10:26:41 -0500 - MIXED/OPEN - Proposed compact three-channel PC817C interface module

- Status: mixed/open
- Category: hardware, wiring, documentation
- Summary: Added a 40.16 × 22.65 mm proposed PC817C interface module diagram with two controller-to-toolhead command channels, one reverse `A_HOME` channel, and 90° JST GH connectors on both short edges.
- Reason: The reserved toolhead envelope is too small for a generic module, while the received board's specified 3.6 V minimum output side does not establish safe compatibility with RP2350 3.3 V GPIO.
- Struggle/failure: The first direct-drive circuit concept omitted the separate RP23CNC `+5V` LED feed needed for ENA/Aux0 to behave as low-side sinks. The revised design preserves logic polarity through that explicit feed. The reverse channel remains deliberately unfinished because the RP23CNC A-home input is not yet verified.
- Evidence: `pc817-three-channel-module-proposal.png` rendered with `tools/render_pc817_module.py` and visually inspected; JST GH manufacturer material identifies 1.25 mm side-entry SMT headers; wiring table and BOM retain the design as proposed.
- Files/commit: `pc817-three-channel-module-proposal.png`, `tools/render_pc817_module.py`, `docs/hardware/BOM.md`, `docs/hardware/WIRING_TABLE.md`, and change note `HW-20260806-001`; commit not yet created.
- Result: A compact, rectangular layout now exists for CAD fit review. The board uses 3 PC817C DIP-4 packages, 2 5-pin 90° JST GH headers, 0603 passives, and a DNP `R6` safety link for `A_HOME`.
- Retry conditions: Rework the board if actual enclosure clearance, connector mating direction, RP23CNC source/sink behavior, or E-18 controller-input behavior differs from these assumptions.
- Next action: Confirm the CAD fit and bench-test ENA/Aux0 first; do not populate R6 or connect A_HOME until E-18 passes.

---

<a id="elog-20260803082000"></a>
### 🟨 2026-08-03 08:20:00 -0500 - MIXED/OPEN - Added B07WFGTNQC optocoupler to schematic

- Status: mixed/open
- Category: hardware, wiring, documentation
- Summary: Added the B07WFGTNQC 4-channel optocoupler isolation / voltage-converter module to the power-distribution schematic and documented `CH1` for RP23CNC `M3/M5` into Pro Micro `GP8` and `CH2` for RP23CNC `HOME_ARM` into Pro Micro `GP10`.
- Reason: The selected schematic needed to show the newly supplied optocoupler module and its actual command-signal wiring, not just the power branches.
- Struggle/failure: The first expanded render placed the signal section too close to the power section, and a bulk coordinate shift distorted labels and terminals. The SVG was replaced with a fixed-coordinate layout and re-rendered.
- Evidence: Amazon B07WFGTNQC listing describes 3.3 V or 5 V input control and 3.6-24 V output-side operation; `power-distribution-schematic.svg` parsed as XML; `power-distribution-schematic.png` rendered with Chrome headless and visually inspected for separated signal lanes and the visible S7V8F5 `VOUT/GND` to Pro Micro `RAW/5V/GND` power connection.
- Files/commit: `power-distribution-schematic.svg`, `power-distribution-schematic.png`, `docs/hardware/BOM.md`, `docs/hardware/WIRING_TABLE.md`, `docs/hardware/POWER_DISTRIBUTION.md`, `docs/integration/INTERFACES.md`, `docs/project/ROADMAP.md`, and change note `HW-20260803-003`; commit not yet created.
- Result: The current schematic now includes the optocoupler command path, explicitly shows the 5 V regulator output feeding the Pro Micro power input, and leaves the reverse `A_HOME` path as a separate verified switch-like interface.
- Retry conditions: Revise after inspecting the received B07WFGTNQC silkscreen/manual or bench-testing if channel direction, common rails, pullup behavior, or output-side 3.3 V compatibility differs from the schematic assumptions.
- Next action: Bench-test one channel from RP23CNC-side voltage into a 3.3 V Pro Micro-safe output before connecting to `GP8` or `GP10`.

---

<a id="elog-20260803071556"></a>
### 🟨 2026-08-03 07:15:56 -0500 - MIXED/OPEN - Added power-distribution document and schematic

- Status: mixed/open
- Category: hardware, wiring, documentation
- Summary: Added a dedicated power-distribution current-state document and a PNG/SVG power-only schematic that shows the current MEISHILE 12 V, fused 12 V branch, Pololu D36V50F6 6 V, toolhead 6 V terminal, Pololu S7V8F5 5 V, and Pro Micro 3.3 V sensor power path.
- Reason: The buck/regulator components were already listed in the BOM and wiring table, but the power path needed one organized view that separated distribution wiring from signal wiring.
- Struggle/failure: The first schematic render still visually bundled conductors near the drag-chain boundary and made the 6 V routing harder to inspect. It was redrawn with straight 12 V load lanes and a single labeled toolhead 6 V terminal block before local DRV8833 and S7V8F5 branches.
- Evidence: `power-distribution-schematic.svg` parsed as XML, `power-distribution-schematic.png` rendered with Chrome headless and visually inspected, BOM and wiring table cross-linked to `docs/hardware/POWER_DISTRIBUTION.md`, and roadmap tasks updated to the D36V50F6/S7V8F5 regulator chain.
- Files/commit: `docs/hardware/POWER_DISTRIBUTION.md`, `power-distribution-schematic.svg`, `power-distribution-schematic.png`, `docs/README.md`, `docs/hardware/BOM.md`, `docs/hardware/WIRING_TABLE.md`, `docs/project/ROADMAP.md`, and change note `HW-20260803-002`; commit not yet created.
- Result: The buck/regulator path is now documented as current state: B085T73CSD and B0F1WB3LJ5 modules are spares, the D36V50F6 is the selected DIN-side 6 V regulator, and the S7V8F5 is the selected toolhead-local 5 V regulator.
- Retry conditions: Revisit the topology if the D36V50F6 droops/overheats under actuator load, if the S7V8F5 lets the RP2350 reset during motor motion, or if the final terminal hardware cannot provide clean branch protection.
- Next action: Complete `E-11`, `E-14`, `E-15`, and `E-15A`, then replace fuse, terminal, wire-gauge, and branch-protection TBDs with measured values.

---

<a id="elog-20260803061431"></a>
### 🟨 2026-08-03 06:14:31 -0500 - MIXED/OPEN - Added RP23CNC interface schematic

- Status: mixed/open
- Category: hardware, wiring, documentation
- Summary: Added a PNG/SVG schematic showing the planned RP23CNC-to-Pro-Micro interface through a HiLetgo level shifter and Zopsc optocoupler.
- Reason: The toolhead interface needed a readable image that separates the RP23CNC-to-Pro-Micro logic inputs from the Pro-Micro-to-RP23CNC `A_HOME` switch-like output.
- Struggle/failure: The first render placed the lower optocoupler title too close to the terminal labels, so the schematic was widened and the lower section was given more vertical room before final rendering.
- Evidence: `rp23cnc-pro-micro-interface-schematic.svg`; Chrome headless render to `rp23cnc-pro-micro-interface-schematic.png`; visual inspection for separated wire lanes and no terminal-to-terminal wire overlap.
- Files/commit: `rp23cnc-pro-micro-interface-schematic.svg`, `rp23cnc-pro-micro-interface-schematic.png`, `docs/hardware/WIRING_TABLE.md`, and change note `HW-20260803-001`; commit not yet created.
- Result: The image now shows `SPINDLE ENA OUT` and `AUX0 HOME_ARM OUT` through the HiLetgo level shifter to Pro Micro `GP8` and `GP10`, and Pro Micro `GP9 A_HOME OUT` through the Zopsc optocoupler to the RP23CNC A limit/home input.
- Retry conditions: Revise after exact RP23CNC terminal names, common points, polarity, and voltage behavior are verified with the board/manual/meter.
- Next action: Verify the RP23CNC terminals before powered wiring.

---

<a id="elog-20260802213620"></a>
### 🟨 2026-08-02 21:36:20 -0500 - MIXED/OPEN - Added Onshape API CAD workflow

- Status: mixed/open
- Category: hardware, CAD, documentation
- Summary: Added a signed Onshape API helper and local credential setup script for repeatable CAD document metadata and export workflows.
- Reason: The course project will need traceable CAD model documentation, exported geometry, model snapshots, and report evidence as the hardware design stabilizes.
- Struggle/failure: The API secret was provided visually, but it was not written into the repository. Live API access still requires entering the credentials into Windows environment variables.
- Evidence: `python -m py_compile tools\onshape\onshape_client.py`; sample URL parsing returned `did`, `w`, and `e` IDs; CAD README updated with setup and usage commands.
- Files/commit: `tools/onshape/onshape_client.py`, `tools/onshape/set_onshape_env.ps1`, `docs/hardware/cad/README.md`, and change note `HW-20260802-003`; commit not yet created.
- Result: The repo now has a local path for listing Onshape documents, reading document metadata, listing workspace elements, and requesting Part Studio STEP exports using environment-based credentials.
- Retry conditions: Revisit after first live Onshape API call if an endpoint path, translation flow, or account permission differs from the documented assumptions.
- Next action: Run `tools\onshape\set_onshape_env.ps1`, test `list-documents`, and then export the first relevant plotter CAD snapshot for documentation.

---

<a id="elog-20260802172626"></a>
### 🟨 2026-08-02 17:26:26 -0500 - MIXED/OPEN - Selected shielded stepper cable

- Status: mixed/open
- Category: hardware, wiring, documentation
- Summary: Recorded the purchased KWANGIL 20 AWG 4C AMESB shielded cable as the selected replacement cable for NEMA17 stepper phase wiring.
- Reason: The drag chains may place NEMA17 wiring near toolhead power and RP23CNC control signals, so the stepper runs need a shielded cable with a clear drain-wire termination.
- Struggle/failure: Plain four-conductor automotive cable was rejected because it did not appear twisted or shielded. A previously discussed shielded cable did not clearly document a separate drain wire.
- Evidence: Amazon listing text for KWANGIL B0GVBF51Q7 identifying `OS+Drain+TC BRD`; project-owner purchase note; BOM and wiring table updates.
- Files/commit: `docs/hardware/BOM.md`, `docs/hardware/WIRING_TABLE.md`, and change note `HW-20260802-002`; commit not yet created.
- Result: Each NEMA17 motor uses one four-conductor cable for `A+`, `A-`, `B+`, and `B-`; the shield/drain bonds to PE/chassis at the TB6600/DIN-rail end only and is cut back/insulated at the motor end.
- Retry conditions: Revisit if the received cable lacks the expected drain wire, is too stiff for the drag chain, does not fit connectors/strain reliefs, or creates measurable motion/noise issues.
- Next action: Inspect the received cable, confirm drain-wire continuity to shield, and run E-01 before cutting or splicing motor leads.

---

<a id="elog-20260802115836"></a>
### 🟨 2026-08-02 11:58:36 -0500 - MIXED/OPEN - Added local 5 V toolhead regulator

- Status: mixed/open
- Category: hardware, wiring, documentation
- Summary: Added the purchased Pololu S7V8F5 5 V step-up/step-down regulator as the toolhead-local logic regulator, selected the Pololu D36V50F6 as the DIN-side fixed 6 V regulator, and clarified the Pro Micro mediated TMAG5273-to-RP23CNC homing path.
- Reason: The toolhead power architecture now sends only the 6 V rail through the drag chain and locally generates 5 V for the SparkFun Pro Micro RP2350, reducing harness conductors while preserving brownout margin.
- Struggle/failure: The existing fixed 5 V buck modules remain spares because they were not selected for 6 V-to-5 V toolhead logic regulation near motor-current dips. The adjustable B085T73CSD modules are also superseded for the final 6 V rail by the fixed-output D36V50F6.
- Evidence: BOM and wiring table updated; interface contract updated; explanatory diagrams updated; E-14/E-15 changed to the D36V50F6 and E-15A added for S7V8F5 characterization; `toolhead-wiring-diagram.svg` parsed as XML; `toolhead-wiring-diagram.png` rendered and visually checked; documentation indexes regenerated and checked.
- Files/commit: `docs/hardware/BOM.md`, `docs/hardware/WIRING_TABLE.md`, `docs/integration/INTERFACES.md`, `docs/testing/TEST_PLAN.md`, `docs/electronics_layout_and_wiring.html`, `docs/full_wiring_diagram.html`, `toolhead-wiring-diagram.svg`, `toolhead-wiring-diagram.png`, and change note `HW-20260802-001`; commit not yet created.
- Result: The component list and diagrams now reflect a DIN-mounted Pololu D36V50F6 6 V regulator feeding the drag-chain toolhead rail, a toolhead-mounted Pololu S7V8F5 local 5 V regulator, RP23CNC `SPINDLE ENA OUT` into Pro Micro `GP8` through a 5 V-to-3.3 V interface, RP23CNC `Aux 0` into Pro Micro `GP10` `HOME_ARM` through the same interface, and the intended final `GP9` conditioned `A_HOME` output path from Pro Micro to the RP23CNC A limit/home input.
- Retry conditions: Revisit if E-14/E-15/E-15A show poor regulation, overheating, excessive ripple, or RP2350 resets during actuator movement.
- Next action: Bench-test the D36V50F6 and S7V8F5 regulator chain with the RP2350/sensors active and the actuator moving.

---

<a id="elog-20260731110349"></a>
### 🟩 2026-07-31 11:03:49 -0500 - SUCCESS - Added RP2350 toolhead prototype firmware

- Status: success
- Category: firmware, hardware, wiring, documentation
- Summary: Added Arduino C++ sketches for the SparkFun Pro Micro RP2350 toolhead controller using the prototype DRV8833, HX711, TMAG5273, and M3/M5 pin assignments.
- Reason: The toolhead wiring now needed flashable bench firmware to verify motor direction, load-cell readings, magnetic telemetry, and command-input behavior.
- Struggle/failure: The first pass could not be compiled until `arduino-cli` was installed. Final force thresholds and gains remain raw-count placeholders until calibration tests E-07/E-08.
- Evidence: Pin assignments checked against `docs/hardware/WIRING_TABLE.md`; the SparkFun Pro Micro RP2350 Arduino variant uses GPIO-numbered pins and Qwiic on `GPIO17/GPIO16`; the integrated sketch includes serial bench commands, lift-first startup behavior, driver fault handling, optional sensor bring-up paths, and compiles for `rp2040:rp2040:sparkfun_promicrorp2350` using `HX711 Arduino Library` 0.7.5, `SparkFun TMAG5273 Arduino Library` 2.0.0, and `SparkFun Toolkit` 1.2.0 with 73,148 bytes program storage and 11,708 bytes dynamic memory. The new `bench_motor_command` sketch compiles with 60,328 bytes program storage and 10,872 bytes dynamic memory; the new `bench_sensors` sketch compiles with 70,668 bytes program storage and 11,648 bytes dynamic memory.
- Files/commit: `firmware/README.md`, `firmware/pen_pressure/bench_motor_command/bench_motor_command.ino`, `firmware/pen_pressure/bench_sensors/bench_sensors.ino`, `firmware/pen_pressure/pro_micro_rp2350_toolhead/pro_micro_rp2350_toolhead.ino`, `firmware/pen_pressure/README.md`, `docs/integration/INTERFACES.md`, and change note `RPSW-20260731-001`; commit not yet created.
- Result: The prototype firmware is ready for Arduino IDE installation and staged bench flashing after required libraries are installed.
- Retry conditions: Revisit after Arduino compile/upload, GP pin mapping confirmation, DRV8833 direction test, HX711 calibration, or TMAG5273 Qwiic test.
- Next action: Flash `bench_sensors`, then `bench_motor_command`, then the integrated `pro_micro_rp2350_toolhead` sketch before attempting force-control plotting.

---

<a id="elog-20260731104117"></a>
### 🟨 2026-07-31 10:41:17 -0500 - MIXED/OPEN - Added toolhead wiring diagram

- Status: mixed/open
- Category: hardware, wiring, documentation
- Summary: Added a no-wire-crossing top-down toolhead wiring diagram covering the SparkFun Pro Micro RP2350, DRV8833, TMAG5273 Qwiic sensor, HX711, load cell, N20 actuator, and DIN rail harness inputs.
- Reason: The toolhead prototype needed a readable wiring artifact with exact connection points and point-to-point routing instead of ambiguous split wires.
- Struggle/failure: Earlier generated layouts crossed power and sensor wires and one intermediate pass placed DRV8833 signal labels away from their terminals. The diagram was rerouted with separated lanes and aligned inputs.
- Evidence: `toolhead-wiring-diagram.svg` parsed as valid XML; `toolhead-wiring-diagram.png` rendered through Chrome headless; visual inspection confirmed no wire-to-wire crossings in the updated layout.
- Files/commit: `toolhead-wiring-diagram.svg`, `toolhead-wiring-diagram-viewer.html`, `toolhead-wiring-diagram.png`, `docs/hardware/WIRING_TABLE.md`, and change note `HW-20260731-001`; commit not yet created.
- Result: Prototype pin assignments are recorded for `GP4/GP5` to DRV8833 `IN1/IN2`, `GP6` to `EEP`, `GP7` from `ULT`, `GP2/GP3` to HX711 `DT/SCK`, Qwiic to TMAG5273, and RP23CNC spindle `ENA` to `GP8` through an interface circuit.
- Retry conditions: Revise after physical module inspection, DRV8833 label verification, HX711 3.3 V bench test, load-cell color identification, or RP23CNC M3/M5 level-shifter/opto selection.
- Next action: Bench-test TMAG5273, HX711, and DRV8833 separately before running the integrated toolhead state machine.

---

<a id="elog-20260704174119"></a>
### 🟩 2026-07-04 17:41:19 -0500 - SUCCESS - Added project management overview HTML

- Status: success
- Category: documentation, project-management
- Summary: Added a root-level HTML dashboard for at-a-glance project status, current phase, next work, blockers, subsystem status, and links to controlling documents.
- Reason: The roadmap and engineering log are detailed, but the repository needed a quick visual project management overview accessible directly from the root folder.
- Struggle/failure: A Markdown overview was rejected after the requested format was clarified; the final artifact is HTML for faster visual scanning.
- Evidence: Change note `WSW-20260704-001`; `project_management_overview.html`.
- Files/commit: `project_management_overview.html`, `README.md`, `docs/START_HERE.md`, `docs/changes/windows-software/2026/2026-07-04-project-management-overview-html.md`, and `docs/project/ENGINEERING_LOG.md`; commit not yet created.
- Result: The project now has a root dashboard while keeping the roadmap, test plan, wiring table, interface contract, engineering log, and change index as authoritative sources.
- Next action: Update the dashboard whenever phase status, immediate priorities, or major blockers change.

<a id="elog-20260704123000"></a>
### 🟨 2026-07-04 12:30:00 -0500 - MIXED/OPEN - Added electronics layout wiring HTML

- Status: mixed/open
- Category: hardware, wiring, firmware, documentation
- Summary: Added a standalone dark-mode HTML planning diagram for the current electronics layout and wiring concept, covering RP23CNC Ethernet control, 12 V distribution, X/Y/A TB6600 drivers, toolhead electronics, and the TMAG5273/RP2040 magnetic calibration adapter.
- Reason: The wiring table is authoritative but dense; the project needed a visual overview that shows the current architecture while preserving all TBD gates.
- Struggle/failure: None.
- Evidence: Change note `HW-20260704-001`; `docs/electronics_layout_and_wiring.html`.
- Files/commit: `docs/electronics_layout_and_wiring.html`, `docs/hardware/WIRING_TABLE.md`, `docs/changes/hardware/2026/2026-07-04-electronics-layout-wiring-html.md`, and `docs/project/ENGINEERING_LOG.md`; commit not yet created.
- Result: A browser-viewable electronics layout exists with a nighttime-friendly palette, and the wiring table explicitly states that the HTML is explanatory only.
- Retry conditions: Update the diagram when terminal labels, fusing, E-stop architecture, RP23CNC input behavior, or toolhead controller placement become verified.
- Next action: Visually inspect the HTML and keep using `docs/hardware/WIRING_TABLE.md` as the source of truth for actual wiring.

<a id="elog-20260704120000"></a>
### 🟨 2026-07-04 12:00:00 -0500 - MIXED/OPEN - Planned magnetic homing calibration

- Status: mixed/open
- Category: firmware, hardware, wiring, test, documentation
- Summary: Added a planned homing and magnetic bed-calibration architecture using physical X/Y limit switches, RP23CNC/grblHAL motion, a TMAG5273 Qwiic Hall sensor, an RP2040 adapter, a center magnet, and an outer theta-index magnet.
- Reason: The XY theta plotter needs repeatable X/Y homing, geometric bed-center calibration, and A/theta index detection without making grblHAL parse raw I2C sensor data.
- Struggle/failure: A direct TMAG5273 grblHAL plugin was rejected for first bring-up because it adds custom real-time firmware before proving that the host-coordinated RP2040 adapter approach is insufficient. Treating the center magnet as a theta reference was also rejected because it cannot define angular phase.
- Evidence: Change note `RPSW-20260704-001`; `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`.
- Files/commit: `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`, `firmware/README.md`, `firmware/grblhal/README.md`, `firmware/grblhal/UPCOMING_CODING_STEPS.md`, `docs/integration/INTERFACES.md`, `docs/hardware/WIRING_TABLE.md`, `docs/testing/TEST_PLAN.md`, `docs/changes/rp23cnc-software/2026/2026-07-04-magnetic-homing-calibration-plan.md`, and `docs/project/ENGINEERING_LOG.md`; commit not yet created.
- Result: Homing and calibration responsibilities are documented: grblHAL owns motion and digital home/limit handling; the RP2040/TMAG5273 path supplies magnetic readings and, after verification, may provide a conditioned `A_HOME` signal.
- Retry conditions: Consider custom grblHAL code only after host-coordinated scans prove a concrete limitation.
- Next action: Verify TMAG5273 readings, RP2040 telemetry, RP23CNC input requirements, and scan repeatability before recording thresholds or wiring status.

<a id="elog-20260615095711"></a>
### 🟨 2026-06-15 09:57:11 -0500 - MIXED/OPEN - Created reference CAD for Tecmojo sliding shelf

- Status: mixed/open
- Category: hardware, documentation
- Summary: Added parametric STEP assemblies for the Tecmojo `14130201` 1U sliding shelf at its published 350 mm and 500 mm rack-post depths.
- Reason: Electronics placement and cable-clearance planning need a usable 3D shelf envelope before plotter integration is finalized.
- Struggle/failure: The Amazon catalog dimensions `20.9 x 3.35 x 1.73 in` do not describe the installed shelf, and an older manual listed only 350-400 mm adjustment. The current manufacturer manual and specification sheet resolved SKU `14130201` to 482.6 mm width, 350-500 mm adjustment, and 44 mm height. Tecmojo did not provide production CAD for the product, leaving sheet, slide, vent, hole, and stop details to be inferred from images.
- Evidence: Amazon ASIN `B0BMW9V6MS`; current Tecmojo manual and specification sheet; valid 13-solid STEP re-imports; body envelopes `482.6 x 350 x 44.45 mm` and `482.6 x 500 x 44.45 mm`; rendered previews; change note `HW-20260615-001`.
- Files/commit: `tools/cad/generate_tecmojo_14130201.py`, `docs/hardware/cad/`, `docs/hardware/BOM.md`, `docs/changes/hardware/2026/2026-06-15-tecmojo-sliding-shelf-reference-cad.md`, and `docs/project/ENGINEERING_LOG.md`; commit not yet created.
- Result: Minimum- and maximum-depth layout models are available for electronics packaging work, with published interfaces separated from inferred geometry.
- Retry conditions: Replace image-derived constants after measuring the received shelf or if Tecmojo publishes production CAD for SKU `14130201`.
- Next action: Confirm the received SKU/revision and record physical dimensions before drilling a mounting plate or depending on vent and fastener locations.

<a id="elog-20260609130334"></a>
### 🟨 2026-06-09 13:03:34 -0500 - MIXED/OPEN - Planned RP23U5XBB Ethernet bring-up

- Status: mixed/open
- Category: firmware, hardware, documentation
- Summary: Reviewed the RP23CNC user manual and assembly instructions and converted them into a staged RP23U5XBB/Wiz850io firmware and Ethernet bring-up plan.
- Reason: The controller and Ethernet kit have been received, so the next work must distinguish physical assembly gates from reproducible firmware configuration and network verification.
- Struggle/failure: The reported `RP23U5BB` name differed from the official `RP23U5XBB` name. Front-board photography later resolved the identity as `RP23U5XBB V1.01`. Overview photographs cannot replace magnified joint inspection or continuity tests. A custom source build was deferred because the Web Builder is the documented baseline path.
- Evidence: Official RP23CNC user manual versions 1.0/1.01; official RP23U5XBB assembly instructions; supplied module photograph showing a Wiznet W5500 and two six-pin rows; lab notes `docs/report/lab-notes/2026-06-09-rp23cnc-w5500-module-inspection.md` and `docs/report/lab-notes/2026-06-09-rp23u5xbb-v1.01-board-inspection.md`; change note `RPSW-20260609-001`.
- Files/commit: `firmware/README.md`, `firmware/grblhal/README.md`, `firmware/grblhal/UPCOMING_CODING_STEPS.md`, `docs/changes/`, and `docs/project/ENGINEERING_LOG.md`; commit not yet created.
- Result: The received board is identified as RP23U5XBB V1.01, visible assembly evidence is archived, and upcoming work specifies remaining solder/continuity gates, four-axis/W5500 build options, USB recovery, DHCP/Telnet proof, settings capture, and the threshold for custom plugin code.
- Retry conditions: Revise the plan if the received PCB revision, module marking, current Web Builder, or boot output differs from the reviewed manual.
- Next action: Photograph the board revision and kit contents, complete E-16/E-17, then generate and archive the first UF2.

<a id="elog-20260607140221"></a>
### 🟩 2026-06-07 14:02:21 -0500 - SUCCESS - Animated pen-up preview travel

- Status: success
- Category: software, testing
- Summary: Made pen-up travel visibly interpolate from the lift point to its destination and paced it with the configured travel command duration.
- Reason: The full travel overlay appeared immediately and fixed 100 mm/s pacing made rapid moves look like endpoint jumps during playback.
- Struggle/failure: Coordinate interpolation already existed, so the initial assumption that travel positions were not interpolated was incomplete; the premature full-segment overlay was the main visual defect.
- Evidence: Change note `WSW-20260607-006`; synthetic midpoint/timing test; sample-preview travel checks; Python compilation; `git diff --check`; documentation index validation.
- Files/commit: `software/qt_svg_to_gcode.pyw`, `software/README.md`, `docs/HANDOFF.md`, `docs/changes/`, `docs/project/ENGINEERING_LOG.md`; commit not yet created.
- Result: The gray pen-up marker and active route now advance continuously across each travel command.
- Retry conditions: Revisit travel pacing after measured RP23CNC coordinated X/Y/A rapid behavior is available.
- Next action: Verify perceived playback speed against the assembled machine once axis rates are calibrated.

<a id="elog-20260607131627"></a>
### 🟩 2026-06-07 13:16:27 -0500 - SUCCESS - Added cooperative preview cancellation

- Status: success
- Category: software
- Summary: Added a Cancel button and cooperative cancellation checkpoints throughout preview geometry and motion generation.
- Reason: Accidental high-density settings or very large contour files could leave preview generation running for an unreasonable time with no safe way to stop it.
- Struggle/failure: Forced thread termination was rejected because it could corrupt Qt, OpenGL, Python, or geometry-cache state. Stage-boundary-only cancellation was insufficient for nested fill loops.
- Evidence: Change note `WSW-20260607-005`; core cancellation tests for gyroid generation and a 5,000-point plan; offscreen Qt lifecycle test retained the previous 527-command preview and restored controls; Python compilation; `git diff --check`.
- Files/commit: `software/qt_svg_to_gcode.pyw`, `software/converter_core/cancellation.py`, `geometry.py`, `kinematics.py`, `gcode.py`, `software/README.md`, `docs/HANDOFF.md`, `docs/changes/`, `docs/project/ENGINEERING_LOG.md`; commit not yet created.
- Result: Preview creation can be safely stopped without force-closing the program or losing the last successful preview.
- Retry conditions: Add more checkpoints if a measured operation remains unresponsive to cancellation for an unacceptable interval.
- Next action: Consider applying the same worker/cancellation pattern to Save G-code if large synchronous conversions become disruptive.

<a id="elog-20260607122144"></a>
### 🟩 2026-06-07 12:21:44 -0500 - SUCCESS - Added single-file engineering-log topic navigation

- Status: success
- Category: documentation, project management
- Summary: Added generated high-level topic views and stable anchors to the existing chronological engineering log without copying entry bodies.
- Reason: The chronological log will become difficult to browse by subsystem, but splitting or duplicating entries would weaken the single source of truth.
- Struggle/failure: Historical entries recorded only as `Before 2026-06-05` initially generated duplicate date-based anchors; title slugs were added for date-only entries.
- Evidence: Change note `WSW-20260607-004`; `python tools\docs_index.py --write`; `python tools\docs_index.py --check`; Python compilation; `git diff --check`.
- Files/commit: `docs/project/ENGINEERING_LOG.md`, `tools/docs_index.py`, `docs/README.md`, `AGENTS.md`, `docs/changes/`; commit not yet created.
- Result: One Markdown file now supports chronological reading and topic-based lookup while storing each full event exactly once.
- Retry conditions: Introduce separate archive files only after the documented engineering-log scaling threshold is reached.
- Next action: Categorize future events accurately and regenerate the indexes after edits.

<a id="elog-20260607120221"></a>
### 🟩 2026-06-07 12:02:21 -0500 - SUCCESS - Reduced documentation navigation and indexing friction

- Status: success
- Category: documentation, project management
- Summary: Added task-oriented documentation navigation, clarified document ownership, reduced duplicate recording requirements, and automated categorized change indexes and link validation.
- Reason: The initial organization was searchable but would become clunky because onboarding began with a 483-line reference and each note required manual edits to several indexes.
- Struggle/failure: Treating every incidental edit as both a change note and engineering-log event would make the record noisier than the project. Rewriting the full technical handoff would risk losing valuable rationale.
- Evidence: Change note `WSW-20260607-003`; `python tools\docs_index.py --check`; Python compilation; `git diff --check`.
- Files/commit: `docs/README.md`, `tools/docs_index.py`, `AGENTS.md`, `docs/START_HERE.md`, `docs/HANDOFF.md`, `docs/changes/`, `docs/project/ENGINEERING_LOG.md`; commit not yet created.
- Result: Contributors can navigate by task, meaningful history remains preserved, and category indexes cannot silently drift from note metadata.
- Retry conditions: Split large historical files only when search and task-oriented navigation no longer provide adequate access.
- Next action: Use generated indexes and keep detailed information in one authoritative location with links elsewhere.

<a id="elog-20260607115739"></a>
### 🟩 2026-06-07 11:57:39 -0500 - SUCCESS - Made continuous maintainability a repository requirement

- Status: success
- Category: documentation, decision
- Summary: Added explicit instructions requiring focused cleanup, technical-debt tracking, proportional verification, and evidence-based optimization during future work.
- Reason: Long-running projects become difficult to modify when maintainability depends on conversational memory or occasional cleanup requests.
- Struggle/failure: The expectation had been stated in conversation but was not yet encoded in repository instructions, so a new thread could miss it.
- Evidence: `AGENTS.md` maintainability section, `docs/START_HERE.md`, and change note `WSW-20260607-002`.
- Files/commit: `AGENTS.md`, `docs/START_HERE.md`, `docs/changes/`, `docs/project/ENGINEERING_LOG.md`; commit not yet created.
- Result: Future threads opened in this repository receive the maintainability policy automatically.
- Retry conditions: Revise the policy when a recurring maintenance problem demonstrates that the current rules are insufficient.
- Next action: Apply the policy during each implementation and add concrete larger cleanup work to the roadmap when discovered.

<a id="elog-20260607115128"></a>
### 🟩 2026-06-07 11:51:28 -0500 - SUCCESS - Added categorized change documentation and preview progress

- Status: success
- Category: software, documentation
- Summary: Added responsive preview generation with stage, percentage, and elapsed-time feedback, then established indexed Windows-software, RP23CNC-software, and hardware change streams with mandatory repository instructions.
- Reason: Preview generation provided no indication of active work, and subsystem changes were difficult to find inside the long chronological handoff and engineering log.
- Struggle/failure: The first progress widget reused the existing numeric `preview_progress` playback field; integration testing caught the collision. A background geometry path also contained a direct Qt log write and was corrected to avoid cross-thread widget access.
- Evidence: `python -m py_compile software\qt_svg_to_gcode.pyw`; `git diff --check`; offscreen PySide6 preview test generated 527 commands and restored controls; `docs/changes/windows-software/2026/2026-06-07-preview-build-progress.md`.
- Files/commit: `software/qt_svg_to_gcode.pyw`, `software/README.md`, `AGENTS.md`, `CLAUDE.md`, `docs/changes/`, `docs/START_HERE.md`, `docs/HANDOFF.md`, `docs/project/ROADMAP.md`; commit not yet created.
- Result: Preview work is visible and non-blocking, and future changes now require a categorized note plus the chronological audit entry without waiting for an owner reminder.
- Retry conditions: Replace stage-based percentages only if core geometry/planner APIs provide reliable item-level callbacks.
- Next action: Use the new category indexes for all subsequent converter, RP23CNC, firmware, hardware, and wiring changes.

<a id="elog-20260606210916"></a>
### 🟨 2026-06-06 21:09:16 -0500 - MIXED/OPEN - Identified exact purchased RP23CNC kit

- Status: mixed/open
- Category: hardware, firmware, documentation
- Summary: Identified the purchased controller as Brookwood Design RP23CNC variant `48493912129751`, With Assembly and Ethernet Kits.
- Reason: Generic RP23CNC assumptions needed to be tied to the exact purchased configuration.
- Struggle/failure: The product title can sound assembled, but the listing explicitly requires the customer to solder connectors and Ethernet components.
- Evidence: https://brookwood-design-77.myshopify.com/products/ro?variant=48493912129751 and https://www.grbl.org/rp23u5xbb
- Files/commit: BOM, wiring table, test plan, roadmap, and `firmware/grblhal/README.md`; commit recorded after this entry.
- Result: Kit inventory, soldering, visual inspection, continuity, and power-rail checks are now required before board power or firmware bring-up.
- Retry conditions: Mark assembly tasks complete only after E-16 and E-17 evidence exists.
- Next action: Record the received PCB revision and photograph all kit contents before soldering.

<a id="elog-20260606185824"></a>
### 🟩 2026-06-06 18:58:24 -0500 - SUCCESS - Added roadmap completion checkboxes

- Status: success
- Category: documentation, project management
- Summary: Converted every roadmap phase and task into Markdown checklists and separated previously combined phases.
- Reason: Completion state needed to be visible at both phase and task level in VS Code Markdown Preview.
- Struggle/failure: The earlier roadmap used prose bullets and a status table, so individual task completion could not be marked.
- Evidence: `docs/project/ROADMAP.md`.
- Files/commit: `docs/project/ROADMAP.md`, `docs/project/ENGINEERING_LOG.md`; commit recorded after this entry.
- Result: Phase 0 is checked; all unverified hardware, firmware, motion, toolhead, integration, and report tasks remain unchecked.
- Retry conditions: Check tasks only when evidence exists; do not use partial completion as completed.
- Next action: Begin Phase 1 and update boxes as electrical tests pass.

<a id="elog-20260606185401"></a>
### 🟩 2026-06-06 18:54:01 -0500 - SUCCESS - Promoted RP23CNC upstream reference

- Status: success
- Category: documentation, firmware
- Summary: Added `phil-barrett/RP23CNC` as the canonical board reference in onboarding, architecture, firmware, and controller-configuration documentation.
- Reason: Board schematics, revisions, pin assignments, and RP23CNC-specific guidance must remain traceable to the upstream hardware repository.
- Struggle/failure: The link previously appeared only in the BOM source list and was easy to miss during controller work.
- Evidence: https://github.com/phil-barrett/RP23CNC
- Files/commit: `docs/START_HERE.md`, `docs/architecture/SYSTEM_ARCHITECTURE.md`, `firmware/README.md`, `firmware/grblhal/README.md`, `firmware/grblhal/config/README.md`; commit recorded after this entry.
- Result: Controller-facing documents now point directly to the authoritative upstream repository.
- Retry conditions: Replace the link only if the upstream project relocates.
- Next action: Record the exact received RP23CNC board revision and archive the matching schematic before pin assignment.

<a id="elog-20260606184528"></a>
### 🟥 2026-06-06 18:45:28 -0500 - STRUGGLE - Misinterpreted requested log structure

- Status: struggle
- Category: documentation
- Summary: Split struggles into a separate topic-based document even though the requested design was one chronological record containing both struggles and successes.
- Reason: The phrase "alongside the chronology" was interpreted as a separate file instead of interleaved chronological entries.
- Struggle/failure: This reduced the ability to see the sequence from failure to resolution.
- Evidence: Project-owner correction after commit `1ef58cb`.
- Files/commit: `1ef58cb`; corrected by the commit following this entry.
- Result: Separate register removed and all records returned to this chronology.
- Retry conditions: Create a separate failure register only after explicit approval.
- Next action: Use colored status markers while preserving strict chronological order.

<a id="elog-20260606184106"></a>
### 🟥 2026-06-06 18:41:06 -0500 - STRUGGLE - Separated struggles from chronology

- Status: struggle
- Category: documentation
- Summary: Moved the topic-based failure index into a separate document.
- Reason: Attempted to optimize lookup by topic.
- Struggle/failure: The change contradicted the intended single chronological narrative.
- Evidence: Commit `1ef58cb` and subsequent project-owner correction.
- Files/commit: `1ef58cb`.
- Result: Rejected and reversed.
- Retry conditions: Do not retry without explicit approval.
- Next action: Keep struggles interleaved with successes by occurrence time.

<a id="elog-20260606183731"></a>
### 🟩 2026-06-06 18:37:31 -0500 - SUCCESS - Required failure details in log

- Status: success
- Category: documentation
- Summary: Made failures, blockers, rejected approaches, and recovery details mandatory parts of the engineering chronology.
- Reason: Future contributors and AI sessions must not repeatedly attempt approaches that already failed.
- Struggle/failure: The initial log emphasized successful commits and did not make difficult debugging history easy to search.
- Evidence: Existing debugging history in `docs/HANDOFF.md` and recent hardware-source conflicts.
- Files/commit: `docs/project/ENGINEERING_LOG.md`; commit recorded after this entry.
- Result: Added failure-specific fields and a searchable index of known struggles.
- Retry conditions: Add or revise an indexed item whenever new evidence changes why an approach might work.
- Next action: Log future failed tests at the time they occur, including exact configuration and evidence.

<a id="elog-20260606183425"></a>
### 🟩 2026-06-06 18:34:25 -0500 - SUCCESS - Established rolling engineering chronology

- Status: success
- Category: documentation
- Summary: Created this engineering log and reconstructed the major project milestones from Git commit timestamps.
- Reason: The Systems Integration report and AI handoffs require a reliable dated account of software, hardware, wiring, test, and decision work.
- Struggle/failure: Earlier history was distributed across Git messages and a long handoff document rather than one chronology.
- Evidence: Repository Git history through commit `87cf328`.
- Files/commit: `docs/project/ENGINEERING_LOG.md`; commit recorded after this entry.
- Result: Updating this log is now part of the mandatory session handoff procedure.
- Retry conditions: Not applicable.
- Next action: Use actual timestamps for future work and link detailed bench measurements to dated lab notes.

<a id="elog-20260606181652"></a>
### 🟨 2026-06-06 18:16:52 -0500 - MIXED/OPEN - Selected adjustable toolhead buck converter

- Status: mixed/open
- Category: hardware, wiring
- Summary: Selected two purchased B085T73CSD adjustable buck modules for the toolhead's 6 V supply. Existing fixed 5 V modules became spares.
- Reason: The adjustable module can supply the actuator's rated 6 V and has more claimed current margin.
- Struggle/failure: The previous fixed 5 V module was below the motor's rated voltage and had marginal unverified current capacity.
- Evidence: Amazon listing supplied by the project owner; acceptance tests E-14 and E-15 remain open.
- Files/commit: `87cf328`; `docs/hardware/BOM.md`, `docs/hardware/WIRING_TABLE.md`, `docs/testing/TEST_PLAN.md`.
- Result: Selected but not bench-verified. Output must be set with a multimeter before connecting the DRV8833.
- Retry conditions: Reconsider another regulator if E-15 shows unacceptable droop, ripple, or temperature.
- Next action: Inspect module terminals, set 6.0 V, and characterize it under actuator load.

<a id="elog-20260606180405"></a>
### 🟥 2026-06-06 18:04:05 -0500 - STRUGGLE - Fixed 5 V buck was marginal

- Status: struggle
- Category: hardware, wiring
- Summary: Added B0F1WB3LJ5 fixed 5 V buck modules as an actuator-supply candidate.
- Reason: The project owner already had these modules available.
- Struggle/failure: Listing current limits left insufficient confidence for actuator stall or seek loads, and fixed 5 V sacrifices motor performance.
- Evidence: Listing specified about 1.5 A continuous and 1.8 A maximum output.
- Files/commit: `164bcdc`.
- Result: Later superseded for the actuator by the adjustable B085T73CSD module; retained as a spare for lower-current 5 V loads.
- Retry conditions: Use for the actuator only if measured demand is comfortably below its tested continuous capacity and 5 V performance is acceptable.
- Next action: Use only where measured load and thermal margin are acceptable.

<a id="elog-20260606173843"></a>
### 🟨 2026-06-06 17:38:43 -0500 - MIXED/OPEN - Documented received S-120-12 terminal layout

- Status: mixed/open
- Category: hardware, wiring, documentation
- Summary: Corrected the main supply model to MEISHILE S-120-12 and documented terminals 1-7: L, N, protective earth, -V, -V, +V, +V, plus the adjacent +V ADJ control.
- Reason: Physical unit inspection superseded inconsistent reseller model information.
- Struggle/failure: Reseller data named a different model, and the QR-linked PDF was a web-viewer capture with little extractable text.
- Evidence: Project-owner inspection and archived QR-linked PDF `docs/hardware/references/MEISHILE-S-120-12-manual.pdf`.
- Files/commit: `a15ce9d`.
- Result: Supply terminal functions are documented. Mains enclosure, fusing, earth continuity, and DC branch allocation remain unresolved.
- Retry conditions: Re-extract or OCR the PDF only if a specific unreadable manual detail is needed.
- Next action: Complete test E-11 before applying power.

<a id="elog-20260606172407"></a>
### 🟥 2026-06-06 17:24:07 -0500 - STRUGGLE - Reseller power data was contaminated

- Status: struggle
- Category: hardware, documentation
- Summary: Added internally consistent same-ASIN details from Ubuy.
- Reason: The secondary listing exposed more product fields than Amazon.
- Struggle/failure: The same page mixed contradictory 30 A / 360 W specifications from another product.
- Evidence: Ubuy page for ASIN B0781ZJ7GP.
- Files/commit: `be5a6a3`.
- Result: Recorded useful secondary data but rejected contradictory 30 A / 360 W text as listing contamination.
- Retry conditions: Accept conflicting data only if confirmed by the received unit or manufacturer documentation.
- Next action: Prefer physical markings and manufacturer documentation over reseller text.

<a id="elog-20260606160510"></a>
### 🟨 2026-06-06 16:05:10 -0500 - MIXED/OPEN - Selected 12 V main power supply

- Status: mixed/open
- Category: hardware
- Summary: Added the MEISHILE 12 V, 10 A, 120 W supply to the BOM, wiring table, and electrical tests.
- Reason: Project owner identified the purchased main supply.
- Evidence: Amazon ASIN B0781ZJ7GP.
- Files/commit: `3a3ffab`.
- Result: Supply selected; ratings still require confirmation from the received unit and bench measurements.
- Next action: Verify output voltage, adjustment, protection, and thermal margin.

<a id="elog-20260606155507"></a>
### 🟩 2026-06-06 15:55:07 -0500 - SUCCESS - Created authoritative wiring table

- Status: success
- Category: wiring, documentation
- Summary: Added a status-driven master table covering power, motion, motor phases, safety, toolhead, and communications.
- Reason: The system needed a continuously updated physical connection record rather than relying on a conceptual diagram.
- Evidence: `docs/hardware/WIRING_TABLE.md`.
- Files/commit: `bf2f5f7`.
- Result: All uncertain terminals remain TBD and require evidence before status promotion.
- Next action: Update the table after every component inspection, pin assignment, or wiring test.

<a id="elog-20260606154605"></a>
### 🟩 2026-06-06 15:46:05 -0500 - SUCCESS - Organized hardware integration and expanded converter behavior

- Status: success
- Category: software, hardware, documentation
- Summary: Added the AI handoff structure, BOM, interfaces, roadmap, tests, architecture decisions, firmware placeholders, and report templates. Also committed accumulated converter fill-planning and preview changes.
- Reason: Prepare for RP23CNC integration, repeatable AI handoffs, and Systems Integration reporting.
- Evidence: Repository documents and Python syntax validation.
- Files/commit: `b0ecd9a`.
- Result: Project structure now mirrors host software, motion firmware, toolhead control, testing, and reporting responsibilities.
- Next action: Complete electrical characterization before powered integration.

<a id="elog-20260605105612"></a>
### 🟩 2026-06-05 10:56:12 -0500 - SUCCESS - Updated sparse-infill handoff notes

- Status: success
- Category: software, documentation
- Summary: Consolidated the implemented sparse-infill behavior and known constraints in the handoff.
- Struggle/failure: Pattern generation required repeated fixes for clipping, compound regions, and preserving distinct lattice geometry.
- Files/commit: `a3b1459`.
- Result: Converter state became reproducible for the next development session.
- Retry conditions: Revisit algorithms when a repeatable SVG regression case demonstrates incorrect geometry.

<a id="elog-20260605092307"></a>
### 🟨 2026-06-05 09:23:07 -0500 through 10:50:32 -0500 - MIXED/OPEN - Developed sparse fill patterns

- Status: mixed/open
- Category: software
- Summary: Added selectable fill patterns, expanded pattern options, clipped generated geometry to boundaries and compound regions, introduced shared lattices, and preserved pattern identity.
- Reason: Support reportable, distinct fill strategies while keeping generated pen paths inside artwork regions.
- Struggle/failure: Early pattern implementations crossed boundaries, disappeared at edges, or collapsed different patterns into similar geometry.
- Evidence: Commits `03b8a1b`, `feb05b7`, `132241c`, `f476730`, `60f8d6d`, `cf4154c`, `34e7275`, `0ed21ee`, and `302ac5c`.
- Result: Converter supports multiple clipped sparse-infill strategies.
- Retry conditions: Replace the current clipping/generation approach only with regression coverage for compound and boundary cases.
- Next action: Validate generated patterns on physical hardware after motion bring-up.

<a id="elog-20260605090940"></a>
### 🟩 2026-06-05 09:09:40 -0500 through 09:15:25 -0500 - SUCCESS - Added preview navigation

- Status: success
- Category: software
- Summary: Added preview zoom controls followed by mouse zoom and pan interactions.
- Evidence: Commits `56a78ef` and `c3bb3ee`.
- Result: Artwork and motion previews are easier to inspect.

<a id="elog-20260605090415"></a>
### 🟩 2026-06-05 09:04:15 -0500 - SUCCESS - Chose RP23CNC and grblHAL

- Status: success
- Category: decision, firmware
- Summary: Recorded RP23CNC with grblHAL as the motion-control architecture.
- Reason: Reuse proven G-code parsing, coordinated planning, acceleration, homing, limits, and step generation.
- Evidence: Commit `690617b`; ADR-001 was added later.
- Result: Custom firmware is limited to configuration and toolhead integration unless a demonstrated requirement requires more.
- Next action: Identify the exact board revision and reproduce a known grblHAL build.

<a id="elog-20260605082830"></a>
### 🟩 2026-06-05 08:28:30 -0500 - SUCCESS - Established project repository

- Status: success
- Category: software, documentation
- Summary: Committed the initial SVG-to-G-code converter project, firmware/report folders, samples, and handoff documentation.
- Evidence: Commit `f3e2162`.
- Result: Created the baseline for subsequent software and integration work.

<a id="elog-20260605-opengl-preview-type-and-binding-bugs"></a>
### 🟥 Before 2026-06-05 - Time not recorded - STRUGGLE - OpenGL preview type and binding bugs

- Status: struggle
- Category: software
- Summary: Preview development encountered repeated paint exceptions, incorrect bed rotation, a theta uniform stuck at zero, and brittle VBO attribute binding.
- Reason: PySide6/OpenGL type and overload behavior differed from assumptions in the original implementation.
- Struggle/failure: `QVector4D` was unpacked as a tuple; bed theta sign was reversed; generic scalar `setUniformValue` selected an integer overload; raw `glVertexAttribPointer` was unreliable.
- Evidence: Resolved debugging history in `docs/HANDOFF.md`.
- Files/commit: Exact originating commits were not preserved in the current Git history.
- Result: Return a tuple, use positive bed theta, call `setUniformValue1f`, and use `setAttributeBuffer`.
- Retry conditions: Do not restore the failed forms without focused regression tests.
- Next action: Preserve future debugging events at the time they occur.

<a id="elog-20260605-theta-dp-winding-reference-failed"></a>
### 🟥 Before 2026-06-05 - Time not recorded - STRUGGLE - Theta DP winding reference failed

- Status: struggle
- Category: software
- Summary: A tangent-following winding reference excluded valid low-winding theta solutions.
- Reason: The reference itself accumulated winding, moving desirable candidates outside the search window.
- Struggle/failure: Candidate winding was encoded relative to a moving, winding reference.
- Evidence: Kinematics gotchas in `docs/HANDOFF.md`.
- Files/commit: Exact originating commit not recorded.
- Result: Use principal angles and nearest-wrap edge costs so winding emerges from the selected path.
- Retry conditions: Do not retry tangent-reference anchoring.
- Next action: Add a hard net-winding constraint later if cable management requires it.

<a id="elog-20260605-hold-steady-theta-grid-tradeoff"></a>
### 🟨 Before 2026-06-05 - Time not recorded - MIXED/OPEN - Hold-steady theta grid tradeoff

- Status: mixed/open
- Category: software, decision
- Summary: A 45-degree orientation grid made planning and execution much faster but left the bed stationary for roughly 94% of segments.
- Reason: Uniform hold-steady candidates dominated the motion cost.
- Struggle/failure: The faster result conflicted with the project goal that theta visibly participates in curve generation.
- Evidence: Measurements recorded in `docs/HANDOFF.md`.
- Files/commit: Exact experiment commit not recorded.
- Result: Grid disabled by default.
- Retry conditions: Enable only when throughput is explicitly prioritized over visible theta participation.
- Next action: Keep the tradeoff available as a documented non-default option.

<a id="elog-20260806-added-viewable-pc817-wiring-diagram"></a>
### 🟩 2026-08-06 - SUCCESS - Added viewable PC817 wiring diagram

- Status: success
- Category: hardware, documentation
- Summary: Added a standalone SVG electrical diagram for the three PC817C
  perfboard paths, including diode orientation, local pullups/filters, isolated
  grounds, and the gated A-home R6 connection.
- Evidence: `hardware/pc817-interface/pc817-perfboard-wiring-schematic.svg`.
- Result: The circuit can be inspected without relying on a Mermaid renderer or
  opening KiCad. `PERFBOARD_BUILD.md` remains the construction source of truth.
- Next action: Complete E-18 before fitting R6 or attaching the controller
  A-home wire.

<a id="elog-20260806-added-annotated-perfboard-build-map"></a>
### 🟩 2026-08-06 - SUCCESS - Added annotated perfboard build map

- Status: success
- Category: hardware, documentation
- Summary: Added an annotated component-side view of the exact 14 × 6 perfboard
  arrangement so build callouts can be read without interpreting the KiCad view.
- Evidence: `hardware/pc817-interface/pc817-perfboard-callouts.svg`.
- Result: The electrical schematic and physical component placement now have
  distinct, directly viewable diagrams.

<a id="elog-20260806-added-translucent-interconnection-overlay"></a>
### 🟩 2026-08-06 - SUCCESS - Added translucent interconnection overlay

- Status: success
- Category: hardware, documentation
- Summary: Added a translucent component-side board view with every underside
  electrical net overlaid in a distinct color and a pin/pad legend.
- Evidence: `hardware/pc817-interface/pc817-perfboard-interconnections.svg`.
- Result: The user can inspect logical component interconnections visually while
  retaining `PERFBOARD_BUILD.md` as the physical wiring source of truth.

<a id="elog-20260808-added-no-overlap-pc817-schematic"></a>
### 🟩 2026-08-08 - SUCCESS - Added no-overlap PC817 schematic

- Status: success
- Category: hardware, documentation
- Summary: Added a conventional, row-separated schematic for U1, U2, and U3
  so every connection can be followed without crossing wires.
- Evidence: `hardware/pc817-interface/pc817-clean-schematic.svg`.
- Result: The project has separate visual artifacts for physical placement,
  logical net overlay, and clear electrical signal flow.

<a id="elog-20260809-verified-rp23cnc-a-home-electrical-requirement"></a>
### 🟨 2026-08-09 - MIXED/OPEN - Verified RP23CNC A-home electrical requirement

- Status: mixed/open
- Category: hardware
- Summary: Reviewed RP23CNC V1.0 schematic page 4. The A-axis `LIMA` input is
  a 12 V active-low, switch-to-`GND1` optocoupler-input path with a 2 kΩ series
  resistor, not a 3.3 V or 5 V logic input.
- Evidence: `https://github.com/phil-barrett/RP23CNC/blob/main/Schematic/V1.0%20schematic.pdf`, page 4; `Documentation/featurelist.md` identifies limit inputs as 12 V compatible.
- Result: The expected idle input voltage is approximately 12 V and assertion
  is a low-side sink. However, the generic purchased PC817C is specified at a
  50% minimum CTR at 5 mA; U3's approximately 5 mA LED drive cannot guarantee
  the approximately 5.3 mA required by this input. R6/A_HOME remains open.
- Next action: Add and test a controller-side output driver, or select an
  optocoupler with guaranteed CTR sufficient for the 5.3 mA sink load.

<a id="elog-20260810-minimized-and-verified-pc817-layout"></a>
### 🟩 2026-08-10 - SUCCESS - Minimized and verified PC817 layout

- Status: success with bench follow-up
- Category: hardware, rp23cnc-software
- Summary: Rebuilt the 14 × 6 all-through-hole PC817 interface around
  channel-aligned connector pins, rotated reverse-direction U3 180 degrees,
  omitted optional C3 rail bypassing, and moved `HOME_ARM` from unavailable GP10 to
  exposed GPIO20.
- Reason: The original perfboard was difficult to wire and its recovered route
  contained electrical errors. Bench work also found U1 pin 2 unconnected and
  an unresolved GP8 idle-pullup fault.
- Evidence: KiCad 10.0.5 reports zero ERC errors, zero error-level DRC errors,
  zero unconnected items, and zero schematic-parity issues. Route complexity
  fell from 110 segments / 337.35 mm to 38 segments / 161.83 mm with no vias.
  An exported-netlist audit matched all 46 schematic component pins to their
  PCB reference/pad/net assignments.
  The installed U3 sample switched a 12 V / 2.2 kΩ test load from about 12 V
  idle to 0.2 V asserted. The GPIO20 firmware compiled for
  `rp2040:rp2040:sparkfun_promicrorp2350` at 73,212 bytes program storage and
  11,708 bytes dynamic memory.
- Result: `pc817-perfboard-v2-minwire.kicad_pcb` is the current rebuild source.
  Firmware and interface documents now use GPIO20 for `HOME_ARM`.
- Next action: Rebuild, verify U1/U2 idle and asserted levels, repeat the U3
  load test, then fit R6 only if U3 passes.

<a id="elog-20260810-passed-all-pc817-bench-channels"></a>
### 🟩 2026-08-10 - SUCCESS - Passed all PC817 bench channels

- Status: success with controller-harness follow-up
- Category: hardware
- Summary: Completed U1, U2, U3, and isolation tests on the assembled
  three-channel PC817 board.
- Struggle/failure: U1 initially had its pin-2/ENA connection missing. U2
  initially failed because one wire was disconnected. GP8 initially read low
  because the Pro Micro 3.3 V/GND wires had not been connected to the tool-side
  terminal.
- Evidence: After repairs, U1 GP8 was 3.311 V unloaded and the Pro Micro test
  sketch changed it HIGH/LOW as ENA was opened/grounded. U2 GPIO20 likewise
  changed HIGH/LOW as AUX0 was opened/grounded. U3 held about 12 V idle and
  0.2 V asserted through the 12 V / 2.2 kΩ simulated `LIMA` load. Final
  `CTRL_GND` to `TOOL_GND` continuity test was open.
- Result: The board's three isolated channels work with the specified bench
  stimuli. A direct `A_HOME` wire or 0 Ω R6 link is valid for the tested U3
  sample.
- Next action: Do not infer actual RP23CNC ENA/Aux0 terminal behavior from the
  simulation; complete F-05 and the remaining E-18 system tests before
  connecting the controller harness.

<a id="elog-20260810-recorded-recommended-system-test-sequence"></a>
### 🟩 2026-08-10 - SUCCESS - Recorded recommended system test sequence

- Status: implemented
- Category: hardware, rp23cnc-software
- Summary: Added a separate dependency-ordered operating sequence for the
  existing test plan, from pre-power inspection through integrated validation.
- Reason: The formal test plan defines individual pass conditions but did not
  provide a concise execution order for safe staged bring-up.
- Evidence: `docs/testing/RECOMMENDED_TEST_SEQUENCE.md`.
- Result: The sequence makes E-17, supply/regulator checks, F-05, E-18,
  N20 no-load testing, and T-01 explicit gates before their dependent work.
- Next action: Record bench results in `TEST_PLAN.md` and dated lab notes as
  tests are actually performed.

<a id="elog-20260810-adopted-direct-header-toolhead-harness"></a>
### 🟩 2026-08-10 - SUCCESS - Adopted direct-header toolhead harness

- Status: implemented, harness verification pending
- Category: hardware, rp23cnc-software
- Summary: Adopted separate board-specific connectors: DRV8833 logic on
  consecutive GP4–GP7 and PC817 on consecutive `GND`, `RST` NC, `3V3`, GP29,
  GP28, GP27.
- Evidence: `hardware/pc817-interface/PRO_MICRO_JST_HARNESS.md` and the
  regenerated v2 KiCad design.
- Result: PC817 firmware signals are now GP29 M3/M5, GP28 HOME_ARM, and GP27
  A_HOME; no connector position uses reset.
- Next action: Repeat E-18 U1/U2/U3/isolation checks after repinning.

<a id="elog-20260811-reconciled-e-stop-and-hd064rt-topology"></a>
### 🟨 2026-08-11 - HARDWARE/PLANNED - Reconciled E-stop and HD064RT topology

- Status: planned; E-19 required before any powered operation.
- Category: hardware, rp23cnc-software
- Summary: Recorded the installed HCDC HD064RT eight-channel DIN fuse module as
  the post-relay motor/tool distribution point and assigned the purchased
  mxuteuk HB2-BS544's two NC contacts independently to RP23CNC Halt and K1
  coil interruption.
- Reason: Earlier advice incorrectly proposed redundant inline holders instead
  of using the installed DIN distribution hardware.
- Result: The planned E-stop topology keeps RP23CNC alive on a separately fused
  control branch while K1 removes positive 12 V from HD064RT OUT1-OUT4 (X, Y,
  A, and D36V50F6). E-19 is the required verification gate.
- Evidence: `docs/hardware/ESTOP_TOPOLOGY.md`, the purchased-switch wiring
  diagram, `docs/hardware/references/RP23CNC-user-manual.pdf` pages 4, 9, 29,
  and 30, and the HD064RT product identification.
- Risk: K1 selection, physical RP23CNC E-stop terminals/polarity, FMAIN/FCTRL
  hardware, branch fuse values, and all powered behavior remain unverified.

<a id="elog-20260811-reassigned-hx711-to-adjacent-gp0-gp1-pins"></a>
### 🟩 2026-08-11 - SUCCESS - Reassigned HX711 to adjacent GP0/GP1 pins

- Status: implemented; bench verification pending.
- Category: hardware, rp23cnc-software
- Summary: Moved HX711 `DOUT` and `SCK` from GP2/GP3 to GP0/GP1 so the sensor
  JST can use a cleaner adjacent-header location beside the crowded PC817
  harness.
- Evidence: `docs/hardware/WIRING_TABLE.md` rows TH-010/TH-011 and both
  matching Arduino sketches.
- Result: GP0 is `DOUT`; GP1 is `SCK`; no existing project assignment uses
  either pin.
- Next action: Compile the updated sketches and complete E-07/E-08 after the
  physical sensor harness is connected.

<a id="elog-20260812-recorded-load-cell-wire-mapping"></a>
### 🟩 2026-08-12 - SUCCESS - Recorded load-cell wire mapping

- Status: documented; E-07 calibration pending.
- Category: hardware
- Summary: Recorded the selected uxcell 300 g load cell's supplied wire map:
  Red `EXC+` to HX711 `E+`, Black `EXC-` to `E-`, Green `SEN+` to `A+`, and
  White `SEN-` to `A-`.
- Evidence: Manufacturer specification supplied by the project owner.
- Next action: Verify the received connector and calibrate the installed load
  cell in E-07.

<a id="elog-20260812201639"></a>
### 🟨 2026-08-12 20:16:39 -0500 - MIXED/OPEN - Advanced toolhead perfboard wiring

- Status: physical assembly implemented; unpowered and powered verification pending.
- Category: hardware
- Summary: All intended Pro Micro toolhead connections and all four DRV8833
  logic pins were wired. The DRV8833 and S7V8F5 now share a perfboard, with a
  two-pin JST position reserved for the arriving 6 V twisted pair.
- Evidence: Project-owner work report; `docs/hardware/WIRING_TABLE.md` rows
  PWR-009 through PWR-011B and TH-002 through TH-005.
- Result: `OUT1` and `OUT2` remain intentionally open pending the 22 AWG
  twisted motor pair and unloaded direction test. New E-14B checks the
  completed perfboard before its first 6 V connection.
- Risk: No continuity, short-circuit, rail, driver-enable, or motor behavior
  result is implied by physical wiring alone.
- Next action: Complete the remaining E-14B signal/isolation checks and record
  exact rail readings; test the upstream D36V50F6 in E-14 before fitting the
  motor lead and running E-05/T-01.

<a id="elog-20260812202203"></a>
### 🟩 2026-08-12 20:22:03 -0500 - SUCCESS - Powered toolhead local branches from a 6 V bench supply

- Status: partial E-14B/E-15A pass; upstream and loaded testing pending.
- Category: hardware
- Summary: After continuity checks, a bench supply set to 6 V was connected to
  the toolhead JST. The DRV8833 received its correct supply rail, and the
  S7V8F5 supplied the Pro Micro at its correct voltage.
- Evidence: `docs/report/lab-notes/2026-08-12-e-14b-toolhead-local-power.md`.
- Result: The local 6 V branch and 5 V controller branch are now
  bench-verified. No motor was attached; no assertion is made about the
  upstream D36V50F6, cable harness, motor transients, noise, ripple, or heat.
- Next action: Record exact readings, complete/record the remaining E-14B
  isolation checks, then run E-14 and the remaining E-15A conditions.

<a id="elog-20260812202625"></a>
### 🟩 2026-08-12 20:26:25 -0500 - SUCCESS - Confirmed Pro Micro logic-harness continuity

- Status: E-14B signal continuity passed; controller-isolation recording and
  powered functional tests remain.
- Category: hardware
- Summary: Continuity was checked successfully for every currently wired
  conductor connected to the Pro Micro, including the DRV8833 logic interface.
- Evidence: Project-owner bench report; updated
  `docs/report/lab-notes/2026-08-12-e-14b-toolhead-local-power.md`.
- Result: The local physical pin map is now continuity-checked. This validates
  conductor endpoints, but does not prove firmware polarity, DRV8833 behavior,
  PC817 functional isolation, or motor direction.
- Next action: Record exact rail readings, test the D36V50F6 in E-14, and fit
  the motor pair only for E-05/T-01.

<a id="elog-20260812203500"></a>
### 🟥 2026-08-12 20:35:00 -0500 - STRUGGLE - Exact DRV8833 module corrected generic sleep/fault labels

- Status: initial interpretation was incorrect; resolved by the 2026-08-13 firmware correction.
- Category: hardware, rp23cnc-software
- Summary: The owner supplied Amazon ASIN B08RMWTDLM, identifying the installed
  ACEIRMC DRV8833 board. Its listing states that `ULT` is low-level sleep and
  `EEP` is the output-protection/fault pin, opposite the prior generic mapping.
- Struggle/failure: The existing GP6→`EEP` and GP7→`ULT` wires passed a
  continuity test, but continuity cannot detect swapped functional labels.
- Evidence: [ACEIRMC B08RMWTDLM product listing](https://www.amazon.com/dp/B08RMWTDLM),
  seller description; `docs/report/lab-notes/2026-08-12-e-14b-toolhead-local-power.md`.
- Result: The exact labels showed that the *existing physical harness* was
  right: GP7→`ULT` and GP6→`EEP`. The previously assigned firmware constants
  were reversed.
- Next action: Correct the firmware mapping, inspect the `J2` solder bridge,
  and complete E-14C before fitting the N20 or running any motor command.

<a id="elog-20260813-corrected-drv8833-firmware-mapping-without-harness-rework"></a>
### 🟩 2026-08-13 - SUCCESS - Corrected DRV8833 firmware mapping without harness rework

- Status: code mapping corrected; E-14C functional verification remains open.
- Category: hardware, rp23cnc-software
- Summary: Retained the continuity-checked ACEIRMC harness: GP7 drives `ULT`
  (low-true sleep) and GP6 reads `EEP` (protection/fault). Updated the bench
  and integrated firmware constants, wiring table, test plan, and harness note.
- Evidence: Project-owner continuity report and [ACEIRMC B08RMWTDLM product listing](https://www.amazon.com/dp/B08RMWTDLM).
- Result: No physical driver-end rewiring is needed. The software now drives
  the pin wired to `ULT` and reads the pin wired from `EEP`.
- Next action: With no motor connected, inspect/record J2 and run E-14C; then
  attach the motor only for the unloaded E-05 direction test.

<a id="elog-20260813-made-e-05-a-one-shot-boot-test"></a>
### 🟩 2026-08-13 - SUCCESS - Made E-05 a one-shot boot test

- Status: implemented; physical E-05 test pending.
- Category: hardware, rp23cnc-software
- Summary: Changed the N20 no-load direction sketch to wait three seconds after
  boot, run each direction for 500 ms with a two-second pause, then stop and
  sleep the DRV8833.
- Reason: A normal USB cable can back-power the Pro Micro's 5 V rail while the
  toolhead's 6 V supply is powering its local regulator. The test must work
  after USB is unplugged.
- Result: Upload with 6 V disconnected, unplug USB, then apply 6 V to perform
  the direction test. Serial output is optional rather than required.

<a id="elog-20260813-verified-n20-bidirectional-motion-at-the-toolhead"></a>
### 🟨 2026-08-13 - MIXED/OPEN - Verified N20 bidirectional motion at the toolhead

- Status: direction verified; connection reliability and no-load current remain open.
- Category: hardware, rp23cnc-software
- Summary: The one-shot E-05 test moved the N20 in both directions from a 6 V
  bench supply. Its first pulse retracted/lifted the pen; its reverse pulse
  moved the pen down.
- Evidence: Project-owner observation; during pre-motion diagnosis `ULT` rose
  to approximately 3.3 V, `EEP` remained approximately 2.98 V, and one output
  switched to the 6 V motor rail.
- Result: The installed code mapping GP7→`ULT`, GP6←`EEP`, and GP4/GP5 motor
  control are functionally proven. A suspected intermittent motor-path
  connection must be repaired and flex-tested before no-load current or loaded
  actuator work.
- Next action: Recheck and strain-relieve both `OUT1`/`OUT2` motor connections,
  record E-05 no-load current, then proceed to E-06 only with a current limit.

<a id="elog-20260814-repaired-intermittent-drv8833-output-solder-joint"></a>
### 🟩 2026-08-14 - SUCCESS - Repaired intermittent DRV8833 output solder joint

- Status: bidirectional motor drive is reliable; no-load current measurement remains open.
- Category: hardware
- Summary: The suspected motor-path intermittency was traced to one inadequately
  soldered DRV8833 output pin. The joint was repaired and the N20 now runs
  reliably under the E-05 one-shot direction test.
- Evidence: Project-owner post-repair test report.
- Result: The motor, output pair, driver, and tested firmware operate
  bidirectionally. The earlier output-path reliability risk is resolved.
- Next action: Measure and record E-05 no-load current at 6 V before any
  loaded/current-limited E-06 testing.

<a id="elog-20260814-passed-e-05-n20-no-load-current-test"></a>
### 🟩 2026-08-14 - SUCCESS - Passed E-05 N20 no-load current test

- Status: E-05 passed; loaded/stall characterization remains separate.
- Category: hardware
- Summary: At a 6.0 V bench input, toolhead idle current was 0.017 A. The N20
  drew 0.043 A while retracting/lifting and 0.043 A while lowering the pen.
- Evidence: Project-owner bench measurements after repair of the DRV8833 output
  solder joint.
- Result: The measured motor contribution is approximately 0.026 A in either
  direction, confirming low no-load demand on the current 6 V rail and driver.
- Next action: Do not hand-stall the actuator. Define a controlled E-06
  current-limited test only if its result is needed for the pen mechanism.

<a id="elog-20260814-passed-e-15a-toolhead-rails-during-n20-motion"></a>
### 🟩 2026-08-14 - SUCCESS - Passed E-15A toolhead rails during N20 motion

- Status: motor-only E-15A passed; sensor and final-rail characterization remain open.
- Category: hardware
- Summary: With a 6.0 V bench input, the DRV8833 motor rail held near 6 V and
  the S7V8F5 logic rail held near 5 V while the N20 moved in both directions.
  The Pro Micro did not reset.
- Evidence: Project-owner bench measurements and observation.
- Result: The present 6 V motor and local 5 V logic branches operate together
  without an observed rail collapse during the unloaded direction test.
- Next action: Characterize HX711/load cell and TMAG5273 separately; repeat
  power characterization after the upstream D36V50F6 is installed.

<a id="elog-20260814-required-complete-records-for-every-e-series-test"></a>
### 🟩 2026-08-14 - SUCCESS - Required complete records for every E-series test

- Status: implemented for future E-series work.
- Category: documentation, hardware
- Summary: Strengthened the test-plan and lab-note requirements so every E-*
  test records its configuration, procedure, measurements, difficulties,
  failed attempts, corrective actions, repeat result, and evidence. When code
  or commands are used, the exact test version is embedded in a code block.
- Reason: A simple pass/fail record does not preserve enough information to
  reproduce bench work or understand how a defect was overcome.
- Evidence: `docs/testing/TEST_PLAN.md`, `docs/report/LAB_NOTE_TEMPLATE.md`,
  and `docs/report/lab-notes/README.md`.
- Result: Future electrical-characterization tests have a consistent, auditable
  record that includes both failure/recovery history and passing evidence.

<a id="elog-20260814-started-e-07-hx711-calibration"></a>
### 🟨 2026-08-14 - MIXED/OPEN - Started E-07 HX711 calibration

- Status: test fixture and record prepared; bench readings pending.
- Category: hardware, rp23cnc-software
- Summary: Added a dedicated HX711-only E-07 sketch using GP0/GP1 and a dated
  lab note containing the exact source code, required power isolation, and
  known-mass procedure.
- Reason: Begin load-cell calibration without energizing the motor driver or
  combining sensor behavior with the separate TMAG5273 test.
- Evidence: `firmware/pen_pressure/e07_hx711_calibration/e07_hx711_calibration.ino`
  and `docs/report/lab-notes/2026-08-14-e-07-hx711-calibration.md`.
- Next action: Upload over USB with the 6 V JST disconnected; tare unloaded,
  record idle readings, then record stable deltas for known masses.

<a id="elog-20260814-hx711-first-raw-reading-attempt-passed-communication"></a>
### 🟨 2026-08-14 - MIXED/OPEN - HX711 first raw-reading attempt passed communication

- Status: electrical response proven; repeatable mechanical zero/calibration pending.
- Category: hardware
- Summary: The HX711 on GP0/GP1 reported ready data and large signed raw-count
  changes when the pen/load path was loaded. The initial unloaded tare was
  47,909 counts, but the resting zero shifted after the load was released.
- Struggle/failure: The first trial cannot be calibrated because the post-load
  condition did not return to the original mechanical baseline. This is likely
  force-path position/preload or friction/hysteresis, not an ADC communication
  fault.
- Evidence: Full serial capture is embedded in
  `docs/report/lab-notes/2026-08-14-e-07-hx711-calibration.md`.
- Next action: Repeat from a defined retracted/no-contact position, then use a
  scale or known forces at the pen tip to obtain two stable calibration points.

<a id="elog-20260814-prepared-e-07b-uart-toolhead-service-test"></a>
### 🟨 2026-08-14 - MIXED/OPEN - Prepared E-07B UART toolhead service test

- Status: firmware compiled; physical service-adapter harness not yet connected.
- Category: hardware, rp23cnc-software
- Summary: Prepared a GP20/GP21 UART1 diagnostic interface so the toolhead can
  retain its local 6 V/5 V/3.3 V power path while a PC receives HX711 telemetry
  and issues individual, safety-limited N20 steps. The Pro Micro USB-C port is
  unplugged during this test; the USB-to-TTL adapter connects GND/RX/TX only
  and its VCC remains open.
- Reason: The normal USB-C port would introduce a second 5 V source during
  motor-powered force calibration. Direct known-mass loading of the gray block
  proved the sensor but was mechanically nonrepeatable.
- Evidence: `firmware/pen_pressure/e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino`
  compiled with `arduino-cli` for `rp2040:rp2040:sparkfun_promicrorp2350`.
- Next action: Connect the service adapter, upload E-07B with 6 V disconnected,
  then test pen-tip force on a digital scale with 6 V enabled and the onboard
  USB-C unplugged.

<a id="elog-20260814-corrected-e-07b-uart1-serial-instance"></a>
### 🟨 2026-08-14 - MIXED/OPEN - Corrected E-07B UART1 serial instance

- Status: corrected firmware compiled; re-upload and live telemetry pending.
- Category: hardware, rp23cnc-software
- Summary: The UART adapter itself passed a TXD-to-RXD loopback test, but the
  first E-07B program had no output and GP20 was about 160 mV. Investigation of
  the installed Arduino-Pico core showed that `Serial1` is UART0; GP20/GP21 are
  UART1 and require the `Serial2` object. The sketch now uses `Serial2`.
- Struggle/failure: The original `Serial1` selection compiled successfully but
  could not route UART0 to GP20, so compilation alone was insufficient evidence
  of the intended UART pin mapping.
- Evidence: E-07B recompiled for `rp2040:rp2040:sparkfun_promicrorp2350` after
  the `Serial2` correction. Adapter loopback and voltage observations were
  reported by the project owner.
- Next action: Upload the corrected E-07B source with 6 V disconnected; then
  power the toolhead locally and confirm its startup banner at 115200 baud.

<a id="elog-20260814-passed-e-07b-uart-service-bring-up"></a>
### 🟩 2026-08-14 - SUCCESS - Passed E-07B UART service bring-up

- Status: GP20/GP21 UART telemetry is available for powered toolhead testing.
- Category: hardware, rp23cnc-software
- Summary: After re-uploading the corrected `Serial2` E-07B sketch, startup
  telemetry appeared through the DSD TECH SH-U09C2 adapter at 115200 baud while
  the toolhead operated from its local 6 V supply and the Pro Micro USB-C port
  was unplugged.
- Evidence: Project-owner live Serial Monitor observation; E-07 lab note and
  TH-016/TH-017 wiring-table entries.
- Result: The temporary service UART is verified. E-07 force calibration is
  still open and must now proceed through pen-tip/digital-scale measurements.

<a id="elog-20260814-first-e-07b-automated-pen-tip-contact"></a>
### 🟨 2026-08-14 - PARTIAL - First E-07B automated pen-tip contact

- Status: first instrumented contact point passed; repeatability and additional
  force levels remain open.
- Category: hardware, rp23cnc-software
- Summary: The first absolute load-cell threshold caused false positives from
  normal lead-screw/mechanism load transfer. The E-07B approach was revised to
  learn three no-contact 50 ms pulse changes and stop on a 50,000-count
  residual. The revised test stopped on pulse 4 at a measured 49.4 g / 0.485 N
  pen-tip force, reporting `hx_delta=-284196` and `residual=-124308`.
- Evidence: live UART capture and scale observation recorded in the dated E-07
  lab note; provisional magnitude is about 5,753 counts/g with negative sign.
- Next action: lift off, verify return-to-zero, and record at least two more
  gentle scale-force points before setting a production calibration factor.

<a id="elog-20260814-passed-e-08-hx711-rate-and-noise-measurement"></a>
### 🟩 2026-08-14 - SUCCESS - Passed E-08 HX711 rate and noise measurement

- Status: the installed force-loop timing evidence is available.
- Category: hardware, rp23cnc-software
- Summary: Two stationary 15-second HX711 windows each returned 179 samples,
  establishing an installed rate of 11.933 Hz. Peak-to-peak noise was 300 and
  484 counts; standard deviation was 69.1 and 120.5 counts.
- Evidence: E-08 UART result blocks, exact source fingerprint, and dated E-08
  lab note.
- Result: Use a three-ready-sample median (about 0.25 s) and no more than about
  4 Hz correction cadence after actuator settling. Mechanical preload remains
  the dominant force uncertainty, not ADC noise.

<a id="elog-20260814-e-09-qwiic-i2c-startup"></a>
### 🟥 2026-08-14 - BLOCKED - E-09 Qwiic I2C startup

- Status: service UART passed; magnetic-sensor bus diagnosis is required.
- Category: hardware, rp23cnc-software
- Summary: E-09's deferred I2C initialization printed its pre-I2C message but
  did not return after command `i`. This ruled out the prior UART1 mapping
  issue and localized the failure to the Qwiic/TMAG I2C stage.
- Evidence: UART capture in the dated E-09 lab note.
- Next action: with power off, verify GP16/SDA, GP17/SCL, 3V3, and TOOL_GND
  continuity and absence of shorts; with power on, measure sensor 3.3 V and
  the idle SDA/SCL levels before retrying E-09.

<a id="elog-20260814-passed-e-09-tmag5273-intended-wiring-test"></a>
### 🟩 2026-08-14 - SUCCESS - Passed E-09 TMAG5273 intended-wiring test

- Status: corrected TMAG I2C wiring and bench magnetic response are verified.
- Category: hardware, rp23cnc-software
- Summary: Correcting the signal pair to GP16/SDA and GP17/SCL restored sensor
  communication. Stable near-magnet magnitude was 7.51 mT with a 0.28 mT span;
  far magnitude was 0.24 mT with a 0.25 mT span; return over the magnet was
  7.44 mT.
- Evidence: E-09 exact-source fingerprint and UART readings in the dated lab
  note.
- Result: A conservative initial magnitude threshold is 3.5 mT with 1.0 mT
  hysteresis. Final A_HOME scan geometry remains E-18 work.

<a id="elog-20260814-e-18-repinned-pc817-harness-pre-check"></a>
### 🟨 2026-08-14 - PARTIAL - E-18 repinned PC817 harness pre-check

- Status: repinned harness accepted; actual RP23CNC terminal integration is
  still required.
- Category: hardware
- Summary: With all power disconnected, CTRL_GND to TOOL_GND had no continuity.
  After powering only the toolhead side, TOOL_3V3 measured 3.3 V and GP29
  measured 2.739 V relative to TOOL_GND, a valid idle HIGH level.
- Evidence: dated E-18 repinned-harness lab note, project-owner multimeter
  readings, earlier successful U1/U2/U3 5 V / 12 V + 2.2 kOhm bench evidence,
  and previously recorded GP29/GP28/GP27 harness continuity.
- Next action: F-05 must verify the real RP23CNC ENA and Aux0 terminal
  behavior and LIMA input before the controller harness is connected.

<a id="elog-20260814-passed-e-17-rp23cnc-pre-power-inspection"></a>
### 🟩 2026-08-14 - SUCCESS - Passed E-17 RP23CNC pre-power inspection

- Status: controller is cleared for USB-only baseline flashing.
- Category: hardware, rp23cnc-software
- Summary: Magnified visual inspection found good solder joints without visible
  bridges. With all power removed, the main 12 V positive-to-negative and the
  labeled 5 V rail-to-ground continuity checks both had no beep.
- Evidence: dated E-17 lab note; saved Web Builder configuration and UF2 build
  record with SHA-256.
- Next action: flash the USB-only grblHAL baseline and capture its F-01 boot
  banner before attaching controller I/O or 12 V machine power.

<a id="elog-20260814-passed-f-01-rp23cnc-grblhal-baseline-boot"></a>
### 🟩 2026-08-14 - SUCCESS - Passed F-01 RP23CNC grblHAL baseline boot

- Status: controller firmware baseline is running over native USB.
- Category: rp23cnc-software, hardware
- Summary: The generated four-axis RP2350/RP23U5XBB UF2 booted on COM9.
  `$I` reported grblHAL 1.1f.20260813, XYZA, W5500 detection, and the
  SD-card/Ymodem plugins expected from the saved Web Builder configuration.
- Evidence: dated F-01 lab note, build record, saved JSON configuration, UF2
  SHA-256, and project-owner ioSender capture.
- Next action: capture the initial `$$` settings dump before changing settings;
  then perform unpowered F-03/F-04 and controller output F-05 tests.

<a id="elog-20260814-f-01-first-run-control-input-alarm"></a>
### 🟨 2026-08-14 - PARTIAL - F-01 first-run control-input alarm

- Status: baseline firmware is valid; temporary control-input inversion is
  required before settings can be queried or changed from the console.
- Category: rp23cnc-software, hardware
- Summary: `SIGNALS:HSE` and `ALARM:10` caused `$ $` and `$14=70` console
  commands to return error 79 because grblHAL blocks commands during a critical
  event. The board manual identifies the same initial condition and directs
  using ioSender's Control signals settings UI to invert Feed Hold, Cycle
  Start, and E-stop, then reboot.
- Evidence: project-owner ioSender console capture and RP23CNC user manual,
  page 23.
- Next action: apply the documented temporary inversion through ioSender, then
  capture the settings dump and continue unpowered I/O testing.

<a id="elog-20260814155936"></a>
### 🟩 2026-08-14 15:59:36 -0500 - SUCCESS - Cleared RP23CNC first-run control alarm

- Status: controller reached `IDLE`; initial settings capture remains next.
- Category: rp23cnc-software, hardware, test
- Summary: With isolated-input 12 V present and main 12 V machine power,
  drivers, motors, and PC817 controller-side wiring still disconnected, the
  project owner used ioSender's saved control-signal inversion and clicked
  **Unlock**. ioSender changed from `ALARM:10` to `IDLE` and displayed
  `Caution: Unlocked`.
- Struggle/failure: Before the isolated-input supply and inversion were made
  active, grblHAL showed `SIGNALS:HSE` and blocked console configuration writes
  with error 79.
- Evidence: project-owner ioSender screenshot; dated F-01 lab note.
- Result: The alarm condition is resolved for the present bench configuration.
  No motion output or controller-to-toolhead electrical connection has been
  tested.
- Next action: send `$$` while `IDLE`, preserve the full settings dump, then
  continue F-03/F-04 and F-05 with machine loads disconnected.

<a id="elog-20260814160300"></a>
### 🟨 2026-08-14 16:03:00 -0500 - MIXED/OPEN - Isolated missing grblHAL settings-list response

- Status: USB commands work; use the ioSender settings UI as the present
  configuration-reading path.
- Category: rp23cnc-software, test
- Summary: In `IDLE`, the controller echoed `$$` without returning a settings
  list. `$HELP` immediately returned the command help-topic list, including
  Settings, Control signals, and all axis groups. `$HELP Settings` then
  returned the supported setting IDs/descriptions and `ok`, but not their
  current values.
- Evidence: project-owner console capture and dated F-01 lab note.
- Result: Communication and normal-command parsing are proven. The missing
  response is limited to the `$$` settings-list path or its display in this
  firmware/sender combination.
- Next action: select **Settings: Grbl → Reload** to obtain the current
  configuration, without changing or saving values; investigate `$$` only if
  it later blocks configuration export or recovery.

<a id="elog-20260814161000"></a>
### 🟩 2026-08-14 16:10:00 -0500 - SUCCESS - Passed F-02 RP23CNC converter-command parser dry run

- Status: parser acceptance is verified; physical STEP/DIR output testing is
  next.
- Category: rp23cnc-software, test
- Summary: With only USB and `ISO 12V` connected, the controller accepted
  `G21`, `G90`, zero-distance XYZA `G0`/`G1`, `M3`, `G4 P0.1`, `M5`, and `M2`.
  Program end reported `M5` in the final modal state.
- Evidence: exact ioSender transcript in the dated F-02 lab note.
- Result: The converter's present G-code interface subset parses on the
  flashed RP23CNC build. No physical output/load claim is implied because all
  driver, motor, and PC817 controller-side connections remained detached.
- Next action: F-03 unpowered STEP/DIR/ENABLE identification and polarity
  test.

<a id="elog-20260814163000"></a>
### 🟩 2026-08-14 16:30:00 -0500 - SUCCESS - Passed F-03 RP23CNC X/Y/A bare-output test

- Status: controller-side X/Y/A stepper signals are characterized; TB6600
  input polarity/topology remains the next physical interface test.
- Category: hardware, rp23cnc-software, test
- Summary: For X, Y, and A, `DIR` held 0 V for a positive logical move and 5 V
  for a negative logical move. `STEP` was 0 V idle and registered about 50 mV
  on a DC meter only while moving. `EN` was 5 V idle and 0 V only during moves.
- Evidence: complete procedure and measurements in the dated F-03 lab note;
  wiring-table entries MOT-001 through MOT-009.
- Result: All three controller output groups have the same observed contract:
  5 V direction logic, pulsed STEP, and active-low enable. No TB6600, motor,
  or PC817 controller-side wire was attached.
- Risk/limitation: a DC meter averages STEP pulses and does not verify pulse
  width or edge quality. E-03 will prove actual TB6600 input compatibility.
- Next action: perform F-04 limit input tests before connecting drivers, then
  establish one TB6600's final input wiring under E-03.

<a id="elog-20260814164500"></a>
### 🟨 2026-08-14 16:45:00 -0500 - MIXED/OPEN - Selected X/Y SPDT roller limit switches

- Status: X/Y switch part is selected; controller wiring and polarity are not
  yet verified.
- Category: hardware, wiring, test
- Summary: The project owner identified the X/Y switches as HiLetgo KW12-3
  roller-lever SPDT microswitches. The documented plan uses their `COM` and
  `NC` contacts for a fail-safe circuit.
- Evidence: Amazon ASIN B07X142VGC and hardware selection change note
  `HW-20260814-004`.
- Result: F-04 now has a defined switch part, but cannot start until each
  received switch's terminal behavior and the exact RP23CNC input-pair labels
  are inspected.
- Next action: meter-check `COM`-`NC` with the lever released/pressed, provide
  a close controller-terminal photo, then wire and run F-04.

<a id="elog-20260814170000"></a>
### 🟨 2026-08-14 17:00:00 -0500 - MIXED/OPEN - Staged temporary X/Y limit-switch harness before drag-chain routing

- Status: short bench leads are the next F-04 fixture; permanent moving cable
  routing is deliberately deferred.
- Category: hardware, wiring, mechanical
- Summary: The project owner will connect the selected X/Y switches with basic
  short wires to verify their operation and RP23CNC connection before using the
  crowded drawer-side drag chain. That chain currently fits the 4-conductor
  shielded motor cable tightly and may require replacement with a larger,
  suitable-radius chain for the remaining moving conductors.
- Reason: A visible temporary harness isolates limit-switch electrical testing
  from unresolved cable-carrier capacity and bend-radius constraints.
- Evidence: project-owner wiring plan; BOM and roadmap updates.
- Result: Permanent X/Y limit routing is not authorized until the selected
  carrier's internal envelope, dynamic bend radius, cable fill, and free travel
  are measured against the complete harness.
- Next action: F-04 switch continuity check on short leads, then inspect the
  controller terminal labels. Evaluate the alternate drag chain in place before
  installing permanent cable.

<a id="elog-20260814173000"></a>
### 🟨 2026-08-14 17:30:00 -0500 - HARDWARE/OPEN - Initial E-stop uses RP23CNC Halt input

- Status: planned; no E-stop conductor or configuration change has been made.
- Category: hardware, safety, rp23cnc-software
- Summary: The initial E-stop architecture uses NC-A from the purchased
  mxuteuk 2NC mushroom across the RP23CNC's 12 V opto-isolated Halt input.
  NC-B remains insulated. K1 and its flyback diode are excluded from the
  project, rather than being purchase prerequisites.
- Reason: This follows the RP23CNC manual's supported control-input method and
  avoids representing a relay-based motor-energy-removal design as required.
- Next action: identify the installed E-stop terminal pair, meter-check SW1,
  perform E-19, then set and verify the NC-compatible E-stop inversion.

<a id="elog-20260815090000"></a>
### 🟨 2026-08-15 09:00:00 -0500 - HARDWARE/PARTIAL - Recorded TB6600 factory switch state

- Status: E-02 partial; no powered driver or motor test has occurred.
- Category: hardware, test
- Summary: The reported factory state is SW2/SW4 ON and SW1/SW3/SW5/SW6 OFF.
  A clear received-label photograph maps it to 8 microsteps (1600 pulses/revolution)
  and 2.0 A.
- Result: The factory current exceeds the selected motor's 1.5 A/phase rating.
  Subject to confirmation of each received unit's printed table, E-04 will set
  SW4 ON/SW5 ON/SW6 OFF before the first motor-power test.
- Risk: TB6600 clones can use different switch tables; all three labels and
  switch numbering must be photographed/confirmed before changing them.

<a id="elog-20260815100000"></a>
### 🟨 2026-08-15 10:00:00 -0500 - HARDWARE/PLANNED - Selected A-axis TB6600 baseline from measured 12:1 reduction

- Status: configuration baseline selected; it is not yet physically set or
  calibrated.
- Category: hardware, rp23cnc-software, motion
- Summary: The project owner measured 12 motor rotations for one bed rotation.
  The selected A-axis baseline remains the received TB6600's 8-microstep row
  (`SW1 OFF`, `SW2 ON`, `SW3 OFF`), rather than moving to 16 or 32 microsteps.
  With the 1.8 degree motor, this yields 1,600 pulses per motor revolution,
  19,200 pulses per bed revolution, and 0.01875 bed degree per pulse.
- Result: Under the established motor-shaft-degree A contract, the initial
  grblHAL A calibration is 4.444444 steps per A degree; one bed revolution is
  4,320 commanded A degrees. The 1.5 A/phase current row remains the required
  current baseline (`SW4 ON`, `SW5 ON`, `SW6 OFF`).
- Reason: The 12:1 reduction already provides fine angular resolution. Higher
  microstep settings would increase step-pulse demand and reduce incremental
  torque without a demonstrated benefit, which is counterproductive for the
  high-travel A axis.
- Next action: With the driver unpowered, complete E-04 on a received unit,
  then run M-04 and M-05 to verify the calculated motor and bed travel.

<a id="elog-20260815101500"></a>
### 🟨 2026-08-15 10:15:00 -0500 - HARDWARE/PLANNED - Set X/Y initial calibration from confirmed 20-tooth pulleys

- Status: initial configuration recorded; physical calibration remains pending.
- Category: hardware, rp23cnc-software, motion
- Summary: The project owner confirmed 20-tooth GT2 motor pulleys on both X
  and Y. At the selected 16-microstep TB6600 setting, both axes start at 80.0
  steps/mm: `(200 * 16) / (2 mm * 20 teeth)`.
- Result: Use `$100=80.000000` and `$101=80.000000` as initial values after
  the drivers are correctly configured; use 1.5 A/phase for all three motors.
- Risk/limitation: M-03 is still required because the calculated value does
  not account for actual pulley geometry, belt tension/compliance, or assembly
  error.

<a id="elog-20260819143203"></a>
### 🟨 2026-08-19 14:32:03 -0500 - HARDWARE/PARTIAL - Confirmed 17HS15 coil pairs and recorded Y cable exception

- Status: E-01 partial; coil grouping is known for X, Y, and A, but winding
  resistance and powered direction tests remain open.
- Category: hardware, wiring, test
- Summary: The project owner used a hand-turn generated-voltage test to confirm
  black/green and red/blue as the two coil pairs on all three 17HS15 motors.
  The Y motor's installed shielded cable preserves the pairs as black/green and
  red/white, with cable white spliced to the motor's blue lead.
- Evidence: Owner bench report; E-01 lab note
  `docs/report/lab-notes/2026-08-19-e-01-y-stepper-coil-pair-test.md`; hardware
  change note `HW-20260819-001`.
- Result: The master wiring table has axis-specific phase records, preventing a
  false assumption that Y has a blue cable conductor. The polarity order is
  retained as black/green and red/blue until M-01 confirms direction.
- Next action: Measure each motor's winding resistance, set each TB6600's
  current/microstep switches while unpowered, then complete low-speed M-01.

<a id="elog-20260819150000"></a>
### 🟥 2026-08-19 15:00:00 -0500 - HARDWARE/CORRECTED - Corrected B0FQ5GBNZ1 TB6600 DIP mapping

- Status: documented configuration corrected; E-02/E-04 still require physical
  label comparison and unpowered setting inspection.
- Category: hardware, motion, test
- Struggle/failure: Earlier documentation and advice incorrectly transcribed the
  B0FQ5GBNZ1 1.5 A row as SW4/SW5/SW6 = ON/ON/OFF. That setting is the listing's
  1.0 A row, not its 1.5 A row.
- Evidence: Direct inspection of the product-label image at the project-owner
  supplied Amazon B0FQ5GBNZ1 listing; dated E-02 lab note.
- Result: The source-specific mapping is 8× = SW1/SW2/SW3 OFF/ON/OFF, 16× =
  OFF/OFF/ON, and 1.5 A = SW4/SW5/SW6 ON/OFF/ON. X/Y start at 16× and A at 8×.
- Next action: With all drivers de-energized, physically compare each label and
  set X/Y/A according to `HW-20260819-002`; then inspect E-04 before M-01.

<a id="elog-20260819152227"></a>
### 🟨 2026-08-19 15:22:27 -0500 - HARDWARE/CORRECTED - Limited installed motor shielding to Y

- Status: current cable record corrected; PE continuity and isolation testing
  remain required before mains power.
- Category: hardware, wiring, safety
- Struggle/failure: The prior record conflated a purchased KWANGIL shielded
  cable with the cables actually installed, creating X/A shield-drain rows that
  do not exist physically.
- Evidence: Project-owner correction: only the Y motor cable is shielded.
- Result: X/A retain supplied unshielded 24 AWG leads; only Y's drain connects
  to the PE/chassis point at the TB6600 end. The KWANGIL cable remains a future
  option, not installed machine wiring.
- Next action: Verify Y drain-to-PE continuity and isolation from `-V` before
  mains power; add physical wiring records before installing shielded X/A cable.

<a id="elog-20260819160638"></a>
### 🟨 2026-08-19 16:06:38 -0500 - HARDWARE/PLANNED - Recorded actual HD064RT output allocation

- Status: owner allocation recorded; no branch has been continuity-checked or
  energized as a result of this record.
- Category: hardware, wiring, power distribution
- Summary: The owner assigned the HCDC HD064RT outputs as `OUT1` RP23CNC,
  `OUT4` Pololu D36V50F6, `OUT6` X TB6600, `OUT7` Y TB6600, and `OUT8` A
  TB6600. `OUT2`, `OUT3`, and `OUT5` have no load and remain intentionally
  unused.
- Result: The master wiring table, power-distribution document, BOM, and
  E-stop allocation now match the physical distribution plan. The controller's
  branch fuse is `OUT1`/`FCTRL`; the selected starting values are 2 A for
  `OUT1` and the three TB6600 branches and 3 A intended for the D36V50F6
  branch.
- Evidence: Project-owner allocation report. The stated values are planned;
  no claim is made about currently fitted fuse markings or live behavior.
- Risk: A branch fuse, terminal label, polarity, conductor gauge, current, and
  E-stop behavior must all be physically checked before power. Do not assume a
  factory 3 A fuse remains installed just because it shipped with the module.
- Next action: With all power removed, inspect and record each fitted fuse;
  then complete the applicable current, polarity, and E-19 checks before any
  powered TB6600 or toolhead test.

<a id="elog-20260820154152"></a>
### 🟨 2026-08-20 15:41:52 -0500 - HARDWARE/PARTIAL - Verified main-supply no-load path through HD064RT

- Status: partial E-11; this is not a loaded-power or safety-certification
  result.
- Category: hardware, wiring, power, test
- Summary: With the main supply energized and no downstream loads reported,
  the project owner measured 12.05 VDC at the HD064RT fuse-block input and
  12.05 VDC at one output pair. Observed polarity matched the block markings.
- Evidence: `docs/report/lab-notes/2026-08-20-e-11-main-supply-no-load-path-test.md`.
- Result: The supply-to-distribution no-load path is consistent with the
  intended nominal 12 V rail; no polarity reversal was observed.
- Risk: Meter identity/accuracy and the particular output pair were not
  recorded. Supply-terminal reading, PE/chassis bonding, adjustment range,
  label photo, fitted fuses, branch terminal checks, and loaded behavior are
  still unverified.
- Next action: With power removed, complete the PE continuity test and record
  the exact fitted fuse ratings; then finish the remaining E-11 no-load checks
  before connecting a TB6600 or toolhead load.

<a id="elog-20260821-segregated-mains-input-and-dc-output-routes"></a>
### 🟩 2026-08-21 - HARDWARE - Segregated mains-input and DC-output routes

- Status: physical-routing improvement implemented; E-11 remains partial.
- Category: hardware, wiring, power, safety
- Summary: The project owner rerouted the mains-input and DC-output conductors
  near the main supply and HD064RT fuse block so they no longer overlap.
- Reason: A physical crossover was eliminated to provide clearer segregation
  between mains and extra-low-voltage wiring.
- Evidence: Owner report; `HW-20260821-001`; follow-up in
  `docs/report/lab-notes/2026-08-20-e-11-main-supply-no-load-path-test.md`.
- Result: The two conductor routes are now visually separate.
- Risk: This does not verify the remaining electrical and mechanical gates:
  PE bonding, fitted fuses, strain relief, supply adjustment range, and loaded
  operation.
- Next action: With power removed, verify PE continuity and fitted-fuse
  ratings before any branch load is connected.

<a id="elog-20260822-verified-x-y-limit-live-input-reporting"></a>
### 🟨 2026-08-22 - HARDWARE/PARTIAL - Verified X/Y limit live-input reporting

- Status: partial F-04; X/Y live reporting passed, but hard-limit alarm and
  fault-path testing remain open.
- Category: hardware, wiring, safety, test
- Summary: The owner meter-verified each HiLetgo KW12-3 `COM`–`NC` contact,
  wired `COM` to the RP23CNC `SIG` terminal and `NC` to `GND`, and used
  ioSender 2.0.47 to operate each input separately. Both X and Y were inactive
  released and active only while their own switch was pressed.
- Result: `$5=0` is correct for the installed X/Y switches. `$21=0` remains
  required until unused Z/A inputs are made deterministic and hard-limit alarm
  testing is deliberately performed.
- Evidence: `HW-20260822-001` and
  `docs/report/lab-notes/2026-08-22-f-04-x-y-limit-live-input-test.md`.
- Next action: Resolve unused input states, then test a controlled hard-limit
  alarm before enabling hard limits; keep drivers/motors out of any limit test
  until their dedicated commissioning gate.

<a id="elog-20260822-routed-toolhead-pc817-harness-through-drag-chains"></a>
### 🟨 2026-08-22 - HARDWARE - Routed toolhead PC817 harness through drag chains

- Status: physical routing complete; endpoint and functional verification are
  open.
- Category: hardware, wiring, toolhead
- Summary: The owner routed the five planned controller-side PC817 conductors
  through the drag chains: controller `5V`, spindle `ENA`, `Aux 0`, controller
  `GND`, and `LIMA`/`A_HOME`.
- Result: The moving-harness route is in place without yet claiming endpoint
  termination, continuity, isolation, controller-output behavior, or powered
  operation.
- Risk: `CTRL_GND` and `TOOL_GND` must remain isolated. Do not connect the
  controller-side `ENA`, `Aux 0`, or `LIMA` ends until F-05/E-18 tests pass.
- Evidence: Owner report and `HW-20260822-002`.
- Next action: Label and continuity-test the routed conductors, prove ground
  isolation, then perform the gated controller-output tests.

<a id="elog-20260822-added-motorless-prb-g38-feasibility-gate"></a>
### 🟨 2026-08-22 - RP23CNC-SOFTWARE/PLANNED - Added motorless PRB/G38 feasibility gate

- Status: F-08 planned; no endpoint reassignment or probe-function pass is
  claimed.
- Category: rp23cnc-software, hardware, probing, magnetic calibration
- Summary: Added a motorless test for the proposed use of RP23CNC `PRB` to
  capture TMAG5273 threshold transitions during X/Y raster and A-index moves.
  The test uses internal grblHAL position counters with TB6600 signal leads and
  motors disconnected.
- Evidence boundary: RP23CNC documentation establishes an isolated 12 V probe
  input, and grblHAL implements G38 cycles and probe-coordinate reporting, but
  neither explicitly certifies this complete Hall-raster/rotary-A use case.
- Result: The authoritative wiring remains GP27/PC817C U3 -> `LIMA`. F-08 must
  prove direct `PRB` polarity, X trigger/release capture, coordinate reporting,
  and installed-build A behavior before the isolated path or any retermination
  is attempted.
- Evidence: `RPSW-20260822-001`; `docs/testing/TEST_PLAN.md` F-08.
- Next action: Perform the direct-input F-08 procedure without motor wiring,
  record every command and result in a dated lab note, and proceed to the
  GP27/U3 path only if the direct stage passes.

<a id="elog-20260822-corrected-rp2350-toolhead-ownership"></a>
### 🟩 2026-08-22 - RP23CNC-SOFTWARE/CORRECTED - Corrected RP2350 toolhead ownership

- Status: current-state documentation corrected and ADR-002 accepted; no wiring
  or firmware changed.
- Category: rp23cnc-software, hardware, toolhead, documentation
- Summary: Replaced stale descriptions of a separate RP2040 magnetic adapter
  with the installed architecture: the SparkFun Pro Micro RP2350 toolhead
  controller owns both pen-pressure control and TMAG5273 magnetic sensing/output.
- Struggle/failure: Current documents retained terminology from the earlier
  standalone-adapter plan even after the functions moved onto the selected
  Pro Micro RP2350 toolhead controller.
- Result: Firmware, architecture, interface, wiring, testing, handoff, and
  current visual-overview documents now describe one combined toolhead MCU.
  ADR-002 records the Pro Micro RP2350 placement as accepted and the matching
  roadmap item is complete; GP27 `LIMA` versus `PRB` remains test-gated.
  Historical change records and dated lab notes remain unchanged where their
  older terminology is part of the original evidence.
- Evidence: Owner correction; `RPSW-20260822-002`; current GP27/GP28/GP29 and
  Qwiic wiring records.
- Next action: Continue E-18 and F-08 against the Pro Micro RP2350 toolhead
  controller; do not infer that this naming correction verifies either test.

<a id="elog-20260822-implemented-gated-magnetic-registration"></a>
### 🟨 2026-08-22 - RP23CNC-SOFTWARE/IMPLEMENTED - Implemented gated magnetic registration

- Status: source implemented and statically verified; hardware commissioning
  and controller feasibility remain open.
- Category: rp23cnc-software, hardware, architecture, testing
- Summary: Implemented the Pro Micro RP2350 dual-core pressure/magnetic split,
  two-phase GP28/GP27 protocol, probe-enabled RP23CNC candidate configuration,
  and P100 physical-home/centroid-raster/A-registration macro. No moving-harness
  conductor was added and the installed GP27/U3 endpoint remains `LIMA`.
- Evidence: Arduino-Pico compile passed with warnings enabled at 75,628 bytes
  flash and 15,816 bytes globals; `tools/validate_homing_macro.py` passed its
  structural and synthetic arithmetic checks; `RPSW-20260822-003`; ADR-003.
- Safety boundary: All actuator, lift, pressure, magnetic, and production macro
  commissioning gates remain false. No candidate UF2 was generated or flashed,
  no physical wire was reterminated, and no motor or PRB test is claimed.
- Correction: The center-registration path now has a separate locked
  `sensor_to_pen_offset_valid` gate. P100 applies the installed `pen - TMAG`
  XY vector to G54 so X0/Y0 locates the pen tip, not the magnetic sensor.
- Next action: Complete T-01/T-02 and E-18, then run F-08 motorless on the exact
  candidate build before considering GP27/U3 retermination or magnetic motion.

<a id="elog-20260823-partially-terminated-toolhead-control-harness"></a>
### 🟨 2026-08-23 - HARDWARE/PARTIAL - Partially terminated toolhead-control harness

- Status: four controller-side conductors are reported connected; electrical
  verification and the reverse return connection remain open.
- Category: hardware, wiring, toolhead, rp23cnc
- Summary: The owner supplied an annotated PC817C board image and reported that
  J1.1 `CTRL_5V`, J1.2 `ENA`, J1.4 `AUX0`, and J1.5 `CTRL_GND` are now wired at
  the RP23CNC. J1.6 `A_HOME` is not connected. No connection to `PRB` is
  claimed.
- Evidence boundary: The report and image establish board-side conductor
  identity, not the exact controller terminal labels, continuity, isolation,
  output polarity/current, or energized behavior.
- Result: The interface wiring state is updated to partially terminated. The
  installed reverse-return assignment remains `LIMA`; `PRB` remains a
  test-gated candidate.
- Evidence: `HW-20260823-001` and
  `docs/report/lab-notes/2026-08-23-rp23cnc-toolhead-control-partial-termination.md`.
- Next action: With power removed, check continuity and `CTRL_GND`/`TOOL_GND`
  isolation; then perform F-05/E-18. Do not connect the return to `PRB` before
  F-08 passes.

<a id="elog-20260823-set-x-axis-motor-shielding-plan"></a>
### 🟨 2026-08-23 - HARDWARE/PLANNED - Set X-axis motor shielding plan

- Status: X is the sole planned shielded motor run; its final cable installation
  and PE bond are unverified.
- Category: hardware, wiring, stepper, shielding
- Summary: The owner corrected the motor-cable convention: only the X-axis
  toolhead-travel motor cable will have a grounded sheath. Y and A are
  unshielded, with black/green and red/blue as their two coil pairs.
- Result: The prior current-state record assigning shielding to Y is superseded.
  The X shield is designated for a driver/DIN-end PE/chassis bond only, never a
  DC or signal-ground connection.
- Evidence: Owner instruction; `HW-20260823-002`.
- Next action: Before energizing X, install and continuity-test the X shield
  bond, confirm its isolation from DC `-V` and signal ground, and complete
  phase/direction checks.

<a id="elog-20260823-corrected-x-axis-phase-b-cable-color"></a>
### 🟨 2026-08-23 - HARDWARE/CORRECTED - Corrected X-axis Phase B cable color

- Status: driver-side X Phase B color corrected; continuity and powered checks
  remain open.
- Category: hardware, wiring, stepper, x-axis
- Summary: The owner corrected the X TB6600 Phase B mapping: `B+` is red and
  `B-` is white. White is the shielded-cable-side continuation of the motor's
  blue B- lead.
- Result: The current X connection record is `A+` black, `A-` green, `B+` red,
  and `B-` white. Y/A remain unshielded with black/green and red/blue pairs.
- Evidence: Owner correction; `HW-20260823-003`.
- Next action: Power-off continuity-check the red/white X Phase B run and
  white-to-blue motor splice before driver energization.

<a id="elog-20260823-recorded-x-sheath-protective-earth-bond"></a>
### 🟨 2026-08-23 - HARDWARE/PARTIAL - Recorded X sheath protective-earth bond

- Status: the reported X sheath PE landing is recorded; terminal and continuity
  verification remain open.
- Category: hardware, mains, protective earth, shielding
- Summary: The owner reports red mains live to `L`, blue neutral to `N`, and a
  green earth conductor at the power supply's protective-earth terminal. The
  green X motor-cable sheath/drain is landed at the same PE terminal.
- Safety boundary: The PE symbol/printed terminal marking—not wire color—is
  authoritative. The X shield must never be connected to `-V`, a motor phase,
  `L`, `N`, or signal ground.
- Evidence: Owner report; `HW-20260823-004`.
- Next action: With all power removed, inspect terminal markings, measure
  low-resistance PE-to-chassis continuity, and confirm shield isolation from
  DC `-V` and all motor-phase conductors.

<a id="elog-20260823-verified-mains-terminals-and-x-sheath-landing"></a>
### 🟩 2026-08-23 - HARDWARE/VERIFIED - Verified mains terminals and X sheath landing

- Status: AC terminal identities and X sheath PE landing verified; continuity
  and powered checks remain open.
- Category: hardware, mains, protective earth, shielding
- Summary: With power removed, the owner verified red at printed `L`, blue at
  printed `N`, and the green wall-earth conductor plus green X sheath/drain at
  the protective-earth symbol terminal.
- Result: The physical terminal mapping is verified without relying on color
  alone. No claim is made for PE-to-chassis resistance, shield isolation,
  enclosure protection, or powered behavior.
- Evidence: `HW-20260823-005` and
  `docs/report/lab-notes/2026-08-23-mains-terminal-and-x-sheath-verification.md`.
- Next action: Measure PE-to-chassis continuity and shield isolation from DC
  `-V`/motor phases, then complete the remaining E-11 checks.

<a id="elog-20260823-verified-x-sheath-dc-negative-isolation"></a>
### 🟩 2026-08-23 - HARDWARE/VERIFIED - Verified X sheath DC-negative isolation

- Status: X sheath-to-DC-`-V` isolation passed; other PE/shield checks remain
  open.
- Category: hardware, protective earth, shielding, isolation
- Summary: The owner meter-verified no continuity between the green X
  motor-cable sheath and the DC `-V` return.
- Result: The sheath is not a DC return path. This result does not establish
  PE-to-chassis continuity or isolation from motor-phase conductors.
- Evidence: `HW-20260823-006`.
- Next action: Verify PE-to-chassis continuity and sheath isolation from all
  motor phases before any mains/motor power test.

<a id="elog-20260823-verified-supply-protective-earth-chassis-path"></a>
### 🟩 2026-08-23 - HARDWARE/VERIFIED - Verified supply protective-earth chassis path

- Status: power-supply PE-to-chassis path passed; X sheath motor-phase isolation
  and remaining mains checks are open.
- Category: hardware, protective earth, mains, shielding
- Summary: The owner verified the protective-earth terminal-to-supply-chassis
  path. The powder-coated machine structure is deliberately not used as the PE
  reference; the green X sheath remains landed at supply PE.
- Result: The PE reference does not depend on electrical contact through powder
  coating. This does not verify enclosure bonding or powered mains behavior.
- Evidence: `HW-20260823-007`.
- Next action: Verify X sheath isolation from every motor-phase conductor, then
  complete the remaining E-11 checks before energizing a load.

<a id="elog-20260823-verified-x-sheath-motor-phase-isolation"></a>
### 🟩 2026-08-23 - HARDWARE/VERIFIED - Verified X sheath motor-phase isolation

- Status: X sheath PE connection and isolation from DC `-V` and motor phases
  are verified.
- Category: hardware, protective earth, shielding, isolation, stepper
- Summary: The owner meter-verified no continuity between the green X
  motor-cable sheath and any motor-phase conductor.
- Result: The X sheath is correctly isolated from energized motor wiring and
  DC return while retaining its protective-earth path.
- Evidence: `HW-20260823-008`.
- Next action: Complete remaining enclosure/strain-relief and powered E-11
  checks, then proceed with controlled motor commissioning.

<a id="elog-20260823-plan-motor-harness-strain-relief-cad"></a>
### 🟨 2026-08-23 - HARDWARE/PLANNED - Plan motor-harness strain-relief CAD

- Status: CAD design planned; no physical strain relief is installed or verified.
- Category: hardware, CAD, cable management, stepper
- Summary: The owner will design strain-relief features for the X, Y, and A
  motor wire harnesses.
- Acceptance criteria: The design must grip harness cable jackets rather than individual
  conductors, preserve bend radius and service slack, relieve TB6600 terminals,
  and preserve the X sheath's PE bond and isolation.
- Evidence: Owner plan; `HW-20260823-009`.
- Next action: Measure cable diameters, exit directions, mounting geometry, and
  drag-chain clearance before selecting CAD dimensions.

<a id="elog-20260825-plan-slow-pi-toolhead-force-control"></a>
### 🟨 2026-08-25 - RP23CNC-SOFTWARE/PLANNED - Plan slow PI toolhead force control

- Status: implementation and all gains remain test-gated.
- Category: rp23cnc-software, hardware, toolhead, force-control
- Summary: Selected a bounded pulse-based P/PI trim strategy for the N20,
  lead-screw, load-cell toolhead. Mechanical compliance handles fast pen
  vibration; the roughly 4 Hz useful force correction cadence handles slow
  paper/bed-height variation.
- Reason: E-08 measured 11.93 HX711 samples/s and the mechanism has stiction,
  backlash, and Z-dependent preload. A conventional fast PID or force-error D
  term would not be evidence-supported.
- Evidence: E-05 no-load motor result, E-07 partial calibration and preload
  observation, E-08 sample/noise measurement, and the documented plan
  `RPSW-20260825-001`.
- Safety boundary: No commissioning flag or firmware force constant changed.
  E-06, E-07, T-01, and T-02 must precede T-03 gain selection.
- Next action: Characterize short motor pulses against a scale, establish a
  repeatable force calibration, then tune P before adding a leaky I term.

<a id="elog-20260827-adjusted-presentation-slide-deck-and-added-power-schematic"></a>
### 🟩 2026-08-27 - SUCCESS - Adjusted presentation slide deck and added power schematic

- Status: presentation slide deck updated.
- Category: documentation, project management
- Summary: Removed the "Dual-Core Toolhead Subsystem" slide (Slide 5) from `independent_study_presentation.html` since code implementation on the Pro Micro has not yet started. Re-indexed the remaining slides and updated Slide 6 (Troubleshooting & Pivots) to frame the sensor rate PI loop as a design/planned strategy rather than a completed implementation. Also integrated `power-distribution-schematic.png` into Slide 4 (Power Distribution & Hardware Wiring) with a side-by-side split layout, removed the misleading "Bench Verified" header tags, and set granular status symbols (green check marks for verified items, an amber check mark for the partially verified ground loops/EMI spikes item as the TB6600s have not yet been wired to motors, and hollow circles for planned/unverified items). Toned down exaggerated claims by changing "100% Complete" on Slide 3 to "Functional" and removing the "Ready for live demonstration" conclusion sentence from Slide 8. Built a zoomable click-to-expand lightbox modal allowing full-screen viewing of the schematic with Escape key dismissal. Also removed the redundant "Illustrative" word from the 12 V branches box heading, replaced the redundant "Rules" box with a clean "Legend" box (shifting color-coded wire identifiers upward), changed the `6 V` line color from orange to light brown (`#b46522`) for contrast, separated the `12 V` (red) and `5 V` (dark yellow, `#ca8a04`) lines in the Legend box, and re-rendered `power-distribution-schematic.png`. Added a new Slide 7 (System Verification & Test Status) mapping the current passed/partial/planned status of all subsystem bench, grblHAL firmware, and motion/integration tests from `docs/testing/TEST_PLAN.md`, re-indexing subsequent slides (total 9). Integrated a CSS-styled inline status legend at the top of Slide 4 and Slide 7 to clearly define the Checked (Verified), Partially Verified, and Planned markers, subdivided the Slide 7 future tests card into distinct Phase 2, Phase 3, and Phase 4 lists, renamed the system term on Slide 2 to "Pen Force Control System", marked all power bus items verified on Slide 4, renamed the project headers and title to "XY Theta Pen Plotter", updated the Slide 2 title to "3-Tier Independent Execution Context", changed the host stack description on Slide 2 to "SVG - G-code Converter • ioSender", and renamed the grammatically incorrect "Toolhead Embedded" step to "Toolhead Subsystem". Renamed E-18 on Slide 7 to "Opto-isolator circuit", marked F-07 (XYZA 4-axis config check) as partially verified, removed the redundant subtitle from Slide 8, and renamed card tags on Slide 8 from "Phase" to "Step 1-4" to prevent confusion with Slide 7's phases.
- Reason: Avoid misrepresenting uncompleted Pro Micro software milestones, ensure academic objectivity, support interactive visual schematic analysis, present formal test plan progress, provide clear marker definitions, accurately partition future tests by roadmap phase, present a fully verified power subsystem status, align project naming terminology, correct grammatical phrasing on Slide 2, and clarify step-by-step roadmap terminology in the upcoming independent study presentation.
- Evidence: updated [independent_study_presentation.html](../../independent_study_presentation.html), [power-distribution-schematic.svg](../../power-distribution-schematic.svg), and [power-distribution-schematic.png](../../power-distribution-schematic.png).
- Next action: run the docs index check tool to regenerate topic links and validate stability.

<a id="elog-20260828083705"></a>
### 🟩 2026-08-28 08:37:05 -0500 - SUCCESS - Established sequential agent execution policy

- Status: implemented; applies to all future repository work.
- Category: documentation, project management
- Summary: The working agreement now assigns bounded routine work to Luna and
  reserves Sol for judgment-heavy decisions, safety-sensitive work,
  cross-subsystem tradeoffs, nontrivial diagnosis, and uncertainty review.
- Result: Agent work is one job at a time in stated order. Parallel,
  speculative, and background batches are prohibited, and Sol must not be used
  for overnight, unattended, recurring, or long-running work.
- Evidence: Owner instruction; `WSW-20260828-001`; `AGENTS.md`; and
  `docs/START_HERE.md`.
- Next action: Apply the policy to future tasks and keep any model substitution
  within the same routine-work versus judgment-work boundary.

<a id="elog-20260830-plan-toolhead-motor-preload-physical-envelope-test"></a>
### 🟨 2026-08-30 - HARDWARE/PLANNED - Plan toolhead motor/preload physical-envelope test

- Status: T-01 has been expanded into planned sub-tests; no physical force,
  spring-rate, motor-capability, or controller-limit result is claimed.
- Category: hardware, rp23cnc-software, toolhead, testing, force-control
- Summary: Added T-01A through T-01F to measure the installed spring geometry
  and force curve, preload, hysteresis, motor static hold, retract reserve,
  command-to-force response, and the resulting control envelope. The selected
  spring is nominally 0.027 in wire x 0.295 in OD x 1.19 in free length, but
  the test requires measurements of the installed part and mechanism.
- Reason: The N20 must retract against the actual preload and the slow,
  pulse-based force loop must use measured travel, force, stiction, backlash,
  thermal, and timing bounds rather than nominal dimensions or unloaded motor
  current.
- Safety boundary: E-06, E-15, and E-07 remain gates for loaded conclusions.
  The test uses guarded travel and a scale/force fixture; it does not hand-stall
  the actuator or authorize firmware constants before evidence exists.
- Evidence: `HW-20260830-001`; `docs/testing/TEST_PLAN.md` T-01A through
  T-01F; `docs/testing/RECOMMENDED_TEST_SEQUENCE.md`.
- Next action: Run T-01A unpowered, then complete the remaining sub-tests in
  the documented dependency order and record each attempt in a dated lab note.

<a id="elog-20260830-add-toolhead-test-stop-go-rules"></a>
### 🟨 2026-08-30 - HARDWARE/PLANNED - Add toolhead test stop/go rules

- Status: documentation clarification only; no test result changed.
- Category: hardware, toolhead, testing
- Summary: Added explicit pass/proceed and fail-or-partial/stop decisions to
  the toolhead portion of the recommended test sequence. T-01A must establish
  safe geometry before powered motion; loaded motor, sensor, and preload tests
  each block their dependent test until their formal evidence exists.
- Reason: A dependency-only order could be read as permission to continue when
  a test was partial or failed.
- Evidence: `HW-20260830-002`;
  `docs/testing/RECOMMENDED_TEST_SEQUENCE.md`.
- Next action: Start T-01A and record its result in a dated lab note; do not
  power the actuator into an unmeasured compression range.

<a id="elog-20260830-record-preliminary-toolhead-preload-current"></a>
### 🟨 2026-08-30 - HARDWARE/PARTIAL - Record preliminary toolhead preload current

- Status: preliminary retract-current observation recorded; E-06 and T-01
  remain open.
- Category: hardware, toolhead, n20, preload, testing
- Summary: With the spring installed, the owner reported approximately
  0.019-0.050 A while retracting and 0.18 A at the reported fully compressed
  end condition. The current rise occurs where the motor is opposing the
  greatest observed spring load.
- Evidence boundary: The setup did not record supply/current limit, PWM,
  spring compression, meter bandwidth, peak current, force, or temperature.
  This does not establish stall current, driver margin, spring solid-height
  margin, continuous holding capability, or a safe firmware limit.
- Safety boundary: Do not operate at a fully compressed spring condition.
  Establish the guarded working end point, then run E-06/T-01C/T-01D with a
  current-limited supply and recorded thermal/force evidence.
- Evidence: `HW-20260830-003`;
  `docs/report/lab-notes/2026-08-30-t-01-preload-current-observation.md`.
- Next action: Complete T-01A measurements, then repeat at the intended maximum
  working compression with a recorded supply limit and a peak-capable current
  measurement.

<a id="elog-20260830-set-proposed-toolhead-lift-datum"></a>
### 🟨 2026-08-30 - HARDWARE/PARTIAL - Set proposed toolhead LIFT datum

- Status: proposed geometry measured; pen stop and solid-height verification
  remain open.
- Category: hardware, toolhead, spring, preload, testing
- Summary: The owner measured the spring at 1.190 in free length and selected
  0.535 in compression for the proposed LIFT position. The installed spring
  length is therefore 0.655 in, and the pen tip measured 0.1885 in above the
  bed. An integrated pen-mount stop is planned to make pen insertion height
  repeatable.
- Evidence boundary: This does not establish the spring solid length, coil-bind
  margin, working contact force, or a safe firmware limit.
- Evidence: `HW-20260830-004`;
  `docs/report/lab-notes/2026-08-30-t-01a-toolhead-lift-datum.md`.
- Next action: Build and verify the pen stop, then measure `L_solid` and
  document the margin before treating this LIFT position as safe.

<a id="elog-20260830-plan-toolhead-lift-home-switch"></a>
### 🟨 2026-08-30 - HARDWARE/PLANNED - Plan toolhead LIFT-home switch

- Status: proposed local position-reference circuit; no connection or powered
  test has been completed.
- Category: hardware, rp23cnc-software, toolhead, lift-home, testing
- Summary: The owner identified microswitch terminals `1` and `3` as the
  intended COM/NO pair for a normally-open LIFT-home switch. The proposed dry
  contact connects only between Pro Micro RP2350 `GP2` and `TOOL_GND`; the
  firmware will use an internal pullup, making pressed read LOW.
- Reason: The pen carriage rides a linear rail and its spring compression does
  not change the floating load-cell reading, so the load cell cannot establish
  retracted height.
- Safety boundary: The switch is an electrical reference, not a hard stop. A
  mechanical backstop and verified spring solid-height margin remain mandatory;
  do not connect 5 V, 6 V, or PC817C `CTRL_GND` to this input.
- Evidence: `HW-20260830-005`;
  `docs/report/lab-notes/2026-08-30-t-01g-lift-home-switch-terminal-identification.md`;
  T-01G planned.
- Next action: Meter-check the released/pressed contact behavior, install the
  switch and moving flag, then perform the ten-cycle guarded T-01G test before
  enabling firmware homing.

<a id="elog-20260901-separate-normal-pen-clear-from-lift-home"></a>
### 🟨 2026-09-01 - MIXED/PLANNED - Separate normal pen clear from LIFT home

- Status: interface and test-plan decision recorded; no mechanism, wiring,
  firmware threshold, or clearance result is claimed.
- Category: hardware, rp23cnc-software, toolhead, m3, m5, load-cell,
  lift-home, testing
- Summary: Normal high-cycle M5 is now defined as `PEN_CLEAR`: retract to the
  filtered no-contact load-cell release band, then issue one bounded clearance
  pulse. M3 still seeks contact and enters force hold. The planned GP2 switch
  is retained only for full `LIFT_HOME` reference at boot, recovery, or an
  explicit service action.
- Reason: A full movement to the distant lift-home switch on every plotting
  stroke would be unnecessary and slow. The load cell can identify paper
  release quickly, but cannot turn a no-contact value into an absolute actuator
  position.
- Safety boundary: `PEN_CLEAR` requires measured hysteresis, debounce, pulse
  bound, and pen-tip gap. `LIFT_HOME` still requires T-01G switch verification,
  a separate mechanical backstop, and solid-height margin. No raw HX711 count,
  nominal spring length, or unmeasured motor time is authorized as a control
  constant.
- Evidence: `HW-20260901-001`; `docs/testing/TEST_PLAN.md` T-01H; and
  `firmware/pen_pressure/CONTROL_STRATEGY.md`.
- Next action: Complete E-07, then perform T-01H to establish signed
  `F_contact_on`/`F_release_off`, debounce, the clearance-pulse command, and
  30-cycle pen-clear evidence. Keep the normal M5 behavior commissioning-gated
  until that result exists.

<a id="elog-20260901-persist-toolhead-force-profile-separately-from-boot-baseline"></a>
### 🟨 2026-09-01 - MIXED/PLANNED - Persist toolhead force profile separately from boot baseline

- Status: calibration-storage acceptance plan recorded; no profile has been
  stored, loaded, or validated on hardware.
- Category: hardware, rp23cnc-software, toolhead, load-cell, calibration,
  nonvolatile-storage, testing
- Summary: T-01I now requires the scale-derived force profile to be committed
  through an explicit service action and survive five power cycles. Every boot
  then takes a fresh RAM-only no-contact baseline after `LIFT_HOME`; it may
  compensate drift but may never overwrite the accepted profile.
- Reason: Normal operation needs calibrated force values to remain available,
  while automatic re-calibration from an unloaded reading could hide sensor or
  mechanism faults and corrupt the known scale mapping.
- Safety boundary: Profile schema/checksum, force tolerances, and baseline/noise
  bounds are TBD until E-07, T-01E, and T-01H provide measured evidence. An
  invalid profile or implausible baseline must keep force control disabled.
- Evidence: `HW-20260901-002`; `docs/testing/TEST_PLAN.md` T-01I; and
  `firmware/pen_pressure/CONTROL_STRATEGY.md`.
- Next action: Complete the existing scale and pulse tests, define the profile
  fields/limits, then run T-01I before enabling persistent force control.

<a id="elog-20260902080550"></a>
### 🟩 2026-09-02 08:05:50 -05:00 - SUCCESS - Added current system data-flow chart

- Status: current-state documentation implemented; no hardware, firmware, or
  interface behavior changed.
- Category: windows-software, rp23cnc-software, hardware, documentation,
  data-flow, system-architecture
- Summary: Added `docs/system_data_flow.html`, a single visual reference with
  five separately routed scenarios: normal plotting, P100 startup registration,
  toolhead lifecycle, fault/recovery, and bench commissioning. Each connector
  has a dedicated lane and does not cross another connector or a component.
- Decision: The older `docs/homing_data_flow.html` remains archived because it
  represents a superseded homing architecture; it was not extended.
- Evidence: `RPSW-20260902-001`; documentation review against
  `docs/integration/INTERFACES.md`,
  `firmware/pen_pressure/README.md`, and
  `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`; documentation index
  write/check passed.
- Next action: Update the visual whenever an interface contract, P100 route,
  or toolhead fault/handshake behavior changes.

<a id="elog-20260902081743"></a>
### 🟩 2026-09-02 08:17:43 -05:00 - SUCCESS - Corrected mobile data-flow layout

- Status: documentation-layout correction complete; no hardware, firmware, or
  interface behavior changed.
- Category: windows-software, rp23cnc-software, hardware, documentation,
  data-flow, mobile-layout
- Struggle/failure: The initial SVG chart used long return connectors that
  crossed through nodes and overlapped visual elements on a phone. The supplied
  mobile screenshot made the problem visible.
- Resolution: Replaced connector routing with responsive top-to-bottom cards
  and adjacent down arrows. The two independent branches appear side by side
  only when space permits and otherwise stack; there are no drawn paths that
  can cross a node or another path.
- Evidence: `RPSW-20260902-001`; `docs/system_data_flow.html`; mobile-layout
  review against the supplied screenshot; documentation index write/check.

<a id="elog-20260902082406"></a>
### 🟩 2026-09-02 08:24:06 -05:00 - SUCCESS - Made data-flow visual a controlled record

- Status: documentation control record implemented; no hardware, firmware, or
  interface behavior changed.
- Category: windows-software, rp23cnc-software, hardware, documentation,
  data-flow, change-control
- Summary: Added `docs/architecture/SYSTEM_DATA_FLOW_RECORD.md` as the audit
  companion to the macro view. It defines eight traceable data-path baselines,
  what would count as an inconsistency, and the required evidence/disposition
  process before the chart can be redrawn.
- Evidence: `RPSW-20260902-001`; system-data-flow record; documentation index
  write/check.

<a id="elog-20260902-plan-interchangeable-tool-force-preflight"></a>
### 🟨 2026-09-02 - MIXED/PLANNED - Plan interchangeable-tool force preflight

- Status: interface, control, and test decision recorded; no automatic P100
  preflight or new force-control firmware has been implemented.
- Category: hardware, rp23cnc-software, toolhead, load-cell, p100, testing
- Summary: The toolhead is now planned to accept pens, markers, and pencils at
  different clamp heights without a shared vertical pen-tip datum. It will use
  the calibrated load-cell residual to distinguish contact from clear. T-01J
  was added to validate each intended tool's contact, release, force target,
  and clearance pulse.
- Reason: The previous 0.1885 in retract gap was measured with one installed
  pen and cannot safely represent all interchangeable tools. A no-contact
  reading identifies release but cannot measure an absolute air gap.
- Safety boundary: The planned P100 preflight must home, baseline, guarded-seek
  to paper, clear normally, and confirm clear-band return. The current P100
  macro lacks a toolhead acknowledgement and must not claim it performs that
  validation. A failed tool preflight leaves plotting disabled.
- Evidence: `HW-20260902-001`; `docs/testing/TEST_PLAN.md` T-01J;
  `firmware/pen_pressure/CONTROL_STRATEGY.md`.
- Next action: Complete E-07/T-01H, run T-01J with the intended pen and pencil
  types, then design and test a P100/toolhead acknowledgement before automating
  the preflight.

<a id="elog-20260902-recorded-intended-p100-data-movement"></a>
### 🟩 2026-09-02 - SUCCESS - Recorded intended P100 data movement

- Status: current-state planning reference documented; no macro, wire, or
  firmware behavior changed.
- Category: rp23cnc-software, hardware, p100, toolhead, documentation
- Summary: Recorded P100 Q0 in six data-movement sections: start command,
  toolhead GP2 home verification through the existing GP28/GP27 handshake,
  X/Y homing, magnetic registration, per-run M3/M5 touch check, and ready
  state.
- Safety boundary: GP2 remains local to the Pro Micro. P100 must wait for the
  existing GP27 acknowledgement rather than infer home from a fixed delay. The
  planned touch-check acknowledgement needs a defined third GP28/GP27 phase;
  it adds no wire or RP23CNC pin and is not yet implemented.
- Evidence: `HW-20260902-001`;
  `firmware/grblhal/HOMING_AND_MAGNETIC_CALIBRATION.md`.

<a id="elog-20260902-added-interactive-p100-data-movement-map"></a>
### 🟩 2026-09-02 - SUCCESS - Added interactive P100 data-movement map

- Status: documentation visual implemented; no macro, wire, or firmware
  behavior changed.
- Category: rp23cnc-software, hardware, p100, toolhead, documentation
- Summary: Added an interactive P100 process map. Hover, keyboard focus, or tap
  selects each of the six stages and exposes its command, sensor data, reply,
  and decision owner.
- Safety boundary: The map labels the GP2-verified home and per-run touch check
  as planned commissioning-gated behavior, not current `P100.macro` behavior.
- Evidence: `HW-20260902-001`; `docs/p100-data-movement.html`.

<a id="elog-20260902-added-summer-progress-presentation"></a>
### 🟩 2026-09-02 - SUCCESS - Added summer progress presentation

- Status: presentation artifact implemented; it summarizes current work and
  commissioning-gated plans without claiming unverified hardware results.
- Category: windows-software, rp23cnc-software, hardware, presentation,
  documentation
- Summary: Added a seven-slide professor update covering summer progress,
  high-level system split, homing, P100 data movement, M3/M5 force control, and
  the remaining path to a first calibration drawing.
- Evidence: `RPSW-20260902-002`;
  `docs/report/Theta_Pen_Plotter_Summer_Progress_Update.pptx`; all slides
  rendered and `slides_test.py` reported no overflow.
- Next action: Update the progress deck only when measured commissioning or
  calibration-drawing evidence changes the presentation narrative.

<a id="elog-20260902-added-native-p100-presentation-interaction"></a>
### 🟩 2026-09-02 - SUCCESS - Added native P100 presentation interaction

- Status: presentation interaction implemented; no machine firmware, wiring,
  or control behavior changed.
- Category: windows-software, rp23cnc-software, hardware, presentation, P100
- Summary: The P100 overview slide now has six native hover/click regions. Each
  opens the corresponding process-detail view, and every detail view includes a
  **Back to overview** control.
- Evidence: `RPSW-20260902-003`;
  `docs/report/Theta_Pen_Plotter_Summer_Progress_Update.pptx`; PowerPoint
  action settings were checked for six overview targets and the return action;
  all 13 slides rendered and `slides_test.py` reported no overflow.
- Limitation: This is PowerPoint navigation, not embedded HTML execution. The
  underlying P100 plan remains commissioning-gated.

<a id="elog-20260902-aligned-p100-presentation-detail-states"></a>
### 🟩 2026-09-02 - SUCCESS - Aligned P100 presentation detail states

- Status: presentation correction implemented; no machine firmware, wiring, or
  control behavior changed.
- Category: windows-software, rp23cnc-software, hardware, presentation, P100
- Summary: Corrected the six interactive P100 detail views so their in-map
  detail panel matches the selected card. Removed the redundant outer detail
  panel; the right side now gives only navigation guidance and the return
  control.
- Evidence: `RPSW-20260902-004`;
  `docs/report/Theta_Pen_Plotter_Summer_Progress_Update.pptx`; all 13 slides
  rendered, `slides_test.py` passed, and all six card actions plus back action
  were verified in PowerPoint.
- Limitation: The PowerPoint overlay mirrors the HTML map's data; it does not
  embed webpage execution.

<a id="elog-20260902-expanded-p100-presentation-views-to-full-slide"></a>
### 🟩 2026-09-02 - SUCCESS - Expanded P100 presentation views to full slide

- Status: presentation-layout correction implemented; no machine firmware,
  wiring, or control behavior changed.
- Category: windows-software, rp23cnc-software, hardware, presentation, P100
- Summary: Removed white presentation chrome and redundant outer panels from
  the P100 overview/detail views. The dark map now fills the slide height and
  the background fills the widescreen canvas; detail states retain only a
  compact Back control.
- Evidence: `RPSW-20260902-005`;
  `docs/report/Theta_Pen_Plotter_Summer_Progress_Update.pptx`; all 13 slides
  rendered, `slides_test.py` passed, and six card targets plus the Back action
  were checked in PowerPoint.
- Rationale: The map preserves its aspect ratio instead of being stretched
  horizontally, avoiding distorted text and cards.

<a id="elog-20260902-refreshed-summer-presentation-opening-render"></a>
### 🟩 2026-09-02 - SUCCESS - Refreshed summer presentation opening render

- Status: presentation visual update implemented; no machine firmware, wiring,
  or control behavior changed.
- Category: windows-software, rp23cnc-software, hardware, presentation
- Summary: Replaced the title-slide toolhead image with the current full-color
  CAD render, while retaining the user’s title-slide text and divider changes.
- Evidence: `RPSW-20260902-006`;
  `docs/report/Theta_Pen_Plotter_Summer_Progress_Update.pptx`; title slide
  inspected, all 13 slides rendered, `slides_test.py` passed, and native P100
  navigation actions were checked in PowerPoint.
- Next action: Run the deck in Slide Show mode on the classroom computer before
  presenting, to confirm display scaling and mouse-over navigation.

<a id="elog-20260903-added-mobile-wiring-table-view"></a>
### 🟩 2026-09-03 - IMPLEMENTED - Added mobile wiring-table view

- Status: documentation view implemented; wiring data and hardware behavior
  unchanged.
- Category: hardware, documentation, mobile usability.
- Summary: Added a generated responsive card view of every Markdown table in
  `docs/hardware/WIRING_TABLE.md`, with a filter field for tablet/phone use.
- Evidence: `python tools/generate_wiring_table_mobile.py` completed from the
  authoritative table; the generated HTML includes mobile-first cards and a
  two-column wider-screen layout.
- Next action: Regenerate the view after each wiring-table edit and check it on
  the target tablet when practical.

<a id="elog-20260903-landed-tb6600-power-branches"></a>
### 🟩 2026-09-03 - IMPLEMENTED - Landed TB6600 power branches

- Status: owner-reported physical wiring progress; no electrical or powered
  verification is claimed.
- Category: hardware, power-distribution, wiring, TB6600, X/Y/A.
- Summary: Positive and return conductors from HD064RT `OUT6`, `OUT7`, and
  `OUT8` are now physically landed at the X, Y, and A TB6600 branches.
- Owner selected a 3 A starting fuse for each TB6600 branch (`OUT6`/`OUT7`/
  `OUT8`); fitted fuse inserts and current suitability remain unverified.
- Owner reports the six fuse-block-to-driver conductors are 20 AWG.
- Evidence: project-owner wiring report. The master wiring table retains
  `planned — wired, unverified` until exact terminal labels, polarity, fuse
  markings, continuity, and power-on behavior are recorded.
- Next action: With power removed, inspect the six terminations and branch
  fuses; then continue the staged E-03 and one-axis M-01/M-02 bring-up.

<a id="elog-20260903-recorded-tb6600-signal-and-a-axis-commissioning-baseline"></a>
### 🟩 2026-09-03 - IMPLEMENTED - Recorded TB6600 signal and A-axis commissioning baseline

- Status: documentation correction and commissioning baseline; no powered
  driver or motion result is claimed.
- Category: hardware, rp23cnc-software, TB6600, A-axis, calibration, homing.
- Summary: Promoted the already-supplied common-cathode TB6600 signal pattern
  into the master wiring table: axis `G` to `PUL-`/`DIR-`/`ENA-`, and
  `Stp`/`Dir`/`En` to `PUL+`/`DIR+`/`ENA+`. Recorded the X/Y 80 steps/mm
  baseline and the A 12:1, 19,200-pulse/bed-revolution, 0.01875-degree/pulse
  calculation, including a two-rotation scan-time formula.
- Evidence: supplied `plotter-wiring-schematic.svg` and
  `plotter-pinout-schematic.html`; arithmetic review. E-03 and M-01 through
  M-05 remain required hardware verification.
- Next action: With power removed, confirm received terminal labels, fuses,
  and DIP states; then use E-03 and one-axis low-speed M-01/M-02 testing to
  establish reliable loaded motion and the production A scan rate.

<a id="elog-20260903-added-opto-isolation-presentation-slide"></a>
### 🟩 2026-09-03 - SUCCESS - Added opto-isolation presentation slide

- Status: presentation explanation implemented; no machine firmware, wiring,
  or control behavior changed.
- Category: windows-software, rp23cnc-software, hardware, presentation
- Summary: Added a compact signal-flow slide for U1/U2/U3, showing the
  RP23CNC-to-Pro Micro directions, GPIO endpoints, voltage domains, and the
  isolated-boundary rationale.
- Evidence: `RPSW-20260903-008`;
  `docs/report/Theta_Pen_Plotter_Summer_Progress_Update.pptx`; the new slide
  was visually inspected, all 13 slides rendered, and `slides_test.py` passed.
- Limitation: GP27 remains routed to LIMA; the candidate PRB endpoint remains
  gated by F-08.

<a id="elog-20260902-set-opening-slide-to-full-bleed-machine-render"></a>
### 🟩 2026-09-02 - SUCCESS - Set opening slide to full-bleed machine render

- Status: presentation visual update implemented; no machine firmware, wiring,
  or control behavior changed.
- Category: windows-software, rp23cnc-software, hardware, presentation
- Summary: Filled the title slide with the supplied machine render and added a
  dark translucent title panel so the presentation text remains legible.
- Evidence: `RPSW-20260902-007`;
  `docs/report/Theta_Pen_Plotter_Summer_Progress_Update.pptx`; the opening slide
  was rendered and inspected, and `slides_test.py` passed for all 13 slides.
- Next action: Run the deck in Slide Show mode on the classroom computer before
  presenting, to confirm display scaling and mouse-over navigation.

<a id="elog-20260904-corrected-axis-specific-motor-cable-colors-in-diagrams"></a>
### 🟩 2026-09-04 - IMPLEMENTED - Corrected axis-specific motor cable colors in diagrams

- Status: documentation correction implemented; no physical wiring or motor
  behavior changed.
- Category: hardware, wiring, TB6600, X/Y/A.
- Summary: Updated the straight-lane, photo-style, top-down, and full HTML
  wiring views so X shows the shielded cable's white `B-` conductor continuing
  to the motor's blue lead, while Y and A retain stock blue `B-` leads.
- Reason: the former visual labels repeated the stock black/green/red/blue
  mapping for every axis and therefore did not match the installed X harness.
- Evidence: regenerated PNG previews were visually inspected; SVG sources
  were parsed as XML; the authoritative table retains the same mapping.
- Next action: complete final X phase-continuity and motor-direction checks
  before treating the driver-to-motor paths as powered-verified.

<a id="elog-20260904124726"></a>
### 🟩 2026-09-04 12:47:26 -0500 - IMPLEMENTED - Rerouted top-down wiring schematic into clean lanes

- Status: explanatory wiring-diagram update implemented; no physical wiring or
  terminal assignment changed.
- Category: hardware, wiring, TB6600, X/Y/A.
- Summary: Rebuilt `plotter-top-down-wiring-schematic.svg` with independent
  orthogonal lanes for each RP23CNC axis, explicit signal-common blocks,
  horizontal motor leads, and a far-right DIN power corridor.
- Reason: the previous layout used diagonal power branches and repeated signal
  fan-outs that crossed or overlaid one another, making individual paths hard
  to follow.
- Evidence: SVG XML parse passed; Chrome headless rendered the PNG preview;
  visual inspection confirmed separated signal, motor, and power routes.
- Struggle: the first clean-lane draft still overlaid the PSU-to-DIN `+V` and
  `0V` routes and put the X white terminal on the opposite side of its motor
  block. Both issues were corrected before recording this result.
- Next action: compare the explanatory routes against the installed terminal
  silkscreens and verify the physical harness before applying power.

<a id="elog-20260904144351"></a>
### 🟨 2026-09-04 14:43:51 -0500 - MIXED/OPEN - Recorded completed TB6600 signal harness wiring

- Status: physical installation reported complete; installed-driver behavior
  remains open.
- Category: hardware, wiring, TB6600, X/Y/A.
- Summary: The owner reported all X, Y, and A TB6600 signal pins and common
  returns wired over approximately six-inch runs using 24 AWG conductors.
  Black is common `G`, yellow is `En`, white is `Dir`, and blue is `Stp`.
- Evidence: owner report; current entries MOT-001 through MOT-008 in
  `docs/hardware/WIRING_TABLE.md` and `HW-20260904-003`.
- Limitation: Wiring completion is not a functional pass. Power-off continuity
  and short checks plus the one-axis-at-a-time E-03 input test remain required.
- Next action: verify every endpoint and the common-cathode polarity before
  applying motor power; keep motors disconnected during E-03.

<a id="elog-20260904144801"></a>
### 🟨 2026-09-04 14:48:01 -0500 - MIXED/OPEN - Verified TB6600 signal-harness continuity

- Status: physical continuity gate complete; installed-driver behavior remains
  open.
- Category: hardware, wiring, TB6600, X/Y/A.
- Summary: The owner reported end-to-end continuity for all three six-inch
  RP23CNC-to-TB6600 signal harnesses, including the black common-`G` paths and
  their common-block jumpers.
- Evidence: owner report and
  `docs/report/lab-notes/2026-09-04-pre-e03-tb6600-signal-harness-continuity.md`.
- Limitation: Meter model, readings, inter-wire short checks, powered signal
  response, and input-current behavior were not recorded. The result does not
  close E-03.
- Next action: complete the power-off short check, then run E-03 one driver at
  a time with motors disconnected and record the functional pass/fail result.

<a id="elog-20260904152239"></a>
### 🟨 2026-09-04 15:22:39 -0500 - MIXED/OPEN - Moved pen/TMAG XY offset ownership to P100

- Status: converter implementation and documentation updated; physical P100
  registration remains unverified.
- Category: software, firmware, test, coordinate-frames, tool-offset, p100
- Summary: Removed the converter's `tool_offset_x_mm`/
  `tool_offset_y_mm` settings and XY translation. G-code and preview positions
  now share one direct frame; P100 remains the sole owner of the measured
  `pen - TMAG` correction and G54 registration.
- Reason: Applying the correction in both the converter and P100 would shift
  the pen twice. Keeping the correction at the runtime registration seam also
  allows the saved G-code to remain independent of the current machine setup.
- Evidence: `WSW-20260904-001`; three coordinate-frame regression tests;
  Python syntax check; documentation index write/check.
- Limitation: The measured P100 offset, commissioning gate, and physical
  pen-at-center result remain open until magnetic registration is commissioned.
- Next action: Validate P100's installed `pen - TMAG` values and run a
  pen-lifted calibration pattern before production plotting.

<a id="elog-20260904-clarified-n20-endpoint-stall-current"></a>
### 🟨 2026-09-04 - HARDWARE/PARTIAL - Clarified N20 endpoint stall current

- Status: owner-reported endpoint-stall observation clarified; formal T-01C
  preload-hold acceptance remains open.
- Category: hardware, toolhead, n20, preload, testing
- Summary: The owner clarified that the approximately `0.18 A` reading occurred
  when the N20 retracted to the travel endpoint and pressed the LIFT_HOME
  switch. It is an endpoint stall current, not current measured while holding a
  selected operating preload.
- Evidence boundary: The spring identity/compression, force, rail behavior,
  driver-fault state, and temperatures were not recorded. Therefore the result
  does not establish T-01C preload-hold capability or qualify the full
  DRV8833/regulator electrical or thermal margin.
- Evidence: `docs/report/lab-notes/2026-08-30-t-01-preload-current-observation.md`;
  `docs/testing/TEST_PLAN.md`.
- Next action: Repeat at the guarded working compression with a current-limited
  supply and record hold dwell, force/position, rail voltage, current, driver
  state, and temperatures; then complete T-01C/T-01D.

<a id="elog-20260904-corrected-n20-unloaded-current-after-alignment"></a>
### 🟨 2026-09-04 - HARDWARE/PARTIAL - Corrected N20 unloaded current after alignment

- Status: E-05 unloaded-current baseline corrected; spring-loaded capability
  remains separately qualified only by owner report.
- Category: hardware, toolhead, n20, alignment, testing
- Summary: The owner clarified that aligned unloaded N20 motion current is
  `0.009 A`. The earlier `0.043 A` toolhead motion reading included extra
  mechanical load from a lead screw that was not nearly straight against the
  heat-set insert; the alignment has since been corrected.
- Result: `0.009 A` is now the normal unloaded-motion baseline. The earlier
  `0.043 A` result remains historical evidence that the rail survived a
  higher accidental alignment load, but is not the normal no-load value.
- Limitation: This correction does not replace the spring-installed
  `0.019-0.050 A` observation or qualify the reported `0.18 A` stall current,
  loaded rail margin, or formal T-01C hold dwell.
- Evidence: `docs/report/lab-notes/2026-08-12-e-14b-toolhead-local-power.md`;
  `docs/testing/TEST_PLAN.md`;
  `docs/changes/hardware/2026/2026-09-04-correct-n20-unloaded-current-after-alignment.md`.
- Next action: Use the corrected alignment for the next controlled spring-load
  test and record current, force, rail voltage, dwell, and temperatures.

<a id="elog-20260904-passed-bounded-n20-endpoint-stall-test"></a>
### 🟨 2026-09-04 - HARDWARE/PARTIAL - Passed bounded N20 endpoint-stall test

- Status: bounded E-06 endpoint-stall observation passed; T-01C preload-hold
  evidence was not recorded.
- Category: hardware, toolhead, n20, preload, testing
- Summary: With the lead screw aligned against the heat-set insert, the owner
  tested the N20 at 6.0 V with a 0.20 A bench-supply current limit. The motor
  retracted until it could travel no farther and pressed the LIFT_HOME switch;
  the supply read 0.18 A at that endpoint for approximately 30 seconds and the
  endpoint test repeated successfully 10 times.
- Result: The bounded switch-pressed endpoint-stall observation passed without
  reaching the supply limit. No known-compression operating-preload hold was
  measured.
- Limitation: Current was read at the supply; rail voltage, driver fault state,
  temperature, spring identity/compression, operating preload force, and
  long-duration endurance were not recorded. T-01C remains open.
- Evidence: `docs/report/lab-notes/2026-09-04-e-06-t-01c-n20-stall-preload-hold.md`;
  `docs/testing/TEST_PLAN.md`.
- Next action: Repeat the guarded current/hold test at a known safe spring
  compression, then continue the mechanical/force characterization sequence.

<a id="elog-20260904-made-pulse-response-per-tool-during-preflight"></a>
### 🟩 2026-09-04 - HARDWARE/IMPLEMENTED - Made pulse response per-tool during preflight

- Status: control-test architecture clarified; no physical test result changed.
- Category: hardware, rp23cnc-software, toolhead, force-control
- Summary: The project owner noted that the pulse-duration-to-force response
  will differ for each loaded pen or pencil. T-01E now establishes global N20
  actuator bounds, while T-01J performs a short bounded response check and
  selects per-tool force/threshold settings.
- Decision: Keep the load cell as the force authority. Do not apply one
  universal open-loop pulse-to-force curve to all tools; allow only bounded
  per-tool overrides inside the global actuator limits.
- Evidence: `docs/decisions/ADR-005-per-tool-pulse-response-preflight.md`;
  `docs/testing/TEST_PLAN.md`;
  `docs/changes/hardware/2026/2026-09-04-per-tool-pulse-response-preflight.md`.
- Next action: Complete T-01J for each intended pen or pencil after the global
  T-01E limits and load-cell calibration are accepted.

<a id="elog-20260904-replaced-toolhead-preload-spring"></a>
### 🟨 2026-09-04 - HARDWARE/OPEN - Replaced toolhead preload spring

- Status: replacement installed; current spring geometry and force envelope are
  unverified.
- Category: hardware, toolhead, spring, preload, testing
- Summary: The owner replaced the previously installed spring with an
  owner-reported compression spring measuring 0.4 mm wire diameter x 7 mm
  outside diameter x 25 mm free length.
- Decision: Treat the prior 0.535 in LIFT compression, 0.1885 in pen clearance,
  and spring-loaded N20/E-06 observations as historical to the removed spring.
  They are not control values for the current assembly.
- Evidence: `docs/report/lab-notes/2026-09-04-t-01a-new-spring-installation.md`;
  `docs/testing/TEST_PLAN.md`;
  `docs/changes/hardware/2026/2026-09-04-replace-toolhead-preload-spring.md`.
- Limitation: No replacement-spring free-length, solid-height, force, safe
  compression, clearance, or loaded-current measurement has been recorded.
- Next action: repeat T-01A unpowered, then repeat the guarded loaded actuator
  and force-envelope checks before reusing any prior preload setting.

<a id="elog-20260905-recovered-rp23cnc-usb-recognition"></a>
### 🟩 2026-09-05 - HARDWARE/VERIFIED - Recovered RP23CNC USB recognition

- Status: USB bring-up recovered; TB6600 signal verification remains open.
- Category: hardware, RP23CNC, USB, power-selector, TB6600.
- Summary: The RP23CNC was not recognized while the front `SWC USB` selector
  was on `SWC` and the board's main 12 V input was absent. With power removed,
  selecting `USB` restored laptop recognition.
- Interpretation: `USB` is required for USB-only board power. `SWC` is required
  when the main 12 V input supplies the onboard switching converter; USB can
  then remain connected for ioSender data.
- Evidence: `docs/report/lab-notes/2026-09-05-rp23cnc-usb-source-selector.md`;
  `docs/changes/hardware/2026/2026-09-05-rp23cnc-usb-source-selector-bringup.md`.
- Limitation: No STEP, DIR, or ENA waveform has been measured yet.
- Next action: run E-03 one TB6600 at a time with motors disconnected and the
  oscilloscope referenced to RP23CNC signal ground.

<a id="elog-20260905-passed-installed-tb6600-signal-response-test"></a>
### 🟩 2026-09-05 - HARDWARE/SUCCESS - Passed installed TB6600 signal response test

- Status: E-03 passed for the installed X, Y, and A TB6600 signal harnesses.
- Category: hardware, RP23CNC, TB6600, stepper, commissioning.
- Summary: The owner tested the completed common-cathode signal wiring with
  motor phases disconnected. ioSender commands returned `ok`; the A-axis
  status moved 150 -> 160 -> 150 for relative positive and negative moves.
- Result: `ENA+` measured about 4.82 V at idle and 0 V while moving; `DIR+`
  measured about 0 V for positive A and 4.82 V for negative A; `PUL+` reached
  about 5.22 V on the oscilloscope during motion. X and Y were reported to
  match the A-axis response.
- Struggle/recovery: The initial console view appeared to contain only sent
  command text; enabling visible replies and sending one command at a time
  exposed the expected acknowledgements. An early direction check used
  `ENA+`; moving the meter to `DIR+` separated the two signal roles.
- Evidence: `docs/report/lab-notes/2026-09-05-e-03-tb6600-installed-signal-response.md`;
  `docs/testing/TEST_PLAN.md`; `docs/hardware/WIRING_TABLE.md`;
  `docs/changes/hardware/2026/2026-09-05-tb6600-installed-signal-response.md`.
- Limitation: Motor-phase order, current/microstep DIP settings, loaded
  motion, physical direction, lost-step behavior, and thermal margin remain
  open for E-04/M-01 and later tests. Status reports also showed `Pn:ZA`; the
  active Z/A input state must be resolved before full-machine homing.
- Next action: perform E-04 DIP/current confirmation, then connect one motor
  at a time for M-01 under current-limited power.

<a id="elog-20260905-passed-initial-a-axis-direction-jog"></a>
### 🟨 2026-09-05 - HARDWARE/PARTIAL - Passed initial A-axis direction jog

- Status: Initial A-axis portion of M-01 passed; repeatability and heating
  evidence remain open.
- Category: hardware, A-axis, TB6600, stepper, motion testing.
- Summary: With the A TB6600 at 8× microstep and 1.5 A/phase, the owner ran
  `G1 A10 F120` and `G1 A-10 F120` in incremental mode. The A mechanism moved
  counterclockwise for positive A and clockwise for negative A. The Y TB6600
  was then tested with `G1 Y1 F60` and `G1 Y-1 F60`; positive Y moved north and
  negative Y moved south. The X TB6600 then moved east for `G1 X1 F60` and
  west for `G1 X-1 F60`.
- Result: The A positive move completed at approximately `0.44 A`, both Y
  moves were reported at about `0.43 A`, and both X moves at about `0.42 A`.
  All readings were below the 2 A temporary test limit. No stall or failed
  move was reported in the final direction checks.
- Evidence: `docs/report/lab-notes/2026-09-05-m-01-a-axis-direction-jog.md`;
  `docs/testing/TEST_PLAN.md`.
- Limitation: An initial X attempt was reported as jerking forward and
  backward; the subsequent X east/west result was clean, but the exact wiring
  correction was not recorded. Motor/driver temperature, repeat-cycle
  return-to-mark, and lost-step behavior were not measured; M-01 remains
  partial.
- Result update: After ten X `+5`/`-5` cycles at `F60`, the owner reports that
  the physical carriage/frame marks returned to the exact starting position.
  This provides no observable X lost-step or coupling-slip evidence for that
  cycle test.
- Result update: After ten Y `+5`/`-5` cycles at `F60`, the owner reports that
  the physical carriage/frame marks also returned to the exact starting
  position. This provides no observable Y lost-step or coupling-slip evidence
  for that cycle test.
- Thermal observation: No noticeable heating was reported at the X or Y
  motors or TB6600 drivers during the initial jog and return checks. This was a
  touch-based observation without numeric temperature readings.
- Next action: Repeat positive/negative A moves for multiple cycles and record
  motor/driver temperature for all three axes.

<a id="elog-20260905-completed-m-01-low-speed-jog-test"></a>
### 🟩 2026-09-05 - HARDWARE/SUCCESS - Completed M-01 low-speed jog test

- Status: M-01 passed for the conducted low-speed X/Y/A jog and return checks.
- Category: hardware, X-axis, Y-axis, A-axis, TB6600, stepper, motion testing.
- Summary: X moved east/west, Y moved north/south, and A moved
  counterclockwise/clockwise for positive/negative commands. Supply readings
  were approximately 0.42 A, 0.43 A, and 0.44 A respectively.
- Result: X and Y physical carriage marks returned exactly after ten positive
  and negative cycles. The A motor pulley returned to the exact same position
  relative to the motor body after its repeat cycle set. No stalls were
  reported.
- Thermal observation: No noticeable heating was reported at any motor or
  TB6600 driver; all remained cold to the touch. This is qualitative evidence,
  not a numeric temperature measurement.
- Evidence: `docs/report/lab-notes/2026-09-05-m-01-a-axis-direction-jog.md`;
  `docs/testing/TEST_PLAN.md`.
- Limitation: The earlier X jerking symptom was corrected/retested, but the
  exact wiring change was not recorded. Longer dwell, quantitative temperature
  measurement, rate ramp, and dimensional calibration remain separate tests.
- Next action: begin M-02 one-axis rate-ramp testing under the same current
  and mechanical safety limits.

<a id="elog-20260905-m-02-a-axis-rate-ramp-through-f600"></a>
### 🟨 2026-09-05 - HARDWARE/IN PROGRESS - M-02 A-axis rate ramp through F600

- Status: M-02 remains in progress; the A-axis rate ramp has been validated
  through `F600` for the recorded move pattern.
- Category: hardware, A-axis, TB6600, stepper, motion testing.
- Result: `F180`, `F240`, `F300`, `F360`, `F420`, `F480`, `F540`, and `F600`
  completed without reported stalls or jerks. At both `F480` and `F540`, the mechanism
  returned exactly to its physical reference mark and remained cool to the
  touch. The `F480` supply current was approximately `0.465 A`, the `F540`
  supply current was approximately `0.476 A`, and the `F600` supply current was
  approximately `0.485 A`.
- Result update: An apparent `0.5 mm` F600 return offset was later traced to the
  operator moving the pulley during inspection. It is discarded as a
  reference-handling error, not a machine repeatability failure.
- Measurement limitation: an earlier longer run showed approximately
  `0.47-0.476 A`, but the exact rate was not recorded; dwell duration and
  instrumented temperature were not captured.
- Decision: treat `F600` as the highest qualified A-axis rate for now, not as the
  absolute configured maximum. Check the A-axis maximum-rate setting before
  commanding a higher rate.
- Evidence: `docs/report/lab-notes/2026-09-05-m-02-a-axis-rate-ramp.md`;
  `docs/testing/TEST_PLAN.md`.
- Next action: repeat one bounded `F600` cycle from an untouched verified
  reference, then record the configured rate ceiling and continue M-02 on X/Y.
