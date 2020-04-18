/**
 * Orientation Controller
 *
 * Acts as an I2C Slave.
 */

#include <Wire.h>
#include "OrientationSensor.h"

OrientationSensor orientationSensor = OrientationSensor();

const byte STATE_WAITING = 0x00;
const byte STATE_INIT = 0x01;
const byte STATE_CALIBRATING_COMPASS = 0x02;
const byte STATE_ORIENTATION_UPDATE = 0x03;


byte state = STATE_WAITING;

void setup() {
    Serial.begin(9600);
    Wire.begin(0x03);
    Wire.onReceive(onReceive);
    Wire.onRequest(onRequest);


    // Setup Orientation Sensor
    // @TODO: Add compass sensor and move to I2C init request
    orientationSensor.setSerialDebug(true);
    orientationSensor.setDeclination(13.63);
}

void onReceive(int count) {
    Serial.println("DID RECEIVE");
    // Master has sent data

    // Step 1. Master must signal it is ready to start the sensor(s)
    // Step 1.1. (Start the sensors)

    // Step 2. Master must request that compass calibration begins
    // Step 2.2 (Begin calibration)
    state = Wire.read();
}

void onRequest() {
    Wire.write(state);
    // Master has requested data

    // Step 1. Send signal that setup has begun.
    // Step 1.1 Send signal that setup has complete.

    // Step 2. Signal that compass calibration has begun.
    // Step 2.2. Signal that compass calibration has complete.
}



void loop() {
    switch (state) {
        case STATE_INIT:
            Serial.println('INIT');
            orientationSensor.init();
            state = STATE_WAITING;
            return;
        case STATE_CALIBRATING_COMPASS:
            Serial.println('CAL COMPASS');
            calibrateCompass();
            state = STATE_WAITING;
            return;
        case STATE_ORIENTATION_UPDATE:
            Serial.println('UPDATE ORIENATION');
            orientationSensor.update();
            state = STATE_WAITING;
            return;
        default:
            state = STATE_WAITING;
            //Serial.println('no update...');
            delay(100);
    }
}


void initSensors() {

}

void calibrateCompass() {
    Serial.println("xxxCalibrating!");
    orientationSensor.calibrateMag();
    Serial.println("xxxCalibration Done!");
}