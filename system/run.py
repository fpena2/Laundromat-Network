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
            print("{},{}/n".format(int(time.time()), a.get(2000)), file=f)
except Exception:
    pass
