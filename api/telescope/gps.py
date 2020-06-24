import gps_pb2
import gps_pb2_grpc
import grpc


class GPS(object):
    def __init__(self, service_address):
        self.service_address = service_address

    def start(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = gps_pb2_grpc.GpsServiceStub(channel)
            stub.StartUpdating(gps_pb2.StartRequest(stop_when_found=True))

    def stop(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = gps_pb2_grpc.GpsServiceStub(channel)
            stub.StopUpdating(gps_pb2.EmptyRequest())

    def status(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = gps_pb2_grpc.GpsServiceStub(channel)
            return stub.GetStatus(gps_pb2.EmptyRequest())

    def position(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = gps_pb2_grpc.GpsServiceStub(channel)
            return stub.GetPosition(gps_pb2.EmptyRequest())
