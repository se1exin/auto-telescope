#include <Stepper.h>
#include "SparkFun_MAG3110.h"


// Stepper positioning
float targetPosX = 0;
float currentPosX = 0;
float targetPosY = 0;
float currentPosY = 0;

const int STEP_SPEED = 15;
const int STEPS_PER_REV = 64;
const int STEPS_PER_REV_REAL = 4096; // Gear ration 64:1

// X and Y axis steppers
Stepper stepperX(STEPS_PER_REV, 8, 9, 10, 11);
Stepper stepperY(STEPS_PER_REV, 3, 4, 5, 6);

// The 28BYJ-48 stepper need to have pin 2 and 3 reversed to rotate counter-clockwise.
// See https://forum.arduino.cc/index.php?topic=549927.0
Stepper stepperXRev(STEPS_PER_REV, 8, 10, 9, 11);
Stepper stepperYRev(STEPS_PER_REV, 3, 5, 4, 6);

// Digital compass
MAG3110 mag = MAG3110();

// Mag smoothing
const int numMagReadings = 10;
float magReadings[numMagReadings];
int magReadingIndex = 0;
float magReadingTotal = 0;
float magReadingAverage = 0;

float magHeading = 0;
int calibrationSteps = 0;

String serialInput;

void setup() {
  Serial.begin(9600);

  stepperX.setSpeed(60);
  stepperY.setSpeed(60);
  stepperXRev.setSpeed(60);
  stepperYRev.setSpeed(60);

  // Setup Magnetometer
  Wire.begin();
  Wire.setClock(400000); // I2C fast mode, 400kHz
  mag.initialize();

  // Initialize smoothing array
  for (int thisReading = 0; thisReading < numMagReadings; thisReading++) {
    magReadings[thisReading] = 0.0;
  }
//
//  
//  mag.setOffset(MAG3110_X_AXIS, MAG3110_X_OFFSET);
//  mag.setOffset(MAG3110_Y_AXIS, MAG3110_Y_OFFSET);
//  mag.setOffset(MAG3110_Z_AXIS, MAG3110_Z_OFFSET);
}

void loop() {
  if (!magReady()) {
    stepForwardsX();
    // stepBackwardsX();
    calibrationSteps++;
    return;
  }

  
  checkForSerialData();

  updateMagReadings();
  
  // Distance between where we are and where we want to go
  currentPosX = targetPosX - magReadingAverage;
  // currentPosX = targetPosX - magHeading;
  Serial.print("Current pos: ");
  Serial.print(magReadingAverage);
  Serial.print(" - offset: ");
  Serial.println(currentPosX);
  delay(5);

  // Determine which direction is the most efficient to reach the target
  // magHeading is a value between -180 and 180
  // 

  return;
  
  if (currentPosX < 0.2) {
    stepForwardsX();
  } else if (currentPosX > -0.2) {
    stepBackwardsX();
  }
  
}


bool magReady() {
  if(!mag.isCalibrated()) {
    if(!mag.isCalibrating()) {
      mag.enterCalMode();
    } else {
      Serial.println("Calibrating..");
      mag.calibrate();
    }
    return false;
  }
  
  return true;
}

void updateMagReadings() {
  
  if(mag.dataReady()) {
    magHeading = mag.readHeading();
    magReadingTotal = magReadingTotal - magReadings[magReadingIndex];
    magReadings[magReadingIndex] = magHeading;
    magReadingTotal = magReadingTotal + magReadings[magReadingIndex];
    magReadingIndex++;
    if (magReadingIndex >= numMagReadings) {
      magReadingIndex = 0;
    }
    magReadingAverage = magReadingTotal / numMagReadings;
  }
}

void checkForSerialData() {
  while(Serial.available()) {
    serialInput = Serial.readStringUntil(';');
    if (serialInput.length() > 1) {
      // Recieved a command
      if (serialInput[0] == 'x') {
        targetPosX = extractStepperVal(serialInput);
      }
      if (serialInput[0] == 'y') {
        targetPosY = extractStepperVal(serialInput);
      }
    }
  }
}

int extractStepperVal(String input) {
  serialInput.remove(0, 1); // Remove the command char (e.g. 'x' or 'y')
  int stepperVal = serialInput.toInt();

  // Make sure the value is within stepper bounds
  if (stepperVal < 0) {
    stepperVal = 0;
  } else if (stepperVal > 360) {
    stepperVal = 360;
  }

  return stepperVal;
}


void stepForwardsX() {
  stepperX.step(1);
}

void stepBackwardsX() {
  stepperXRev.step(-1);
}

void moveStepper(Stepper stepper, int &currentPos, int targetPos, int stepSpeed) {
  if (targetPos > currentPos) {
    currentPos += 1;
  }
  if (targetPos < currentPos) {
    currentPos -= 1;
  }

  if (targetPos != currentPos) {
    stepper.step(1);
    delay(stepSpeed);
  }
}
