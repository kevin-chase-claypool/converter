# Lab Note: 2026-08-14 - E-07 HX711 Load-Cell Calibration

## Objective

Verify the HX711 and 300 g load cell are electrically alive, establish the raw
zero/noise behavior, determine the force sign, and collect at least one known-
mass calibration point.

## Configuration

- Hardware: SparkFun Pro Micro RP2350; HiLetgo HX711; uxcell 300 g load cell.
- Mechanical force path: the load cell's fixed side is attached to the gantry;
  its moving side carries the gray actuator/guide block. The blue piece holds
  the pen, and the pen itself slides through the gray guide block. The linear
  rail guides the moving assembly; its axial friction should be minimal.
- Wiring: HX711 `DT` to GP0; `SCK` to GP1; HX711 `VCC` to Pro Micro `3V3`;
  HX711 `GND` to Pro Micro GND. Load-cell red to `E+`, black to `E-`, green to
  `A+`, white to `A-`.
- Power: 6 V toolhead JST disconnected. USB is the only test power source.
- Firmware: `firmware/pen_pressure/e07_hx711_calibration/e07_hx711_calibration.ino`.
- Instruments: USB Serial Monitor at 115200 baud; known calibration mass TBD.

## Code, commands, and configuration used

```cpp
/*
  E-07: HX711 load-cell raw reading and calibration test

  Target: SparkFun Pro Micro RP2350 using the Arduino-Pico board package.

  Wiring:
    GP0 <- HX711 DT/DOUT
    GP1 -> HX711 SCK
    Pro Micro 3V3 -> HX711 VCC
    Pro Micro GND -> HX711 GND
    Load cell: red -> E+, black -> E-, green -> A+, white -> A-

  Keep the 6 V toolhead JST disconnected. USB powers this sensor-only test.
  Open Serial Monitor at 115200 baud and send:
    t  tare with the pen/load cell unloaded
    p  print the current reading immediately
    ?  print help

  Place a known mass on the pen/load cell after taring. Record the stable
  hx_delta value and whether it rises or falls. If it falls, the sign can be
  handled in later firmware; do not swap load-cell wires during E-07.
*/
#include <Arduino.h>
#include "HX711.h"

constexpr uint8_t PIN_HX711_DT = 0;
constexpr uint8_t PIN_HX711_SCK = 1;
constexpr uint32_t SERIAL_BAUD = 115200;
constexpr uint32_t REPORT_PERIOD_MS = 500;
constexpr uint8_t TARE_SAMPLES = 20;

HX711 scale;
long tareRaw = 0;
long lastRaw = 0;

bool readRaw(long &value) {
  if (!scale.is_ready()) return false;
  value = scale.read();
  lastRaw = value;
  return true;
}

void tare() {
  long total = 0;
  uint8_t count = 0;
  while (count < TARE_SAMPLES) {
    long sample = 0;
    if (readRaw(sample)) {
      total += sample;
      count++;
    }
    delay(10);
  }
  tareRaw = total / TARE_SAMPLES;
  Serial.print(F("Tare raw="));
  Serial.println(tareRaw);
}

void report() {
  long raw = lastRaw;
  const bool ready = readRaw(raw);
  Serial.print(F("hx_ready="));
  Serial.print(ready ? F("1") : F("0"));
  Serial.print(F(" hx_raw="));
  Serial.print(lastRaw);
  Serial.print(F(" hx_tare="));
  Serial.print(tareRaw);
  Serial.print(F(" hx_delta="));
  Serial.println(lastRaw - tareRaw);
}

void printHelp() {
  Serial.println(F("E-07 commands: t=tare, p=print, ?=help"));
}

void setup() {
  Serial.begin(SERIAL_BAUD);
  delay(500);
  scale.begin(PIN_HX711_DT, PIN_HX711_SCK);
  Serial.println(F("E-07 HX711 calibration test"));
  printHelp();
  if (!scale.is_ready()) {
    Serial.println(F("HX711 not ready: check VCC, GND, GP0, and GP1."));
  }
}

void loop() {
  static uint32_t lastReportMs = 0;
  while (Serial.available() > 0) {
    switch (static_cast<char>(Serial.read())) {
      case 't': case 'T': tare(); break;
      case 'p': case 'P': report(); break;
      case '?': printHelp(); break;
      default: break;
    }
  }
  if (millis() - lastReportMs >= REPORT_PERIOD_MS) {
    lastReportMs = millis();
    report();
  }
}
```

