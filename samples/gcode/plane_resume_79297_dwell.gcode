(Resume plane.gcode from block 79297 after a P115 handshake timeout.)
(Console evidence: [MSG:P115 toolhead ready acknowledgement timed out] then)
(error:39, MPos -238.200,-108.725,21828.171 / DRO -5.766,86.401,5683.616.)
(That message is P115's completion phase, not its release phase: GP27/PRB did go)
(inactive, then never re-asserted ready inside the bound.)
(Start point is the end of block 79296: X-38.7076 Y116.1859 A1155.21, pen down)
(in a keep-down raster. This lifts, positions to that exact point, re-draws 79297,)
(then runs 79298-79315 with the pen commands unchanged.)
(No G65 P115 calls anywhere: every pen transition uses the fixed G4 dwell the)
(converter emits when "Wait for GP27 toolhead ready" is unticked, so a missed)
(GP27 edge cannot abort these last blocks again.)
(The opening M5 dwell is 1.5 s rather than the usual 0.8 s because the missed)
(handshake was a completion timeout on a pen clear. Confirm PRB is inactive /)
(the pen is clear before Cycle Start.)
(A values are shifted by +4320 motor degrees: the same bed orientation as)
(plane.gcode, but a ~208 degree lead-in move instead of a one-turn spin.)
(One bed turn is 4320 motor degrees at the 12:1 ratio.)
G21
G90
G94
G17
G54
M5
G4 P1.5
G0 F3000 X-38.7076 Y116.1859 A5475.21
M3
G4 P10
G1 F700
G1 X-38.7076 Y116.7914 A5479.0873 F3968.3279 (y_theta)
(contour 4141)
M5
G4 P0.8
G0 X-39.1911 Y115.9621 A5479.0873
M3
G4 P2.5
G1 F700
G1 X-38.9408 Y115.9621 A5482.392 F3944.4362 (x_theta)
G1 X-24.75 Y115.9621 A5479.7432 F712.0897 (x_theta)
G1 X-24.75 Y115.7937 A5478.7901 F4023.1856 (y_theta)
G1 X-39.6859 Y115.7937 A5482.0231 F716.2106 (x_theta)
M5
G4 P0.8
M65 P0
G4 P3.0
M64 P0
G53 G0 X-10 Y-436 (park home)
M2
