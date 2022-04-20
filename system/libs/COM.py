import socketio
import requests
import threading
import json
import time


class SocketIO(threading.local):

    def __init__(self, url) -> None:
        self.sio = socketio.Client(logger=True, engineio_logger=False)
        self.url = f"http://{url}"
        self.isConnected = False

    def setup(self):
        self.call_backs()

    def run(self):
        self.setup()
        self.connect_loop()

    def send(self, time_unix, current_amps, id, owner):
        try:
            self.sio.emit(
                'data', {
                    'time': time_unix,
                    'current': current_amps,
                    'ID': id,
                    'owner': owner
                })
        except Exception as e:
            print("--EXCEPTION: ", e)

    def kill(self):
        self.sio.disconnect()

    def connect_loop(self):
        while not self.isConnected:
            try:
                self.sio.connect(self.url)
            except Exception as e:
                print("--EXCEPTION:", e)
            else:
                self.isConnected = True
            print("--DEBUG: attempting to reconnect...")
            time.sleep(5)

    def call_backs(self):

        @self.sio.event
        def connect():
            print('--DEBUG: connected to server')

        @self.sio.event
        def disconnect():
            print('--DEBUG: disconnected from server')
            self.connect_loop()


class HTTPIO(threading.local):

    def __init__(self, url) -> None:
        self.url = f"http://{url}"

    def send(self, time_unix, current_amps, id, owner):
        msg = {
            'time': time_unix,
            'current': current_amps,
            'ID': id,
            'owner': owner
        }
        response = requests.post(self.url, msg)
        print("Got: ", response, " With: ", json.dumps(msg))
