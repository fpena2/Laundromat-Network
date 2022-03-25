import sys
import time
import signal
import numpy as np
from pathlib import Path
import argparse
import threading

# Add libs path 
main_dir = Path(__file__).parents[1]
if (libsPath := main_dir.joinpath("libs/")):
    sys.path.append(str(libsPath))
    print("Adding libs")
    from COM import SocketIO

# Testing Params
parser = argparse.ArgumentParser()
parser.add_argument('--pool', type=int, default=1)
opts = parser.parse_args()


def work():
    name = threading.current_thread().name
    print("Name: {}".format(name))

    # Setup Object
    url = "ec2-52-14-96-75.us-east-2.compute.amazonaws.com"
    cObj = SocketIO(url)
    cObj.run()

    # Send data
    for i in range(1000):
        utime = str(int(time.time()))
        noise = abs(np.random.normal(0,0.02))
        current = str(0.07 + noise)
        cObj.send(utime, current, name)
        time.sleep(2)

        # End transmission
        if i >= 10:
            cObj.kill()
            break

def main():
    for worker in range(0, opts.pool):
        threading.Thread(target=work).start()

main()