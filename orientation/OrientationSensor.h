//
// Created by selexin on 13/4/20.
//

// Wrapper class for the MPU9250 library, to provide a simpler interface.
// Might be abstracted so that different sensors can be swapped out.
// Requires the Sparkfun MPU9250 Library: https://github.com/sparkfun/SparkFun_MPU-9250_Breakout_Arduino_Library/

#ifndef STEPPER_CONTROL2_ORIENTATIONSENSOR_H
#define STEPPER_CONTROL2_ORIENTATIONSENSOR_H

// #include "Arduino.h"
#include "MPU9250.h"

#define I2Cclock 400000
#define I2Cport Wire
#define MPU9250_ADDRESS MPU9250_ADDRESS_AD0   // Use either this line or the next to select which I2C address your device is using
//#define MPU9250_ADDRESS MPU9250_ADDRESS_AD1


class OrientationSensor {
private:
    MPU9250 sensor;
    bool serialDebug;
    bool online;
    float declination;

public:
    OrientationSensor();

    bool isMagCalibrating;

    void setSerialDebug(bool serialDebug);

    void setDeclination(float declination);

    void init();

    void calibrateMag();

    void update();

    float getYaw();

    float getPitch();

    float getRoll();
};


#endif //STEPPER_CONTROL2_ORIENTATIONSENSOR_H