## Procedure

1. Confirm the 6 V JST is unplugged; connect the Pro Micro to USB.
2. Upload the listed E-07 sketch using the SparkFun Pro Micro RP2350 board
   target and open Serial Monitor at 115200 baud.
3. Verify `hx_ready=1` with the pen/load cell unloaded.
4. Send `t`, leave the mechanism untouched, and record at least 10 idle lines.
5. First, gently apply and release force at the pen tip in the normal upward
   bed-reaction direction. Confirm that `hx_delta` changes and returns toward
   zero. A negative sign is acceptable.
6. **Stage 1 — direct cell calibration:** place a securely supported known mass
   on the gray load-cell-mounted block only if the mass contacts no gantry,
   rail, pen, or other structure. Its force must be aligned with the cell's
   sensitive axis. Record stable deltas for at least two masses and remove each
   mass to check return toward zero. This calibrates the HX711/load-cell chain
   without lead-screw or guide friction.
7. **Stage 2 — pen-tip validation:** use a small digital scale under the pen
   tip and compare its indicated force with stable `hx_delta` values while the
   actuator is held at a fixed position. This captures actual screw/guide
   friction and any force-path loss.
8. Record at least 10 stable lines at each force level, then remove the force
   and confirm return toward zero.

## Results

### First raw-reading attempt

The HX711 reported `hx_ready=1` for nearly every 500 ms telemetry line. One
`hx_ready=0` line immediately after tare is expected when the report occurs
between ADC conversions; it did not interrupt later readings.

Before tare, the unloaded raw value settled approximately between 47,700 and
49,327 counts. The unloaded tare was 47,909 counts. Immediately after tare,
the delta rose gradually from 125 to 1,389 counts. A later applied/released
load produced a strong negative response, reaching -621,802 counts relative to
that tare. After the change, readings settled near -84,000 counts relative to
the original tare, then varied around -94,000 to -101,000 counts.

