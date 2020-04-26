from stepper import Stepper
import time

stp = Stepper(0x07)
stp.enable()

print("Full Step")
stp.set_mode_full_step()
time.sleep(1)
for x in range(0, 200):
	stp.step_forward()

print("Half Step")
stp.set_mode_half_step()

for x in range(0, 200):
	stp.step_forward()


print("Quarter Step")
stp.set_mode_quarter_step()

for x in range(0, 200):
	stp.step_forward()


print("Eigth Step")
stp.set_mode_eigth_step()

for x in range(0, 200):
	stp.step_forward()

stp.disable()