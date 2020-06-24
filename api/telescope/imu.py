import grpc
import imu_pb2
import imu_pb2_grpc


class IMU(object):
    def __init__(self, service_address):
        self.service_address = service_address

    def configure(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = imu_pb2_grpc.ImuServiceStub(channel)
            stub.Configure(imu_pb2.EmptyRequest())

    def calibrate(self):
        """
        Calibrates the Mag and Accel/Gyro sensors
        """
        self.stop()

        self.calibrate_mpu()

        # Calibration function resets the sensors, so we need to reconfigure them
        self.configure()

    def calibrate_mag(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = imu_pb2_grpc.ImuServiceStub(channel)
            return stub.CalibrateMag(imu_pb2.EmptyRequest())

    def calibrate_mpu(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = imu_pb2_grpc.ImuServiceStub(channel)
            return stub.CalibrateMPU(imu_pb2.EmptyRequest())

    def start(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = imu_pb2_grpc.ImuServiceStub(channel)
            return stub.StartUpdating(imu_pb2.EmptyRequest())

    def stop(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = imu_pb2_grpc.ImuServiceStub(channel)
            return stub.StopUpdating(imu_pb2.EmptyRequest())

    def status(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = imu_pb2_grpc.ImuServiceStub(channel)
            return stub.GetStatus(imu_pb2.EmptyRequest())

    def position(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = imu_pb2_grpc.ImuServiceStub(channel)
            return stub.GetPosition(imu_pb2.EmptyRequest())
