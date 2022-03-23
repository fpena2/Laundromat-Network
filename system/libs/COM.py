import socketio 
import threading

class SocketIO(threading.local):
    def __init__(self, url ) -> None:
        self.sio = socketio.Client(logger=True, engineio_logger=True)
        self.url = f"http://{url}/"

    def setup(self):
        self.call_backs() 
    
    def run(self):
        self.setup()
        # TODO: https://github.com/miguelgrinberg/python-socketio/discussions/773
        self.sio.connect(self.url)
        # self.sio.wait()

    def send(self, time_unix, current_amps, id):
        self.sio.emit('data', {'time': time_unix, 'current': current_amps, 'ID': id})
    
    def kill(self):
        self.sio.disconnect()

    def call_backs(self):
        @self.sio.event
        def connect():
            print('connection established')

        @self.sio.event
        def disconnect():
            print('disconnected from server')

