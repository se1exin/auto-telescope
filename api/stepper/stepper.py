import smbus
import time

CMD_RESET = 0x45;
CMD_ENABLE = 0x46;
CMD_DISABLE = 0x47;
CMD_SET_MODE_FULL_STEP = 0x48;
CMD_SET_MODE_HALF_STEP = 0x49;
CMD_SET_MODE_QUARTER_STEP = 0x50;
CMD_SET_MODE_EIGTH_STEP = 0x51;
CMD_STEP_FORWARD = 0x56;
CMD_STEP_BACKWARD = 0x57;

DEVICE_BUS = 1
DEVICE_ADDR = 0x07


class Stepper(object):
	def __init__(self, address=DEVICE_ADDR):
		self.address = address
		self.bus = smbus.SMBus(DEVICE_BUS)
		self.enabled = False

		# Stepper position config and tracking
		self.steps_per_rev = 200
		self.step_factor = 1.0  # E.g. full step, half step, etc
		self.current_pos = 0.0
		self.reset()

	def sleep(self):
		time.sleep(0.001)

	def send_cmd(self, cmd):
		try:
			self.bus.write_byte(self.address, cmd)
			self.sleep()
		except Exception as ex:
			print(ex)

	def reset(self):
		self.send_cmd(CMD_RESET)
		self.enabled = False

	def enable(self):
		self.enabled = True
		self.send_cmd(CMD_ENABLE)

	def disable(self):
		self.enabled = False
		self.send_cmd(CMD_DISABLE)

	def set_mode_full_step(self):
		self.send_cmd(CMD_SET_MODE_FULL_STEP)
		self.step_factor = 1

	def set_mode_half_step(self):
		self.send_cmd(CMD_SET_MODE_HALF_STEP)
		self.step_factor = 0.5

	def set_mode_quarter_step(self):
		self.send_cmd(CMD_SET_MODE_QUARTER_STEP)
		self.step_factor = 0.25

	def set_mode_eigth_step(self):
		self.send_cmd(CMD_SET_MODE_EIGTH_STEP)
		self.step_factor = 0.125

	def step_forward(self):
		self.send_cmd(CMD_STEP_FORWARD)
		self.current_pos += self.step_factor

	def step_reverse(self):
		self.send_cmd(CMD_STEP_BACKWARD)
		self.current_pos -= self.step_factor
