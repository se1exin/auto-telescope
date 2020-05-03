import threading
import time

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
from skyfield.api import load
from skyfield.toposlib import Topos
from telescope.telescope import Telescope

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

telescope = Telescope()


@app.route("/start", methods=["POST"])
def start():
    if not telescope.started:
        telescope.start()
        x = threading.Thread(target=status_emitter, daemon=True)
        x.start()

    status = telescope.status()
    return jsonify({"success": True, **status,})


def status_emitter():
    with app.test_request_context():
        while True:
            try:
                status = telescope.status()
                socketio.emit("status", status)
            except Exception as ex:
                print(ex)
                pass
            time.sleep(0.3)


@app.route("/status")
def get_status():
    status = telescope.status()
    return jsonify({"success": True, **status})


@app.route("/imu/calibrate", methods=["POST"])
def imu_calibrate():
    result = telescope.imu_calibrate()
    return jsonify({"success": True, **result})


@app.route("/imu/start", methods=["POST"])
def imu_start():
    return jsonify({"success": telescope.imu_start()})


@app.route("/imu/stop", methods=["POST"])
def imu_stop():
    return jsonify({"success": telescope.imu_stop()})


@app.route("/imu/mag/dump", methods=["POST"])
def imu_mag_dump():
    """
    Function for debugging mag calibration
    """
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
        mag_data = telescope.imu.mpu9250.raw_mag
        print(mag_data)
        if mag_data is not None:
            readings.append(mag_data)
            x.append(mag_data[0])
            y.append(mag_data[1])
            z.append(mag_data[2])
        time.sleep(time_step)

    writer = csv.writer(open("mag_dump.csv", "w"))
    for row in readings:
        writer.writerow(row)

    fig = plt.figure()
    ax1 = fig.add_subplot(111)
    ax1.scatter(x, y, marker=".", label="XY")
    ax1.scatter(x, z, marker=".", label="XY")
    ax1.scatter(y, z, marker=".", label="YZ")
    plt.legend(loc="upper left")
    plt.savefig("static/my_plot.png")

    return jsonify({"success": True})


@app.route("/gps/start", methods=["POST"])
def gps_start():
    return jsonify({"success": telescope.gps_start()})


@app.route("/gps/stop", methods=["POST"])
def gps_stop():
    return jsonify({"success": telescope.gps_stop()})


@app.route("/position", methods=["POST"])
def update_position():
    content = request.get_json()
    pos_x = content["x"]
    pos_y = 0.0  # @TODO: Implement Y axis (still needs hardware)

    result = telescope.move_to_position(pos_x, pos_y)

    return jsonify({"success": result})


@app.route("/planet")
def move_to_planet():
    planet_name = request.args.get("name")
    lat = -33.8870539
    lng = 151.1756034

    ts = load.timescale()
    t = ts.now()

    planets = load("de421.bsp")
    earth, target_planet = planets["earth"], planets[planet_name]

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

    return jsonify({"x": pos_x, "y": pos_y, "_x": az.degrees, "_y": alt.degrees})


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=8080)
