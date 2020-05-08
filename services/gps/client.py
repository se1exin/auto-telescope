"""
An example gRPC Client for the GPS Service
"""

import logging

import grpc

import gps_pb2
import gps_pb2_grpc


def get_status(stub):
    status = stub.GetStatus(gps_pb2.EmptyRequest())
    print(
        "Status: is_updating: %s, has_position: %s"
        % (status.is_updating, status.has_position)
    )
    return status


def get_position(stub):
    position = stub.GetPosition(gps_pb2.EmptyRequest())
    print(
        "Position: latitude: %s, longitude: %s, declination: %s"
        % (position.latitude, position.longitude, position.declination)
    )
    return position


def start_updating(stub):
    request = gps_pb2.StartRequest(stop_when_found=True)
    stub.StartUpdating(request)


def stop_updating(stub):
    stub.StopUpdating(gps_pb2.EmptyRequest())


def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = gps_pb2_grpc.GpsServiceStub(channel)
        print("-------------- GetStatus --------------")
        status = get_status(stub)
        print(repr(status))

        if not status.is_updating and not status.has_position:
            print("-------------- StartUpdating --------------")
            start_updating(stub)

            status = get_status(stub)

        print("-------------- GetPosition --------------")
        get_position(stub)


if __name__ == "__main__":
    logging.basicConfig()
    run()
