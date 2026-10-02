(A-axis repeatability test - lost motion after a full bed revolution)
(one bed revolution = 4331.9664 A motor degrees; ratio 12.03324 motor deg per bed deg)
(prerequisite: HOME and P100, so work X0 Y0 is the registered bed centre)
(each station draws a radial tick, rotates out and back, redraws the tick)
(ticks on top of each other = the bed returned)
(a gap s mm at radius R mm is degrees(s/R) of lost motion for that out-and-back)
(stations at radii 100, 160 mm; 2 revolutions each way at F15000)
G21
G90
G94
G17
G54
G0 F3000
M5
G4 P0.8
(station: r=100 mm)
G0 X100 Y0
M3
G4 P10
G1 F700
G1 X95 Y0
G1 X105 Y0
G91
G1 A4331.9664 F15000
G1 A4331.9664 F15000
G1 A-4331.9664 F15000
G1 A-4331.9664 F15000
G90
G1 X95 Y0
G1 X105 Y0
M5
G4 P0.8
(station: r=160 mm)
G0 X160 Y0
M3
G4 P2.5
G1 F700
G1 X155 Y0
G1 X165 Y0
G91
G1 A4331.9664 F15000
G1 A4331.9664 F15000
G1 A-4331.9664 F15000
G1 A-4331.9664 F15000
G90
G1 X155 Y0
G1 X165 Y0
M5
G4 P0.8
G53 G0 X-10 Y-436 (park home)
M2
