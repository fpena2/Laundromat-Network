import os
import sys
sys.path.append(os.path.abspath("./libs/"))
from Measurements import Measure

# Initialize Objects 
a = Measure()

try: 
    for i in range(50):
        print(a.get(2000))
except Exception:
    pass