```text
Tare raw=47909
hx_ready=0 hx_raw=48034 hx_tare=47909 hx_delta=125
hx_ready=1 hx_raw=48059 hx_tare=47909 hx_delta=150
hx_ready=1 hx_raw=48145 hx_tare=47909 hx_delta=236
hx_ready=1 hx_raw=48109 hx_tare=47909 hx_delta=200
hx_ready=1 hx_raw=48166 hx_tare=47909 hx_delta=257
hx_ready=1 hx_raw=48324 hx_tare=47909 hx_delta=415
hx_ready=1 hx_raw=48379 hx_tare=47909 hx_delta=470
hx_ready=1 hx_raw=48461 hx_tare=47909 hx_delta=552
hx_ready=1 hx_raw=48481 hx_tare=47909 hx_delta=572
hx_ready=1 hx_raw=49088 hx_tare=47909 hx_delta=1179
hx_ready=1 hx_raw=49298 hx_tare=47909 hx_delta=1389
hx_ready=1 hx_raw=49246 hx_tare=47909 hx_delta=1337
hx_ready=1 hx_raw=3029 hx_tare=47909 hx_delta=-44880
hx_ready=1 hx_raw=-260312 hx_tare=47909 hx_delta=-308221
hx_ready=1 hx_raw=-439892 hx_tare=47909 hx_delta=-487801
hx_ready=1 hx_raw=-418717 hx_tare=47909 hx_delta=-466626
hx_ready=1 hx_raw=-386167 hx_tare=47909 hx_delta=-434076
hx_ready=1 hx_raw=-35139 hx_tare=47909 hx_delta=-83048
hx_ready=1 hx_raw=-36201 hx_tare=47909 hx_delta=-84110
hx_ready=1 hx_raw=-36399 hx_tare=47909 hx_delta=-84308
hx_ready=1 hx_raw=-36378 hx_tare=47909 hx_delta=-84287
hx_ready=1 hx_raw=-36363 hx_tare=47909 hx_delta=-84272
hx_ready=1 hx_raw=-36458 hx_tare=47909 hx_delta=-84367
hx_ready=1 hx_raw=-36445 hx_tare=47909 hx_delta=-84354
hx_ready=1 hx_raw=-95995 hx_tare=47909 hx_delta=-143904
hx_ready=1 hx_raw=-457708 hx_tare=47909 hx_delta=-505617
hx_ready=1 hx_raw=-470206 hx_tare=47909 hx_delta=-518115
hx_ready=1 hx_raw=-542654 hx_tare=47909 hx_delta=-590563
hx_ready=1 hx_raw=-573893 hx_tare=47909 hx_delta=-621802
hx_ready=1 hx_raw=-53130 hx_tare=47909 hx_delta=-101039
hx_ready=1 hx_raw=-47059 hx_tare=47909 hx_delta=-94968
hx_ready=1 hx_raw=-46190 hx_tare=47909 hx_delta=-94099
hx_ready=1 hx_raw=-45775 hx_tare=47909 hx_delta=-93684
```

## Difficulties and corrective actions

The first post-load resting value did not return to the original tare. Possible
causes are changed pen position, guide/lead-screw stiction, residual external
force, or structural preload. Do not swap sensor wires: the large signed raw
response confirms the electrical chain is working. Re-establish an identical
unloaded pen position, wait for settling, tare again, and capture an untouched
baseline before applying known force.

### Direct 57.2 g calibration point

With the mechanism unloaded and stationary, a new tare was taken at 15,217
counts. A known 57.2 g mass was then placed only on the gray
load-cell-mounted block. After the initial settling samples, 13 readings were
between 275,329 and 277,220 counts relative to tare, with a mean of 275,888
counts. The observed sign is positive for this loading direction.

| Known mass | Equivalent force | Mean change from tare | Preliminary sensitivity |
| --- | ---: | ---: | ---: |
| 57.2 g | 0.561 N | +275,888 counts | 4,823 counts/g (491,830 counts/N) |

This is a valid first direct-cell calibration point. It intentionally bypasses
lead-screw and guide friction; it must be confirmed with a second mass and
later compared against a pen-tip/digital-scale measurement.

### Repeat 57.2 g placement and return-to-zero check

After a new tare of 2,114 counts, the repeat placement settled at a mean
change of +250,159 counts (eight samples, 249,900 to 250,721 counts). This is
about 9% below the first direct-cell result. After the mass was removed, the
last nine samples remained at a mean of +63,742 counts rather than returning
near zero. The mass response remains clear, but the return-to-zero test does
not pass yet.

Treat the final block as a failed mechanical repeatability observation until
confirmed otherwise: it is consistent with residual preload, lead-screw/guide
stiction, or the mass/gray-block touching another structure. It is not evidence
of a HX711 communication or load-cell wiring problem.

### Improved 57.2 g repeat

After re-establishing an unloaded configuration and taring at 79,603 counts,
the pre-load baseline stayed within approximately -700 counts of tare. The
57.2 g placement then settled at a mean of +216,328 counts (nine samples,
215,881 to 216,909 counts). Assuming the final nine readings were taken after
removing the mass, their mean residual was +10,481 counts. This is a substantial
improvement over the prior +63,742-count residual, but it is still about 4.8%
of this trial's loaded response and therefore is not yet a clean return to zero.

