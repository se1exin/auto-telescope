#include "OrientationSensor.h"
#include "EasyDriver.h"

// Stepper setup
EasyDriver stepper = EasyDriver(2, 3, 4, 5, 6);

// Stepper positioning
float targetPosX = 0;
float currentPosX = 0;
float targetPosY = 0;
float currentPosY = 0;

// Digital compass
OrientationSensor orientationSensor = OrientationSensor();

// Mag smoothing
float magHeading = 0;

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

    while(!Serial){};

    // Setup Orientation Sensor
    orientationSensor.setSerialDebug(true);
    orientationSensor.setDeclination(13.63);
    orientationSensor.init();

    stepper.reset();
}

bool caled = false;
void loop() {

    if (!caled && !orientationSensor.isMagCalibrating) {
        Serial.println("DO CAL");
        orientationSensor.calibrateMag();
    }

    if (orientationSensor.isMagCalibrating) {
        Serial.println("CALING");
        stepper.setMode(EASYDRIVER_MODE_FULL_STEP);
        stepper.stepForward();
        return;
    }
    caled = true;

    orientationSensor.update();

    magHeading = orientationSensor.getYaw();

    // Check if the enable/disable button has been pressed
    if (digitalRead(MOTOR_SWITCH_PIN) == HIGH) {
        motorsEnabled = !motorsEnabled;
        delay(500); // Quick delay to avoid detecting the same press multiple times
    }

    stepper.enable(motorsEnabled);


    // Distance between where we are and where we want to go
    currentPosX = targetPosX - magHeading;
//
    Serial.print("Current pos: ");
    Serial.print(magHeading);
    Serial.print(" - offset: ");
    Serial.println(currentPosX);

    // Determine which direction is the most efficient to reach the target
    // magHeading is a value between -180 and 180
    //
    stepper.setMode(EASYDRIVER_MODE_FULL_STEP);
    if (currentPosX < 1) {
        if (currentPosX >= -5) {
            // stepper.setMode(EASYDRIVER_MODE_EIGHTH_STEP);
        }
        stepper.stepForward();

    } else if (currentPosX > -1) {
        if (currentPosX <= 5) {
            // stepper.setMode(EASYDRIVER_MODE_EIGHTH_STEP);
        }
        stepper.stepReverse();
    } else {
        stepper.enable(false);
    }


}
