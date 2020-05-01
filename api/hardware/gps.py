import threading

import serial
import pynmea2


class GPS(object):
    def __init__(self, serial_address="/dev/ttyS0"):
        self.serial_address = serial_address
        self.latitude = 0
        self.longitude = 0
        self.has_position = False
        self.updating = False

    def stop_updating(self):
        self.updating = False

    def start_updating(self):
        if self.updating:
            return

        self.updating = True
        x = threading.Thread(target=self._update_loop, daemon=True)
        x.start()
        return True

    def _update_loop(self):
        serial_port = serial.Serial(self.serial_address, 9600, timeout=0.5)
        while self.updating:
            result = str(serial_port.readline(), 'utf-8')
            if result.find('GGA') > 0:
                msg = pynmea2.parse(result)
                self.latitude = msg.latitude
                self.longitude = msg.longitude
                self.has_position = True
        serial_port.close()
