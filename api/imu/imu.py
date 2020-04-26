import sys
sys.path.append("")

import time
from MPU9250.mpu9250 import MPU9250


class IMU(object):

    def __init__(self):
        self.mpu9250 = MPU9250()
        self.is_calibrating_mag = False
        self.yaw = 0.0
        self.pitch = 0.0
        self.roll = 0.0
        self.updating = False

    def init(self):
        self.mpu9250.initMPU9250()
        print("MPU9250 initialized for active data mode....")
        self.mpu9250.initAK8963()
        print("AK8963 initialized for active data mode....")

    def calibrate_mag(self):
        self.is_calibrating_mag = True
        self.mpu9250.magCalMPU9250()
        self.is_calibrating_mag = False

    def calibrate_mpu(self):
        self.mpu9250.calibrateMPU9250()

    def get_position(self):
        return {
            'yaw': self.yaw,
            'pitch': self.pitch,
            'roll': self.roll,
        }

    def update(self):
        self.updating = True
        while True:
            try:
                self.mpu9250.update()
                result = self.mpu9250.euler
                self.roll = result[0]
                self.pitch = result[1]
                self.yaw = result[2]
            except:
                pass