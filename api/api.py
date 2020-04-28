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
	imu.stop_updating()

	# To calibrate the mag we need to move the sensor around.
	# The best we can do is just spin the motor as fast as we can during calibration
	stepper.enable()
	stepper.set_mode_full_step()

	# Start calibration in another thread so we can rotate the motor in this thread.
	# x = threading.Thread(target=imu.calibrate_mag)
	# x.start()

	while imu.is_calibrating_mag:
		stepper.step_forward()
		pass

	# Mag calibration complete
	stepper.disable()

	# The rest of the sensors (accel, gyro) must be calibrated while not moving
	# time.sleep(1)
	imu.calibrate_mpu()

	imu.configure()

	# Calibration function resets the sensors, so we need to reconfigure them
	return jsonify({
		'success': True,
		'magBias': imu.mpu9250.magBias,
		'magScale': imu.mpu9250.magScale
	})


@app.route("/imu/start", methods=["POST"])
def imu_start():
	if imu.updating:
		return jsonify({'success': False})

	x = threading.Thread(target=imu.start_updating, daemon=True)
	x.start()
	return jsonify({'success': True})


@app.route("/imu/stop", methods=["POST"])
def imu_stop():
	if not imu.updating:
		return jsonify({'success': False})

	imu.stop_updating()
	return jsonify({'success': True})

@app.route("/imu/mag/dump", methods=["POST"])
def imu_mag_dump():
	import csv
	import matplotlib.pyplot as plt
	# Take a bunch of raw mag samples and dump them to file for analysis
	readings = list()
	x = list()
	y = list()
	z = list()
	time_step = 0.01
	sample_duration = int(15 / time_step)
	for _ in range(0, sample_duration):
		mag_data = imu.mpu9250.raw_mag
		print(mag_data)
		if mag_data is not None:
			readings.append(mag_data)
			x.append(mag_data[0])
			y.append(mag_data[1])
			z.append(mag_data[2])
		time.sleep(time_step)

	writer = csv.writer(open("mag_dump.csv", 'w'))
	for row in readings:
		writer.writerow(row)

	fig = plt.figure()
	ax1 = fig.add_subplot(111)
	ax1.scatter(x, y, marker='.', label="XY")
	ax1.scatter(x, z, marker='.', label="XY")
	ax1.scatter(y, z, marker='.', label="YZ")
	plt.legend(loc='upper left')
	plt.savefig('static/my_plot.png')

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

	# Mag algorithm can take a few seconds to stabilise after movement
	# To move to the target position, we first move to an estimated position,
	# then wait for stabilisation and see how far off we are.
	# We keep doing this until we hit the target

	are_we_there_yet = False

	while not are_we_there_yet:
		mag_pos = imu.yaw
		distance = pos_x - mag_pos
		rotate_time = 5000

		# We can't accurately estimate how to rotate the stepper yet.
		# To do so we need to direct connection to the stepper motor driver (currently over I2C to an arduino)
		# and we also need to know the gear ratios.
		# With a direct connection and known gear ratios we should be able to predict and turn the stepper pretty
		# close to the target direction... but for now we will just use the following basic narrow-down logic.

		# As the distance gets small, slow down the motor speed and time between rotation/stabilisation attempts
		if abs(distance) > 90:
			stepper.set_mode_full_step()
		elif abs(distance) > 30:
			stepper.set_mode_half_step()
			rotate_time = 2000
		elif abs(distance) > 5:
			stepper.set_mode_quarter_step()
			rotate_time = 1000
		else:
			stepper.set_mode_eigth_step()
			rotate_time = 500

		start_time = time.time() * 1000

		while ((time.time() * 1000) - start_time) < rotate_time:
			if distance < 0:
				stepper.step_reverse()
			else:
				stepper.step_forward()

		time.sleep(3)  # Wait for mag stabilisation
		mag_pos = imu.yaw

		are_we_there_yet = int(mag_pos) == pos_x

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