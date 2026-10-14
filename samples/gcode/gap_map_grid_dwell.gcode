(gap map: 5x5 grid over the used area, bed parked)
(pen-up measurement program: no wiring, read the gauge at each stop)
(requires HOME + bed registration, so G54 X0 Y0 is the bed centre)
(keep the toolhead clear of the bed at the working height)
(record the gap at every stop; the bed does not move in this program)
G21
G90
G94
G17
G54
G0 F3000
M5
G4 P1.0
G0 X-100.000 Y-100.000
G4 P0.3
M5
(stop) G54 X-100.0 Y-100.0 - read gap, then Cycle Start
G4 P25
G0 X-50.000 Y-100.000
G4 P0.3
M5
(stop) G54 X-50.0 Y-100.0 - read gap, then Cycle Start
G4 P25
G0 X0.000 Y-100.000
G4 P0.3
M5
(stop) G54 X0.0 Y-100.0 - read gap, then Cycle Start
G4 P25
G0 X50.000 Y-100.000
G4 P0.3
M5
(stop) G54 X50.0 Y-100.0 - read gap, then Cycle Start
G4 P25
G0 X100.000 Y-100.000
G4 P0.3
M5
(stop) G54 X100.0 Y-100.0 - read gap, then Cycle Start
G4 P25
G0 X100.000 Y-50.000
G4 P0.3
M5
(stop) G54 X100.0 Y-50.0 - read gap, then Cycle Start
G4 P25
G0 X50.000 Y-50.000
G4 P0.3
M5
(stop) G54 X50.0 Y-50.0 - read gap, then Cycle Start
G4 P25
G0 X0.000 Y-50.000
G4 P0.3
M5
(stop) G54 X0.0 Y-50.0 - read gap, then Cycle Start
G4 P25
G0 X-50.000 Y-50.000
G4 P0.3
M5
(stop) G54 X-50.0 Y-50.0 - read gap, then Cycle Start
G4 P25
G0 X-100.000 Y-50.000
G4 P0.3
M5
(stop) G54 X-100.0 Y-50.0 - read gap, then Cycle Start
G4 P25
G0 X-100.000 Y0.000
G4 P0.3
M5
(stop) G54 X-100.0 Y0.0 - read gap, then Cycle Start
G4 P25
G0 X-50.000 Y0.000
G4 P0.3
M5
(stop) G54 X-50.0 Y0.0 - read gap, then Cycle Start
G4 P25
G0 X0.000 Y0.000
G4 P0.3
M5
(stop) G54 X0.0 Y0.0 - read gap, then Cycle Start
G4 P25
G0 X50.000 Y0.000
G4 P0.3
M5
(stop) G54 X50.0 Y0.0 - read gap, then Cycle Start
G4 P25
G0 X100.000 Y0.000
G4 P0.3
M5
(stop) G54 X100.0 Y0.0 - read gap, then Cycle Start
G4 P25
G0 X100.000 Y50.000
G4 P0.3
M5
(stop) G54 X100.0 Y50.0 - read gap, then Cycle Start
G4 P25
G0 X50.000 Y50.000
G4 P0.3
M5
(stop) G54 X50.0 Y50.0 - read gap, then Cycle Start
G4 P25
G0 X0.000 Y50.000
G4 P0.3
M5
(stop) G54 X0.0 Y50.0 - read gap, then Cycle Start
G4 P25
G0 X-50.000 Y50.000
G4 P0.3
M5
(stop) G54 X-50.0 Y50.0 - read gap, then Cycle Start
G4 P25
G0 X-100.000 Y50.000
G4 P0.3
M5
(stop) G54 X-100.0 Y50.0 - read gap, then Cycle Start
G4 P25
G0 X-100.000 Y100.000
G4 P0.3
M5
(stop) G54 X-100.0 Y100.0 - read gap, then Cycle Start
G4 P25
G0 X-50.000 Y100.000
G4 P0.3
M5
(stop) G54 X-50.0 Y100.0 - read gap, then Cycle Start
G4 P25
G0 X0.000 Y100.000
G4 P0.3
M5
(stop) G54 X0.0 Y100.0 - read gap, then Cycle Start
G4 P25
G0 X50.000 Y100.000
G4 P0.3
M5
(stop) G54 X50.0 Y100.0 - read gap, then Cycle Start
G4 P25
G0 X100.000 Y100.000
G4 P0.3
M5
(stop) G54 X100.0 Y100.0 - read gap, then Cycle Start
G4 P25
M5
M2
