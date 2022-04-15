from flask import Flask, jsonify, request, current_app, render_template, g
from flask_socketio import SocketIO, send, emit
from flask_caching import Cache
from engineio.payload import Payload

import copy, logging, json, asyncio, time

from collections import deque

from storage import get_store
from dotenv import load_dotenv
from laundromats import LocationFactory
from detector import det_manager

# server config
app = Flask(__name__)
app.config["SECRET KEY"] = "test"
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

# socketio config
Payload.max_decode_packets = 500
socketio = SocketIO(app)
#cache = Cache(app)

power_levels = {}

def get_pi_id(name):
    # .e.g. Thread-3 (work)
    num = name.split()[0].split("-")[1]
    return int(num)

def get_device_power_usage():
    data = {}
    data["devices"] = []
    for (device_id, (current, time)) in power_levels.items():
        device = {}
        device["id"] = device_id
        device["power_level"] = current
        device["recorded_time"] = time
        device["status"] = det_manager.step(device_id)

        data["devices"].append(device)

    return data

# routes
@app.route("/", methods = ["GET"])
#@cache.cached(timeout=50)
def index():
    request_origin = request.environ.get("HTTP_ORIGIN", "")
#    app.logger.info(f"GET - /index.html from {request_origin}")
    return render_template("index.html")


@app.route("/locations", methods = ["GET"])
def get_laundromat_locations():
    app.logger.info(f"GET - api request to laundromat locations")
    locations = []
    for location in LocationFactory.generate_locations():
        locations.append(location.serialize())
    return jsonify(laundromats=locations), 200

@app.route("/find_laundromat", methods = ["GET"])
def recommend_laundromat():
    user_lat, user_lon = float(request.args.get("lat")), float(request.args.get("lon"))
    if not user_lat or not user_lon:
        return {"message": "failure"}, 404
    locations = list(map(json.loads, get_laundromat_locations()[0].get_json()["laundromats"]))

    # TODO: function to recommend, currently picks closest dist
    dist = map(lambda x: abs(x["lat"] - user_lat) + abs(x["lon"] - user_lon), locations)
    min_dist = float("inf")
    idx = 0
    for i, val in enumerate(dist):
        if val < min_dist:
            idx = i
            min_dist = val
    return jsonify(message="success", laundromat=locations[idx]), 200

@app.route("/devicePowerUsageRequest", methods = ["GET"])
def getHTTPDevPowerUsageRequest():
#    app.logger.info("HTTP GET from client")
    data = get_device_power_usage()
    return data, 200

@app.route("/data", methods = ["POST"])
def post_data():
    global power_levels
    data = request.form
    device_id = data.get("ID")
    power_levels[device_id] = (data.get("current"), data.get("time"))
    if det_manager.is_new_device(device_id):
        det_manager.add_detector(device_id)

    #app.logger.info(f"HTTP - Received: sent power_levels")
    response = {"message": "success"}
    return response, 200

@socketio.on("data")
def handle_message(data):
    global power_levels
    device_id = data.get("ID")
    power_levels[device_id] = (data["current"], data["time"])
    if det_manager.is_new_device(device_id):
        det_manager.add_detector(device_id)

@socketio.on("devicePowerUsageRequest")
def handle_data_request():
    global power_levels

    data = get_device_power_usage()
    emit("devicePowerUsage", data, broadcast = False)

@app.errorhandler(500)
@app.errorhandler(404)
def page_not_found(error):
    app.logger.error(error)
    response = {"message": "failure"}
    return response, 404

if __name__ == "__main__":
   print("===== Starting the server =======")
   socketio.run(app, host="0.0.0.0") # ssl_context="adhoc")
   #app.run(host = "0.0.0.0", port = 8080)
