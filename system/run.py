import time
import os
import sys
import uuid
import argparse
# Import custom libs 
sys.path.append(os.path.abspath("./libs/"))
from Measure import Measure
from COM import SocketIO

# Initialize Params 
url = "ec2-18-191-244-170.us-east-2.compute.amazonaws.com/socketio"
devID = os.uname().nodename

# Initialize Objects 
mObj = Measure()
cObj = SocketIO(url)
cObj.run()

# Testing Params
parser = argparse.ArgumentParser()
parser.add_argument('-d', dest='__debug__', default=False, action='store_true')
args = parser.parse_args()

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
            cObj.send(unixTime, current, devID)
            
            # Print to console 
            print(msg)

except Exception as e:
    print(e)
