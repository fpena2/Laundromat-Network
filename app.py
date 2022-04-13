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

queue = deque()

# socketio config
Payload.max_decode_packets = 500
socketio = SocketIO(app)
cache = Cache(app)

# databases
s3 = get_store("s3")
mongo = get_store("mongo")

# from testing
washer_lr_payload = {
        "power_level": 0.0,
        "device": "washer",
        "recorded_time": time.time() 
    }

dryer_lr_payload = {
        "power_level": 0.0,
        "device": "dryer",
        "recorded_time": time.time() 
    }

registered_devices = {}

pi_data = {}

power_levels = {}

def get_pi_id(name):
    # .e.g. Thread-3 (work)
    num = name.split()[0].split("-")[1]
    return int(num)


# routes
@app.route("/", methods = ["GET"])
@cache.cached(timeout=50)
def index():
    request_origin = request.environ.get("HTTP_ORIGIN", "")
#    app.logger.info(f"GET - /index.html from {request_origin}")
    return render_template("index.html")

@app.route("/laundromat", methods = ["GET"])
def get_laundromats():
    lm1 = {
        "name": "cleaners",
        "id": 1200,
        "num_washers": 5,
        "num_dryers": 10,
    }

    lon, lat = request.args.get("longitude", 0.0), request.args.get("latitude", 0.0)
    request_origin = request.environ.get("HTTP_ORIGIN", "")
    app.logger.info(f"GET - /laundromat from {request_origin}, ({lon}, {lat}) ")
    payload = {"laundromats": [lm1], "message": "success"}
    return payload, 200

@app.route("/devicePowerUsageRequest", methods = ["GET"])
def getHTTPDevPowerUsageRequest():
#    app.logger.info("HTTP GET from client")
    global dryer_lr_payload
    global washer_lr_payload
    global queue
    global pi_data
    global registered_devices

    data = { 
        "device": request.args.get("device"),
        "lmid": request.args.get("lmid"),
        "deviceid": request.args.get("deviceid")
    }

    client_id = int(data["deviceid"])
    pi_key = registered_devices.get(client_id, 0)
    npayload = pi_data.get(pi_key, data)
    npayload["deviceid"] = data["deviceid"]
    npayload["lmid"] = data["lmid"]

    if data["device"].lower() == "washer":
        #data["device"] = washer_lr_payload["device"] 
        npayload["power_level"] = washer_lr_payload["power_level"]
        npayload["recorded_time"] = washer_lr_payload["recorded_time"]
        return npayload, 200
    else:
        #data["device"] = dryer_lr_payload["device"] 
        npayload["power_level"] = dryer_lr_payload["power_level"]
        npayload["recorded_time"] = dryer_lr_payload["recorded_time"]
    return npayload, 200

@app.route("/", methods = ["POST"])
def get_data():
    global dryer_lr_payload
    global queue
    global registered_devices
    global pi_data

    payload = request.get_json(cache = False, force = True)
    pi_id = get_pi_id(payload["ID"])
    registered_devices[pi_id - 1] = payload["ID"]

    dryer_lr_payload["power_level"] = float(payload["current"])
    dryer_lr_payload["recorded_time"] = float(payload["time"])
    dryer_lr_payload["device"] = "dryer"
    pi_data[payload["ID"]] = dryer_lr_payload
    
    npayload = {}
    npayload["power_level"] = float(payload["current"])
    npayload["recorded_time"] = float(payload["time"])
    npayload["device"] = "dryer"
    queue.append(npayload)

    #asyncio.run(mongo.store(payload))
    #s3.store(payload)
    app.logger.info(f"HTTP - Received: {payload}")
    response = {"message": "success"}
    return response, 200

@socketio.on("data")
def handle_message(data):
    global power_levels
    power_levels[get_pi_id(data["ID"])] = (data["current"], data["time"])

@socketio.on("devicePowerUsageRequest")
def handle_data_request(data):
    global power_levels

    current = 5
    time = 5
    if data["deviceid"] in power_levels.keys():
        current, time = power_levels[data["deviceid"]]

    data["power_level"] = current
    data["recorded_time"] = time
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
