import sys
import time
import csv
import numpy as np
from pathlib import Path
import argparse
import threading
import random
# Add libs path
main_dir = Path(__file__).parents[1]
if (libsPath := main_dir.joinpath("libs/")):
    print("Adding libs")
    sys.path.append(str(libsPath))
    from COM import SocketIO, HTTPIO

# Choose a random owner name (testing)
OWNERS = ["Super Laundry", "Mega Laundry", "Cheap Fast Laundry"]

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
def work():
    name = threading.current_thread().name
    owner = random.choice(OWNERS)
    print("Name: {}".format(name))

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
        # Clean up the name
        name = ''.join([i for i in name if i.isalnum()])
        # Send data
        utime = str(int(time.time()))
        current = str(template[start][1])
        cObj.send(utime, current, name, owner)
        time.sleep(2)

        # Increment
        start += 1

        # Re-start
        if start >= template_size:
            start = 0

        # Debug
        print(f"name: {name}, i:{start}, data:{template[start][1]}")


# Entry
def main():
    for worker in range(0, opts.pool):
        threading.Thread(target=work).start()


main()