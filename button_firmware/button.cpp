#include "button.h"

Button::Button(int _t, long _interval) {
    t        = _t;
    interval = _interval;
    armed    = 0;
    top1     = 0;
    top2     = 0;

    pinMode(red,   OUTPUT);
    pinMode(green, OUTPUT);
    pinMode(blue,  OUTPUT);
    pinMode(ir,    OUTPUT);
    digitalWrite(red,   LOW);
    digitalWrite(green, LOW);
    digitalWrite(blue,  LOW);
    digitalWrite(ir,    LOW);
    
    pinMode(motor,      OUTPUT);
    pinMode(led1,       OUTPUT);
    pinMode(led2,       OUTPUT);
    pinMode(sensor_pwr, OUTPUT);
    motor_off();
    digitalWrite(led1,       LOW);
    digitalWrite(led2,       LOW);
    digitalWrite(sensor_pwr, LOW);
    
    pinMode(sw1,    INPUT);
    pinMode(sw2,    INPUT);
    pinMode(sensor, INPUT);
    pinMode(ID_01,  INPUT);
    pinMode(ID_02,  INPUT);
    pinMode(ID_04,  INPUT);
    pinMode(ID_08,  INPUT);
    pinMode(ID_16,  INPUT);
    pinMode(ID_32,  INPUT);
}

String Button::readID () {
  // determines the ID of the device from the jumper positions and returns it as a string
  // the format of the ID is a six letter prefix specifying the device type followed by an underscore and a three-digit number, such as 'ABCDEF_000'
  String ret = "BUTTON_";
  
  int n =  0;
  n = n +  1 * digitalRead(ID_01);
  n = n +  2 * digitalRead(ID_02);
  n = n +  4 * digitalRead(ID_04);
  n = n +  8 * digitalRead(ID_08);
  n = n + 16 * digitalRead(ID_16);
  n = n + 32 * digitalRead(ID_32);

  if(n<100) ret += "0";
  if(n<10 ) ret += "0";
  ret += n;
  return(ret);
}

void Button::signal_startup_complete () {
  //signal to human using led lights
  digitalWrite(led1, HIGH);
  digitalWrite(led2, HIGH);
  delay(100);
  digitalWrite(led1, LOW);
  digitalWrite(led2, LOW);
  delay(100);
  digitalWrite(led1, HIGH);
  digitalWrite(led2, HIGH);
  delay(100);
  digitalWrite(led1, LOW);
  digitalWrite(led2, LOW);
  
  //signal to master using Serial
  Serial.println("OK");
}

void Button::arm (int _red_val, int _green_val, int _blue_val) {
  analogWrite(red,   _red_val);
  analogWrite(green, _green_val);
  analogWrite(blue,  _blue_val);
  digitalWrite(ir, HIGH);
  digitalWrite(sensor_pwr, HIGH);
  armed = 1;
  delay(100);
  int temp = analogRead(sensor);
  previousMillis = millis();
  top1 = 0;
  top2 = 0;
  for(int i = 0; i < buf1_size; i++) {
    buf1[i] = temp;
  }
  for(int i = 0; i < buf2_size; i++) {
    buf2[i] = temp;
  }
}

void Button::disarm () {
  digitalWrite(red,   LOW);
  digitalWrite(green, LOW);
  digitalWrite(blue,  LOW);
  digitalWrite(ir,    LOW);
  digitalWrite(sensor_pwr, LOW);
  armed = 0;
  delay(100);
}

float Button::mean_buf1() {
  float sum_buf = 0;

  // cycle through the buffer, starting at top +1 until end, then continuing from start to top
  for(int i=top1, k=0; k<buf1_size; i++, k++) {
    if(i >= buf1_size) i = 0;
    sum_buf += buf1[i];
  }
  float m = sum_buf / float(buf1_size);
  return m;
}

float Button::mean_buf2() {
  float sum_buf = 0;

  // cycle through the buffer, starting at top +1 until end, then continuing from start to top
  for(int i=top2, k=0; k<buf2_size; i++, k++) {
    if(i >= buf2_size) i = 0;
    sum_buf += buf2[i];
  }
  float m = sum_buf / float(buf2_size);
  return m;
}

bool Button::triggered() {
  // interval: the time between two frames, in milliseconds
   if(!armed) return 0;
   currentMillis = millis();
   if (currentMillis - previousMillis >= interval) {
    // if interval milliseconds have passed, write the new sensor value to the top of the buffer
     previousMillis = currentMillis;
     buf1[top1] = analogRead(sensor);
     buf2[top2] = buf1[top1];
     top1 ++;
     top2 ++;
     if(top1 >= buf1_size) top1 = 0;
     if(top2 >= buf2_size) top2 = 0;
     
     //determine mean value of both buffers
     int buf1_mean = mean_buf1();
     int buf2_mean = mean_buf2();
     if(abs(buf1_mean - buf2_mean) > t) {
       disarm();
       return 1;
     } else {
       return 0;
     }
   } else {
     return 0;
   }
}

void Button::read_sensor(int _seconds, int _framerate, int _red_val, int _green_val, int _blue_val) {
  // _seconds:    number of seconds to read
  // _framerate:  number of frames to read each second
  // nframes:     the total number of frames to read
  // n_millis:    the total number of milliseconds this will take
  // framelength: the interval between two frames (should not be called interval, since this is already a parameter of button
  // current_t:   the current time in milliseconds
  // previous_t:  the previous time (last time measured) in milliseconds
  
  unsigned long framelength = 1000/_framerate;
  int nframes               = _seconds*_framerate;
  unsigned long n_millis    = _seconds*1000;
  unsigned long current_t   = millis();
  unsigned long previous_t  = millis();
  int values[nframes];
  
  arm(_red_val, _green_val, _blue_val);
  for (int count = 0; count <= nframes; current_t = millis()) {
    if (current_t >= (previous_t + count * framelength) ) {
      values[count] = analogRead(sensor);
      count ++;
    }
  }
  Serial.println("OK");
  for (int i = 0; i<nframes; i++) {
    Serial.println(values[i]);
  }
  disarm();
}

bool Button::sw1_pressed () {
 if(digitalRead(sw1) == LOW) return true;
 else return false;
}

bool Button::sw2_pressed () {
 if(digitalRead(sw2) == LOW) return true;
 else return false;
}

void Button::sw1_routine () {
  delay(10);
  if(digitalRead(sw1) == HIGH) return;
  digitalWrite(led1, HIGH);
  arm(0,0,0);
  int m = mean_buf1();
  while(digitalRead(sw1) == LOW) {
    int s = analogRead(sensor);
    s = constrain(s,0,m);
    s = map(s,0,m,255,0);
    analogWrite(red, s);
    analogWrite(green, s);
    analogWrite(blue, s);
  }
  digitalWrite(led1, LOW);
  disarm();
}

void Button::sw2_routine () {
  delay(10);
  if(digitalRead(sw2) == HIGH) return;
  digitalWrite(led2, HIGH);
  delay(100);
  digitalWrite(led2, LOW);
  motor_on();
  while(digitalRead(sw2) == LOW) {
    
  }
  motor_off();
  delay(10);
}

void Button::set_threshold (int _t) {
  t = _t;
}

void Button::klick(int kt) {
  motor_on();
  delay (kt);
  motor_off();
  delay(10);
}

void Button::klick(int kt, int s) {
  s = map(s,0,100,255,0);
  analogWrite(motor, s);
  delay (kt);
  motor_off();
  delay(10);
}

void Button::motor_off() {
  digitalWrite(motor, HIGH);
}

void Button::motor_on() {
  digitalWrite(motor, LOW);
}

