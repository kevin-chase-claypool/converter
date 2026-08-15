# PC817C three-channel isolated interface

The current construction source is the minimum-wire, all-through-hole version:

- [`pc817-perfboard-v2-minwire.kicad_pcb`](pc817-perfboard-v2-minwire.kicad_pcb)
- [`pc817-perfboard-v2-minwire.kicad_sch`](pc817-perfboard-v2-minwire.kicad_sch)
- [`pc817-perfboard-v2-minwire.kicad_pro`](pc817-perfboard-v2-minwire.kicad_pro)
- [`PERFBOARD_BUILD.md`](PERFBOARD_BUILD.md)
- [`PRO_MICRO_JST_HARNESS.md`](PRO_MICRO_JST_HARNESS.md)

The board remains 40.16 × 22.65 mm on a 14 × 6, 2.54 mm grid. It uses only
through-hole parts, two 1×6 2.54 mm screw terminals on the short sides, and two
mounting holes on the right short side. It can be fabricated as a two-layer PCB
or followed as a point-to-point perfboard wiring map.

The v2 placement is optimized around complete electrical nets rather than the
appearance of three identical rows. U1 and U2 face the same direction for the
controller-to-toolhead paths. U3 is deliberately rotated 180 degrees because
its signal travels from the toolhead back to the controller. That rotation,
channel-aligned terminal order, and omission of the optional C3 rail bypass
reduce the recovered v1 route from 110 segments / 337.35 mm to 38 segments /
161.83 mm: 65% fewer segments and 52% less routed length. There are no vias.

The direct-header harness uses `GP29` (U1 M3/M5), `GP28` (U2 `HOME_ARM`), and
`GP27` (U3 `A_HOME`) so the PC817 connector can occupy the consecutive Pro
Micro run `GND`, `RST` (NC), `3V3`, `GP29`, `GP28`, `GP27`. U1/U2 outputs are
active-low: R3/R4 pull GP29/GP28 to local 3.3 V while an illuminated PC817
pulls the corresponding input to `TOOL_GND`. Controller and toolhead grounds
remain galvanically isolated.

U3 is the reverse `GP27` to `A_HOME` channel. The RP23CNC `LIMA` input is a 12 V
active-low input that asserts when U3 sinks it to `CTRL_GND`; neither 12 V nor
3.3 V is driven into `A_HOME`. A bench test of the installed U3 sample, using
12 V and a 2.2 kΩ simulated controller load, measured approximately 12 V idle
and 0.2 V asserted. The completed bench assembly passed the same U1/U2/U3
circuit tests on the prior GP8/GP20/GP9 map; repeat them after repinning to
GP29/GP28/GP27. R6 may now be a direct `A_HOME`-to-`A_HOME_SW` wire or a 0 Ω
link.
This sample-specific measurement does not change the generic PC817C CTR limit;
test again if U3 is replaced.

KiCad 10.0.5 verification of v2 reports zero ERC violations, zero error-level
DRC violations, zero unconnected pads, and zero schematic-parity issues. An
independent exported-netlist audit matched all 46 schematic component pins to
their PCB pads, including both six-position terminal blocks. The
full visual DRC may still flag dense silkscreen clearances; those warnings do
not represent electrical faults and should be reviewed if manufacturing a PCB.

The v1.2 files and older rendered diagrams are retained as historical evidence.
The manually recovered `pc817-perfboard-v1.2-routed.kicad_pcb` contains known
shorts/opens and must not be used as a construction source.
