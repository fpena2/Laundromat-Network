from flask import Flask, request, current_app, render_template, g
from flask_socketio import SocketIO, send, emit
from flask_caching import Cache
from engineio.payload import Payload

import copy, logging, json, asyncio, time

from collections import deque

from storage import get_store
from dotenv import load_dotenv

# server config
app = Flask(__name__)
app.config["SECRET KEY"] = "test"
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

# socketio config
Payload.max_decode_packets = 500
socketio = SocketIO(app)
cache = Cache(app)

power_levels = {}

def get_pi_id(name):
    # .e.g. Thread-3 (work)
    num = name.split()[0].split("-")[1]
    return int(num)

def get_device_power_usage():
    data = {}
    data["devices"] = []
    for (id, (current, time)) in power_levels.items():
        device = {}
        device["id"] = id
        device["power_level"] = current
        device["recorded_time"] = time

        data["devices"].append(device)

    return data

# routes
@app.route("/", methods = ["GET"])
@cache.cached(timeout=50)
def index():
    request_origin = request.environ.get("HTTP_ORIGIN", "")
#    app.logger.info(f"GET - /index.html from {request_origin}")
    return render_template("index.html")

@app.route("/devicePowerUsageRequest", methods = ["GET"])
def getHTTPDevPowerUsageRequest():
#    app.logger.info("HTTP GET from client")
    data = get_device_power_usage()
    return data, 200

@app.route("/data", methods = ["POST"])
def post_data():
    global power_levels
    data = request.form
    power_levels[get_pi_id(data.get("ID"))] = (data.get("current"), data.get("time"))

    app.logger.info(f"HTTP - Received: {payload}")
    response = {"message": "success"}
    return response, 200

@socketio.on("data")
def handle_message(data):
    global power_levels
    power_levels[get_pi_id(data["ID"])] = (data["current"], data["time"])

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
   socketio.run(app, host = "0.0.0.0", port = 8080)
   #app.run(host = "0.0.0.0", port = 8080)

