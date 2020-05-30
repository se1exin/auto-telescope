#!/usr/bin/python
# -*- coding: utf-8 -*-

# Simple example of the easydriver Python library.
# Dave Finch 2013

from easydriver import EasyDriver

# Direction of rotation is dependent on how the motor is connected.
# If the motor runs the wrong way swap the values of cw and ccw.
cw = True
ccw = False

"""
Arguments to pass or set up after creating the instance.
Step GPIO pin number.
Delay between step pulses in seconds.
Direction GPIO pin number.
Microstep 1 GPIO pin number.
Microstep 2 GPIO pin number.
Microstep 3 GPIO pin number.
Sleep GPIO pin number.
Enable GPIO pin number.
Reset GPIO pin number.
Name as a string.
"""

# Create an instance of the easydriver class.
# Not using sleep, enable or reset in this example.
stepper = EasyDriver(
    pin_step=26,
    pin_direction=19,
    pin_ms1=6,
    pin_ms2=5,
    pin_sleep=13,
    pin_enable=0,
    delay=0.004,
    gear_ratio=18,
)

stepper.enable()
stepper.wake()
# Set motor direction to clockwise.
stepper.set_direction(ccw)

# Set the motor to run in 1/8 of a step per pulse.
stepper.set_full_step()

# Do some steps.
gear_ratio = 20.142857143  # to 1
steps = 200 * gear_ratio
for i in range(0, int(steps)):
    stepper.step()

stepper.disable()
# Clean up (just calls GPIO.cleanup() function.)
stepper.finish()
