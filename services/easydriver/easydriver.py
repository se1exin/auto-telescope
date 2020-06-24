# Adapted from: https://github.com/davef21370/EasyDriver

import sys
import time

import RPi.GPIO as gpio


class EasyDriver(object):
    def __init__(
        self,
        pin_step=-1,
        delay=1.1,
        pin_direction=-1,
        pin_ms1=-1,
        pin_ms2=-1,
        pin_ms3=-1,
        pin_sleep=-1,
        pin_enable=-1,
        pin_reset=-1,
        pin_killswitch_left=-1,
        pin_killswitch_right=-1,
        pin_killswitch_power=-1,
        gear_ratio=1,
        base_steps_per_rev=200,
        name="Stepper",
    ):
        self.pin_step = pin_step
        self.delay = delay / 2
        self.pin_direction = pin_direction
        self.pin_microstep_1 = pin_ms1
        self.pin_microstep_2 = pin_ms2
        self.pin_microstep_3 = pin_ms3
        self.pin_sleep = pin_sleep
        self.pin_enable = pin_enable
        self.pin_reset = pin_reset
        self.pin_killswitch_left = pin_killswitch_left
        self.pin_killswitch_right = pin_killswitch_right
        self.pin_killswitch_power = pin_killswitch_power
        self.name = name
        self.base_steps_per_rev = base_steps_per_rev
        self.gear_ratio = gear_ratio
        self.current_position = 0.0

        self.enabled = False
        self.sleeping = False
        self.direction = True
        self.steps_per_rev = self.base_steps_per_rev
        self.degrees_per_step = 360 / (self.steps_per_rev * self.gear_ratio)

        gpio.setmode(gpio.BCM)
        gpio.setwarnings(False)

        if self.pin_step > -1:
            gpio.setup(self.pin_step, gpio.OUT)
        if self.pin_direction > -1:
            gpio.setup(self.pin_direction, gpio.OUT)
            gpio.output(self.pin_direction, True)
        if self.pin_microstep_1 > -1:
            gpio.setup(self.pin_microstep_1, gpio.OUT)
            gpio.output(self.pin_microstep_1, False)
        if self.pin_microstep_2 > -1:
            gpio.setup(self.pin_microstep_2, gpio.OUT)
            gpio.output(self.pin_microstep_2, False)
        if self.pin_microstep_3 > -1:
            gpio.setup(self.pin_microstep_3, gpio.OUT)
            gpio.output(self.pin_microstep_3, False)
        if self.pin_sleep > -1:
            gpio.setup(self.pin_sleep, gpio.OUT)
            gpio.output(self.pin_sleep, True)
        if self.pin_enable > -1:
            gpio.setup(self.pin_enable, gpio.OUT)
            gpio.output(self.pin_enable, False)
        if self.pin_reset > -1:
            gpio.setup(self.pin_reset, gpio.OUT)
            gpio.output(self.pin_reset, True)
        if self.pin_killswitch_left > -1:
            gpio.setup(self.pin_killswitch_left, gpio.IN, pull_up_down=gpio.PUD_DOWN)
        if self.pin_killswitch_right > -1:
            gpio.setup(self.pin_killswitch_right, gpio.IN, pull_up_down=gpio.PUD_DOWN)
        if self.pin_killswitch_power > -1:
            gpio.setup(self.pin_killswitch_power, gpio.OUT)
            gpio.output(self.pin_killswitch_power, gpio.HIGH)

        # Make sure the controller is in low power mode until we need it
        self.sleep()

    def killswitch_left_on(self):
        return self.pin_killswitch_left > -1 and gpio.input(self.pin_killswitch_left) == gpio.HIGH

    def killswitch_right_on(self):
        return self.pin_killswitch_right > -1 and gpio.input(self.pin_killswitch_right) == gpio.HIGH

    def step_forward(self):
        self.set_direction(True)
        self.step()
        self.current_position += self.degrees_per_step
        return self.current_position

    def step_reverse(self):
        self.set_direction(False)
        self.step()
        self.current_position -= self.degrees_per_step
        return self.current_position

    def step(self):
        if self.killswitch_left_on() or self.killswitch_right_on():
            # Instead of actually stepping just pretend..
            time.sleep(self.delay * 2)
            return
        # self.wake()
        gpio.output(self.pin_step, True)
        time.sleep(self.delay)
        gpio.output(self.pin_step, False)
        time.sleep(self.delay)
        # self.sleep()

    def set_direction(self, direction):
        gpio.output(self.pin_direction, direction)
        self.direction = direction

    def set_full_step(self):
        gpio.output(self.pin_microstep_1, False)
        gpio.output(self.pin_microstep_2, False)
        if self.pin_microstep_3 > -1:
            gpio.output(self.pin_microstep_3, False)
        self.steps_per_rev = self.base_steps_per_rev

    def set_half_step(self):
        gpio.output(self.pin_microstep_1, True)
        gpio.output(self.pin_microstep_2, False)
        if self.pin_microstep_3 > -1:
            gpio.output(self.pin_microstep_3, False)
        self.steps_per_rev = self.base_steps_per_rev * 2

    def set_quarter_step(self):
        gpio.output(self.pin_microstep_1, False)
        gpio.output(self.pin_microstep_2, True)
        if self.pin_microstep_3 > -1:
            gpio.output(self.pin_microstep_3, False)
        self.steps_per_rev = self.base_steps_per_rev * 4

    def set_eighth_step(self):
        gpio.output(self.pin_microstep_1, True)
        gpio.output(self.pin_microstep_2, True)
        if self.pin_microstep_3 > -1:
            gpio.output(self.pin_microstep_3, False)
        self.steps_per_rev = self.base_steps_per_rev * 8

    def set_sixteenth_step(self):
        gpio.output(self.pin_microstep_1, True)
        gpio.output(self.pin_microstep_2, True)
        if self.pin_microstep_3 > -1:
            gpio.output(self.pin_microstep_3, True)
        self.steps_per_rev = self.base_steps_per_rev * 16

    def sleep(self):
        gpio.output(self.pin_sleep, False)
        self.sleeping = True

    def wake(self):
        gpio.output(self.pin_sleep, True)
        self.sleeping = False

    def disable(self):
        gpio.output(self.pin_enable, True)
        self.enabled = False

    def enable(self):
        gpio.output(self.pin_enable, False)
        self.enabled = True

    def reset(self):
        gpio.output(self.pin_reset, False)
        time.sleep(1)
        gpio.output(self.pin_reset, True)
        self.enabled = False
        self.sleeping = False

    def set_delay(self, delay):
        self.delay = delay / 2

    def finish(self):
        gpio.cleanup()
