#include <SoftwareSerial.h>

int BT_TX=3;
int BT_RX=2;
SoftwareSerial b_rciv(BT_RX, BT_TX);
unsigned long timestamp; 

void setup(){
  Serial.begin(9600);
  b_rciv.begin(9600);
//  b_rciv.println("ATcommand");
}

void loop(){

//  if (millis() - timestamp > 500){
    b_rciv.println("AT-DISI?");
    Serial.write(b_rciv.read());
//    timestamp = millis();
//  }
//
//  if(b_rciv.available()){
//    Serial.write(b_rciv.read());
//  }
//
//  if(Serial.available()){
//    b_rciv.write(Serial.read());
//  }
}
