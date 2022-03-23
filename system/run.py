import time
import os
import sys
import uuid
sys.path.append(os.path.abspath("./libs/"))
from Measure import Measure
from COM import SocketIO

# Initialize Params 
__device__ = os.environ["USER"]
url = "ec2-18-191-244-170.us-east-2.compute.amazonaws.com/socketio"

# Initialize Objects 
mObj = Measure()
cObj = SocketIO(url)
cObj.setup()
cObj.run()

try: 
    # filename = str(uuid.uuid4())
    filename = "test"
    with open("./logs/{}.csv".format(filename), "w") as f:
        while True:
            unixTime = str(int(time.time()))
            current = str(mObj.get(interval_ms=2000))
            # Print to file
            print("{},{}".format(unixTime, current), file=f)
            f.flush()
            # Push to server 
            cObj.send(unixTime, current)

except Exception as e:
    print(e)
