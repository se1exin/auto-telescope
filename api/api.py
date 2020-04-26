import threading
import time

from flask import Flask, request, jsonify
from flask_cors import CORS
from skyfield.api import load
from skyfield.toposlib import Topos
from skyfield.trigonometry import position_angle_of

from stepper.stepper import Stepper
from imu.imu import IMU


app = Flask(__name__)
CORS(app)

stepper = Stepper()
imu = IMU()
imu.configure()


@app.route("/calibrate", methods=["POST"])
def calibrate():
	# To calibrate the mag we need to move the sensor around.
	# The best we can do is just spin the motor as fast as we can during calibration
	stepper.enable()
	stepper.set_mode_full_step()

	# Start calibration in another thread so we can rotate the motor in this thread.
	x = threading.Thread(target=imu.calibrate_mag)
	x.start()

	while imu.is_calibrating_mag:
		# stepper.step_forward()
		pass

	# Mag calibration complete
	stepper.disable()

	# The rest of the sensors (accel, gyro) must be calibrated while not moving
	time.sleep(1)
	imu.calibrate_mpu()

	# Calibration function resets the sensors, so we need to reconfigure them
	imu.configure()
	return jsonify({'success': True})


@app.route("/position")
def get_position():
	return jsonify(imu.get_position())

@app.route("/position", methods=["POST"])
def update_position():
	content = request.get_json()
	pos_x = content["x"]

	stepper.enable()
	stepper.set_mode_half_step()

	mag_pos = imu.get_mag()
	while mag_pos['x'] != pos_x:
		print(mag_pos)
		stepper.step_forward()
		mag_pos = imu.get_mag()

	stepper.disable()

	return jsonify({'success': True})


@app.route("/planet")
def move_to_planet():
	planet_name = request.args.get('name')
	lat = -33.8870539
	lng = 151.1756034

	ts = load.timescale()
	t = ts.now()

	planets = load('de421.bsp')
	earth, target_planet = planets['earth'], planets[planet_name]

	current_pos = earth + Topos(latitude_degrees=lat, longitude_degrees=lng)
	current_pos_time = current_pos.at(t)

	alt, az, d = current_pos_time.observe(target_planet).apparent().altaz()

	pos_x = az.degrees
	pos_y = alt.degrees

	# Our servos can only move 180deg, so to reach and azimuth angle > 180
	# we need to invert both the x and y
	if pos_x > 180:
		pos_x = pos_x - 180
		pos_y = pos_y - 90

	# send_position(pos_x, pos_y)

	return jsonify({
		'x': pos_x,
		'y': pos_y,
		'_x': az.degrees,
		'_y': alt.degrees
	})

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8080)