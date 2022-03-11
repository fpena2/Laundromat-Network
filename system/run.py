import time
import os
import sys
import uuid
sys.path.append(os.path.abspath("./libs/"))
from Measurements import Measure

# Initialize Objects 
a = Measure()
__device__ = os.environ["USER"]

try: 
    filename = str(uuid.uuid4())
    with open("./logs/{}.csv".format(filename), "w") as f:
        while True:
            unixTime = str(int(time.time()))
            current = str(a.get(2000))
            print("{},{}/n".format(unixTime, current), file=f)
except Exception as e:
    print(e)
