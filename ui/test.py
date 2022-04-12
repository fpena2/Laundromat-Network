import time
import socketio
from random import randrange

if __name__ == "__main__":
    print("running")

    socket = socketio.Client(logger=True)

    #socket.connect("http://ec2-18-191-244-170.us-east-2.compute.amazonaws.com")
    socket.connect("https://test.theofficialjosh.com")

    while True:
        print("Sending a message")
        current = randrange(10)
        socket.emit('data', {'time': str(int(time.time())), 'current': current, 'ID': 1200})
        time.sleep(1)


