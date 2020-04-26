import sys
sys.path.append("")

import time
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

    def configure(self):
        self.mpu9250.configure()

    def calibrate_mag(self):
        self.is_calibrating_mag = True
        self.mpu9250.calibrateAK8963()
        self.is_calibrating_mag = False

    def calibrate_mpu(self):
        self.mpu9250.calibrateMPU6500()

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
