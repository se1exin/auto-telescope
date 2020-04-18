//
// Created by selexin on 13/4/20.
//

// Based heavily on the MPU9250BasicAHRS_I2C sketch

#include "quaternionFilters.h"
#include "OrientationSensor.h"

OrientationSensor::OrientationSensor() {
    sensor = MPU9250(MPU9250_ADDRESS, I2Cport, I2Cclock);
    serialDebug = false;
    online = false;
    declination = 0.0;
    isMagCalibrating = false;
}


void OrientationSensor::setSerialDebug(bool serialDebug) {
    OrientationSensor::serialDebug = serialDebug;
}

void OrientationSensor::setDeclination(float declination) {
    OrientationSensor::declination = declination;
}

void OrientationSensor::init() {
    // Wire.begin();

    // Read the WHO_AM_I register, this is a good test of communication
    byte sensorAddress = sensor.readByte(MPU9250_ADDRESS, WHO_AM_I_MPU9250);

    if (serialDebug) {
        Serial.print("MPU9250 I AM 0x");
        Serial.print(sensorAddress, HEX);
        Serial.print(" I should be 0x");
        Serial.println(0x71, HEX);
    }

    // WHO_AM_I should always be 0x71
    if (sensorAddress != 0x71) {
        if (serialDebug) {
            Serial.print("Could not connect to MPU9250: 0x");
            Serial.println(sensorAddress, HEX);

            // Communication failed, stop here
            Serial.println(F("Communication failed, abort!"));
            Serial.flush();
        }

        return;
    }
    sensor.MPU9250SelfTest(sensor.selfTest);
    /* NOTE: serialDebug blocks max out Arduino memory
    if (serialDebug) {
        Serial.print(F("x-axis self test: acceleration trim within : "));
        Serial.print(sensor.selfTest[0], 1);
        Serial.println("% of factory value");
        Serial.print(F("y-axis self test: acceleration trim within : "));
        Serial.print(sensor.selfTest[1], 1);
        Serial.println("% of factory value");
        Serial.print(F("z-axis self test: acceleration trim within : "));
        Serial.print(sensor.selfTest[2], 1);
        Serial.println("% of factory value");
        Serial.print(F("x-axis self test: gyration trim within : "));
        Serial.print(sensor.selfTest[3], 1);
        Serial.println("% of factory value");
        Serial.print(F("y-axis self test: gyration trim within : "));
        Serial.print(sensor.selfTest[4], 1);
        Serial.println("% of factory value");
        Serial.print(F("z-axis self test: gyration trim within : "));
        Serial.print(sensor.selfTest[5], 1);
        Serial.println("% of factory value");
    }
     */

    // Get sensor resolutions, only need to do this once
    sensor.getAres();
    sensor.getGres();
    sensor.getMres();

    // Calibrate gyro and accelerometers, load biases in bias registers
    sensor.calibrateMPU9250(sensor.gyroBias, sensor.accelBias);

    // Initialize device for active mode read of acclerometer, gyroscope, and
    sensor.initMPU9250();
    if (serialDebug) {
        Serial.println("MPU9250 initialized for active data mode....");
    }

    // Read the WHO_AM_I register of the magnetometer, this is a good test of communication
    byte compassAddress = sensor.readByte(AK8963_ADDRESS, WHO_AM_I_AK8963);
    /* NOTE: serialDebug blocks max out Arduino memory
    if (serialDebug) {
        Serial.print("AK8963 ");
        Serial.print("I AM 0x");
        Serial.print(compassAddress, HEX);
        Serial.print(" I should be 0x");
        Serial.println(0x48, HEX);
    }
     */

    if (compassAddress != 0x48) {
        // Communication failed, stop here
        if (serialDebug) {
            Serial.println(F("Communication failed, abort!"));
            Serial.flush();
        }
        return;
    }

    // Get magnetometer calibration from AK8963 ROM
    sensor.initAK8963(sensor.factoryMagCalibration);

    /* NOTE: serialDebug blocks max out Arduino memory
    if (serialDebug) {
        Serial.println("AK8963 initialized for active data mode....");

        //  Serial.println("Calibration values: ");
        Serial.print("X-Axis factory sensitivity adjustment value ");
        Serial.println(sensor.factoryMagCalibration[0], 2);
        Serial.print("Y-Axis factory sensitivity adjustment value ");
        Serial.println(sensor.factoryMagCalibration[1], 2);
        Serial.print("Z-Axis factory sensitivity adjustment value ");
        Serial.println(sensor.factoryMagCalibration[2], 2);
    }
    */

    /* NOTE: serialDebug blocks max out Arduino memory
    if (serialDebug) {
        Serial.println("AK8963 mag biases (mG)");
        Serial.println(sensor.magBias[0]);
        Serial.println(sensor.magBias[1]);
        Serial.println(sensor.magBias[2]);

        Serial.println("AK8963 mag scale (mG)");
        Serial.println(sensor.magScale[0]);
        Serial.println(sensor.magScale[1]);
        Serial.println(sensor.magScale[2]);

        Serial.println("Magnetometer:");
        Serial.print("X-Axis sensitivity adjustment value ");
        Serial.println(sensor.factoryMagCalibration[0], 2);
        Serial.print("Y-Axis sensitivity adjustment value ");
        Serial.println(sensor.factoryMagCalibration[1], 2);
        Serial.print("Z-Axis sensitivity adjustment value ");
        Serial.println(sensor.factoryMagCalibration[2], 2);
    }
    */

    online = true;
}

