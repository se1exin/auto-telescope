#include <Wire.h>
#include "EasyDriver.h"


// Orientation values
const int ORIENTATION_CONTROLLER_ADDRESS = 0x03;
const byte ORIENTATION_STATE_WAITING = 0x45;
const byte ORIENTATION_STATE_INIT = 0x46;
const byte ORIENTATION_STATE_CAL_COMPASS = 0x47;
const byte ORIENTATION_STATE_UPDATING = 0x48;

float yaw = 0;
float pitch = 0;
float roll = 0;

byte orientationState = ORIENTATION_STATE_WAITING;
int orientationStateCount = 0;
int orientationStateDelta = 0;
bool orientationHasData = false;


// Stepper setup
EasyDriver stepper = EasyDriver(2, 3, 4, 5, 6);



// Stepper positioning
float targetPosX = 0;
float currentPosX = 0;
float targetPosY = 0;
float currentPosY = 0;

// Motor enable/disable button
const int MOTOR_SWITCH_PIN = 13;
bool motorsEnabled = false; // Will be updated with push button

// Gear Ratios
//int gear1a = 20; // Num teeth on gear on stepper shaft
//int gear1b = 60; // Num teeth on big gear on main shaft
//int gear2a = 14; // Num teeth on small gear on main shaft
//int gear2b = 94; // Num teeth on platform internal gear
//
//float gear1ratio = gear1b / gear1a; // (3) Every rotation of gear1b causes gear1a this many rotations
//float gear2ratio = gear2b / gear2a; // (6.7142) Every rotation of gear2b causes gear2a this many rotations
//
//float gear1a2bratio = gear1ratio * gear2ratio; // 20.142857143

void setup() {
    pinMode(MOTOR_SWITCH_PIN, INPUT);

    Serial.begin(38400);
    Wire.begin();

    Serial.println("BEGIN");

    stepper.reset();

    setOrientationState(ORIENTATION_STATE_INIT);
}

void loop() {
  // Check if the enable/disable button has been pressed
  if (digitalRead(MOTOR_SWITCH_PIN) == HIGH) {
      motorsEnabled = !motorsEnabled;
      delay(500); // Quick delay to avoid detecting the same press multiple times
  }

  stepper.enable(motorsEnabled);

  // Get orientation status
  orientationStateDelta = millis() - orientationStateCount;

  if (orientationStateCount == 0 || orientationStateDelta > 250) {
    // Request state every 1 seconds
    orientationState = getOrientationState();
    orientationStateCount = millis();  
  }
  

  switch (orientationState) {
    case ORIENTATION_STATE_WAITING:
      Serial.println("> Orientation waiting");
      setOrientationState(ORIENTATION_STATE_INIT);
      Serial.println("  requesting init");
      return;
    
    case ORIENTATION_STATE_CAL_COMPASS:
      // Serial.println("> Orientation Cal Compass");
      // Rotate the compass during calibration.
      
      stepper.setMode(EASYDRIVER_MODE_FULL_STEP);
      stepper.stepForward();
      return;
    
    case ORIENTATION_STATE_UPDATING:
      orientationHasData = true;
      //Serial.println("> Orientation Updating");
    /*
      Serial.print("Yaw, Roll, Pitch: ");
      Serial.print(yaw);
      Serial.print(" ");
      Serial.print(pitch);
      Serial.print(" ");
      Serial.println(roll);
      */
      // Distance between where we are and where we want to go

      currentPosX = targetPosX - yaw;
      /*
      Serial.print("Current pos: ");
      Serial.print(yaw);
      Serial.print(" - offset: ");
      Serial.println(currentPosX);
      */

      break;
    
    default:
      // Serial.print("Unknown state: ");
      // Serial.println(orientationState);
      // Nothing to do..
      // delay(1000);
      // return;
      if (!orientationHasData) {
        return;
      }
      break;
  }

    

    // Determine which direction is the most efficient to reach the target
    // magHeading is a value between -180 and 180
    //
    stepper.setMode(EASYDRIVER_MODE_EIGHTH_STEP);
    if (currentPosX < 1) {
        if (currentPosX >= -5) {
            stepper.setMode(EASYDRIVER_MODE_EIGHTH_STEP);
        }
        stepper.stepReverse();

    } else if (currentPosX > -1) {
        if (currentPosX <= 5) {
            stepper.setMode(EASYDRIVER_MODE_EIGHTH_STEP);
        }
        stepper.stepForward();
    } else {
        stepper.enable(false);
    }
}

void setOrientationState(byte val) {
  Wire.beginTransmission(ORIENTATION_CONTROLLER_ADDRESS);
  Wire.write(val);
  Wire.endTransmission();
}

byte getOrientationState() {
  Wire.requestFrom(ORIENTATION_CONTROLLER_ADDRESS, 25);

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

    yaw = atof(yawBuffer);
    pitch = atof(pitchBuffer);
    roll = atof(rollBuffer);    
  }

  return status;
}
