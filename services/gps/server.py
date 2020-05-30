import datetime
import logging
import threading
from concurrent import futures

import grpc

import gps_pb2
import gps_pb2_grpc
import pyIGRF
import pynmea2
import serial

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

SERVICE_PORT = 50000


class GpsServiceServicer(gps_pb2_grpc.GpsServiceServicer):
    def __init__(self):
        self.latitude = 0
        self.longitude = 0
        self.has_position = False
        self.is_updating = False
        self.declination = 0.0
        self.serial_port = serial.Serial("/dev/ttyS0", 9600, timeout=0.5)

    def _get_status(self):
        return gps_pb2.StatusResponse(
            is_updating=self.is_updating, has_position=self.has_position
        )

    def GetStatus(self, request, context):
        logger.debug("GetStatus()")
        return self._get_status()

    def GetPosition(self, request, context):
        logger.debug("GetPosition()")
        return gps_pb2.PositionResponse(
            latitude=self.latitude,
            longitude=self.longitude,
            declination=self.declination,
        )

    def StartUpdating(self, request, context):
        logger.debug("StartUpdating()")
        if not self.is_updating:
            x = threading.Thread(
                target=self._update_loop, args=(request.stop_when_found,), daemon=True
            )
            x.start()
        return self._get_status()

    def StopUpdating(self, request, context):
        logger.debug("StopUpdating()")
        self.is_updating = False
        return self._get_status()

    def _update_loop(self, stop_when_found=False):
        self.is_updating = True
        logger.debug("Starting _update_loop")
        while self.is_updating:
            try:
                result = str(self.serial_port.readline(), "utf-8")
                logger.debug("Got message from GPS: %s" % result)
                if result.find("GGA") > 0:
                    msg = pynmea2.parse(result)
                    self.latitude = msg.latitude
                    self.longitude = msg.longitude

                    now = datetime.datetime.now()

                    igrf = pyIGRF.igrf_value(
                        self.latitude, self.longitude, msg.altitude, now.year
                    )
                    self.declination = igrf[0]

                    logger.debug(
                        "Position Update: latitude: %s, longitude: %s, declination: %s"
                        % (self.latitude, self.longitude, self.declination)
                    )

                    self.has_position = True

                    if stop_when_found:
                        # Now we have a lock, just exit to free up resources
                        self.is_updating = False
                        logger.info(
                            "Position found and stop_when_found set. Exiting _update_loop"
                        )

            except Exception as ex:
                logger.error(ex)


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    gps_pb2_grpc.add_GpsServiceServicer_to_server(GpsServiceServicer(), server)
    server.add_insecure_port("[::]:%s" % SERVICE_PORT)
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    logger.info("Starting GPS Service")
    serve()
