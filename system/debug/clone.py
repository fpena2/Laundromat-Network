import sys
import time
import csv
import numpy as np
from pathlib import Path
import argparse
import threading
from threading import Lock, Thread
import string

# Add libs path
main_dir = Path(__file__).parents[1]
if (libsPath := main_dir.joinpath("libs/")):
    print("Adding libs")
    sys.path.append(str(libsPath))
    from COM import SocketIO, HTTPIO

# Testing Params
parser = argparse.ArgumentParser()
parser.add_argument('--pool', type=int, default=1)
parser.add_argument('--type', type=int, default=1)
opts = parser.parse_args()

# Read washing data template
template = None
template_size = 0
with open('template.csv', newline='') as f:
    reader = csv.reader(f)
    template = list(reader)
    template_size = len(template)


# Threads section
def work(name):
    # Determine "owner"
    index = int(int(name.strip(string.ascii_letters)) / 10)
    owner = f"Laundromat_{index}"

    # Setup Object
    url = "ec2-18-188-215-233.us-east-2.compute.amazonaws.com/data"
    if opts.type == 1:
        cObj = HTTPIO(url)
    else:
        cObj = SocketIO(url)
        cObj.run()

    # Main work
    start = np.random.randint(template_size)
    while start < template_size:
        # Send data
        utime = str(int(time.time()))
        current = str(template[start][1])
        res = cObj.send(utime, current, name, owner)
        # Update tracker
        if res > 0:
            print(f"Thread: {name} -> Disconnected")
            track.update({name: res})
        # Increment
        time.sleep(2)
        start += 1
        # Re-start
        if start >= template_size:
            start = 0
        # Debug
        # Log if more than 5% have disconnected
        if len(track.keys()) > 0.05 * opts.pool:
            f = open("res.log", "w")
            print(
                f"Type: {opts.type}, Pool: {opts.pool}, Len: {len(track.keys())}",
                file=f)


# Tracks connection status
track = {}


# Entry
def main():
    print("Starting workers")
    for worker in range(0, opts.pool):
        Thread(target=work, args=(str(worker), )).start()


main()