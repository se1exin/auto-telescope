#include <Wire.h>

const byte ORIENTATION_STATE_WAITING = 0x45;
const byte ORIENTATION_STATE_INIT = 0x46;
const byte ORIENTATION_STATE_CAL_COMPASS = 0x47;
const byte ORIENTATION_STATE_UPDATING = 0x48;

void setup() {
  Serial.begin(9600);
  Wire.begin();
}

void loop() {
  byte orientationState = read();

  switch (orientationState) {
    case ORIENTATION_STATE_WAITING:
      Serial.println("> Orientation waiting");
      send(ORIENTATION_STATE_INIT);
      Serial.println("  requesting init");
      break;
    case ORIENTATION_STATE_INIT:
      // Serial.println("> Orientation Init...");
      break;
    case ORIENTATION_STATE_CAL_COMPASS:
      // Serial.println("> Orientation Cal Compass");
      break;
    case ORIENTATION_STATE_UPDATING:
      // Serial.println("> Orientation Updating");
      break;
  }

  delay(100);
  
}

void send(byte val) {
  Wire.beginTransmission(0x03);
  Wire.write(val);
  Wire.endTransmission();

  delay(500);
}

byte read() {
  // Read 
  Wire.requestFrom(0x03, 25);

  // First byte is the current status
  byte status = Wire.read();

  if (status == ORIENTATION_STATE_UPDATING) {
    char yawBuffer [8];
    char pitchBuffer [8];
    char rollBuffer [8];

    // Next 8 bytes are yaw
    for (int i = 0; i < 8; i++) {
      yawBuffer[i] = Wire.read();
    }

    // Next 8 bytes are pitch
    for (int i = 0; i < 8; i++) {
      pitchBuffer[i] = Wire.read();
    }

    // Last 8 bytes are roll
    for (int i = 0; i < 8; i++) {
      rollBuffer[i] = Wire.read();
    }

    float yaw = atof(yawBuffer);
    float pitch = atof(pitchBuffer);
    float roll = atof(rollBuffer);

    Serial.print("Yaw, Roll, Pitch: ");
    Serial.print(yaw);
    Serial.print(" ");
    Serial.print(pitch);
    Serial.print(" ");
    Serial.println(roll);

    
  }

  return status;
}
