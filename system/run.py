import time
import os
import sys
import uuid
import argparse
# Import custom libs
sys.path.append(os.path.abspath("./libs/"))
from Measure import Measure
from COM import SocketIO

# Params
OWNER = "Super Laundry"

# Testing Params
parser = argparse.ArgumentParser()
parser.add_argument('-d', dest='__debug__', default=False, action='store_true')
parser.add_argument('-f',
                    dest='__offline__',
                    default=False,
                    action='store_true')
args = parser.parse_args()

# Initialize Params
url = "ec2-52-14-96-75.us-east-2.compute.amazonaws.com"
devID = os.uname().nodename
devID = ''.join([i for i in devID if i.isalnum()])

# Initialize Objects
mObj = Measure()
if not args.__offline__:
    cObj = SocketIO(url)
    cObj.run()

try:
    filename = str(uuid.uuid4())
    if args.__debug__:
        filename = "test"

    with open("./logs/{}.csv".format(filename), "w") as f:
        while True:
            unixTime = str(int(time.time()))
            current = str(mObj.get(interval_ms=2000))
            msg = "{},{}".format(unixTime, current)

            # Print to file
            print(msg, file=f)
            f.flush()

            # Push to server
            if not args.__offline__:
                cObj.send(unixTime, current, devID, OWNER)

            # Print to console
            print(msg)

except Exception as e:
    print("--EXCEPTION: ", e)
