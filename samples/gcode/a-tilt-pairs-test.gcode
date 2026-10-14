(bed-tilt quadrant pair test - make_a_tilt_pairs_test.py)
(four pairs of two lines; inside a pair the LONGER line is the A=0 constant)
(and the SHORTER line is the re-draw at that pair's angle - they should land on top)
(zigzag label above each pair counts the angle: 1 tooth = control, A0 into A0)
(2 teeth = 90 deg, 3 teeth = 180, 4 teeth = 270; the control pair sets the baseline)
(measure between the pair's lines: middle gap plus both end overhangs)
(requires HOME + bed registration; pen: finest available, e.g. Pigma Micron 003)
G21
G90
G94
G17
G54
G0 F3000
M5
G65 P115 Q0 A1 W2
(pair control: 1-teeth label)
G0 X-91 Y-67 A0
M3
G65 P115 Q1 B12 A1 W2
G1 X-91 Y-63 A0 F350
M5
G65 P115 Q1 A1 W2
(pair control: constant pass at A=0, 80 mm)
G0 X-90 Y-75 A0
M3
G65 P115 Q1 A1 W2
G1 X-10 Y-75 A0 F350
M5
G65 P115 Q1 A1 W2
(pair control: test pass at bed angle 0, 66 mm)
G0 X-83 Y-75 A0
M3
G65 P115 Q1 A1 W2
G1 X-17 Y-75 A0 F350
M5
G65 P115 Q1 A1 W2
(pair 90 deg: 2-teeth label)
G0 X9 Y-67 A0
M3
G65 P115 Q1 A1 W2
G1 X9 Y-63 A0 F350
G1 X14 Y-63 A0
G1 X14 Y-67 A0
M5
G65 P115 Q1 A1 W2
(pair 90 deg: constant pass at A=0, 80 mm)
G0 X10 Y-75 A0
M3
G65 P115 Q1 A1 W2
G1 X90 Y-75 A0 F350
M5
G65 P115 Q1 A1 W2
(pair 90 deg: test pass at bed angle 90, 66 mm)
G0 X75 Y17 A1082.9916
M3
G65 P115 Q1 A1 W2
G1 X75 Y83 A1082.9916 F350
M5
G65 P115 Q1 A1 W2
(pair 180 deg: 3-teeth label)
G0 X9 Y33 A0
M3
G65 P115 Q1 A1 W2
G1 X9 Y37 A0 F350
G1 X14 Y37 A0
G1 X14 Y33 A0
G1 X19 Y33 A0
G1 X19 Y37 A0
M5
G65 P115 Q1 A1 W2
(pair 180 deg: constant pass at A=0, 80 mm)
G0 X10 Y25 A0
M3
G65 P115 Q1 A1 W2
G1 X90 Y25 A0 F350
M5
G65 P115 Q1 A1 W2
(pair 180 deg: test pass at bed angle 180, 66 mm)
G0 X-17 Y-25 A2165.9832
M3
G65 P115 Q1 A1 W2
G1 X-83 Y-25 A2165.9832 F350
M5
G65 P115 Q1 A1 W2
(pair 270 deg: 4-teeth label)
G0 X-91 Y33 A0
M3
G65 P115 Q1 A1 W2
G1 X-91 Y37 A0 F350
G1 X-86 Y37 A0
G1 X-86 Y33 A0
G1 X-81 Y33 A0
G1 X-81 Y37 A0
G1 X-76 Y37 A0
G1 X-76 Y33 A0
M5
G65 P115 Q1 A1 W2
(pair 270 deg: constant pass at A=0, 80 mm)
G0 X-90 Y25 A0
M3
G65 P115 Q1 A1 W2
G1 X-10 Y25 A0 F350
M5
G65 P115 Q1 A1 W2
(pair 270 deg: test pass at bed angle 270, 66 mm)
G0 X25 Y83 A3248.9748
M3
G65 P115 Q1 A1 W2
G1 X25 Y17 A3248.9748 F350
M5
G65 P115 Q1 A1 W2
M65 P0
G65 P115 Q0 A3 W1
M64 P0
G53 G1 X-10 Y-436 F3000 (park home)
M2
