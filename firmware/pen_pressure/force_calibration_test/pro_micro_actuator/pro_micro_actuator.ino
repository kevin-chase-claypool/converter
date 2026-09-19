/* SparkFun Pro Micro RP2350 force-calibration fixture (Arduino-Pico core).
   GP0 -> Pico GP15 and TOOL_GND -> Pico GND. GP0 HIGH is safe/stop.
   UART1 commands: STATUS, STOP, RUN DOWN|UP pulse_ms settle_ms. */
#include <Arduino.h>
#include <strings.h>

constexpr uint8_t PIN_GATE=0, PIN_IN1=4, PIN_IN2=5, PIN_SLEEP=6, PIN_FAULT=7, PIN_TX=20, PIN_RX=21;
constexpr uint16_t MIN_PULSE=10, MAX_PULSE=100, MAX_SETTLE=10000, LEAD_MS=100;
constexpr bool LOWER_IN1_HIGH=true, LIFT_IN1_HIGH=false;
char line[80]; uint8_t length=0;
bool fault() { return digitalRead(PIN_FAULT)==LOW; }
void safeStop(){ digitalWrite(PIN_IN1,LOW); digitalWrite(PIN_IN2,LOW); digitalWrite(PIN_SLEEP,LOW); digitalWrite(PIN_GATE,HIGH); }
void status(){ Serial2.print(F("STATUS,daq_gate=")); Serial2.print(digitalRead(PIN_GATE)?F("off"):F("on")); Serial2.print(F(",driver_fault=")); Serial2.println(fault()?1:0); }
bool number(const char* s,uint16_t &v){ char* e; unsigned long n=strtoul(s,&e,10); if(!s||!*s||*e||n>65535) return false; v=n; return true; }
void run(bool lower,uint16_t pulse,uint16_t settle){
  if(pulse<MIN_PULSE||pulse>MAX_PULSE||settle>MAX_SETTLE){Serial2.println(F("RUN_REJECTED,reason=bounds"));safeStop();return;}
  if(fault()){Serial2.println(F("RUN_REJECTED,reason=driver_fault"));safeStop();return;}
  digitalWrite(PIN_GATE,LOW); Serial2.print(F("RUN_START,direction="));Serial2.print(lower?F("DOWN"):F("UP"));Serial2.print(F(",pulse_ms="));Serial2.print(pulse);Serial2.print(F(",settle_ms="));Serial2.println(settle); delay(LEAD_MS);
  if(fault()){Serial2.println(F("RUN_ABORTED,reason=driver_fault_before_enable"));safeStop();return;}
  bool high=lower?LOWER_IN1_HIGH:LIFT_IN1_HIGH; digitalWrite(PIN_SLEEP,HIGH);delay(5); digitalWrite(PIN_IN1,high);digitalWrite(PIN_IN2,!high);delay(pulse); bool during=fault(); digitalWrite(PIN_IN1,LOW);digitalWrite(PIN_IN2,LOW);digitalWrite(PIN_SLEEP,LOW);delay(settle);digitalWrite(PIN_GATE,HIGH);Serial2.print(F("RUN_COMPLETE,fault_during_pulse="));Serial2.println(during?1:0);
}
void command(char* text){
  char* v=strtok(text," "); if(!v)return;
  if(!strcasecmp(v,"STATUS")){status();return;} if(!strcasecmp(v,"STOP")){safeStop();Serial2.println(F("STOPPED,driver_asleep=1,daq_gate=off"));return;}
  if(!strcasecmp(v,"CAPTURE")){char* m=strtok(nullptr," "); uint16_t ms; if(!m||strtok(nullptr," ")||!number(m,ms)||ms<100||ms>10000){Serial2.println(F("CAPTURE_REJECTED,usage=CAPTURE 100..10000"));safeStop();return;} digitalWrite(PIN_GATE,LOW);Serial2.println(F("CAPTURE_START"));delay(ms);digitalWrite(PIN_GATE,HIGH);Serial2.println(F("CAPTURE_COMPLETE"));return;}
  if(strcasecmp(v,"RUN")){Serial2.println(F("COMMAND_ERROR,expected=STATUS|RUN|STOP"));return;}
  char *d=strtok(nullptr," "),*p=strtok(nullptr," "),*s=strtok(nullptr," "); uint16_t pulse,settle;
  if(!d||!p||!s||strtok(nullptr," ")||!number(p,pulse)||!number(s,settle)){Serial2.println(F("RUN_REJECTED,usage=RUN DOWN|UP pulse_ms settle_ms"));safeStop();return;}
  if(!strcasecmp(d,"DOWN"))run(true,pulse,settle); else if(!strcasecmp(d,"UP"))run(false,pulse,settle); else {Serial2.println(F("RUN_REJECTED,reason=direction"));safeStop();}
}
void setup(){Serial2.setTX(PIN_TX);Serial2.setRX(PIN_RX);Serial2.begin(115200);pinMode(PIN_GATE,OUTPUT);pinMode(PIN_IN1,OUTPUT);pinMode(PIN_IN2,OUTPUT);pinMode(PIN_SLEEP,OUTPUT);pinMode(PIN_FAULT,INPUT_PULLUP);safeStop();Serial2.println(F("READY,pro_micro_actuator,gate=GP0_to_Pico_GP15"));status();}
void loop(){while(Serial2.available()){char c=Serial2.read();if(c=='\r')continue;if(c=='\n'){line[length]=0;command(line);length=0;}else if(length+1<sizeof(line))line[length++]=c;else{length=0;safeStop();Serial2.println(F("COMMAND_ERROR,reason=line_too_long"));}}}
