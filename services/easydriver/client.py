"""
An example gRPC Client for the EasyDriver Service
"""

import logging

import grpc

import easydriver_pb2
import easydriver_pb2_grpc


def get_status(stub):
    status = stub.GetStatus(easydriver_pb2.EmptyRequest())
    print(
        """
Status: current_position: %s
direction: %s
degrees_per_step: %s
enabled: %s
gear_ratio: %s
killswitch_left_on: %s
killswitch_right_on: %s
name: %s
steps_per_rev: %s
"""
        % (
            status.current_position,
            status.direction,
            status.degrees_per_step,
            status.enabled,
            status.gear_ratio,
            status.killswitch_left_on,
            status.killswitch_right_on,
            status.name,
            status.steps_per_rev,
        )
    )
    return status


def do_step_loop(stub):
    for x in range(0, 100):
        stub.StepForward(easydriver_pb2.EmptyRequest())
        print(get_status(stub))
    for x in range(0, 100):
        stub.StepReverse(easydriver_pb2.EmptyRequest())
        print(get_status(stub))


def run():
    with grpc.insecure_channel("localhost:50000") as channel:
        stub = easydriver_pb2_grpc.EasyDriverServiceStub(channel)
        print("-------------- GetStatus --------------")
        print(get_status(stub))

        stub.Enable(easydriver_pb2.EmptyRequest())
        stub.Wake(easydriver_pb2.EmptyRequest())

        stub.SetFullStep(easydriver_pb2.EmptyRequest())
        do_step_loop(stub)

        stub.SetHalfStep(easydriver_pb2.EmptyRequest())
        do_step_loop(stub)

        stub.SetQuarterStep(easydriver_pb2.EmptyRequest())
        do_step_loop(stub)

        stub.SetEighthStep(easydriver_pb2.EmptyRequest())
        do_step_loop(stub)

        stub.SetSixteenthStep(easydriver_pb2.EmptyRequest())
        do_step_loop(stub)

        stub.Sleep(easydriver_pb2.EmptyRequest())
        stub.Disable(easydriver_pb2.EmptyRequest())


if __name__ == "__main__":
    logging.basicConfig()
    run()
