(M-06 pen-free coordinated X/Y/A repeatability smoke test.)
(Preconditions: pen removed, XY near center, marks on carriage and bed.)
G21
G94
G91

G1 X50 Y50 A720 F20000
G1 X-50 Y-50 A-720 F20000

G1 X-50 Y50 A-720 F20000
G1 X50 Y-50 A720 F20000

G90
