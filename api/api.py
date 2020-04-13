import serial

from flask import Flask, request, jsonify
from flask_cors import CORS
from skyfield.api import load
from skyfield.toposlib import Topos
from skyfield.trigonometry import position_angle_of

serial_port = serial.Serial(
	port='/dev/ttyACM0',
	baudrate=9600
)

app = Flask(__name__)
CORS(app)


def send_position(pos_x, pos_y):
	serial_command = str.encode(
		"x{};y{};".format(pos_x, pos_y)
	)
	serial_port.write(serial_command)


@app.route("/position", methods=["POST"])
def update_servo_positions():
	content = request.get_json()
	send_position(content["x"], content["y"])
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

	send_position(pos_x, pos_y)

	return jsonify({
		'x': pos_x,
		'y': pos_y,
		'_x': az.degrees,
		'_y': alt.degrees
	})

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=8080)