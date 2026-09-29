(F-05A strict P115 pass)
(Q0 accepts the initial verified clear; Q1 must then observe a fresh)
(inactive-then-active edge after each M3 and M5. Stream the whole file so the)
(macro call is already running while the toolhead physically moves.)
(Expected: "P115 toolhead completion acknowledged" three times, no error 39.)
G21 G90
M64 P0
M5
G4 P3.0
G65 P115 Q0
M3
G65 P115 Q1 B12
M5
G65 P115 Q1
M64 P0
