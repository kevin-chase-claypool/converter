(Resume plane.gcode after the P115 completion timeout at block 79297.)
(Console evidence: [MSG:P115 toolhead ready acknowledgement timed out] then)
(error:39, MPos -238.200,-108.725,21828.171 / DRO -5.766,86.401,5683.616.)
(That message is P115's completion phase, not its release phase: GP27/PRB did go)
(inactive, then never re-asserted ready inside the bound.)
(The failed call is the G65 P115 Q1 at block 79300, the wait after the M5 at 79299)
(that lifts the pen off the finished infill. It is skipped: this file contains no)
(G65 P115 call, so the remaining blocks cannot abort again.)
(Blocks 79297-79300 are not re-run. Block 79297 was already drawn before the fault.)
(The new start point is block 79301, the pen-up rapid to X-39.1911 Y115.9621)
(A1159.0873; the lead-in below is that block. Contour 4141 then draws from 79305.)
(The opening M5 uses a fixed 1.5 s dwell because the failed clear was never)
(confirmed by a handshake. Confirm PRB is inactive / the pen is clear before)
(Cycle Start; the travel to the start point happens with the pen up.)
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
G0 F3000 X-39.1911 Y115.9621 A5479.0873
M3
G4 P10
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
