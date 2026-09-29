(F-05A P115 Q7 transition-edge check)
(Stream this whole file in one run. Q7 must already be polling while the pen)
(moves, so the toolhead command and the macro call are emitted back to back.)
(Expected: "P115 Q7 release observed" then "P115 Q7 completion observed".)
G21 G90
M64 P0
M5
G4 P3.0
M3
G65 P115 Q7 B12
M5
G4 P2.0
M64 P0
