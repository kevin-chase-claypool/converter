(rotation-centre cross calibration - make_rotation_center_calibration.py)
(run G65 P113 first; every cross is centred on the freshly registered G54 X0 Y0)
(layout: 330.2 mm test on 355.6 mm round stock, largest ink radius 165.1 mm)
(reference cross is longest and its arrowheads point machine +X and +Y)
(the other crosses replay the same bed-frame cross at their labelled bed angles)
(after the bed returns to A=0, measure each replay cross minus the reference cross)
(positive DX/DY means the replay is toward the reference arrowheads)
(longest to shortest crosses: reference 330.2 mm, control 1 320.2 mm, replay 90 310.2 mm, replay 180 300.2 mm, replay 270 290.2 mm, closing 280.2 mm)
G21
G90
G94
G17
G54
M5
G4 P1
G65 P115 Q0 A1 W2
(reference cross: bed angle 0 deg, arm 165.1 mm)
G1 X-165.1 Y0 A0 F3000 (travel)
M3
G65 P115 Q1 B12 A1 W2
G1 X165.1 Y0 A0 F700
M5
G65 P115 Q1 A1 W2
G1 X0 Y-165.1 A0 F3000 (travel)
M3
G65 P115 Q1 A1 W2
G1 X0 Y165.1 A0 F700
M5
G65 P115 Q1 A1 W2
(control 1 cross: bed angle 0 deg, arm 160.1 mm)
G1 X-160.1 Y0 A0 F3000 (travel)
M3
G65 P115 Q1 A1 W2
G1 X160.1 Y0 A0 F700
M5
G65 P115 Q1 A1 W2
G1 X0 Y-160.1 A0 F3000 (travel)
M3
G65 P115 Q1 A1 W2
G1 X0 Y160.1 A0 F700
M5
G65 P115 Q1 A1 W2
(replay 90 cross: bed angle 90 deg, arm 155.1 mm)
G1 X0 Y-155.1 A1082.9916 F10735.3565 (travel)
M3
G65 P115 Q1 A1 W2
G1 X0 Y155.1 A1082.9916 F700
M5
G65 P115 Q1 A1 W2
G1 X155.1 Y0 A1082.9916 F3000 (travel)
M3
G65 P115 Q1 A1 W2
G1 X-155.1 Y0 A1082.9916 F700
M5
G65 P115 Q1 A1 W2
(replay 180 cross: bed angle 180 deg, arm 150.1 mm)
G1 X150.1 Y0 A2165.9832 F11060.0385 (travel)
M3
G65 P115 Q1 A1 W2
G1 X-150.1 Y0 A2165.9832 F700
M5
G65 P115 Q1 A1 W2
G1 X0 Y150.1 A2165.9832 F3000 (travel)
M3
G65 P115 Q1 A1 W2
G1 X0 Y-150.1 A2165.9832 F700
M5
G65 P115 Q1 A1 W2
(replay 270 cross: bed angle 270 deg, arm 145.1 mm)
G1 X0 Y145.1 A3248.9748 F11407.5547 (travel)
M3
G65 P115 Q1 A1 W2
G1 X0 Y-145.1 A3248.9748 F700
M5
G65 P115 Q1 A1 W2
G1 X-145.1 Y0 A3248.9748 F3000 (travel)
M3
G65 P115 Q1 A1 W2
G1 X145.1 Y0 A3248.9748 F700
M5
G65 P115 Q1 A1 W2
(closing cross: bed angle 0 deg, arm 140.1 mm)
G1 X-140.1 Y0 A0 F30115.3622 (travel)
M3
G65 P115 Q1 A1 W2
G1 X140.1 Y0 A0 F700
M5
G65 P115 Q1 A1 W2
G1 X0 Y-140.1 A0 F3000 (travel)
M3
G65 P115 Q1 A1 W2
G1 X0 Y140.1 A0 F700
M5
G65 P115 Q1 A1 W2
(reference +X and +Y arrowheads; the open end of each V is positive)
G1 X165.1 Y0 A0 F3000 (travel)
M3
G65 P115 Q1 A1 W2
G1 X161.1 Y1.6 A0 F700
G1 X165.1 Y0 A0
G1 X161.1 Y-1.6 A0
M5
G65 P115 Q1 A1 W2
G1 X0 Y165.1 A0 F3000 (travel)
M3
G65 P115 Q1 A1 W2
G1 X1.6 Y161.1 A0 F700
G1 X0 Y165.1 A0
G1 X-1.6 Y161.1 A0
M5
G65 P115 Q1 A1 W2
M65 P0
G65 P115 Q0 A3 W1
M64 P0
G53 G1 X-10 Y-436 F3000 (park home)
M2
