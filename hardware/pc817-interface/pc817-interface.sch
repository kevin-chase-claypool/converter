EESchema Schematic File Version 4
LIBS:power
LIBS:Device
LIBS:Isolator
LIBS:Connector_Generic
EELAYER 29 0
EELAYER END
$Descr A4 11693 8268
encoding utf-8
Sheet 1 1
Title "Three-channel PC817C isolated interface"
Date "2026-08-06"
Rev "0.1"
Comp "Theta Pen Plotter — perfboard build"
Comment1 "R6 MUST REMAIN DNP until E-18 verifies the RP23CNC A-home input."
Comment2 "Use through-hole axial 1N4148 diodes on 2.54 mm perfboard."
Comment3 "J1/J2 are generic 2.54 mm, 5-pin right-angle locking headers; exact series TBD."
Comment4 "The controller-side and toolhead-side grounds are intentionally isolated."
$EndDescr
Text Notes 1000 950 0    120  ~ 24
PC817C THREE-CHANNEL ISOLATED INTERFACE — PERFBOARD SCHEMATIC
Text Notes 1000 1200 0    60   ~ 12
Fits the reserved 40.16 x 22.65 mm envelope only if the selected 2.54 mm perfboard and headers fit mechanically.\n+Do not use 1.25 mm JST-GH headers directly on ordinary 0.1 in / 2.54 mm perfboard.
Text Notes 1550 1950 0    80   ~ 16
J1 — RP23CNC HARNESS (5 V DOMAIN)
Text Notes 8500 1950 0    80   ~ 16
J2 — PRO MICRO HARNESS (3.3 V DOMAIN)
$Comp
L Connector_Generic:Conn_01x05 J1
U 1 1 66080001
P 2000 3000
F 0 "J1" H 2080 3042 50  0000 L CNN
F 1 "RP23CNC harness (2.54 mm RA)" H 2080 2951 50  0000 L CNN
F 2 "" H 2000 3000 50  0001 C CNN
F 3 "~" H 2000 3000 50  0001 C CNN
	1    2000 3000
	1    0    0    -1
$EndComp
Wire Wire Line
	1800 2800 2300 2800
Text Label 2300 2800 0    50   ~ 0
CTRL_5V
Wire Wire Line
	1800 2900 2300 2900
Text Label 2300 2900 0    50   ~ 0
CTRL_GND
Wire Wire Line
	1800 3000 2300 3000
Text Label 2300 3000 0    50   ~ 0
ENA
Wire Wire Line
	1800 3100 2300 3100
Text Label 2300 3100 0    50   ~ 0
AUX0
Wire Wire Line
	1800 3200 2300 3200
Text Label 2300 3200 0    50   ~ 0
A_HOME
$Comp
L Connector_Generic:Conn_01x05 J2
U 1 1 66080002
P 9250 3000
F 0 "J2" H 9330 3042 50  0000 L CNN
F 1 "Pro Micro harness (2.54 mm RA)" H 9330 2951 50  0000 L CNN
F 2 "" H 9250 3000 50  0001 C CNN
F 3 "~" H 9250 3000 50  0001 C CNN
	1    9250 3000
	1    0    0    -1
$EndComp
Wire Wire Line
	9050 2800 8550 2800
Text Label 8550 2800 2    50   ~ 0
TOOL_3V3
Wire Wire Line
	9050 2900 8550 2900
Text Label 8550 2900 2    50   ~ 0
TOOL_GND
Wire Wire Line
	9050 3000 8550 3000
Text Label 8550 3000 2    50   ~ 0
GP8
Wire Wire Line
	9050 3100 8550 3100
Text Label 8550 3100 2    50   ~ 0
GP10
Wire Wire Line
	9050 3200 8550 3200
Text Label 8550 3200 2    50   ~ 0
GP9
Text Notes 3550 1700 0    80   ~ 16
U1: M3/M5 COMMAND — ENA LOW = PC817 ON = GP8 LOW
$Comp
L Isolator:PC817 U1
U 1 1 66080101
P 5250 2200
F 0 "U1" H 5250 2525 50  0000 C CNN
F 1 "PC817C" H 5250 2434 50  0000 C CNN
F 2 "Package_DIP:DIP-4_W7.62mm" H 5050 2000 50  0001 L CIN
F 3 "" H 5250 2200 50  0001 L CNN
	1    5250 2200
	1    0    0    -1
$EndComp
$Comp
L Device:R R1
U 1 1 66080102
P 4450 2100
F 0 "R1" V 4243 2100 50  0000 C CNN
F 1 "680R" V 4334 2100 50  0000 C CNN
F 2 "" V 4380 2100 50  0001 C CNN
F 3 "~" H 4450 2100 50  0001 C CNN
	1    4450 2100
	0    1    1    0
$EndComp
Wire Wire Line
	4150 2100 4300 2100
Text Label 4150 2100 2    50   ~ 0
CTRL_5V
Wire Wire Line
	4600 2100 4950 2100
