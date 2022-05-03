import pickle, os, time
import numpy as np
from detector import det_manager, ModelDecorator


rf = None
gpc = None

with open(os.path.join("models", "rf_model.pkl"), "rb") as fid:
    rf = pickle.load(fid)
rf_d = ModelDecorator(rf, base_ts=time.time(), window_size=3)

with open(os.path.join("models", "gpc.pkl"), "rb") as fid:
    knn = pickle.load(fid)
gpc_d = ModelDecorator(knn, base_ts=time.time(), window_size=3)

for i in range(100):
    ts = np.random.random()
    curr = np.random.random() * np.random.randint(0, 4)
    x = [ts, curr]
    rf_d.step(x)
    gpc_d.step(x)
    print("rf status:", rf_d.get_status()) 
    print("gpc status:", gpc_d.get_status()) 

