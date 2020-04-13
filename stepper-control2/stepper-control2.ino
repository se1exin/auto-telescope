#include "SparkFun_MAG3110.h"
#include "EasyDriver.h"

// Stepper setup
EasyDriver stepper = EasyDriver(2, 3, 4, 5, 6);

// Stepper positioning
float targetPosX = 0;
float currentPosX = 0;
float targetPosY = 0;
float currentPosY = 0;

// Digital compass
MAG3110 mag = MAG3110();

// Mag smoothing
const int numMagReadings = 3;
float magReadings[numMagReadings];
int magReadingIndex = 0;
float magReadingTotal = 0;
float magReadingAverage = 0;

float magHeading = 0;
int printCounter = 0;

// Motor enable/disable button
const int MOTOR_SWITCH_PIN = 13;
bool motorsEnabled = false; // Will be updated with push button

// Gear Ratios
int gear1a = 20; // Num teeth on gear on stepper shaft
int gear1b = 60; // Num teeth on big gear on main shaft
int gear2a = 14; // Num teeth on small gear on main shaft
int gear2b = 94; // Num teeth on platform internal gear

float gear1ratio = gear1b / gear1a; // (3) Every rotation of gear1b causes gear1a this many rotations
float gear2ratio = gear2b / gear2a; // (6.7142) Every rotation of gear2b causes gear2a this many rotations

float gear1a2bratio = gear1ratio * gear2ratio; // 20.142857143



String serialInput;

void setup() {
    pinMode(MOTOR_SWITCH_PIN, INPUT);

    Serial.begin(9600);

    // Setup Magnetometer
    Wire.begin();
    Wire.setClock(400000); // I2C fast mode, 400kHz
    mag.initialize();

    stepper.reset();

    // Initialize smoothing array
    for (int thisReading = 0; thisReading < numMagReadings; thisReading++) {
        magReadings[thisReading] = 0.0;
    }
}

void loop() {
    // Check if the enable/disable button has been pressed
    if (digitalRead(MOTOR_SWITCH_PIN) == HIGH) {
        motorsEnabled = !motorsEnabled;
        delay(500); // Quick delay to avoid detecting the same press multiple times
    }

    stepper.enable(motorsEnabled);


    if (!magReady()) {
        stepper.setMode(EASYDRIVER_MODE_FULL_STEP);
        stepper.stepForward();
        return;
    }

    updateMagReadings();

    // Distance between where we are and where we want to go
    // currentPosX = targetPosX - magReadingAverage;
    currentPosX = targetPosX - magHeading;

    if (printCounter > 50) {
        Serial.print("Current pos: ");
        Serial.print(magReadingAverage);
        Serial.print(" - offset: ");
        Serial.println(currentPosX);
        printCounter = 0;
    }
    printCounter++;

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


bool magReady() {
    if(!mag.isCalibrated()) {
        if(!mag.isCalibrating()) {
            mag.enterCalMode();
        } else {
            // Serial.println("Calibrating..");
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
