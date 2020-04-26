/**
 * Stepper Motor controller: I2C Slave
 * I2C Address: 0x07
 *
 * I2C proxy for the EasyDriver stepper motor driver.
 */

#include <Wire.h>
#include "EasyDriver.h"

EasyDriver stepper = EasyDriver(2, 3, 4, 5, 6);

const int I2C_ADDRESS = 0x07;

/**
 * Send any of the following bytes to set the stepper motor to the applicable state
 */
const byte CMD_RESET = 0x45;
const byte CMD_ENABLE = 0x46;
const byte CMD_DISABLE = 0x47;
const byte CMD_SET_MODE_FULL_STEP = 0x48;
const byte CMD_SET_MODE_HALF_STEP = 0x49;
const byte CMD_SET_MODE_QUARTER_STEP = 0x50;
const byte CMD_SET_MODE_EIGTH_STEP = 0x51;
const byte CMD_STEP_FORWARD = 0x56;
const byte CMD_STEP_BACKWARD = 0x57;
const byte CMD_NULL = 0x00;

byte currentCmd = 0x00;

void setup() {
  Wire.begin(I2C_ADDRESS);
  Wire.onReceive(onReceive);
  stepper.reset();
}

void onReceive(int count) {
  currentCmd = Wire.read(); 
}

void loop() {
  switch (currentCmd) {
    case CMD_RESET:
      stepper.reset();
      currentCmd = CMD_NULL;
      return;
    
    case CMD_ENABLE:
      stepper.enable(true);
      currentCmd = CMD_NULL;
      return;

    case CMD_DISABLE:
      stepper.enable(false);
      currentCmd = CMD_NULL;
      return;

    case CMD_SET_MODE_FULL_STEP:
      stepper.setMode(EASYDRIVER_MODE_FULL_STEP);
      currentCmd = CMD_NULL;
      return;

    case CMD_SET_MODE_HALF_STEP:
      stepper.setMode(EASYDRIVER_MODE_HALF_STEP);
      currentCmd = CMD_NULL;
      return;

    case CMD_SET_MODE_QUARTER_STEP:
      stepper.setMode(EASYDRIVER_MODE_EIGHTH_STEP);
      currentCmd = CMD_NULL;
      return;

    case CMD_SET_MODE_EIGTH_STEP:
      stepper.setMode(EASYDRIVER_MODE_EIGHTH_STEP);
      currentCmd = CMD_NULL;
      return;

    case CMD_STEP_FORWARD:
      stepper.stepForward();
      currentCmd = CMD_NULL;
      return;

    case CMD_STEP_BACKWARD:
      stepper.stepReverse();
      currentCmd = CMD_NULL;
      return;

    default:
      delay(1);
      break;
  }
}
