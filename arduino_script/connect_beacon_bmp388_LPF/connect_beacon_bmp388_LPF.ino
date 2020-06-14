#include <SoftwareSerial.h>
#include "DFRobot_BMP388_I2C.h"
#include "DFRobot_BMP388.h"
#include "Wire.h"
#include "SPI.h"
#include "bmp3_defs.h"

#define BT_RX 2
#define BT_TX 3

static long analogPinTimer = 0; 
// Set the sampling time
#define ANALOG_PIN_TIMER_INTERVAL 2 // milliseconds
unsigned long thisMillis_old;

DFRobot_BMP388_I2C bmp388;

SoftwareSerial b1(BT_RX, BT_TX);
unsigned long timestamp;

int fc = 5; // cutoff frequency 5~10 Hz 정도 사용해보시기 바랍니다
double dt = ANALOG_PIN_TIMER_INTERVAL/1000.0; // sampling time
double lambda = 2*PI*fc*dt;
double x = 0.0;
double x_f = 0.0;
double x_fold = 0.0;

void setup() {
  Serial.begin(9600);
  b1.begin(9600);

  bmp388.set_iic_addr(BMP3_I2C_ADDR_SEC);

  while(bmp388.begin()){
  Serial.println("Initialize error!");
  delay(1000);
}
}
 
void loop() {
  
 unsigned long deltaMillis = 0; // clear last result
 unsigned long thisMillis = millis();  
 if (thisMillis != thisMillis_old) { 
  deltaMillis = thisMillis-thisMillis_old; 
  thisMillis_old = thisMillis;   
 } 

analogPinTimer -= deltaMillis; 

  if(millis() - timestamp > 5000){
    b1.println("AT-DISI?");
    Serial.write(b1.read());
     
     if (analogPinTimer <= 0) {  
     analogPinTimer += ANALOG_PIN_TIMER_INTERVAL; 
     // sensing loop start!! 
     float Pressure = bmp388.readPressure();
  
     x = Pressure; // 아날로그값 읽기
     x_fold = x_f; // 센서 필터 이전값 업데이트
     x_f = lambda/(1+lambda)*x+1/(1+lambda)*x_fold; //필터된 값
     

  Serial.print("LPF_DATA : ");  
  Serial.println(x_f);
 }
      
    timestamp = millis();
  }
  while(b1.available()){
    Serial.write(b1.read());
  }

  while(Serial.available()){
    b1.write(Serial.read());

  }
}
