import socketio 

class SocketIO():
    sio = socketio.Client(logger=True, engineio_logger=True)

    def __init__(self, url ) -> None:
        self.url = f"http://{url}/"

    def setup(self):
        self.call_backs() 
    
    def run(self):
        self.setup()
        self.sio.connect(self.url)
        # self.sio.wait()

    def send(self, time_unix, current_amps):
        self.sio.emit('data', {'time': str(time_unix), 'current': str(current_amps)})
    
    def kill(self):
        self.sio.disconnect()

    def call_backs(self):
        @self.sio.event
        def connect():
            print('connection established')

        @self.sio.event
        def disconnect():
            print('disconnected from server')

