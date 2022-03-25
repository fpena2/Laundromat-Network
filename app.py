from flask import Flask, request, current_app, render_template, g
from flask_socketio import SocketIO, send, emit
from flask_caching import Cache
from engineio.payload import Payload

import copy, logging, json, asyncio, time

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

# routes
@app.route("/", methods = ["GET"])
@cache.cached(timeout=50)
def index():
    request_origin = request.environ.get("HTTP_ORIGIN", "")
    app.logger.info(f"GET - /index.html from {request_origin}")
    return render_template("index.html")

@app.route("/laundromat", methods = ["GET"])
def get_laundromats():
    lm1 = {
        "name": "cleaners",
        "id": 1200,
        "num_washers": 1,
        "num_dryers": 1,
    }

    lon, lat = request.args.get("longitude", 0.0), request.args.get("latitude", 0.0)
    request_origin = request.environ.get("HTTP_ORIGIN", "")
    app.logger.info(f"GET - /laundromat from {request_origin}, ({lon}, {lat}) ")
    payload = {"laundromats": [lm1], "message": "success"}
    return payload, 200

@app.route("/", methods = ["POST"])
def get_data():
    global dryer_lr_payload
    payload = request.get_json(cache = False, force = True)
    dryer_lr_payload["power_level"] = float(payload["current"])
    dryer_lr_payload["recorded_time"] = float(payload["time"])
    dryer_lr_payload["device"] = "dryer"
    #asyncio.run(mongo.store(payload))
    #s3.store(payload)
    app.logger.info(f"HTTP - Received: {payload}")
    response = {"message": "success"}
    return response, 200

@socketio.on("data")
def handle_message(data):
    global washer_lr_payload
    washer_lr_payload["power_level"] = float(data["current"])
    washer_lr_payload["recorded_time"] = float(data["time"])
    washer_lr_payload["device"] = "washer"
    serialized_data = json.dumps(data)
    #asyncio.run(mongo.store(data))
    #asyncio.run(s3.store(data))
    emit("data", serialized_data)
    app.logger.info(f"WebSocket - Received: {data} from Raspberry Pi")

@socketio.on("devicePowerUsageRequest")
def handle_data_request(data):
    global dryer_lr_payload
    global washer_lr_payload

    if data["device"].lower() == "washer":
        #data["device"] = washer_lr_payload["device"] 
        data["power_level"] = washer_lr_payload["power_level"]
        data["recorded_time"] = washer_lr_payload["recorded_time"]
        emit("devicePowerUsage", data, broadcast = False)
    else:
        #data["device"] = dryer_lr_payload["device"] 
        data["power_level"] = dryer_lr_payload["power_level"]
        data["recorded_time"] = dryer_lr_payload["recorded_time"]
        emit("devicePowerUsage", data, broadcast = False)
    app.logger.info(f"Websocket - Received: {data} from client")

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
