import socketio 
import requests
import threading
import json
import time

class SocketIO(threading.local):
    def __init__(self, url ) -> None:
        self.sio = socketio.Client(logger=True, engineio_logger=True)
        self.url = f"http://{url}/"

    def setup(self):
        self.call_backs() 
    
    def run(self):
        self.setup()
        self.sio.connect(self.url)

    def send(self, time_unix, current_amps, id):
        self.sio.emit('data', {'time': time_unix, 'current': current_amps, 'ID': id})
    
    def kill(self):
        self.sio.disconnect()

    def call_backs(self):
        @self.sio.event
        def connect():
            print('--DEBUG: connection established')

        @self.sio.event
        def disconnect():
            print('--DEBUG: disconnected from server')
            while True:
                try:
                    self.sio.connect(self.url)
                except Exception as e:
                    print(e)
                else:
                    self.sio.wait()
                print("--DEBUG: attempting to reconnect...")
                time.sleep(2)
                


class HTTPIO(threading.local):
    def __init__(self, url) -> None:
        self.url = f"http://{url}/"
        self.headers = {"Content-Type": "application/json", "charset": "utf-8"}
    
    def send(self, time_unix, current_amps, id ):
        msg = {'time': time_unix, 'current': current_amps, 'ID': id}
        response = requests.post(self.url, json = msg, headers = self.headers)
        print("Got: ", response, " from: ", json.dumps(msg))
