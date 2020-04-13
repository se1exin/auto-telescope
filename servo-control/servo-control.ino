#include <Servo.h>

// X and Y axis servos
Servo servoX;
Servo servoY; // Not in use yet..

// Servo positioning
int targetPosX = 0;
int currentPosX = 0;
int targetPosY = 0;
int currentPosY = 0;

const int STEP_SPEED = 15;


String serialInput;

void setup() {
  Serial.begin(9600);

  servoX.attach(9);
  servoY.attach(10);
}

void loop() {
  while(Serial.available()) {
    serialInput = Serial.readStringUntil(';');
    if (serialInput.length() > 1) {
      // Recieved a command
      if (serialInput[0] == 'x') {
        targetPosX = extractServoVal(serialInput);
      }
      if (serialInput[0] == 'y') {
        targetPosY = extractServoVal(serialInput);
      }
    }
    
  }


  moveServo(servoX, currentPosX, targetPosX, STEP_SPEED);
  moveServo(servoY, currentPosY, targetPosY, STEP_SPEED);
}

int extractServoVal(String input) {
  serialInput.remove(0, 1); // Remove the command char (e.g. 'x' or 'y')
  int servoVal = serialInput.toInt();

  // Make sure the value is within servo bounds
  if (servoVal < 0) {
    servoVal = 0;
  } else if (servoVal > 180) {
    servoVal = 180;
  }

  return servoVal;
}

void moveServo(Servo servo, int &currentPos, int targetPos, int stepSpeed) {
  if (targetPos > currentPos) {
    currentPos += 1;
  }
  if (targetPos < currentPos) {
    currentPos -= 1;
  }

  if (targetPos != currentPos) {
    servo.write(currentPos);
    delay(stepSpeed);
  }
}
