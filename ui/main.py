from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit
from random import randrange

app = Flask(__name__)
socketio = SocketIO()
socketio.init_app(app, cors_allowed_origins="https://test.theofficialjosh.com")

print("running")

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/laundromats")
def laundromats():
    print("Received GET on /laundromats")
    lm1 = {
        "name": "cleaners",
        "id": 1200,
        "num_washers": 2,
        "num_driers": 2,
    }
    lm2 = {
        "name": "even_cleaners",
        "id": 42,
        "num_washers": 1,
        "num_driers": 1,
    }

    response = {"laundromats": [lm1, lm2]}
    return response

@socketio.on("devicePowerUsageRequest")
def handle_powerUsageRequest(data):
    data["power_level"] = randrange(10)
    emit("devicePowerUsage", data)

if __name__ == "__main__":
    socketio.run(app, certfile='/etc/letsencrypt/live/test.theofficialjosh.com/fullchain.pem', keyfile='/etc/letsencrypt/live/test.theofficialjosh.com/privkey.pem')


