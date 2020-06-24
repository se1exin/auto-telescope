import easydriver_pb2
import easydriver_pb2_grpc
import grpc


class Stepper(object):
    def __init__(self, service_address):
        self.service_address = service_address

    def status(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = easydriver_pb2_grpc.EasyDriverServiceStub(channel)
            return stub.GetStatus(easydriver_pb2.EmptyRequest())

    def disable(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = easydriver_pb2_grpc.EasyDriverServiceStub(channel)
            return stub.Disable(easydriver_pb2.EmptyRequest())

    def enable(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = easydriver_pb2_grpc.EasyDriverServiceStub(channel)
            return stub.Enable(easydriver_pb2.EmptyRequest())

    def sleep(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = easydriver_pb2_grpc.EasyDriverServiceStub(channel)
            return stub.Sleep(easydriver_pb2.EmptyRequest())

    def wake(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = easydriver_pb2_grpc.EasyDriverServiceStub(channel)
            return stub.Wake(easydriver_pb2.EmptyRequest())

    def step_forward(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = easydriver_pb2_grpc.EasyDriverServiceStub(channel)
            return stub.StepForward(easydriver_pb2.EmptyRequest())

    def step_reverse(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = easydriver_pb2_grpc.EasyDriverServiceStub(channel)
            return stub.StepReverse(easydriver_pb2.EmptyRequest())

    def set_full_step(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = easydriver_pb2_grpc.EasyDriverServiceStub(channel)
            return stub.SetFullStep(easydriver_pb2.EmptyRequest())

    def set_half_step(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = easydriver_pb2_grpc.EasyDriverServiceStub(channel)
            return stub.SetHalfStep(easydriver_pb2.EmptyRequest())

    def set_quarter_step(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = easydriver_pb2_grpc.EasyDriverServiceStub(channel)
            return stub.SetQuarterStep(easydriver_pb2.EmptyRequest())

    def set_eighth_step(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = easydriver_pb2_grpc.EasyDriverServiceStub(channel)
            return stub.SetEighthStep(easydriver_pb2.EmptyRequest())

    def set_sixteenth_step(self):
        with grpc.insecure_channel(self.service_address) as channel:
            stub = easydriver_pb2_grpc.EasyDriverServiceStub(channel)
            return stub.SetSixteenthStep(easydriver_pb2.EmptyRequest())
