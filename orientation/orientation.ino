/**
 * Orientation Controller
 *
 * Acts as an I2C Slave.
 */

#include <Wire.h>
#include "OrientationSensor.h"

OrientationSensor orientationSensor = OrientationSensor();

/**
 * Controller will start in the WAITING state. In this state the sensor is NOT initialized or calibrated.
 * Controller should be requested to move to INIT state (via I2C). In this state the sensor will initialize and calibrate Accel and Gyros.
 *      The sensor should NOT be physically moved in the INIT state as the Gyro and Accel sensors are calibrating.
 *      After Accel and Gyro calibration, the Controller will move to the MAG_CALIBRATING state.
 * Controller will be moved to MAG_CALIBRATING state. In this state the sensor cannot be changed and will be calibrating the mag.
 *      The sensor should be physically moved so the mag can calibrate.
 *      After calibration in complete, the Controller will move to the UPDATING state.
 * Controller will be moved to the UPDATING state. In this state the sensor will be continuously updating Roll, Pitch, and Yaw.
 */

const byte STATE_WAITING = 0x45;
const byte STATE_INIT = 0x46;
const byte STATE_MAG_CALIBRATING = 0x47;
const byte STATE_UPDATING = 0x48;

byte state = STATE_WAITING;

char yawBuffer [8];
char pitchBuffer [8];
char rollBuffer [8];

void setup() {
    Serial.begin(9600);
    Wire.begin(0x03);
    Wire.onReceive(onReceive);
    Wire.onRequest(onRequest);

    // Setup Orientation Sensor
    // orientationSensor.serialDebug = true;
}

void onReceive(int count) {
    // Master has sent data. This should set the current state (e.g. to INIT the controller).
    state = Wire.read();
}

void onRequest() {
    // Master has requested data

    // First byte is controller state
    Wire.write(state);

    if (state == STATE_UPDATING && orientationSensor.hasData) {
        // If we are getting position updates, send them after the state byte
        for (int i = 0; i < 8; i++) {
            Wire.write(yawBuffer[i]);
        }

        for (int i = 0; i < 8; i++) {
            Wire.write(pitchBuffer[i]);
        }

        for (int i = 0; i < 8; i++) {
            Wire.write(rollBuffer[i]);
        }
    }
}

void loop() {
    switch (state) {
        case STATE_INIT:
            orientationSensor.init();
            // Immediately move to the mag calibration state
            state = STATE_MAG_CALIBRATING;
            break;
        case STATE_MAG_CALIBRATING:
            orientationSensor.calibrateMag();
            // Move to updating state now that calibration is complete
            delay(2000);
            state = STATE_UPDATING;
            break;
        case STATE_UPDATING:
            orientationSensor.update();

            // Move updated values into the buffers for sending over I2C
            dtostrf(orientationSensor.sensor.yaw, 7, 2, yawBuffer);
            dtostrf(orientationSensor.sensor.pitch, 7, 2, pitchBuffer);
            dtostrf(orientationSensor.sensor.roll, 7, 2, rollBuffer);
            break;
        case STATE_WAITING:
            delay(100);
            break;
    }
}