The variation between the three 57.2 g placements (+275,888, +250,159, and
+216,328 counts) confirms that the present mechanical state/load placement is
not repeatable enough to commit a final counts-per-force calibration factor.

### Third 57.2 g attempt — direct-gray method rejected for calibration

A subsequent tare at 22,456 counts had a stable initial baseline within about
+200 counts. The same 57.2 g object then settled near +302,388 counts (12
samples, excluding handling transients). The final 11 samples, assumed to be
after removing the object, averaged +74,024 counts rather than returning to
zero. This is worse than the preceding removal result and makes the three
loaded responses span +216,328 to +302,388 counts.

The direct-on-gray weight approach successfully proves that the sensing chain
responds, but the gray-block/actuator mechanics are changing the load path or
retaining preload. Do not derive a force scale from these direct placements.
Use a pen-tip force test against a small digital scale as the next calibration
method; that is the force path the finished machine must actually control.

## Interpretation

The HX711 and load-cell wiring are electrically functional. This attempt does
not yet establish a calibration factor or repeatable zero, so it is not enough
for closed-loop force control.

## Decisions and next action

Stop repeating direct-on-gray weight placements for calibration. The next test
must apply force through the pen tip to a small digital scale on the bed, with
the actuator held at a fixed position. Record the scale force and 10 seconds
of stable HX711 readings at each level, then release to verify return toward
the newly tared baseline. Only after that force path is repeatable should a
calibration factor be finalized. After E-07 establishes a valid raw force
direction and calibration factor, measure sample rate/noise in E-08. Do not
enable closed-loop pen force control until both tests have passing evidence.

### Power/telemetry limitation

The current setup cannot run the local 6 V motor supply, Pro Micro, and USB
Serial Monitor together because USB would introduce a second 5 V source. Do
not bypass this by plugging both ordinary power paths in. A motor-driven,
serial-observed pen-tip calibration is deferred until a USB data-only cable
(VBUS disconnected) or equivalent isolated telemetry method is available.
The HX711 electrical test may continue from USB alone; E-07 remains partial.

### Prepared E-07B pen-tip calibration fixture (not yet run)

The normal Pro Micro USB-C port must remain unplugged while the local 6 V rail
powers the toolhead. E-07B instead uses the project owner's DSD TECH SH-U09C2
USB-to-TTL adapter, set to 3.3 V logic. Its `GND` connects to `TOOL_GND`,
`RXD` connects to GP20 (UART1 TX), and `TXD` connects to GP21 (UART1 RX). The
adapter `VCC`/`3V3`/`5V` pin remains disconnected. This provides PC telemetry
and commands without a second 5 V source.

The prepared firmware is
`firmware/pen_pressure/e07b_hx711_actuator_steps/e07b_hx711_actuator_steps.ino`.
Its commands are `t` (tare), `p` (one on-demand report), `d` (one down step),
`u` (one up step), `[`/`]` (adjust 5-100 ms step duration), and `x`
(stop/sleep). Continuous 500 ms output was removed after UART bring-up because
it made individual readings difficult to inspect; this is intentional and
does not affect HX711 acquisition. The source file is the exact code record
for the upcoming pen-tip test.

The current source also has `a`, a supervised automatic approach. It applies
50 ms down pulses and reads three HX711 samples between pulses. The first
three pulses learn the normal no-contact load-cell change caused by the
lead-screw/mechanism; therefore the pen must begin at least 2 mm clear of the
scale. Subsequent pulses stop on a `50,000`-count departure from that learned
per-pulse change (roughly 10 g in the preceding 57.2 g experiments), on a
driver fault, on an `x` abort, or after 20 pulses (about 10 mm observed
travel). This replaced an unsafe absolute-delta criterion after no-contact
motion produced false positives of -44,838 to -83,133 counts. The 20-pulse
limit is per invocation, not a lockout: if the scale is still not contacted,
`a` may be sent again and it continues from the current pen position using the
original tare. The operator must watch the physical approach and keep the
initial force below 100 g.