void OrientationSensor::calibrateMag() {
    isMagCalibrating = true;
    sensor.magCalMPU9250(sensor.magBias, sensor.magScale);

    isMagCalibrating = false;
}

void OrientationSensor::update() {
    if (!online) {
        if (serialDebug) {
            Serial.println("Sensor not online. Cannot run update()");
        }
        return;
    }

    // If intPin goes high, all data registers have new data
    // On interrupt, check if data ready interrupt
    if (sensor.readByte(MPU9250_ADDRESS, INT_STATUS) & 0x01) {
        sensor.readAccelData(sensor.accelCount);  // Read the x/y/z adc values

        // Now we'll calculate the accleration value into actual g's
        // This depends on scale being set
        sensor.ax = (float) sensor.accelCount[0] * sensor.aRes; // - sensor.accelBias[0];
        sensor.ay = (float) sensor.accelCount[1] * sensor.aRes; // - sensor.accelBias[1];
        sensor.az = (float) sensor.accelCount[2] * sensor.aRes; // - sensor.accelBias[2];

        sensor.readGyroData(sensor.gyroCount);  // Read the x/y/z adc values

        // Calculate the gyro value into actual degrees per second
        // This depends on scale being set
        sensor.gx = (float) sensor.gyroCount[0] * sensor.gRes;
        sensor.gy = (float) sensor.gyroCount[1] * sensor.gRes;
        sensor.gz = (float) sensor.gyroCount[2] * sensor.gRes;

        sensor.readMagData(sensor.magCount);  // Read the x/y/z adc values

        // Calculate the magnetometer values in milliGauss
        // Include factory calibration per data sheet and user environmental
        // corrections
        // Get actual magnetometer value, this depends on scale being set
        sensor.mx = (float) sensor.magCount[0] * sensor.mRes
                    * sensor.factoryMagCalibration[0] - sensor.magBias[0];
        sensor.my = (float) sensor.magCount[1] * sensor.mRes
                    * sensor.factoryMagCalibration[1] - sensor.magBias[1];
        sensor.mz = (float) sensor.magCount[2] * sensor.mRes
                    * sensor.factoryMagCalibration[2] - sensor.magBias[2];
    } // if (readByte(MPU9250_ADDRESS, INT_STATUS) & 0x01)

    // Must be called before updating quaternions!
    sensor.updateTime();

    // Sensors x (y)-axis of the accelerometer is aligned with the y (x)-axis of
    // the magnetometer; the magnetometer z-axis (+ down) is opposite to z-axis
    // (+ up) of accelerometer and gyro! We have to make some allowance for this
    // orientationmismatch in feeding the output to the quaternion filter. For the
    // MPU-9250, we have chosen a magnetic rotation that keeps the sensor forward
    // along the x-axis just like in the LSM9DS0 sensor. This rotation can be
    // modified to allow any convenient orientation convention. This is ok by
    // aircraft orientation standards! Pass gyro rate as rad/s
    MahonyQuaternionUpdate(sensor.ax, sensor.ay, sensor.az, sensor.gx * DEG_TO_RAD,
                           sensor.gy * DEG_TO_RAD, sensor.gz * DEG_TO_RAD, sensor.my,
                           sensor.mx, sensor.mz, sensor.deltat);

    // Serial print and/or display at 0.5 s rate independent of data rates
    sensor.delt_t = millis() - sensor.count;

    // update LCD once per half-second independent of read rate
    if (sensor.delt_t > 500) {
        /* NOTE: serialDebug blocks max out Arduino memory
        if (serialDebug) {
            Serial.print("ax = ");
            Serial.print((int) 1000 * sensor.ax);
            Serial.print(" ay = ");
            Serial.print((int) 1000 * sensor.ay);
            Serial.print(" az = ");
            Serial.print((int) 1000 * sensor.az);
            Serial.println(" mg");

            Serial.print("gx = ");
            Serial.print(sensor.gx, 2);
            Serial.print(" gy = ");
            Serial.print(sensor.gy, 2);
            Serial.print(" gz = ");
            Serial.print(sensor.gz, 2);
            Serial.println(" deg/s");

            Serial.print("mx = ");
            Serial.print((int) sensor.mx);
            Serial.print(" my = ");
            Serial.print((int) sensor.my);
            Serial.print(" mz = ");
            Serial.print((int) sensor.mz);
            Serial.println(" mG");

            Serial.print("q0 = ");
            Serial.print(*getQ());
            Serial.print(" qx = ");
            Serial.print(*(getQ() + 1));
            Serial.print(" qy = ");
            Serial.print(*(getQ() + 2));
            Serial.print(" qz = ");
            Serial.println(*(getQ() + 3));
        }
         */

        // Define output variables from updated quaternion---these are Tait-Bryan
        // angles, commonly used in aircraft orientation. In this coordinate system,
        // the positive z-axis is down toward Earth. Yaw is the angle between Sensor
        // x-axis and Earth magnetic North (or true North if corrected for local
        // declination, looking down on the sensor positive yaw is counterclockwise.
        // Pitch is angle between sensor x-axis and Earth ground plane, toward the
        // Earth is positive, up toward the sky is negative. Roll is angle between
        // sensor y-axis and Earth ground plane, y-axis up is positive roll. These
        // arise from the definition of the homogeneous rotation matrix constructed
        // from quaternions. Tait-Bryan angles as well as Euler angles are
        // non-commutative; that is, the get the correct orientation the rotations
        // must be applied in the correct order which for this configuration is yaw,
        // pitch, and then roll.
        // For more see
        // http://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles
        // which has additional links.
        sensor.yaw = atan2(2.0f * (*(getQ() + 1) * *(getQ() + 2) + *getQ() * *(getQ() + 3)),
                           *getQ() * *getQ() + *(getQ() + 1) * *(getQ() + 1) - *(getQ() + 2) * *(getQ() + 2) -
                           *(getQ() + 3) * *(getQ() + 3));
        sensor.pitch = -asin(2.0f * (*(getQ() + 1) * *(getQ() + 3) - *getQ() * *(getQ() + 2)));
        sensor.roll = atan2(2.0f * (*getQ() * *(getQ() + 1) + *(getQ() + 2) * *(getQ() + 3)),
                            *getQ() * *getQ() - *(getQ() + 1) * *(getQ() + 1) - *(getQ() + 2) * *(getQ() + 2) +
                            *(getQ() + 3) * *(getQ() + 3));
        sensor.pitch *= RAD_TO_DEG;
        sensor.yaw *= RAD_TO_DEG;
        sensor.yaw -= OrientationSensor::declination;
        sensor.roll *= RAD_TO_DEG;

        if (serialDebug) {
            Serial.print("Yaw, Pitch, Roll: ");
            Serial.print(sensor.yaw, 2);
            Serial.print(", ");
            Serial.print(sensor.pitch, 2);
            Serial.print(", ");
            Serial.println(sensor.roll, 2);

            Serial.print("rate = ");
            Serial.print((float) sensor.sumCount / sensor.sum, 2);
            Serial.println(" Hz");
        }

        sensor.count = millis();
        sensor.sumCount = 0;
        sensor.sum = 0;
    } // if (sensor.delt_t > 500)
}

float OrientationSensor::getYaw() {
    return sensor.yaw;
}

float OrientationSensor::getPitch() {
    return sensor.pitch;
}

float OrientationSensor::getRoll() {
    return sensor.roll;
}