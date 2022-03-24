from flask import Flask, request, current_app
from flask_socketio import SocketIO, send
from engineio.payload import Payload

import logging, json

# server config
app = Flask(__name__)
app.config["SECRET KEY"] = "test"
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

# socketio config
Payload.max_decode_packets = 500
socketio = SocketIO(app)

@app.route("/", methods = ["POST"])
def get_data():
    payload = request.get_json(cache = False, force = True)
    app.logger.info(f"HTTP - Received: {payload}")
    response = {"message": "success"}
    return response, 200

@app.errorhandler(500)
@app.errorhandler(404)
def page_not_found(error):
    app.logger.error(error)
    response = {"message": "failure"}
    return response, 404

@socketio.on("data")
def handle_message(data):
    serialized_data = json.dumps(data)
    socketio.emit(serialized_data)
    app.logger.info(f"WebSocket - Received: {data}")

if __name__ == "__main__":
   socketio.run(app, host = "0.0.0.0", port = 8080)
   # app.run(host = "0.0.0.0", port = 8080)
