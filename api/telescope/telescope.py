import threading
import time

from hardware.easydriver import EasyDriver
from hardware.gps import GPS
from hardware.imu import IMU


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
            delay=0.004,
        )
        self.gps = GPS()
        self.imu = IMU()
        self.imu.configure()

        # Gear ratio of X axis gear system
        self.gear_ratio_x = 20.142857143  # to 1
        self.moving_to_position = False
        self.target_position_x = 0.0
        self.target_position_y = 0.0

    def status(self):
        # Overall status of all sensors and positions
        return {
            "imu_updating": self.imu.updating,
            "imu_has_position": self.imu.has_position,
            "imu_position_stable": self.imu.position_stable,
            "mag_calibrated": self.imu.mag_calibrated,
            "mpu_calibrated": self.imu.mpu_calibrated,
            "imu_calibrated": self.imu.mag_calibrated and self.imu.mpu_calibrated,
            "yaw": self.imu.yaw,
            "yaw_normalised": self._normalise_yaw(self.imu.yaw),
            "roll": self.imu.roll,
            "pitch": self.imu.pitch,
            "gps_updating": self.gps.updating,
            "gps_has_position": self.gps.has_position,
            "latitude": self.gps.latitude,
            "longitude": self.gps.longitude,
            "declination": self.gps.declination,
            "moving_to_position": self.moving_to_position,
            "target_position_x": self.target_position_x,
            "target_position_y": self.target_position_y,
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
        # self.stepper.set_mode_full_step()

        # Start calibration in another thread so we can rotate the motor in this thread.
        # x = threading.Thread(target=self.imu.calibrate_mag)
        # x.start()

        # while self.imu.is_calibrating_mag:
        # 	self.stepper.step_forward()
        # 	pass

        # Mag calibration complete
        # self.stepper.disable()

        # The rest of the sensors (accel, gyro) must be calibrated while not moving
        # time.sleep(1)
        self.imu.calibrate_mpu()

        # Calibration function resets the sensors, so we need to reconfigure them
        self.imu.configure()

        return {
            "magBias": self.imu.mpu9250.magBias,
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

    def move_to_position(self, position_x, position_y):
        if self.moving_to_position:
            return False

        self.target_position_x = position_x
        self.target_position_y = position_y
        self.moving_to_position = True

        x = threading.Thread(target=self._move_to_position, daemon=True, args=(position_x, position_y,))
        x.start()
        return True

    def _move_to_position(self, position_x, position_y):
        # Mag algorithm can take a few seconds to stabilise after movement
        # To move to the target position, we first move to an estimated position,
        # then wait for stabilisation and see how far off we are.
        # We keep doing this until we hit the target

        while self.moving_to_position:
            mag_pos = self._normalise_yaw(self.imu.yaw)

            print("Are we there yet?", int(mag_pos), position_x)

            if int(mag_pos) == position_x:
                self.moving_to_position = False
                break

            distance = self._distance_between_points(mag_pos, position_x)
            distance_perc = abs(distance) / 360

            self.stepper.enable()
            self.stepper.set_eighth_step()
            steps_per_rev = 1600
            stabilisation_delay = 4

            # As the distance gets smaller, slow down the motor speed and time between rotation/stabilisation attempts
            # if abs(distance) > 120:
            # 	stepper.set_full_step()
            # 	steps_per_rev = 200
            # 	stabilisation_delay = 5
            # 	print("Full step")
            # elif abs(distance) > 60:
            # 	stepper.set_half_step()
            # 	steps_per_rev = 400
            # 	stabilisation_delay = 4
            # 	print("Half step")
            # elif abs(distance) > 30:
            # 	stepper.set_quarter_step()
            # 	steps_per_rev = 800
            # 	stabilisation_delay = 3
            # 	print("Quarter step")
            # else:
            # 	stepper.set_eighth_step()
            # 	steps_per_rev = 1600
            # 	stabilisation_delay = 2
            # 	print("Eighth step")

            steps_required = steps_per_rev * self.gear_ratio_x * distance_perc

            print(
                mag_pos,
                position_x,
                distance,
                distance_perc,
                steps_per_rev,
                steps_required,
            )

            for i in range(1, int(steps_required)):
                # print(self.imu.yaw)
                if distance < 0:
                    self.stepper.step_reverse()
                else:
                    self.stepper.step_forward()

            self.stepper.disable()
            while not self.imu.position_stable:
                time.sleep(0.01)  # Wait for mag stabilisation

        self.moving_to_position = False

    def _normalise_yaw(self, yaw):
        # Yaw is from -180 to +180. 0 == North.
        # Convert to 0 -> 360 degrees
        if yaw < 0:
            return 360 - abs(yaw)
        return yaw

    def _distance_between_points(self, current_pos, target_pos):
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
