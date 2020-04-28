import sys

from ahrs.common import DEG2RAD, RAD2DEG
from ahrs.common.orientation import q2euler

sys.path.append("")

import time
from ahrs.filters import Madgwick
from mpu9250_jmdev.registers import *
from mpu9250_jmdev.mpu_9250 import MPU9250


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
            mode=AK8963_MODE_C100HZ)

        self.is_calibrating_mag = False
        self.updating = False

        self.mpu9250.magBias = [20.7454594017094,
                                10.134935897435899,
                                -11.132967032967032]
        self.mpu9250.magScale = [1.0092850510677809,
                                1.0352380952380953,
                                0.9585537918871252]

        self.roll = 0.0
        self.pitch = 0.0
        self.yaw = 0.0

    def configure(self):
        self.mpu9250.configure()

    def calibrate_mag(self):
        self.is_calibrating_mag = True
        self.mpu9250.calibrateAK8963()
        self.is_calibrating_mag = False

    def calibrate_mpu(self):
        self.mpu9250.calibrateMPU6500()

    def stop_updating(self):
        self.updating = False

    def start_updating(self):
        # Calculate AHRS
        if self.updating:
            return

        self.updating = True
        madgwick = Madgwick(frequency=50, beta=1)
        q = [1, 0, 0, 0]
        while self.updating:
            accel = self.mpu9250.readAccelerometerMaster()
            gyro = list(map(lambda x: x * DEG2RAD, self.mpu9250.readGyroscopeMaster()))
            mag = self.mpu9250.readMagnetometerMaster()
            q = madgwick.updateMARG(acc=accel, gyr=gyro, mag=mag, q=q)

            attitude = q2euler(q)
            self.roll = attitude[0] * RAD2DEG
            self.pitch = attitude[1] * RAD2DEG
            self.yaw = attitude[2] * RAD2DEG

            print(self.yaw)

            # print("roll %f, pitch %f, yaw %f" % (self.roll, self.pitch, self.yaw))
            time.sleep(0.02)

    def get_accel(self):
        data = self.mpu9250.readAccelerometerMaster()
        return {
            'x': data[0],
            'y': data[1],
            'z': data[2],
        }

    def get_gyro(self):
        data = self.mpu9250.readGyroscopeMaster()
        return {
            'x': data[0],
            'y': data[1],
            'z': data[2],
        }

    def get_mag(self):
        data = self.mpu9250.readMagnetometerMaster()
        return {
            'x': data[0],
            'y': data[1],
            'z': data[2],
        }

    def get_position(self):
        return {
            'mag': self.get_mag(),
            'gyro': self.get_gyro(),
            'accel': self.get_accel()
        }


