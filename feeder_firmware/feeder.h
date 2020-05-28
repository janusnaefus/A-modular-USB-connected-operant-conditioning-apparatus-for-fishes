#ifndef BUTTON_H
#define BUTTON_H



#if defined(ARDUINO) && ARDUINO >= 100
#include <Arduino.h>
#else
#include <WProgram.h>
#endif

#include <SPI.h>

#define SPI_MAX_SPEED   1000000

// pins
#define cs_poti           A0
#define vibrator           5
#define ir_led             2
#define ir_sensor_in      A6
#define ir_sensor_out     A5

#define motorPin1         A1
#define motorPin2         A2
#define motorPin3         A3
#define motorPin4         A4
         
#define led                3
#define sw                 4

#define ID_01              6
#define ID_02              7
#define ID_04              8
#define ID_08              9
#define ID_16             A7
#define ID_32             12

//

#define buf_size          20
#define interval           1
#define WRITE_4141 B00000000

#define motor_distance    35
#define motor_speed     1500

const float threshold = 0.5;

class Feeder {
public:
  Feeder();

  String readID ();
  void   signal_startup_complete ();
  void   arm ();
  void   disarm();
  void   count_grains();
  void   read_sensor(int _seconds   = 1,
                     int _framerate = 10);
  bool   sw_pressed();
  void   sw_routine();
  void   set_vibrator_speed (int _s);
  void   start_vibrator();
  void   stop_vibrator();
  void   feed(int _n, int _s = 0);
  void   open_gate();
  void   close_gate();
  void   motor_off();
  void   turn(int _n, int _d);
  float  slope();

  // the following two are public, such that the function calling feed() can retrieve the amount fed and the duration that this took
  unsigned long duration_until_fed;
  int  grains;
  
private:  
  bool b, old_b;  
  int  buf[buf_size];
  int  top; // the top of the buffer - where to insert values
  bool grain_passing;
  unsigned long currentMillis;
  unsigned long previousMillis;
};

#endif