Wire Wire Line
	4950 2300 4650 2300
Text Label 4650 2300 2    50   ~ 0
ENA
$Comp
L Device:D D1
U 1 1 66080103
P 4600 2200
F 0 "D1" V 4554 2280 50  0000 L CNN
F 1 "1N4148" V 4645 2280 50  0000 L CNN
F 2 "Diode_THT:D_DO-35_SOD27_P10.16mm_Horizontal" H 4600 2200 50  0001 C CNN
F 3 "~" H 4600 2200 50  0001 C CNN
	1    4600 2200
	0    1    1    0
$EndComp
Wire Wire Line
	4600 2100 4600 2050
Wire Wire Line
	4600 2350 4600 2300
Text Notes 4080 2475 0    45   ~ 9
D1: reverse clamp; stripe/cathode to U1 pin 1
$Comp
L Device:R R3
U 1 1 66080104
P 6300 2100
F 0 "R3" V 6093 2100 50  0000 C CNN
F 1 "10k" V 6184 2100 50  0000 C CNN
F 2 "" V 6230 2100 50  0001 C CNN
F 3 "~" H 6300 2100 50  0001 C CNN
	1    6300 2100
	0    1    1    0
$EndComp
Wire Wire Line
	5550 2100 6150 2100
Text Label 5700 2100 0    50   ~ 0
GP8
Wire Wire Line
	6450 2100 6800 2100
Text Label 6800 2100 0    50   ~ 0
TOOL_3V3
Wire Wire Line
	5550 2300 5900 2300
Text Label 5900 2300 0    50   ~ 0
TOOL_GND
$Comp
L Device:C C1
U 1 1 66080105
P 5900 2200
F 0 "C1" H 6015 2246 50  0000 L CNN
F 1 "47nF" H 6015 2155 50  0000 L CNN
F 2 "" H 5938 2050 50  0001 C CNN
F 3 "~" H 5900 2200 50  0001 C CNN
	1    5900 2200
	1    0    0    -1
$EndComp
Wire Wire Line
	5900 2050 5900 2100
Wire Wire Line
	5900 2350 5900 2300
Text Notes 3550 3550 0    80   ~ 16
U2: HOME_ARM COMMAND — AUX0 LOW = PC817 ON = GP10 LOW
$Comp
L Isolator:PC817 U2
U 1 1 66080201
P 5250 4050
F 0 "U2" H 5250 4375 50  0000 C CNN
F 1 "PC817C" H 5250 4284 50  0000 C CNN
F 2 "Package_DIP:DIP-4_W7.62mm" H 5050 3850 50  0001 L CIN
F 3 "" H 5250 4050 50  0001 L CNN
	1    5250 4050
	1    0    0    -1
$EndComp
$Comp
L Device:R R2
U 1 1 66080202
P 4450 3950
F 0 "R2" V 4243 3950 50  0000 C CNN
F 1 "680R" V 4334 3950 50  0000 C CNN
F 2 "" V 4380 3950 50  0001 C CNN
F 3 "~" H 4450 3950 50  0001 C CNN
	1    4450 3950
	0    1    1    0
$EndComp
Wire Wire Line
	4150 3950 4300 3950
Text Label 4150 3950 2    50   ~ 0
CTRL_5V
Wire Wire Line
	4600 3950 4950 3950
Wire Wire Line
	4950 4150 4650 4150
Text Label 4650 4150 2    50   ~ 0
AUX0
$Comp
L Device:D D2
U 1 1 66080203
P 4600 4050
F 0 "D2" V 4554 4130 50  0000 L CNN
F 1 "1N4148" V 4645 4130 50  0000 L CNN
F 2 "Diode_THT:D_DO-35_SOD27_P10.16mm_Horizontal" H 4600 4050 50  0001 C CNN
F 3 "~" H 4600 4050 50  0001 C CNN
	1    4600 4050
	0    1    1    0
$EndComp
Wire Wire Line
	4600 3950 4600 3900
Wire Wire Line
	4600 4200 4600 4150
Text Notes 4080 4325 0    45   ~ 9
D2: reverse clamp; stripe/cathode to U2 pin 1
$Comp
L Device:R R4
U 1 1 66080204
P 6300 3950
F 0 "R4" V 6093 3950 50  0000 C CNN
F 1 "10k" V 6184 3950 50  0000 C CNN
F 2 "" V 6230 3950 50  0001 C CNN
F 3 "~" H 6300 3950 50  0001 C CNN
	1    6300 3950
	0    1    1    0
$EndComp
Wire Wire Line
	5550 3950 6150 3950
Text Label 5700 3950 0    50   ~ 0
GP10
Wire Wire Line
	6450 3950 6800 3950
Text Label 6800 3950 0    50   ~ 0
TOOL_3V3
Wire Wire Line
	5550 4150 5900 4150
