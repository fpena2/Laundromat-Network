from flask import Flask, jsonify, request, current_app, render_template, g
from flask_socketio import SocketIO, send, emit
from engineio.payload import Payload

import sys, logging, json, asyncio, time, os, pickle

from laundromats import LocationFactory
from detector import det_manager, ModelDecorator, ModelManager

# server config
app = Flask(__name__)
app.config["SECRET KEY"] = "test"
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

# socketio config
Payload.max_decode_packets = 1500
socketio = SocketIO(app)

# model init
PREDICTION = True
classifier_path = os.path.join("models", "gpc.pkl") 
regressor_path = os.path.join("models", "gamma_regressor.pkl")
model_manager = ModelManager(classifier_path, regressor_path)

class DeviceInfo:
    id = ""
    current = 0.0
    time = 0.0
    owner = ""
    status = 0

laundromat_info = {}

def convert_to_str(status):
    if status == 0:
        return "washing"
    elif status == 1:
        return "rinsing"
    elif status == 2:
        return "spinning"
    return "unknown"

def record_data(data):
    global laundromat_info

    dev = DeviceInfo()
    dev.id = data.get("ID")
    dev.current = data.get("current")
    dev.time = data.get("time")
    dev.owner = data.get("owner")
    dev.status = 1 if float(dev.current) > 0.08 else 0

    if not dev.owner in laundromat_info:
        laundromat_info[dev.owner] = {}

    laundromat_info[dev.owner][dev.id] = dev

    if PREDICTION:
        #if det_manager.is_new_device(dev.id):
        #    det_manager.add_detector(dev.id)
        #det_manager.step(dev.id, float(dev.current))
        if model_manager.is_new_device(dev.id):
            model_manager.add_detector(dev.id)
        model_manager.step(dev.id, [float(dev.time), float(dev.current)])

def get_device_power_usage(laundromatid):
    global laundromat_info
    global model

    data = {}
    data["devices"] = []
    devices = laundromat_info[laundromatid].values()
    for dev in devices:
        device = {}
        device["id"] = dev.id
        device["power_level"] = dev.current
        device["recorded_time"] = dev.time
        #if det_manager.changed_in_window(dev.id):
        #    device["state"] = convert_to_str((dev.status + 1)%3) 
        #    dev.status = device["state"]
        #    laundromat_info[laundromatid][dev.id] = dev
        #else:
        #    device["state"] = convert_to_str(dev.status)
        #device["state"] = "OFF" if dev.status == 0 else "ON"
        if PREDICTION:
            state, ect = model_manager.get_status(dev.id)
            device["state"] = state 
            device["ect"] = ect 
        else:
            device["state"] = "OFF" if dev.status == 0 else "ON"
            device["ect"] = "disabled"

        data["devices"].append(device)

    return data

# routes
@app.route("/", methods = ["GET"])
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

@app.route("/laundromatlist", methods = ["GET"])
def get_laundromatlist():
    # prune laundromats that have no active devices
    for (lmid, devices) in list(laundromat_info.items()):
        for (devid, dev) in list(devices.items()):
            current_time = time.time()
            if current_time - float(dev.time) > 60:
                del devices[devid]
        if len(devices) == 0:
            del laundromat_info[lmid]

    data = {}
    data["laundromats"] = list(laundromat_info.keys())
    return data, 200

@app.route("/devicePowerUsageRequest", methods = ["GET"])
def getHTTPDevPowerUsageRequest():
#    app.logger.info("HTTP GET from client")
    laundromatid = request.args.get("laundromatid")
    data = get_device_power_usage(laundromatid)
    return data, 200

@app.route("/data", methods = ["POST"])
def post_data():
    data = request.form
    record_data(data)

    #app.logger.info(f"HTTP - Received: sent power_levels")
    response = {"message": "success"}
    return response, 200

@socketio.on("data")
def handle_message(data):
    record_data(data)

@socketio.on("devicePowerUsageRequest")
def handle_data_request(data):
    data = get_device_power_usage(data["laundromatid"])
    emit("devicePowerUsage", data, broadcast = False)

@app.errorhandler(500)
@app.errorhandler(404)
def page_not_found(error):
    app.logger.error(error)
    response = {"message": "failure"}
    return response, 404

def start_server(prediction=False):
   global PREDICTION
   PREDICTION = prediction
   socketio.run(app, host="0.0.0.0") # ssl_context="adhoc")

if __name__ == "__main__":
   print("===== Starting the server =======")
   print(sys.argv)
   socketio.run(app, host="0.0.0.0") # ssl_context="adhoc")
   #app.run(host = "0.0.0.0", port = 8080)
