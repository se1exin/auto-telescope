"""
An example gRPC Client for the IMU Service
"""

import logging
import time

import grpc
import imu_pb2
import imu_pb2_grpc


def get_status(stub):
    status = stub.GetStatus(imu_pb2.EmptyRequest())
    print(
        """======== Status ===========
is_updating: %s
has_position: %s
position_stable %s
is_mag_calibrating %s
mag_calibrated %s
mpu_calibrated %s"""
        % (
            status.is_updating,
            status.has_position,
            status.position_stable,
            status.is_mag_calibrating,
            status.mag_calibrated,
            status.mpu_calibrated,
        )
    )
    return status


def get_position(stub):
    position = stub.GetPosition(imu_pb2.EmptyRequest())
    print(
        """======== Position ========
roll_raw: %s
pitch_raw: %s
yaw_raw: %s
roll_filtered: %s
pitch_filtered: %s
yaw_filtered: %s
roll_smoothed: %s
pitch_smoothed: %s
yaw_smoothed: %s"""
        % (
            position.roll_raw,
            position.pitch_raw,
            position.yaw_raw,
            position.roll_filtered,
            position.pitch_filtered,
            position.yaw_filtered,
            position.roll_smoothed,
            position.pitch_smoothed,
            position.yaw_smoothed,
        )
    )
    return position


def start_updating(stub):
    stub.StartUpdating(imu_pb2.EmptyRequest())


def stop_updating(stub):
    stub.StopUpdating(imu_pb2.EmptyRequest())


def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = imu_pb2_grpc.ImuServiceStub(channel)
        print("-------------- GetStatus --------------")
        status = get_status(stub)
        print(repr(status))

        if not status.mpu_calibrated:
            stub.CalibrateMPU(imu_pb2.EmptyRequest())
            stub.Configure(imu_pb2.EmptyRequest())

        if not status.is_updating and not status.has_position:
            print("-------------- StartUpdating --------------")
            start_updating(stub)

            status = get_status(stub)

        print("-------------- GetPosition --------------")
        while True:
            get_position(stub)
            time.sleep(1)


if __name__ == "__main__":
    logging.basicConfig()
    run()
