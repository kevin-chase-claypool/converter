/* Pico 2 force-calibration DAQ: Arduino-Pico core, target Raspberry Pi Pico 2.
   GP2 -> CS1238 SCK, GP3 <- CS1238 DT/DRDY, GP26 <- INA101 OUT, GP15 <- Pro Micro GP0.
   GP15 LOW starts raw capture; HIGH stops. No filtering, tare, or motor control. */
#include <Arduino.h>
#include <CS123x.h>

constexpr uint8_t PIN_CS_SCK = 2, PIN_CS_DOUT = 3, PIN_REFERENCE_ADC = 26, PIN_DAQ_GATE = 15;
CS123x toolhead(CS123X_TYPE_CS1238, PIN_CS_DOUT, PIN_CS_SCK,
                CS123X_CH_A, CS123X_GAIN_128, CS123X_RATE_640Hz, CS123X_INT_REF_OFF);
bool capture = false;
bool previous_gate = false;
uint64_t origin_us = 0, samples = 0;
char command[16]; uint8_t command_length = 0;

void startCapture() {
  if (capture) return;
  origin_us = micros(); samples = 0; capture = true;
  Serial.print(F("TEST_START,source=gp0_gate,monotonic_origin_us=")); Serial.println(origin_us);
  Serial.println(F("SAMPLES_HEADER,toolhead_time_us,toolhead_cs1238_raw,reference_time_us,reference_adc_raw"));
}
void stopCapture(const __FlashStringHelper *reason) {
  if (!capture) return;
  capture = false;
  Serial.print(F("TEST_STOP,reason=")); Serial.print(reason);
  Serial.print(F(",samples=")); Serial.println(samples);
}
void setup() {
  Serial.begin(115200);
  pinMode(PIN_DAQ_GATE, INPUT_PULLUP);
  analogReadResolution(12);
  if (!toolhead.begin() || !toolhead.setConfig(CS123X_CH_A, CS123X_GAIN_128, CS123X_RATE_640Hz, true)) {
    Serial.println(F("READY,pico2_daq,cs1238_config=failed,rate_sps=640"));
    return;
  }
  Serial.println(F("READY,pico2_daq,cs1238_config=ok,rate_sps=640"));
}
void loop() {
  while (Serial.available()) { char c=Serial.read(); if(c=='\r') continue; if(c=='\n'){ command[command_length]=0; if(!strcmp(command,"STATUS")){Serial.print(F("STATUS,configured=1,capture="));Serial.print(capture?1:0);Serial.print(F(",gate="));Serial.println(digitalRead(PIN_DAQ_GATE)==LOW?1:0);} command_length=0;} else if(command_length+1<sizeof(command)) command[command_length++]=c; else command_length=0; }
  const bool gate_on = digitalRead(PIN_DAQ_GATE) == LOW;
  if (gate_on && !previous_gate) startCapture();
  if (!gate_on && previous_gate) stopCapture(F("daq_gate_off"));
  previous_gate = gate_on;
  if (!capture) return;
  const long raw = toolhead.read();
  if (raw == CS123X_TIMEOUT_ERROR) { stopCapture(F("cs1238_timeout")); return; }
  const uint64_t cs_time = micros() - origin_us;
  const int reference_raw = analogRead(PIN_REFERENCE_ADC);
  const uint64_t reference_time = micros() - origin_us;
  Serial.print(F("SAMPLE,")); Serial.print(cs_time); Serial.print(','); Serial.print(raw);
  Serial.print(','); Serial.print(reference_time); Serial.print(','); Serial.println(reference_raw);
  ++samples;
}
