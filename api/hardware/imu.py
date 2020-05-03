import threading
import time
from collections import deque

from ahrs.common import DEG2RAD, RAD2DEG
from ahrs.common.orientation import q2euler
from ahrs.filters import Madgwick
from mpu9250_jmdev.mpu_9250 import MPU9250
from mpu9250_jmdev.registers import *


class IMU(object):
    is_calibrating_mag = False

    def __init__(self):
        self.mpu9250 = MPU9250(
            address_ak=AK8963_ADDRESS,
            address_mpu_master=MPU9050_ADDRESS_68,
            address_mpu_slave=None,
            bus=1,
            gfs=GFS_1000,
            afs=AFS_8G,
            mfs=AK8963_BIT_16,
            mode=AK8963_MODE_C100HZ,
        )

        self.is_calibrating_mag = False
        self.mag_calibrated = False
        self.mpu_calibrated = False
        self.updating = False

        self.mpu9250.magBias = [
            20.7454594017094,
            10.134935897435899,
            -11.132967032967032,
        ]
        self.mpu9250.magScale = [
            1.0092850510677809,
            1.0352380952380953,
            0.9585537918871252,
        ]

        self.has_position = False
        self.position_stable = False  # @TODO: Implement stability detection
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
        self.yaw_smoothed = 0.0

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
        madgwick = Madgwick(frequency=50, beta=1)
        q = [1, 0, 0, 0]

        yaw_readings = deque([])
        yaw_buffer_size = 500

        while self.updating:
            accel = self.mpu9250.readAccelerometerMaster()
            gyro = list(map(lambda x: x * DEG2RAD, self.mpu9250.readGyroscopeMaster()))
            mag = self.mpu9250.readMagnetometerMaster()
            q = madgwick.updateMARG(acc=accel, gyr=gyro, mag=mag, q=q)

            attitude = q2euler(q)
            self.roll = attitude[0] * RAD2DEG
            self.pitch = attitude[1] * RAD2DEG

            # Strangely the sensor yaw is negative to the right. Let's invert that
            self.yaw = -(attitude[2] * RAD2DEG)

            self.has_position = True
            # @TODO: Stability detection

            # Low pass filter for yaw readings
            # Also used to determine if the current yaw reading is 'stable' or not
            yaw_readings.append(self.yaw)
            if len(yaw_readings) >= yaw_buffer_size:
                yaw_readings.popleft()
                yaw_sum = 0
                yaw_diff = self.yaw
                for reading in yaw_readings:
                    yaw_sum += reading
                    yaw_diff -= reading

                average = yaw_sum / yaw_buffer_size
                self.yaw_smoothed = average
                diff = self.yaw - average
                self.position_stable = True if (diff < 0.5) else False
                # print(diff, self.yaw, average)
            else:
                self.position_stable = False

            time.sleep(0.001)

        # We have stopped updating, reset everything back to zero/off
        self.has_position = False
        self.position_stable = False
        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0
