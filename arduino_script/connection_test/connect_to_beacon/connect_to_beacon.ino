#include <SoftwareSerial.h>
#define BT_RX 2
#define BT_TX 3

//SoftwareSerial hm10(2,3); //RX, TX 연결
//SoftwareSerial BTSerial(7,8);
//SoftwareSerial b2(7,8);
SoftwareSerial b1(BT_RX, BT_TX);
unsigned long timestamp;

//char text;
//char list[80];
//int index=0;
//int cnt=0;

void setup() {
  Serial.begin(9600);
  b1.begin(9600);
}
 
void loop() {

  if(millis() - timestamp > 5000){
    b1.println("AT-DISI?");
    Serial.write(b1.read());
    timestamp = millis();
  }
  
  while(b1.available()){
    Serial.write(b1.read());
  }

  while(Serial.available()){
    b1.write(Serial.read());

  }
}
