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

@app.route("/laundromats")
def laundromats():
    print("Received GET on /laundromats")
    lm1 = {
        "name": "cleaners",
        "id": 1200,
        "num_washers": 1,
        "num_driers": 0,
    }

    response = {"laundromats": [lm1]}
    return response

@socketio.on("devicePowerUsageRequest")
def handle_powerUsageRequest(data):
    global lr_pl
    #data["power_level"] = randrange(10)
    print("lr_pl in usage request: " + str(lr_pl))
    data["power_level"] = lr_pl
    emit("devicePowerUsage", data)

@socketio.on("data")
def handle_data_in(data):
    global lr_pl
    lr_pl = data["current"]
    print("lr_pl in data accept: " + str(lr_pl))

if __name__ == "__main__":
    socketio.run(app, certfile='/etc/letsencrypt/live/test.theofficialjosh.com/fullchain.pem', keyfile='/etc/letsencrypt/live/test.theofficialjosh.com/privkey.pem')


