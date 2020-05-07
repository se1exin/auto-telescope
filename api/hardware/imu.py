import math
import threading
import time
from collections import deque

import numpy

from ahrs.common import DEG2RAD, RAD2DEG
from ahrs.common.orientation import q2euler
from ahrs.filters import Madgwick, Mahony
from mpu9250_jmdev.mpu_9250 import MPU9250
from mpu9250_jmdev.registers import *


class IMU(object):
    is_calibrating_mag = False

    def __init__(self, stability_threshold=0.5):
        self.mpu9250 = MPU9250(
            address_ak=AK8963_ADDRESS,
            address_mpu_master=MPU9050_ADDRESS_68,
            address_mpu_slave=None,
            bus=1,
            gfs=GFS_1000,
            afs=AFS_8G,
            mfs=AK8963_BIT_16,
            mode=AK8963_MODE_C100HZ
        )

        self.is_calibrating_mag = False
        self.mag_calibrated = False
        self.mpu_calibrated = False
        self.updating = False

        # How many degrees of variance can be tolerated in stability detection?
        self.stability_threshold = stability_threshold

        self.mpu9250.mbias = [
            20.7454594017094,
            10.134935897435899,
            -11.132967032967032,
        ]

        # OLD
        # self.mpu9250.magScale = [
        #     1.0092850510677809,
        #     1.0352380952380953,
        #     0.9585537918871252,
        # ]
        # self.mpu9250.magScale = [
        #     1.1048321048321048,
        #     1.1441899915182359,
        #     0.8190649666059503
        # ]

        self.has_position = False
        self.position_stable = False
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.yaw_smoothed = 0.0
        self.mag_heading_raw = 0.0

    def configure(self):
        self.mpu9250.configure()

    def calibrate_mag(self):
        self.is_calibrating_mag = True
        self.mpu9250.calibrateAK8963()
        self.is_calibrating_mag = False
        self.mag_calibrated = True

    def calibrate_mpu(self):
        self.mpu9250.calibrateMPU6500()
        self.mpu_calibrated = True

    def stop_updating(self):
        self.updating = False

    def start_updating(self):
        # Calculate AHRS
        if self.updating:
            return False

        self.updating = True
        x = threading.Thread(target=self._update_loop, daemon=True)
        x.start()
        return True

    def _update_loop(self):
        filter = Madgwick(frequency=50, beta=0.1)
        # filter = Mahony()
        q = [1, 0, 0, 0]

        yaw_readings = deque([])
        yaw_buffer_size = 500

        while self.updating:
            accel = self.mpu9250.readAccelerometerMaster()
            gyro = list(map(lambda x: x * DEG2RAD, self.mpu9250.readGyroscopeMaster()))
            mag = self.mpu9250.readMagnetometerMaster()
            self.mag_heading_raw = math.atan2(-mag[1], mag[0]) * RAD2DEG
            q = filter.updateMARG(acc=accel, gyr=gyro, mag=[mag[0], -mag[1], mag[2]], q=q)

            attitude = q2euler(q)
            self.roll = attitude[0] * RAD2DEG
            self.pitch = attitude[1] * RAD2DEG

            # Strangely the sensor yaw is negative to the right. Let's invert that
            self.yaw = (attitude[2] * RAD2DEG)

            self.has_position = True
            # @TODO: Stability detection

            # Low pass filter for yaw readings
            # Also used to determine if the current yaw reading is 'stable' or not
            yaw_readings.append(self.yaw)
            if len(yaw_readings) >= yaw_buffer_size:
                yaw_readings.popleft()

                yaw_numpy = numpy.array(yaw_readings)
                self.yaw_smoothed = yaw_numpy.mean()
                self.position_stable = True if (yaw_numpy.std() < self.stability_threshold) else False
            else:
                self.position_stable = False

            time.sleep(0.0001)

        # We have stopped updating, reset everything back to zero/off
        self.has_position = False
        self.position_stable = False
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
