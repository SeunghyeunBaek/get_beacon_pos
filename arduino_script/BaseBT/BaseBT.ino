#include "DFRobot_BMP388_I2C.h"
#include "DFRobot_BMP388.h"
#include "Wire.h"
#include "SPI.h"
#include "bmp3_defs.h"
#include <SoftwareSerial.h>

static long analogPinTimer = 0; 
// Set the sampling time
#define ANALOG_PIN_TIMER_INTERVAL 2 // milliseconds
unsigned long thisMillis_old;

/* Create a bmp388 object to communicate with IIC.*/
DFRobot_BMP388_I2C bmp388;
SoftwareSerial BTSerial(2,3);

unsigned long timestamp;

int fc = 5; // cutoff frequency 5~10 Hz 정도 사용해보시기 바랍니다
double dt = ANALOG_PIN_TIMER_INTERVAL/1000.0; // sampling time
double lambda = 2*PI*fc*dt;
double x = 0.0;
double x_f = 0.0;
double x_fold = 0.0;

void setup(){
  /*Initialize the serial port*/
  Serial.begin(9600);
  BTSerial.begin(9600);

  /* 
   * @brief Set bmp388 IIC address
   * @param BMP3_I2C_ADDR_PRIM: pin SDO is low
   *        BMP3_I2C_ADDR_SEC: pin SDO is high
   */
  bmp388.set_iic_addr(BMP3_I2C_ADDR_SEC);
  /*Initialize bmp388*/
  while(bmp388.begin()){
    Serial.println("Initialize error!");
    delay(1000);
  }

    unsigned long start = millis();
  unsigned long setup_end = millis();

  
  while(setup_end - start < 10000){
     unsigned long deltaMillis = 0; // clear last result
     unsigned long thisMillis = millis();  
     if (thisMillis != thisMillis_old) { 
      deltaMillis = thisMillis-thisMillis_old; 
      thisMillis_old = thisMillis;   
     } 
    
    analogPinTimer -= deltaMillis;

     if (analogPinTimer <= 0) {  
     analogPinTimer += ANALOG_PIN_TIMER_INTERVAL; 
     // sensing loop start!! 
     float Pressure = bmp388.readPressure();
  
     x = Pressure; // 아날로그값 읽기
     x_f = lambda/(1+lambda)*x+1/(1+lambda)*x_fold; //필터된 값
     x_fold = x_f; // 센서 필터 이전값 업데이트
  
   setup_end = millis();
  }
  
}
}

void loop(){

   unsigned long deltaMillis = 0; // clear last result
   unsigned long thisMillis = millis();  
   if (thisMillis != thisMillis_old) { 
   deltaMillis = thisMillis-thisMillis_old; 
   thisMillis_old = thisMillis;   
   } 

   analogPinTimer -= deltaMillis; 

   

   if (BTSerial.available())
   Serial.write(BTSerial.read());
   if (Serial.available())
   BTSerial.write(Serial.read());
   {

    if (analogPinTimer <= 0) {  
    analogPinTimer += ANALOG_PIN_TIMER_INTERVAL;
  
    float Pressure = bmp388.readPressure();

    x = Pressure; // 아날로그값 읽기
    x_f = lambda/(1+lambda)*x+1/(1+lambda)*x_fold; //필터된 값
    x_fold = x_f; // 센서 필터 이전값 업데이트

    Serial.print("BASE: ");  
    BTSerial.print("BASE : ");
    Serial.println(x_f);
    BTSerial.println(x_f);

    }

   } 

}
