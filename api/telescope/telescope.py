import threading
import time

import gps_pb2
import gps_pb2_grpc
import grpc
import imu_pb2
import imu_pb2_grpc
from hardware.easydriver import EasyDriver
from skyfield.api import load
from skyfield.toposlib import Topos

GPS_SERVICE_ADDRESS = "gps-service:50000"
IMU_SERVICE_ADDRESS = "imu-service:50000"

IMU_STABILITY_THRESHOLD = 0.5  # @TODO: This currently matches the value in imu service. Need to make customisable.


class Telescope(object):
    def __init__(self):
        # Init hardware devices
        self.stepper = EasyDriver(
            pin_step=26,
            pin_direction=19,
            pin_ms1=6,
            pin_ms2=5,
            pin_sleep=13,
            pin_enable=0,
            #pin_reset=11,
            delay=0.001,
            gear_ratio=18,
        )

        # Gear ratio of X axis gear system
        self.gear_ratio_x = 18  # to 18:1
        self.moving_to_target = False
        self.target_found = False
        self.target_position_x = 0.0
        self.target_position_y = 0.0

        self.started = False
        self.target_object = ""

    def start(self):
        if not self.started:
            self.imu_configure()
            self.imu_calibrate()
            self.imu_start()
            self.gps_start()
            self.stepper.disable()
            self.started = True
        return self.status()

    def status(self):
        # Overall status of all sensors and positions
        gps_status = self.gps_status()
        gps_position = self.gps_position()
        imu_status = self.imu_status()
        imu_position = self.imu_position()

        gps = {
            "latitude": gps_position.latitude,
            "longitude": gps_position.longitude,
            "declination": gps_position.declination,
            "is_updating": gps_status.is_updating,
            "has_position": gps_status.has_position,
        }

        imu = {
            "is_updating": imu_status.is_updating,
            "has_position": imu_status.has_position,
            "position_stable": imu_status.position_stable,
            "mag_calibrated": imu_status.mag_calibrated,
            "mpu_calibrated": imu_status.mpu_calibrated,
            "imu_calibrated": imu_status.mag_calibrated and imu_status.mpu_calibrated,
            "roll_raw": imu_position.roll_raw,
            "pitch_raw": imu_position.pitch_raw,
            "yaw_raw": imu_position.yaw_raw + gps_position.declination,
            "roll_filtered": imu_position.roll_filtered,
            "pitch_filtered": imu_position.pitch_filtered,
            "yaw_filtered": self._normalise_yaw(imu_position.yaw_filtered),
            "roll_smoothed": imu_position.roll_smoothed,
            "pitch_smoothed": imu_position.pitch_smoothed,
            "yaw_smoothed": self._normalise_yaw(imu_position.yaw_smoothed),
        }

        return {
            "started": self.started,
            "moving_to_target": self.moving_to_target,
            "target_found": self.target_found,
            "target_position_x": self.target_position_x,
            "target_position_y": self.target_position_y,
            "stepper_position": self.stepper.current_position % 360,
            "gps": gps,
            "imu": imu,
        }

    # IMU functions
    def imu_configure(self):
        with grpc.insecure_channel(IMU_SERVICE_ADDRESS) as channel:
            stub = imu_pb2_grpc.ImuServiceStub(channel)
            stub.Configure(imu_pb2.EmptyRequest())

    def imu_calibrate(self):
        """
        Calibrates the Mag and Accel/Gyro sensors
        """
        self.imu_stop()

        # To calibrate the mag we need to move the sensor around.
        # The best we can do is just spin the motor as fast as we can during calibration
        # self.stepper.enable()
        # self.stepper.set_full_step()
        #
        # # Start calibration in another thread so we can rotate the motor in this thread.
        # x = threading.Thread(target=self.imu.calibrate_mag)
        # x.start()
        #
        # while self.imu.is_calibrating_mag:
        #     self.stepper.step_forward()
        #     time.sleep(0.001)
        #
        # # Mag calibration complete
        # self.stepper.disable()
        #
        # # The rest of the sensors (accel, gyro) must be calibrated while not moving
        # time.sleep(1)
        self.imu_calibrate_mpu()

        # Calibration function resets the sensors, so we need to reconfigure them
        self.imu_configure()

    def imu_calibrate_mag(self):
        with grpc.insecure_channel(IMU_SERVICE_ADDRESS) as channel:
            stub = imu_pb2_grpc.ImuServiceStub(channel)
            return stub.CalibrateMag(imu_pb2.EmptyRequest())

    def imu_calibrate_mpu(self):
        with grpc.insecure_channel(IMU_SERVICE_ADDRESS) as channel:
            stub = imu_pb2_grpc.ImuServiceStub(channel)
            return stub.CalibrateMPU(imu_pb2.EmptyRequest())

    def imu_start(self):
        with grpc.insecure_channel(IMU_SERVICE_ADDRESS) as channel:
            stub = imu_pb2_grpc.ImuServiceStub(channel)
            return stub.StartUpdating(imu_pb2.EmptyRequest())

    def imu_stop(self):
        with grpc.insecure_channel(IMU_SERVICE_ADDRESS) as channel:
            stub = imu_pb2_grpc.ImuServiceStub(channel)
            return stub.StopUpdating(imu_pb2.EmptyRequest())

    def imu_status(self):
        with grpc.insecure_channel(IMU_SERVICE_ADDRESS) as channel:
            stub = imu_pb2_grpc.ImuServiceStub(channel)
            return stub.GetStatus(imu_pb2.EmptyRequest())

    def imu_position(self):
        with grpc.insecure_channel(IMU_SERVICE_ADDRESS) as channel:
            stub = imu_pb2_grpc.ImuServiceStub(channel)
            return stub.GetPosition(imu_pb2.EmptyRequest())

    # GPS Functions
    def gps_start(self):
        with grpc.insecure_channel(GPS_SERVICE_ADDRESS) as channel:
            stub = gps_pb2_grpc.GpsServiceStub(channel)
            stub.StartUpdating(gps_pb2.StartRequest(stop_when_found=True))

    def gps_stop(self):
        with grpc.insecure_channel(GPS_SERVICE_ADDRESS) as channel:
            stub = gps_pb2_grpc.GpsServiceStub(channel)
            stub.StopUpdating(gps_pb2.EmptyRequest())

    def gps_status(self):
        with grpc.insecure_channel(GPS_SERVICE_ADDRESS) as channel:
            stub = gps_pb2_grpc.GpsServiceStub(channel)
            return stub.GetStatus(gps_pb2.EmptyRequest())

    def gps_position(self):
        with grpc.insecure_channel(GPS_SERVICE_ADDRESS) as channel:
            stub = gps_pb2_grpc.GpsServiceStub(channel)
            return stub.GetPosition(gps_pb2.EmptyRequest())

    def move_to_astronomical_object(self, object_name):
        if not object_name:
            raise Exception("Please provide valid object_name.")

        if not self.started:
            raise Exception("Telescope has not been initialised.")

        if not self.gps_status().has_position:
            raise Exception("Cannot target object without GPS position.")

        if self.moving_to_target:
            raise Exception("Another object is currently being targeted.")

        try:
            ts = load.timescale()
            t = ts.now()

            planets = load("de421.bsp")
            earth, target_planet = planets["earth"], planets[object_name]

            gps_position = self.gps_position()

            current_pos = earth + Topos(
                latitude_degrees=gps_position.latitude,
                longitude_degrees=gps_position.longitude,
            )
            current_pos_time = current_pos.at(t)

            alt, az, d = current_pos_time.observe(target_planet).apparent().altaz()
        except Exception as ex:
            raise ex

        self.move_to_position(az.degrees, method="stepper")
        return {
            "x": az.degrees,
            "y": alt.degrees,
        }

    def cancel_move_to_position(self):
        self.moving_to_target = False
        self.target_found = False

    def move_to_position(self, position, method="compass"):
        if method == "compass":
            return self.move_to_compass_position(position)
        else:
            # Use the stepper step count rather than the compass to find the target
            result = self.move_to_compass_position(0)
            degrees = Telescope.degrees_between_points(
                self.stepper.current_position, position
            )
            self.target_position_x = position
            self.rotate_stepper_by_degrees(degrees, variable_speed=False)
            return result

    def move_to_compass_position(
        self, position, allowed_error_margin=IMU_STABILITY_THRESHOLD
    ):
        if self.moving_to_target:
            return False

        self.target_position_x = position

        # Mag algorithm can take a few seconds to stabilise after movement
        # To move to the target position, we first move to an estimated position,
        # then wait for stabilisation and see how far off we are.
        # We keep doing this until we hit the target
        self.moving_to_target = True
        self.target_found = False

        while self.moving_to_target:
            while not self.imu_status().position_stable:
                if not self.moving_to_target:
                    break  # Don't block cancellation requests
                time.sleep(0.1)

            mag_pos = self._normalise_yaw(self.imu_position().yaw_smoothed)
            degrees = self.degrees_between_points(mag_pos, position)

            self.stepper.current_position = mag_pos

            print("Are we there yet?", mag_pos, position, degrees, abs(degrees))
            if abs(degrees) > allowed_error_margin:
                self.rotate_stepper_by_degrees(degrees)
            else:
                break

        self.moving_to_target = False
        self.target_found = True
        return True

    def rotate_stepper_by_degrees(self, degrees, variable_speed=True):
        degrees_abs = abs(degrees)

        self.stepper.enable()
        # As the distance gets smaller, slow down the motor speed and time between rotation/stabilisation attempts
        if degrees_abs < 15 or not variable_speed:
            self.stepper.set_eighth_step()
        elif degrees_abs < 60:
            self.stepper.set_quarter_step()
        elif degrees_abs < 90:
            self.stepper.set_half_step()
        else:
            self.stepper.set_full_step()

        num_steps_required = degrees_abs / self.stepper.degrees_per_step()

        for i in range(0, int(num_steps_required)):
            if degrees < 0:
                self.stepper.step_reverse()
            else:
                self.stepper.step_forward()

        self.stepper.disable()

    def _normalise_yaw(self, yaw):
        # Yaw is from -180 to +180. 0 == North.
        # Convert to 0 -> 360 degrees
        yaw += self.gps_position().declination
        if yaw < 0:
            return 360 - abs(yaw)
        return yaw

    @staticmethod
    def degrees_between_points(current_pos, target_pos):
        """
        Calculate the shortest distance between two points on a circle
        """
        distance = (360 - current_pos) - (360 - target_pos)
        # We can go both clockwise and anti-clockwise. Find the faster way to our target.
        if distance < -180:
            distance = 360 - abs(distance)
        elif distance > 180:
            distance = distance - 360
        return distance
