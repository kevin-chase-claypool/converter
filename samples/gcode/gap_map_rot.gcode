(gap map: bed rotation sweep at r = 60 / 90 mm)
(pen-up measurement program: no wiring, read the gauge at each stop)
(requires HOME + bed registration, so G54 X0 Y0 is the bed centre)
(keep the toolhead clear of the bed at the working height)
(carriage parks at each radius; the bed indexes 30 deg at a time)
G21
G90
G94
G17
G54
G0 F3000
M5
G4 P1.0
(radius 60 mm)
G0 X60.000 Y0.000
G4 P0.5
M5
M0 (r=60 mm, angle 0 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=60 mm, angle 30 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=60 mm, angle 60 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=60 mm, angle 90 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=60 mm, angle 120 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=60 mm, angle 150 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=60 mm, angle 180 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=60 mm, angle 210 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=60 mm, angle 240 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=60 mm, angle 270 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=60 mm, angle 300 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=60 mm, angle 330 deg - read gap, then Cycle Start)
(radius 90 mm)
G0 X90.000 Y0.000
G4 P0.5
M5
M0 (r=90 mm, angle 0 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=90 mm, angle 30 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=90 mm, angle 60 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=90 mm, angle 90 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=90 mm, angle 120 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=90 mm, angle 150 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=90 mm, angle 180 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=90 mm, angle 210 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=90 mm, angle 240 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=90 mm, angle 270 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=90 mm, angle 300 deg - read gap, then Cycle Start)
G91
G1 A360.9972 F6000
G90
G4 P0.5
M5
M0 (r=90 mm, angle 330 deg - read gap, then Cycle Start)
M5
M2
