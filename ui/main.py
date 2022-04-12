import time
from flask import Flask, render_template
from flask_socketio import SocketIO, send, emit
from random import randrange

app = Flask(__name__)
socketio = SocketIO()
socketio.init_app(app, cors_allowed_origins="https://test.theofficialjosh.com")

lr_pl = 5

print("running")

@app.route("/")
def index():
    return render_template('index.html')

lm_list = [
        {
            "name": "lm1",
            "id": 1200,
            "num_washers": 8,
            "num_dryers": 8,
        },
        {
            "name": "lm2",
            "id": 1234,
            "num_washers": 2,
            "num_dryers": 2,
        },
    ]

@app.route("/laundromat")
def laundromats():
    print("Received GET on /laundromats")
    response = {"laundromats": [lm_list[0]]}
    return response

@socketio.on("devicePowerUsageRequest")
def handle_powerUsageRequest(data):
    global lr_pl
    data["power_level"] = randrange(10)
    data["recorded_time"] = str(int(time.time()))
    #data["power_level"] = lr_pl
    emit("devicePowerUsage", data)

@socketio.on("data")
def handle_data_in(data):
    global lr_pl
    lr_pl = data["current"]

if __name__ == "__main__":
    socketio.run(app, certfile='/etc/letsencrypt/live/test.theofficialjosh.com/fullchain.pem', keyfile='/etc/letsencrypt/live/test.theofficialjosh.com/privkey.pem')


