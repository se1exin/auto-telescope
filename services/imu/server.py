import logging
import math
import threading
import time
from collections import deque
from concurrent import futures

import numpy
import grpc

import imu_pb2
import imu_pb2_grpc

from ahrs.common import DEG2RAD, RAD2DEG
from ahrs.common.orientation import q2euler
from ahrs.filters import Madgwick, Mahony
from mpu9250_jmdev.mpu_9250 import MPU9250
from mpu9250_jmdev.registers import *

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

class ImuServiceServicer(imu_pb2_grpc.ImuServiceServicer):
    def __init__(self):
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

        # Status Values
        self.is_updating = False
        self.has_position = False
        self.position_stable = False
        self.is_mag_calibrating = False
        self.mag_calibrated = False
        self.mpu_calibrated = False

        # Position Values
        self.roll_raw = 0.0
        self.pitch_raw = 0.0
        self.yaw_raw = 0.0
        self.roll_filtered = 0.0
        self.pitch_filtered = 0.0
        self.yaw_filtered = 0.0
        self.roll_smoothed = 0.0
        self.pitch_smoothed = 0.0

        # How many degrees of variance can be tolerated in stability detection?
        self.stability_threshold = 0.5

        # Manual Mag Calibration
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

    def _get_status(self):
        return imu_pb2.StatusResponse(
            is_updating=self.is_updating,
            has_position=self.has_position,
            position_stable=self.position_stable,
            is_mag_calibrating=self.is_mag_calibrating,
            mag_calibrated=self.mag_calibrated,
            mpu_calibrated=self.mpu_calibrated,
        )

    def GetStatus(self, request, context):
        logger.debug("GetStatus()")
        return self._get_status()

    def GetPosition(self, request, context):
        logger.debug("GetPosition()")
        return imu_pb2.PositionResponse(
            roll_raw=self.roll_raw,
            pitch_raw=self.pitch_raw,
            yaw_raw=self.yaw_raw,
            roll_filtered=self.roll_filtered,
            pitch_filtered=self.pitch_filtered,
            yaw_filtered=self.yaw_filtered,
            roll_smoothed=self.roll_smoothed,
            pitch_smoothed=self.pitch_smoothed,
            yaw_smoothed=self.yaw_smoothed,
        )

    def Configure(self, request, context):
        logger.debug("Configure()")
        self.mpu9250.configure()

    def CalibrateMag(self, request, context):
        logger.debug("CalibrateMag()")
        self.is_mag_calibrating = True
        self.mpu9250.calibrateAK8963()
        self.is_mag_calibrating = False
        self.mag_calibrated = True
        return self._get_status()

    def CalibrateMPU(self, request, context):
        logger.debug("CalibrateMPU()")
        self.mpu9250.calibrateMPU6500()
        self.mpu_calibrated = True
        return self._get_status()

    def StopUpdating(self, request, context):
        logger.debug("StopUpdating()")
        self.is_updating = False
        return self._get_status()

    def StartUpdating(self, request, context):
        logger.debug("StartUpdating()")
        if self.is_updating:
            return False

        x = threading.Thread(target=self._update_loop, daemon=True)
        x.start()
        return self._get_status()

    def _update_loop(self):
        logger.debug("Starting _update_loop")
        filter = Madgwick(frequency=50, beta=0.1)
        # filter = Mahony()
        q = [1, 0, 0, 0]

        yaw_readings = deque([])
        yaw_buffer_size = 500

        self.is_updating = True
        while self.is_updating:
            accel = self.mpu9250.readAccelerometerMaster()
            gyro = list(map(lambda x: x * DEG2RAD, self.mpu9250.readGyroscopeMaster()))
            mag = self.mpu9250.readMagnetometerMaster()
            self.yaw_raw = math.atan2(-mag[1], mag[0]) * RAD2DEG
            # @TODO: Roll and Pitch raw headings
            q = filter.updateMARG(acc=accel, gyr=gyro, mag=[mag[0], -mag[1], mag[2]], q=q)

            attitude = q2euler(q)
            self.roll_filtered = attitude[0] * RAD2DEG
            self.pitch_filtered = attitude[1] * RAD2DEG
            self.yaw_filtered = attitude[2] * RAD2DEG

            self.has_position = True

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

            # @TODO: Roll and Pitch smoothed headings

            time.sleep(0.0001)

        # We have stopped updating, reset everything back to zero/off
        self.has_position = False
        self.position_stable = False
        self.roll_raw = 0.0
        self.pitch_raw = 0.0
        self.yaw_raw = 0.0
        self.roll_filtered = 0.0
        self.pitch_filtered = 0.0
        self.yaw_filtered = 0.0
        self.roll_smoothed = 0.0
        self.pitch_smoothed = 0.0


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    imu_pb2_grpc.add_ImuServiceServicer_to_server(ImuServiceServicer(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    logger.info("Starting IMU Service")
    serve()
