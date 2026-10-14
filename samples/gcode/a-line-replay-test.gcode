(bed-angle line-replay test - make_a_line_replay_test.py)
(origin = longest line at A=0; every other pass must land on it)
(parallel gap between lines = that angle's offset; fan at the ends = rotation)
(requires HOME + bed registration; pen: finest available, e.g. Pigma Micron 003)
(draw order: origin, 2 control passes at A=0, replays 90/180/270, closing pass)
G21
G90
G94
G17
G54
G0 F3000
M5
G65 P115 Q0 A1 W2
(origin: bed angle 0 deg, half length 70)
G0 X-70 Y0 A0
M3
G65 P115 Q1 B12 A1 W2
G1 X70 Y0 A0 F350
M5
G65 P115 Q1 A1 W2
(control 1: bed angle 0 deg, half length 60)
G0 X-60 Y0 A0
M3
G65 P115 Q1 A1 W2
G1 X60 Y0 A0 F350
M5
G65 P115 Q1 A1 W2
(control 2: bed angle 0 deg, half length 60)
G0 X-60 Y0 A0
M3
G65 P115 Q1 A1 W2
G1 X60 Y0 A0 F350
M5
G65 P115 Q1 A1 W2
(replay 90: bed angle 90 deg, half length 60)
G0 X0 Y-60 A1082.9916
M3
G65 P115 Q1 A1 W2
G1 X0 Y60 A1082.9916 F350
M5
G65 P115 Q1 A1 W2
(replay 180: bed angle 180 deg, half length 60)
G0 X60 Y0 A2165.9832
M3
G65 P115 Q1 A1 W2
G1 X-60 Y0 A2165.9832 F350
M5
G65 P115 Q1 A1 W2
(replay 270: bed angle 270 deg, half length 60)
G0 X0 Y60 A3248.9748
M3
G65 P115 Q1 A1 W2
G1 X0 Y-60 A3248.9748 F350
M5
G65 P115 Q1 A1 W2
(closing: bed angle 0 deg, half length 60)
G0 X-60 Y0 A0
M3
G65 P115 Q1 A1 W2
G1 X60 Y0 A0 F350
M5
G65 P115 Q1 A1 W2
M65 P0
G65 P115 Q0 A3 W1
M64 P0
G53 G1 X-10 Y-436 F3000 (park home)
M2
