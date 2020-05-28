
#include <stdint.h>
#include "button.h"

#define COMMAND_OUT_TRIGGERED    "TRIGGERED"

#define COMMAND_IN_GET_ID        "i"
#define COMMAND_IN_ARM           "a"
#define COMMAND_IN_DISARM        "d"
#define COMMAND_IN_KLICK         "k"
#define COMMAND_IN_READ          "r"
#define COMMAND_IN_SET_THRESHOLD "t"


String readString, command, parameters;

String getValue(String data, char separator, int index)
{
    int found = 0;
    int strIndex[] = { 0, -1 };
    int maxIndex = data.length() - 1;

    for (int i = 0; i <= maxIndex && found <= index; i++) {
        if (data.charAt(i) == separator || i == maxIndex) {
            found++;
            strIndex[0] = strIndex[1] + 1;
            strIndex[1] = (i == maxIndex) ? i+1 : i;
        }
    }
    return found > index ? data.substring(strIndex[0], strIndex[1]) : "";
}

Button* b = new Button();


void triggered () {
  Serial.println(COMMAND_OUT_TRIGGERED);
}

void setup() {
  Serial.begin(9600);
  b -> signal_startup_complete();
}

void loop() {
  
  while (Serial.available()) {
    delay(10);  
    if (Serial.available() >0) {
      char c = Serial.read();  //gets one byte from serial buffer
      readString += c; //makes the string readString
    }
  }

 if (readString.length() >0) {
     if(readString == "ID") {
      Serial.println("OK");
      Serial.println(b -> readID());
     } else {     
         command    = readString.substring(0, 1);
         parameters = readString.substring(1, -1);
    
         if(command == COMMAND_IN_ARM) {
           int  red_val   = getValue(parameters, ',', 0).toInt();
           int  green_val = getValue(parameters, ',', 1).toInt();
           int  blue_val  = getValue(parameters, ',', 2).toInt();
           if(red_val == 0 && green_val == 0 && blue_val == 0) b -> arm();
           else                                                b -> arm(red_val, green_val, blue_val);
           Serial.println("OK");
         }
    
         if(command == COMMAND_IN_DISARM) {
           b -> disarm();
           Serial.println("OK");
         }
    
         if(command == COMMAND_IN_SET_THRESHOLD) {
           int n = getValue(parameters, ',', 0).toInt();
           b -> set_threshold(n);
           Serial.println("OK");
         }
    
         if(command == COMMAND_IN_READ) {
           int n = getValue(parameters, ',', 0).toInt();
           int f = getValue(parameters, ',', 1).toInt();
           if(f == 0) b -> read_sensor(n);
           else       b -> read_sensor(n,f);
           Serial.println("OK");
         }
         
         if(command == COMMAND_IN_KLICK) {
          int kt_i = 0; // index of klicking time
          int s_i  = 1; // index of speed
          int kt, s;
          while(1) {
            if(getValue(parameters, ',', kt_i) != "") kt = getValue(parameters, ',', kt_i).toInt(); else break;
            if(getValue(parameters, ',', s_i)  != "") {
              s  = getValue(parameters, ',', s_i).toInt();
              b -> klick(kt, s);
            } else {
              b -> klick(kt);
            }
            
            kt_i += 2;
            s_i  += 2;
          }
          Serial.println("OK");
         }
         
//         if(command == COMMAND_IN_KLICK) {
//          int t = getValue(parameters, ',', 0).toInt();
//          if(t == 1) b -> klick_1();
//          if(t == 2) b -> klick_2();
//          if(t == 3) b -> klick_3();
//          if(t == 4) b -> klick_4();
//          
//          if(t > 10) b -> klick(t);
//          Serial.println("OK");
//         }
     }
   readString="";
 }

 if (b -> triggered())   triggered();
 if (b -> sw1_pressed()) b -> sw1_routine();
 if (b -> sw2_pressed()) b -> sw2_routine();

}
