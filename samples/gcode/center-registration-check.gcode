(center registration check - is G54 X0 Y0 on the bed's rotation axis?)
(run P113 first: this assumes the freshly registered frame)
(cross arm 4 mm; half a bed revolution = 2165.9832 A motor degrees)
(crosses on top of each other = the origin is on the axis)
(a gap is twice the residual off-axis error, in the gap's direction)
G21
G90
G94
G17
G54
G0 F3000
M5
G4 P0.8
G0 X0 Y0
M3
G4 P10
G1 F700
G1 X-2 Y0
G1 X2 Y0
G1 X0 Y-2
G1 X0 Y2
M5
G4 P0.8
G91
G1 A2165.9832 F20000
G90
G0 X0 Y0
M3
G4 P2.5
G1 F700
G1 X-2 Y0
G1 X2 Y0
G1 X0 Y-2
G1 X0 Y2
M5
G4 P0.8
G91
G1 A-2165.9832 F20000
G90
G53 G0 X-10 Y-436 (park home)
M2
