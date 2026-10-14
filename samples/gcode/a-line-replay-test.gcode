(bed-angle line-replay test - make_a_line_replay_test.py)
(origin = longest line at A=0; every other pass must land on it)
(parallel gap between lines = that angle's offset; fan at the ends = rotation)
(requires HOME + bed registration; pen: finest available, e.g. Pigma Micron 003)
(draw order: origin, 2 control passes at A=0, replays 90/180/270, closing pass)
(identification by total length in mm: origin 140, control 120, replays 112/104/96, closing 128)
(every pass carries a 4 mm perpendicular tag at both ends; the tag ladder repeats the length order)
G21
G90
G94
G17
G54
G0 F3000
M5
G65 P115 Q0 A1 W2
(origin, 140 mm total: bed angle 0 deg, half length 70)
G0 X-70 Y4 A0
M3
G65 P115 Q1 B12 A1 W2
G1 X-70 Y0 A0 F350
G1 X70 Y0 A0
G1 X70 Y4 A0
M5
G65 P115 Q1 A1 W2
(control 1, 120 mm total: bed angle 0 deg, half length 60)
G0 X-60 Y4 A0
M3
G65 P115 Q1 A1 W2
G1 X-60 Y0 A0 F350
G1 X60 Y0 A0
G1 X60 Y4 A0
M5
G65 P115 Q1 A1 W2
(control 2, 120 mm total: bed angle 0 deg, half length 60)
G0 X-60 Y4 A0
M3
G65 P115 Q1 A1 W2
G1 X-60 Y0 A0 F350
G1 X60 Y0 A0
G1 X60 Y4 A0
M5
G65 P115 Q1 A1 W2
(replay 90, 112 mm total: bed angle 90 deg, half length 56)
G0 X-4 Y-56 A1082.9916
M3
G65 P115 Q1 A1 W2
G1 X0 Y-56 A1082.9916 F350
G1 X0 Y56 A1082.9916
G1 X-4 Y56 A1082.9916
M5
G65 P115 Q1 A1 W2
(replay 180, 104 mm total: bed angle 180 deg, half length 52)
G0 X52 Y-4 A2165.9832
M3
G65 P115 Q1 A1 W2
G1 X52 Y0 A2165.9832 F350
G1 X-52 Y0 A2165.9832
G1 X-52 Y-4 A2165.9832
M5
G65 P115 Q1 A1 W2
(replay 270, 96 mm total: bed angle 270 deg, half length 48)
G0 X4 Y48 A3248.9748
M3
G65 P115 Q1 A1 W2
G1 X0 Y48 A3248.9748 F350
G1 X0 Y-48 A3248.9748
G1 X4 Y-48 A3248.9748
M5
G65 P115 Q1 A1 W2
(closing, 128 mm total: bed angle 0 deg, half length 64)
G0 X-64 Y4 A0
M3
G65 P115 Q1 A1 W2
G1 X-64 Y0 A0 F350
G1 X64 Y0 A0
G1 X64 Y4 A0
M5
G65 P115 Q1 A1 W2
M65 P0
G65 P115 Q0 A3 W1
M64 P0
G53 G1 X-10 Y-436 F3000 (park home)
M2
