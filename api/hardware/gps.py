import datetime
import threading

import serial

import pyIGRF
import pynmea2

now = datetime.datetime.now()


class GPS(object):
    def __init__(self, serial_address="/dev/ttyS0"):
        self.serial_address = serial_address
        self.latitude = 0
        self.longitude = 0
        self.has_position = False
        self.updating = False
        self.declination = 0.0  # @TODO: Implement (using pyIGRF library)

    def stop_updating(self):
        self.updating = False

    def start_updating(self):
        if self.updating:
            return False

        self.updating = True
        x = threading.Thread(target=self._update_loop, daemon=True)
        x.start()
        return True

    def _update_loop(self):
        serial_port = serial.Serial(self.serial_address, 9600, timeout=0.5)
        while self.updating:
            try:
                result = str(serial_port.readline(), "utf-8")
                # print(result)
                if result.find("GGA") > 0:
                    msg = pynmea2.parse(result)
                    self.latitude = msg.latitude
                    self.longitude = msg.longitude

                    igrf = pyIGRF.igrf_value(
                        self.latitude, self.longitude, msg.altitude, now.year
                    )
                    self.declination = igrf[0]

                    self.has_position = True

                    # Now we have a lock, just exit to free up resources
                    self.updating = False

            except Exception as ex:
                # print(ex)
                pass

        serial_port.close()
