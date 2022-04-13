import time
import socketio
import requests
from random import randrange

if __name__ == "__main__":
    print("running")

    USE_HTTP = True
    if USE_HTTP:
        while True:
            print("Sending a HTTP message")
            for i in range(50):
                current = randrange(10)
                id = "Thread-" + str(i)
                url = "http://ec2-18-188-215-233.us-east-2.compute.amazonaws.com/"
                requests.post(url + "data", {'ID': id, 'time': str(int(time.time())), 'current': current})
            time.sleep(1)

    socket = socketio.Client(logger=True)

    socket.connect("http://ec2-18-188-215-233.us-east-2.compute.amazonaws.com/")
    #socket.connect("https://test.theofficialjosh.com")

    while True:
        print("Sending a message")
        for i in range(5):
            current = randrange(10)
            id = "Thread-" + str(i)
            socket.emit('data', {'ID': id, 'time': str(int(time.time())), 'current': current})
        time.sleep(1)