### E-07B UART bring-up correction (not yet a force-test result)

The SH-U09C2 adapter loopback test on its assigned PC COM port passed. The
first E-07B upload produced no telemetry and GP20 measured about 160 mV while
GP21 measured 3.3 V. This was a firmware error, not a power or adapter fault:
in Arduino-Pico 6.0.0, `Serial1` is hardware UART0, whereas GP20/GP21 require
hardware UART1, exposed as `Serial2`. The sketch was corrected to use
`Serial2.setTX(20)`, `Serial2.setRX(21)`, and `Serial2.begin(115200)`, then
compiled again. Re-upload the corrected sketch before repeating the UART test.

The corrected sketch was uploaded with the 6 V rail disconnected, then the
Pro Micro USB-C cable was removed and the local 6 V rail was applied. The E-07B
startup telemetry appeared successfully through the SH-U09C2 adapter at 115200
baud. GP20/GP21 service-UART bring-up therefore passes; no pen-tip force
measurement has been recorded yet.

### E-07B first automatic pen-tip contact — 2026-08-14

The initial automatic approach used an absolute 15,000-count threshold and
immediately false-triggered without scale contact: successive no-contact
approach attempts reported deltas of -44,838, -66,590, and -83,133 counts.
This was expected mechanical load transfer during lead-screw motion, not a
sensor/electrical failure. The firmware was changed to learn the first three
no-contact 50 ms pulse deltas and then detect a 50,000-count residual.

With the pen raised at least 2 mm, the scale zeroed, and an unloaded tare of
`37,388` counts, automatic approach reached actual scale contact on pulse 4:

```text
AUTO step=4 hx_delta=-284196 residual=-124308
AUTO contact detected; motor stopped and asleep.
```

The independent scale read **49.4 g** (about 0.485 N). This establishes a
provisional local slope of approximately **-5,753 counts/g**
(`-284,196 / 49.4`), with the negative sign representing the installed load
cell orientation. It is a valid first contact point, not the final calibration:
perform lift-off/return-to-zero and at least two additional gentle force levels
before adopting a production scale factor.

After lifting until the pen was visibly clear and the independent scale had
returned to 0.0 g, the HX711 reported `hx_raw=169290`, `hx_tare=51868`, and
`hx_delta=117422`. Therefore this installed load cell also reports internal
lead-screw/pen-mechanism preload that changes with Z position; it cannot be
assumed to return to an earlier tare merely because the pen is no longer in
scale contact. Subsequent contact runs must tare at their current unloaded
hover position and use the automatic approach's learned per-pulse residual,
not an absolute raw delta, to distinguish contact from normal motion.

### E-07B second automatic pen-tip contact — 2026-08-14

After a new unloaded hover tare of `159,149` counts, the revised automatic
approach produced these learned no-contact and contact values:

```text
AUTO step=1 hx_delta=-147117 (learning)
AUTO step=2 hx_delta=-271054 learned_step_delta=-123937
AUTO step=3 hx_delta=-312104 learned_step_delta=-82493
AUTO step=4 hx_delta=-491201 residual=-96604
AUTO contact detected; motor stopped and asleep.
```

The scale read **65 g**. This independently confirms real pen-tip contact and
the revised residual algorithm's stop behavior. However, it is not consistent
enough with the first 49.4 g / -124,308-residual point to establish a direct
counts-to-grams calibration: approach clearance, Z-position preload, and the
coarse 50 ms (about 0.5 mm) increment materially affect the first-contact
force. E-07 communication, sensor response, and safe contact detection have
passed; force calibration remains partial. A future refinement should use a
coarse approach followed by substantially smaller final approach increments
and collect repeatable force points from the same starting geometry.
