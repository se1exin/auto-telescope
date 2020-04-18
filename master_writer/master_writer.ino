#include <Wire.h>

void setup() {
  Serial.begin(9600);
  Wire.begin();
}

bool isInit = false;

bool isCal = false;

void loop() {
  Serial.println('reading...');
  byte state = read();

  if (state == 0x00 && !isInit) {
      send(0x01);
      isInit = true;
  }

  if (state == 0x00 && !isCal) {
      send(0x02);
      isCal = true;
  }

  if (!isCal) {
    
    isCal = true;  
  }

  
  
  // send(2);

  delay(1000);
  
}

void send(byte val) {
  Wire.beginTransmission(0x03);
  Wire.write(val);
  Wire.endTransmission();

  delay(500);
}

byte read() {
  // Read 
  Wire.requestFrom(0x03, 1);
  return Wire.read();
}
