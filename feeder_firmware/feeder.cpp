#include "feeder.h"

Feeder::Feeder() {

    SPI.begin();
    pinMode(cs_poti,       OUTPUT);
    pinMode(vibrator,      OUTPUT);
    pinMode(ir_led,        OUTPUT );
    pinMode(ir_sensor_out, OUTPUT );
    pinMode(ir_sensor_in,  INPUT );
    
    pinMode(motorPin1, OUTPUT);
    pinMode(motorPin2, OUTPUT);
    pinMode(motorPin3, OUTPUT);
    pinMode(motorPin4, OUTPUT);
    pinMode(led,       OUTPUT);
    pinMode(sw,        INPUT);
    
    digitalWrite(cs_poti,   HIGH);
    digitalWrite(led,       LOW);

    pinMode(ID_01,     INPUT);
    pinMode(ID_02,     INPUT);
    pinMode(ID_04,     INPUT);
    pinMode(ID_08,     INPUT);
    pinMode(ID_16,     INPUT);
    pinMode(ID_32,     INPUT);

  
    motor_off();
    stop_vibrator();
    disarm();
   
    b             = digitalRead(sw);
    old_b         = b;
    grains        = 0;
    grain_passing = false;

    signal_startup_complete();
}

String Feeder::readID () {
  // determines the ID of the device from the jumper positions and returns it as a string
  // the format of the ID is a six letter prefix specifying the device type followed by an underscore and a three-digit number, such as 'ABCDEF_000'
  String ret = "FEEDER_";
  
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

void Feeder::signal_startup_complete () {
  //signal to human using led lights
  digitalWrite(led, HIGH);
  delay(100);
  digitalWrite(led, LOW);
  delay(100);
  digitalWrite(led, HIGH);
  delay(100);
  digitalWrite(led, LOW);
  
  //signal to master using Serial
  Serial.println("OK");
}

void Feeder::arm () {
  digitalWrite(ir_led,        HIGH);
  digitalWrite(ir_sensor_out, HIGH);
  delay(100);
  int temp = analogRead(ir_sensor_in);
  previousMillis = millis();
  top = 0;
  for(int i = 0; i < buf_size; i++) {
    buf[i] = temp;
  }
  grains        = 0;
  grain_passing = false;
}

void Feeder::disarm () {
  digitalWrite(ir_led,        LOW);
  digitalWrite(ir_sensor_out, LOW);
  delay(100);
}

float Feeder::slope() {
  int  s  = buf_size;
  int  x  = 0;
  int  y  = 0;
  float x2 = 0;
  float xy = 0;
  float sx = 0;
  float sy = 0;

  // cycle through the buffer, starting at top +1 until end, then continuing from start to top
  for(int i=top, k=0; k<buf_size; i++, k++) {
    if(i >= buf_size) i = 0;
    x  = k;
    y  = buf[i];
    x2 = x2 + x * x;
    xy = xy + x * y;
    sx = sx + x;
    sy = sy + y;
  }
  float a = (s*xy - sx*sy)/(s*x2 - sx*sx);
  return a;
}

void Feeder::count_grains () {
  currentMillis = millis();
   if (currentMillis - previousMillis >= interval) {
    // if interval milliseconds have passed, write the new sensor value to the top of the buffer
     previousMillis = currentMillis;
     buf[top] = analogRead(ir_sensor_in);
     top ++;
     if(top >= buf_size) top = 0;

     // determine the slope of the buffer
     float a = slope();
     // if no grain is currently passing the sensor and the sensor detects a positive enough slope,
     // count a grain and state that one is currently passing the sensor
     // otherwise, if the sensor detects a negative enough slope, state that the grain has passed.
     if(grain_passing == false) {
      if(a > threshold) {
        grains = grains + 1;
        grain_passing = true;
      }
     } else {
      if(a < -threshold) {
        grain_passing = false;
      }
     }
   }
}

void Feeder::read_sensor(int _seconds, int _framerate) {
  int nframes            = _seconds*_framerate;
  unsigned long n_millis = _seconds*1000;
  int values[nframes];
  
  arm();
  int count = 0;
  for (unsigned long t = millis(); (millis() - t) <= n_millis;) {
    values[count] = analogRead(ir_sensor_in);
    count ++;
    delay(1000/_framerate);
  }
  Serial.println("OK");
  for (int i = 0; i<count; i++) {
    Serial.println(values[i]);
  }
  disarm();
}

bool Feeder::sw_pressed () {
 if(digitalRead(sw) == LOW) return true;
 else return false;
}

void Feeder::sw_routine () {
  delay(10);
  if(digitalRead(sw) == HIGH) return;
  digitalWrite(led, HIGH);
  delay(100);
  digitalWrite(led, LOW);
  feed(1);
}

void Feeder::set_vibrator_speed(int _s) {
  int s = map(_s,0,100,100,127);
  SPI.beginTransaction(SPISettings(SPI_MAX_SPEED, MSBFIRST, SPI_MODE0));
  digitalWrite(cs_poti, LOW);
  SPI.transfer(WRITE_4141);
  SPI.transfer(s);
  digitalWrite(cs_poti, HIGH);
  SPI.endTransaction();
}

void Feeder::start_vibrator() {
  digitalWrite(vibrator, LOW);
}

void Feeder::stop_vibrator() {
  digitalWrite(vibrator, HIGH);
}

void Feeder::feed(int _n, int _s) {

  int feeder_speed = _s;

  unsigned long start_millis_const    = millis();
  unsigned long start_millis          = millis();
  unsigned long current_millis        = millis();
  unsigned long last_speed_increase   = millis();
  
  unsigned long increase_speed_delay  =  3000;
  int           increase_speed_amount =     1;
  unsigned long stop_feeder_delay     = 15000;

  int           old_grains            = 0;
  
  open_gate();
  set_vibrator_speed(90);
  start_vibrator();
  delay(20);
  set_vibrator_speed(feeder_speed);
  arm();
  
  while(grains < _n) {
    count_grains();
    // if a grain has been counted, stop speed increasing by pretending it has already been increased, and stop the end_time counting by resetting the start_millis. also, reset the speed to the beginning.
    if(grains > old_grains) {
      old_grains = grains;
      last_speed_increase = millis();
      start_millis = millis();
      feeder_speed = _s;
      set_vibrator_speed(feeder_speed);
    }
    // if stop_feeder_delay milliseconds have passed since the last grain, something is probably wrong with the feeder. stop (in the future, also send some error message on the serial port).
    if((millis() - start_millis) > stop_feeder_delay) {
      break;
    }
    // if increase_speed_delay milliseconds have passed since the last speed increase or since a grain was last observed, increase the speed.
    if((millis() - last_speed_increase) > increase_speed_delay) {
      feeder_speed = 80;
      last_speed_increase = millis();
      set_vibrator_speed(feeder_speed);
      delay(100);
      set_vibrator_speed(_s);
//      feeder_speed += increase_speed_amount;
//      if(feeder_speed > 100) feeder_speed = 100;
//      last_speed_increase = millis();
//      set_vibrator_speed(feeder_speed);
    }
  }

  duration_until_fed = millis() - start_millis_const;
  
  stop_vibrator();
  disarm();
  close_gate();
}

//void Feeder::feed(int _n, int _s) {
//  open_gate();
//  set_vibrator_speed(_s);
//  start_vibrator();
//  arm();
//  
//  while(grains < _n) {
//    count_grains();
//  }
//
//  stop_vibrator();
//  disarm();
//  close_gate();
//}

void Feeder::open_gate() {
  turn(5,3000); 
  turn(motor_distance,motor_speed);
}

void Feeder::close_gate() {
  delay(500);
  turn(-motor_distance,motor_speed);
  turn(-6,3000); 
}

void Feeder::motor_off () {
  digitalWrite(motorPin4, LOW);
  digitalWrite(motorPin3, LOW);
  digitalWrite(motorPin2, LOW);
  digitalWrite(motorPin1, LOW);
}

void Feeder::turn(int _n, int _d) {
  if(_n<0) {
    _n = -_n; 
    for(int i=0; i<_n; i++) {
      digitalWrite(motorPin1, HIGH);
      delayMicroseconds(_d);
      digitalWrite(motorPin4, LOW);
      delayMicroseconds(_d);
      digitalWrite(motorPin2, HIGH);
      delayMicroseconds(_d);
      digitalWrite(motorPin1, LOW);
      delayMicroseconds(_d);
      digitalWrite(motorPin3, HIGH);
      delayMicroseconds(_d);
      digitalWrite(motorPin2, LOW);
      delayMicroseconds(_d);
      digitalWrite(motorPin4, HIGH);
      delayMicroseconds(_d);
      digitalWrite(motorPin3, LOW);
      delayMicroseconds(_d);
    }
  } else {
    for(int i=0; i<_n; i++) {
      digitalWrite(motorPin4, HIGH);
      delayMicroseconds(_d);
      digitalWrite(motorPin1, LOW);
      delayMicroseconds(_d);
      digitalWrite(motorPin3, HIGH);
      delayMicroseconds(_d);
      digitalWrite(motorPin4, LOW);
      delayMicroseconds(_d);
      digitalWrite(motorPin2, HIGH);
      delayMicroseconds(_d);
      digitalWrite(motorPin3, LOW);
      delayMicroseconds(_d);
      digitalWrite(motorPin1, HIGH);
      delayMicroseconds(_d);
      digitalWrite(motorPin2, LOW);
      delayMicroseconds(_d);
    }
  }
  motor_off();
}
