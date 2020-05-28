#ifndef BUTTON_H
#define BUTTON_H

#if defined(ARDUINO) && ARDUINO >= 100
#include <Arduino.h>
#else
#include <WProgram.h>
#endif

#define red        10
#define green      11
#define blue        9
#define ir          6
#define motor       5
#define sensor     A0
#define sensor_pwr A5
#define sw1        A2
#define sw2        A4
#define led1       A1
#define led2       A3
#define ID_01      12
#define ID_02       8
#define ID_04       7
#define ID_08       4
#define ID_16       3
#define ID_32       2


#define buf1_size  100
#define buf2_size   10

#define motor_on_pwm 255*2/5


class Button {
public:
  Button(int  _t         = 15,
         long _interval  = 1);

  String readID ();
  void   signal_startup_complete ();
  void   arm (int _red_val   = 0,
              int _green_val = 255,
              int _blue_val  = 0);
  void   disarm();
  bool   triggered();
  void   read_sensor(int _seconds   = 1,
                     int _framerate = 10,
                     int _red_val   = 0,
                     int _green_val = 255,
                     int _blue_val  = 0);
  float  mean_buf1();
  float  mean_buf2();
  bool   sw1_pressed();
  bool   sw2_pressed();
  void   sw1_routine();
  void   sw2_routine();
  void   set_threshold (int _t);
  
  void klick(int kt);
  void klick(int kt, int s);
  void double_sweep(int low, int high, int rate, bool start_low);
  void sweep(int low, int high, int rate, bool start_low);
  void burst(int n, int d1, int d2);
  void klick_1();
  void klick_2();
  void klick_3();
  void klick_4();
  void motor_on();
  void motor_off();
  
private:  
  int  t;
  long interval;
  int  buf1[buf1_size];
  int  buf2[buf2_size];
  int  top1;
  int  top2;
  unsigned long currentMillis;
  unsigned long previousMillis;
  
  bool armed;
};

#endif
