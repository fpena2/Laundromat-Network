import sys
import time
import numpy as np
from pathlib import Path
import argparse
import threading
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


# Threads section
def work():
    name = threading.current_thread().name
    print("Name: {}".format(name))

    # Setup Object
    url = "ec2-3-133-105-193.us-east-2.compute.amazonaws.com"
    if opts.type == 2:
        cObj = SocketIO(url)
        cObj.run()
    else:
        cObj = HTTPIO(url)

    # Send data
    for i in range(1000):
        utime = str(int(time.time()))
        noise = abs(np.random.normal(0, 10))
        current = str(2 + noise)
        cObj.send(utime, current, name)
        time.sleep(2)


# Entry
def main():
    for worker in range(0, opts.pool):
        threading.Thread(target=work).start()


main()