#include "feeder.h"

#include <stdint.h>
#define ser_conf        SERIAL_8N1


#define COMMAND_IN_FEED      "f" //should be only one character. of you want to change it, change also the length of the substring to exrtact (search for "COMMAND_IN_READ" to see where.


const int baud           = 9600;

String readString, command, parameters;


Feeder* f;

String getValue(String data, char separator, int index) {
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

void setup() {
  Serial.begin(baud, ser_conf);
  delay(200);
  
  f = new Feeder();
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
      Serial.println(f -> readID());
     } else {
       command    = readString.substring(0, 1);
       parameters = readString.substring(1, 15);
         
       if(command == COMMAND_IN_FEED) {
        int t = getValue(parameters, ',', 0).toInt();
        if(getValue(parameters, ',', 1) == "") {
          f -> feed(t);
        } else {
          int s = getValue(parameters, ',', 1).toInt();
          f -> feed(t, s);
        }
        Serial.println("OK");
        Serial.println(f -> duration_until_fed);
        Serial.println(f -> grains);
        Serial.println("OK");
       }
     }
   readString="";
 }
 if(f -> sw_pressed()) {
  f -> sw_routine();
 }
}