Text Label 5900 4150 0    50   ~ 0
TOOL_GND
$Comp
L Device:C C2
U 1 1 66080205
P 5900 4050
F 0 "C2" H 6015 4096 50  0000 L CNN
F 1 "47nF" H 6015 4005 50  0000 L CNN
F 2 "" H 5938 3900 50  0001 C CNN
F 3 "~" H 5900 4050 50  0001 C CNN
	1    5900 4050
	1    0    0    -1
$EndComp
Wire Wire Line
	5900 3900 5900 3950
Wire Wire Line
	5900 4200 5900 4150
Text Notes 3550 5400 0    80   ~ 16
U3: REVERSE A_HOME OUTPUT — GP9 HIGH = PC817 ON = SWITCH-LIKE CLOSURE
$Comp
L Isolator:PC817 U3
U 1 1 66080301
P 5250 5900
F 0 "U3" H 5250 6225 50  0000 C CNN
F 1 "PC817C" H 5250 6134 50  0000 C CNN
F 2 "Package_DIP:DIP-4_W7.62mm" H 5050 5700 50  0001 L CIN
F 3 "" H 5250 5900 50  0001 L CNN
	1    5250 5900
	1    0    0    -1
$EndComp
$Comp
L Device:R R5
U 1 1 66080302
P 4450 5800
F 0 "R5" V 4243 5800 50  0000 C CNN
F 1 "390R" V 4334 5800 50  0000 C CNN
F 2 "" V 4380 5800 50  0001 C CNN
F 3 "~" H 4450 5800 50  0001 C CNN
	1    4450 5800
	0    1    1    0
$EndComp
Wire Wire Line
	4150 5800 4300 5800
Text Label 4150 5800 2    50   ~ 0
GP9
Wire Wire Line
	4600 5800 4950 5800
Wire Wire Line
	4950 6000 4650 6000
Text Label 4650 6000 2    50   ~ 0
TOOL_GND
$Comp
L Device:D D3
U 1 1 66080303
P 4600 5900
F 0 "D3" V 4554 5980 50  0000 L CNN
F 1 "1N4148" V 4645 5980 50  0000 L CNN
F 2 "Diode_THT:D_DO-35_SOD27_P10.16mm_Horizontal" H 4600 5900 50  0001 C CNN
F 3 "~" H 4600 5900 50  0001 C CNN
	1    4600 5900
	0    1    1    0
$EndComp
Wire Wire Line
	4600 5800 4600 5750
Wire Wire Line
	4600 6050 4600 6000
Text Notes 4080 6175 0    45   ~ 9
D3: reverse clamp; stripe/cathode to U3 pin 1
Wire Wire Line
	5550 5800 6150 5800
$Comp
L Device:R R6
U 1 1 66080304
P 6300 5800
F 0 "R6" V 6093 5800 50  0000 C CNN
F 1 "0R DNP" V 6184 5800 50  0000 C CNN
F 2 "" V 6230 5800 50  0001 C CNN
F 3 "~" H 6300 5800 50  0001 C CNN
	1    6300 5800
	0    1    1    0
$EndComp
Wire Wire Line
	6450 5800 6800 5800
Text Label 6800 5800 0    50   ~ 0
A_HOME
Wire Wire Line
	5550 6000 5900 6000
Text Label 5900 6000 0    50   ~ 0
CTRL_GND
Text Notes 6025 6125 0    55   ~ 11
R6 is intentionally NOT FITTED. Do not connect A_HOME until E-18 passes.
$Comp
L Device:C C3
U 1 1 66080305
P 8000 4000
F 0 "C3" H 8115 4046 50  0000 L CNN
F 1 "100nF" H 8115 3955 50  0000 L CNN
F 2 "" H 8038 3850 50  0001 C CNN
F 3 "~" H 8000 4000 50  0001 C CNN
	1    8000 4000
	1    0    0    -1
$EndComp
Wire Wire Line
	8000 3850 8000 3750
Text Label 8000 3750 0    50   ~ 0
TOOL_3V3
Wire Wire Line
	8000 4150 8000 4250
Text Label 8000 4250 0    50   ~ 0
TOOL_GND
Text Notes 7475 4525 0    55   ~ 11
C3: place near J2 / Pro Micro 3.3 V and ground.
Text Notes 1200 6750 0    65   ~ 13
BUILD + TEST CONDITIONS
Text Notes 1200 6925 0    50   ~ 10
1. Use through-hole PC817C DIP-4 packages, axial 1N4148 diodes, and 1/4 W through-hole resistors on 2.54 mm perfboard.\n+2. J1 and J2 must be 2.54 mm right-angle, locking headers; do not use JST-GH directly on standard perfboard.\n+3. U1/U2: verify the RP23CNC output can act as a 5 V low-side sink before connecting. Do not apply controller 5 V to the toolhead side.\n+4. U3/R6: leave R6 unpopulated; E-18 must prove the RP23CNC A-home input's polarity and required pull-up before fitting it.\n+5. The PC817 only transfers light. CTRL_GND and TOOL_GND stay separate through this module.
$EndSCHEMATC
