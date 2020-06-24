import threading
import time

from skyfield.api import load
from skyfield.toposlib import Topos

from telescope.gps import GPS
from telescope.imu import IMU
from telescope.stepper import Stepper

GPS_SERVICE_ADDRESS = "gps-service:50000"
IMU_SERVICE_ADDRESS = "imu-service:50000"
STEPPER_X_SERVICE_ADDRESS = "stepper-x-service:50000"
STEPPER_Y_SERVICE_ADDRESS = "stepper-y-service:50000"

IMU_STABILITY_THRESHOLD = 0.5  # @TODO: This currently matches the value in imu service. Need to make customisable.


class Telescope(object):
    def __init__(self):
        self.gps = GPS(GPS_SERVICE_ADDRESS)
        self.imu = IMU(IMU_SERVICE_ADDRESS)
        self.stepper_x = Stepper(STEPPER_X_SERVICE_ADDRESS)
        self.stepper_y = Stepper(STEPPER_Y_SERVICE_ADDRESS)

        self.moving_to_target = False
        self.target_found = False
        self.target_position_x = 0.0
        self.target_position_y = 0.0

        self.started = False
        self.target_object = ""

    def start(self):
        if not self.started:
            self.imu.configure()
            self.imu.calibrate()
            self.imu.start()
            self.gps.start()
            self.stepper_x.wake()
            self.stepper_y.wake()
            self.stepper_x.disable()
            self.stepper_y.disable()
            self.started = True
        return self.status()

    def status(self):
        # Overall status of all sensors and positions
        gps_status = self.gps.status()
        gps_position = self.gps.position()
        imu_status = self.imu.status()
        imu_position = self.imu.position()

        stepper_x_status = self.stepper_x.status()
        stepper_y_status = self.stepper_y.status()

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

        stepper_x = {
            "current_position": stepper_x_status.current_position,
            "position_normalised": stepper_x_status.current_position % 360,
            "direction": stepper_x_status.direction,
            "degrees_per_step": stepper_x_status.degrees_per_step,
            "enabled": stepper_x_status.enabled,
            "gear_ratio": stepper_x_status.gear_ratio,
            "killswitch_left_on": stepper_x_status.killswitch_left_on,
            "killswitch_right_on": stepper_x_status.killswitch_right_on,
            "name": stepper_x_status.name,
            "sleeping": stepper_x_status.sleeping,
            "steps_per_rev": stepper_x_status.steps_per_rev,
        }

        stepper_y = {
            "current_position": stepper_y_status.current_position,
            "position_normalised": stepper_y_status.current_position % 360,
            "direction": stepper_y_status.direction,
            "degrees_per_step": stepper_y_status.degrees_per_step,
            "enabled": stepper_y_status.enabled,
            "gear_ratio": stepper_y_status.gear_ratio,
            "killswitch_left_on": stepper_y_status.killswitch_left_on,
            "killswitch_right_on": stepper_y_status.killswitch_right_on,
            "name": stepper_y_status.name,
            "sleeping": stepper_y_status.sleeping,
            "steps_per_rev": stepper_y_status.steps_per_rev,
        }

        return {
            "started": self.started,
            "moving_to_target": self.moving_to_target,
            "target_found": self.target_found,
            "target_position_x": self.target_position_x,
            "target_position_y": self.target_position_y,
            "gps": gps,
            "imu": imu,
            "stepper_x": stepper_x,
            "stepper_y": stepper_y
        }

    def move_to_astronomical_object(self, object_name):
        if not object_name:
            raise Exception("Please provide valid object_name.")

        if not self.started:
            raise Exception("Telescope has not been initialised.")

        if not self.gps.status().has_position:
            raise Exception("Cannot target object without GPS position.")

        if self.moving_to_target:
            raise Exception("Another object is currently being targeted.")

        try:
            ts = load.timescale()
            t = ts.now()

            planets = load("de421.bsp")
            earth, target_planet = planets["earth"], planets[object_name]

            gps_position = self.gps.position()

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
            self.stepper_x.set_full_step()

            # Use the stepper step count rather than the compass to find the target
            result = self.move_to_compass_position(0)
            degrees = Telescope.degrees_between_points(
                self.stepper_x.status().current_position, position
            )
            self.target_position_x = position
            self.rotate_stepper_by_degrees(self.stepper_x, degrees, variable_speed=False)
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
            while not self.imu.status().position_stable:
                if not self.moving_to_target:
                    break  # Don't block cancellation requests
                time.sleep(0.1)

            mag_pos = self._normalise_yaw(self.imu.position().yaw_smoothed)
            degrees = self.degrees_between_points(mag_pos, position)

            self.stepper_x.current_position = mag_pos

            print("Are we there yet?", mag_pos, position, degrees, abs(degrees))
            if abs(degrees) > allowed_error_margin:
                self.rotate_stepper_by_degrees(self.stepper_x, degrees, variable_speed=False)
            else:
                break

        self.moving_to_target = False
        self.target_found = True
        return True

    def rotate_stepper_by_degrees(self, stepper, degrees, variable_speed=True):
        degrees_abs = abs(degrees)

        stepper.enable()
        # As the distance gets smaller, slow down the motor speed and time between rotation/stabilisation attempts
        if variable_speed:
            if degrees_abs < 15:
                stepper.set_eighth_step()
            elif degrees_abs < 60:
                stepper.set_quarter_step()
            elif degrees_abs < 90:
                stepper.set_half_step()
            else:
                stepper.set_full_step()

        num_steps_required = degrees_abs / stepper.status().degrees_per_step

        for i in range(0, int(num_steps_required)):
            if not self.moving_to_target:
                break

            if degrees < 0:
                stepper.step_reverse()
            else:
                stepper.step_forward()

        stepper.disable()

    def _normalise_yaw(self, yaw):
        # Yaw is from -180 to +180. 0 == North.
        # Convert to 0 -> 360 degrees
        yaw += self.gps.position().declination
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
