import logging
import os
from concurrent import futures

import easydriver_pb2
import easydriver_pb2_grpc
import grpc
from easydriver import EasyDriver

logger = logging.getLogger(__name__)
logger.setLevel(os.environ.get("LOG_LEVEL", logging.DEBUG))
ch = logging.StreamHandler()
ch.setLevel(os.environ.get("LOG_LEVEL", logging.DEBUG))
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

SERVICE_PORT = 50000


class EasyDriverServiceServicer(easydriver_pb2_grpc.EasyDriverServiceServicer):
    def __init__(self):
        self.stepper = EasyDriver(
            pin_step=int(os.environ.get("PIN_STEP", -1)),
            delay=float(os.environ.get("DELAY", 1.1)),
            pin_direction=int(os.environ.get("PIN_DIRECTION", -1)),
            pin_ms1=int(os.environ.get("PIN_MS1", -1)),
            pin_ms2=int(os.environ.get("PIN_MS2", -1)),
            pin_ms3=int(os.environ.get("PIN_MS3", -1)),
            pin_sleep=int(os.environ.get("PIN_SLEEP", -1)),
            pin_enable=int(os.environ.get("PIN_ENABLE", -1)),
            pin_reset=int(os.environ.get("PIN_RESET", -1)),
            pin_killswitch_left=int(os.environ.get("PIN_KILLSWITCH_LEFT", -1)),
            pin_killswitch_right=int(os.environ.get("PIN_KILLSWITCH_RIGHT", -1)),
            pin_killswitch_power=int(os.environ.get("PIN_KILLSWITCH_POWER", -1)),
            gear_ratio=float(os.environ.get("GEAR_RATIO", 1)),
            base_steps_per_rev=int(os.environ.get("BASE_STEPS_PER_REV", 200)),
            name=os.environ.get("NAME", "Stepper"),
        )

    def GetStatus(self, request, context):
        logger.debug("GetStatus()")
        return easydriver_pb2.StatusResponse(
            enabled=self.stepper.enabled,
            direction=self.stepper.direction,
            degrees_per_step=self.stepper.degrees_per_step,
            current_position=self.stepper.current_position,
            killswitch_left_on=self.stepper.killswitch_left_on(),
            killswitch_right_on=self.stepper.killswitch_right_on(),
            name=self.stepper.name,
            steps_per_rev=self.stepper.steps_per_rev,
            gear_ratio=self.stepper.gear_ratio,
        )

    def StepForward(self, request, context):
        logger.debug("StepForward()")
        return easydriver_pb2.PositionResponse(
            current_position=self.stepper.step_forward()
        )

    def StepReverse(self, request, context):
        logger.debug("StepReverse()")
        return easydriver_pb2.PositionResponse(
            current_position=self.stepper.step_reverse()
        )

    def Disable(self, request, context):
        logger.debug("Disable()")
        self.stepper.disable()
        return easydriver_pb2.EmptyResponse()

    def Enable(self, request, context):
        logger.debug("Enable()")
        self.stepper.enable()
        return easydriver_pb2.EmptyResponse()

    def Sleep(self, request, context):
        logger.debug("Sleep()")
        self.stepper.sleep()
        return easydriver_pb2.EmptyResponse()

    def Wake(self, request, context):
        logger.debug("Wake()")
        self.stepper.wake()
        return easydriver_pb2.EmptyResponse()

    def Reset(self, request, context):
        logger.debug("Reset()")
        self.stepper.reset()
        return easydriver_pb2.EmptyResponse()

    def SetFullStep(self, request, context):
        logger.debug("SetFullStep()")
        self.stepper.set_full_step()
        return easydriver_pb2.EmptyResponse()

    def SetHalfStep(self, request, context):
        logger.debug("SetHalfStep()")
        self.stepper.set_half_step()
        return easydriver_pb2.EmptyResponse()

    def SetQuarterStep(self, request, context):
        logger.debug("SetQuarterStep()")
        self.stepper.set_quarter_step()
        return easydriver_pb2.EmptyResponse()

    def SetEighthStep(self, request, context):
        logger.debug("SetEightStep()")
        self.stepper.set_eighth_step()
        return easydriver_pb2.EmptyResponse()

    def SetSixteenthStep(self, request, context):
        logger.debug("SetSixteenthStep()")
        self.stepper.set_sixteenth_step()
        return easydriver_pb2.EmptyResponse()


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    easydriver_pb2_grpc.add_EasyDriverServiceServicer_to_server(
        EasyDriverServiceServicer(), server
    )
    server.add_insecure_port("[::]:%s" % SERVICE_PORT)
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    logger.info("Starting EasyDriver Service: %s" % os.environ.get("NAME", "Stepper"))
    serve()
