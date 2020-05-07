import threading
import time
from skyfield.api import load
from skyfield.toposlib import Topos

from hardware.easydriver import EasyDriver
from hardware.gps import GPS
from hardware.imu import IMU

IMU_STABILITY_THRESHOLD = 0.8

class Telescope(object):
    def __init__(self):
        # Init hardware devices
        self.stepper = EasyDriver(
            pin_step=4,
            pin_direction=17,
            pin_ms1=27,
            pin_ms2=22,
            pin_sleep=10,
            pin_enable=9,
            pin_reset=11,
            delay=0.001,
            gear_ratio=18,
        )
        self.gps = GPS()
        self.imu = IMU(stability_threshold=IMU_STABILITY_THRESHOLD)
        self.imu.configure()

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
            self.imu_calibrate()
            self.imu_start()
            self.gps_start()
            self.stepper.disable()
            self.started = True
        return self.status()

    def status(self):
        # Overall status of all sensors and positions
        return {
            "started": self.started,
            "imu_updating": self.imu.updating,
            "imu_has_position": self.imu.has_position,
            "imu_position_stable": self.imu.position_stable,
            "mag_calibrated": self.imu.mag_calibrated,
            "mpu_calibrated": self.imu.mpu_calibrated,
            "imu_calibrated": self.imu.mag_calibrated and self.imu.mpu_calibrated,
            "yaw": self.imu.yaw,
            "yaw_smoothed": self._normalise_yaw(self.imu.yaw_smoothed),
            "yaw_normalised": self._normalise_yaw(self.imu.yaw),
            "roll": self.imu.roll,
            "pitch": self.imu.pitch,
            "gps_updating": self.gps.updating,
            "gps_has_position": self.gps.has_position,
            "latitude": self.gps.latitude,
            "longitude": self.gps.longitude,
            "declination": self.gps.declination,
            "moving_to_target": self.moving_to_target,
            "target_found": self.target_found,
            "target_position_x": self.target_position_x,
            "target_position_y": self.target_position_y,
            "stepper_position": self.stepper.current_position % 360,
            "mag_heading_raw": self.imu.mag_heading_raw + self.gps.declination,
        }

    # IMU functions
    def imu_calibrate(self):
        """
        Calibrates the Mag and Accel/Gyro sensors
        """
        self.imu.stop_updating()

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
        self.imu.calibrate_mpu()

        # Calibration function resets the sensors, so we need to reconfigure them
        self.imu.configure()

        return {
            "mbias": self.imu.mpu9250.mbias,
            "magScale": self.imu.mpu9250.magScale,
        }

    def imu_start(self):
        return self.imu.start_updating()

    def imu_stop(self):
        return self.imu.stop_updating()

    def gps_start(self):
        return self.gps.start_updating()

    def gps_stop(self):
        return self.gps.stop_updating()

    def mag_calibrate(self):
        self.imu.calibrate_mag()
        return {
            "magBias": self.imu.mpu9250.magBias,
            "magScale": self.imu.mpu9250.magScale,
        }

    def move_to_astronomical_object(self, object_name):
        if not object_name:
            raise Exception("Please provide valid object_name.")

        if not self.started:
            raise Exception("Telescope has not been initialised.")

        if not self.gps.has_position:
            raise Exception("Cannot target object without GPS position.")

        if self.moving_to_target:
            raise Exception("Another object is currently being targeted.")

        try:
            ts = load.timescale()
            t = ts.now()

            planets = load("de421.bsp")
            earth, target_planet = planets["earth"], planets[object_name]

            current_pos = earth + Topos(latitude_degrees=self.gps.latitude, longitude_degrees=self.gps.longitude)
            current_pos_time = current_pos.at(t)

            alt, az, d = current_pos_time.observe(target_planet).apparent().altaz()
        except Exception as ex:
            raise ex

        self.move_to_position(az.degrees, method='stepper')
        return {
            "x": az.degrees,
            "y": alt.degrees,
        }

    def cancel_move_to_position(self):
        self.moving_to_target = False
        self.target_found = False

    def move_to_position(self, position, method='compass'):
        if method == 'compass':
            return self.move_to_compass_position(position)
        else:
            # Use the stepper step count rather than the compass to find the target
            result = self.move_to_compass_position(0)
            degrees = Telescope.degrees_between_points(self.stepper.current_position, position)
            self.target_position_x = position
            self.rotate_stepper_by_degrees(degrees, variable_speed=False)
            return result

    def move_to_compass_position(self, position, allowed_error_margin=IMU_STABILITY_THRESHOLD):
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
            while not self.imu.position_stable:
                if not self.moving_to_target:
                    break  # Don't block cancellation requests
                time.sleep(0.1)

            mag_pos = self._normalise_yaw(self.imu.yaw_smoothed)
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
        yaw += self.gps.declination
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
