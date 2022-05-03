from abc import ABC, abstractmethod
from collections import deque
from scipy.stats import mode

import sdt.changepoint
import numpy as np
import time, os, pickle

class ModelDecorator:
    def __init__(self, classifier, regressor, base_ts=time.time(), window_size=3):
        self.classifier_window = deque([], maxlen=window_size)
        self.regressor_window = deque([], maxlen=window_size)
        self.window_size = window_size
        self.classifier = classifier
        self.regressor = regressor
        self.base_ts = base_ts
        self.N = 0
        self.mu = 0

    def step(self, x):
        self.N += 1
        alpha = 1.0/self.N
        self.mu = (alpha)*x[1] + (1 - alpha)*self.mu # x[1] = current
        secs = x[0] - self.base_ts # x[0] = device timestamp
        x_ = np.hstack([x, secs, self.mu]).reshape(1, -1)
        status_pred = self.classifier.predict(x_)[0]
        ect_pred = self.regressor.predict(x_[:,1:])[0]
        self.classifier_window.append(status_pred)
        self.regressor_window.append(ect_pred)

    def get_status(self):
        if len(self.classifier_window) == 0:
            return "Unknown", -1

        status = mode(self.classifier_window)[0][0]
        ect = np.mean(self.regressor_window)
        return status, ect

class ModelManager:
    def __init__(self, classifier_path, regressor_path):
        self.models = {}
        self.classifier_path = classifier_path
        self.regressor_path = regressor_path
        self.classifier, self.regressor = None, None

        with open(classifier_path, "rb") as fid:
            self.classifier = pickle.load(fid)

        with open(regressor_path, "rb") as fid:
            self.regressor = pickle.load(fid)

    def add_detector(self, key):
        self.models[key] = ModelDecorator(self.classifier, self.regressor, base_ts=time.time())

    def remove_detector(self, key):
        del self.models[key]

    def get_status(self, key):
        if key not in self.models:
            return "not found"
        model = self.models[key]
        return model.get_status()

    def step(self, key, x):
        if key not in self.models:
            return

        self.models[key].step(x)

    def is_new_device(self, key):
        return key not in self.models


class BaseDetector:
    def __init__(self, threshold, smoother=None, window=[], window_size=128, min_samples=150):
        self._window = deque(window, maxlen=window_size)
        self._window_size = window_size
        self._smoother = smoother
        self._is_triggered = False
        self._min_samples = min_samples
        self._threshold = threshold
        self._N = 0 # num_samples seen so far
        self._ts = 0
    
    @property
    def ts(self):
        return self._ts

    @property
    def min_samples(self):
        return self._min_samples

    @property
    def window(self):
        return self._window

    @property
    def smoother(self):
        return self._smoother

    @smoother.setter
    def smoother(self, kernel_func):
        self._smoother = kernel_func

    @property
    def threshold(self):
        return self._threshold

    @threshold.setter
    def threshold(self, new_threshold):
        self._threshold = threshold

    @abstractmethod
    def step(self, data_pt):
        self._window.append(data_pt)
        return False, 0.0, 0.0

class PeltDetector(BaseDetector):
    def __init__(self, threshold, min_samples, smoother=None, window=[], window_size=128, cost="l2"):
        super().__init__(threshold, smoother=smoother, window=window, window_size=window_size, min_samples=min_samples)
        self._det = sdt.changepoint.Pelt(cost=cost)#, min_size=min_samples)
        self._N = 0
        self._most_recent_cp = -1 

    def step(self, data_pt):
        self._N += 1
        super().step(data_pt)
        return False, 0.0, 0.99

    def changed_in_window(self):
        #if self._N > self._min_samples:
        window = np.array(self._window)
        changed = self._det.find_changepoints(window, penalty=0.8)
        if (len(changed) > 0 and changed[-1] != self._most_recent_cp):
            self._most_recent_cp = changed[-1]
            return True
        return False
        #print(changed, self._changepoints)
        #if len(changed) > 0:
        #    self._changepoints.add(changed[-1])
        #return len(self._changepoints) != len(changed)

class ThresholdDetector(BaseDetector):
    def __init__(self, threshold, min_samples, smoother=None, window=[], window_size=50):
        super().__init__(threshold, smoother=smoother, window=window, window_size=window_size, min_samples=min_samples)
        self._sum = 0.0
        self._sumsq = 0.0
        self._is_reset = False
        self._changepoints = [] # changepoints time stamps
        self._ts = 0
        self._next_check = 0
        self._mu = 0.0

    def step(self, data_pt):
        super().step(data_pt)
        self._next_check -= 1
        self._N += 1
        self._ts += 1
        self._sum += data_pt
        self._sumsq += data_pt**2
        estimated_time_till_next = 0.0
        confidence = 0.99

        self._prev_mu = self._mu
        self._mu = self._sum / self._N

        if self._N > self._min_samples: #or self._is_reset:
            var = (self._sumsq - self._N * self._mu ** 2) / (self._ts) # or self.N - 1 
            window_mu = sum(self._window) / len(self._window)
            
            #ratio = abs(self._mu - self._prev_mu)
            ratio = window_mu / self._mu
            print("ts =", self._ts, "N =", self._N, "sum =", self._sum, "sumsq =", self._sumsq, "mu =", self._mu, "ratio =", ratio, "window_mu =", window_mu)
            if (ratio > self._threshold): # or (ratio < -self._threshold):
                self._changepoints.append(self._ts)
                self.reset()
                return True, estimated_time_till_next, confidence
        return False, estimated_time_till_next, confidence

    def changed_in_window(self):
        if len(self._changepoints) == 0:
            return False

        last_changepoint = self._changepoints[-1]
        if (self._N > self._min_samples) and (self._next_check <= 0) and (abs(self._ts - last_changepoint) <= self._window_size):
            self._next_check = abs(self._ts - last_changepoint)
            self._N = 0
            return True
        return False
        
    def reset(self):
        self._sum = 0
        self._sumsq = 0
        self._N = 0
        self._is_reset = True

class OnlineBayesDetector(BaseDetector):
    def __init__(self, threshold, min_samples, inv_lambda = 250.0, smoother=None, window=[], window_size=20):
        super().__init__(threshold, smoother=smoother, window=window, window_size=window_size, min_samples=min_samples)
        self._detector = sdt.changepoint.BayesOnline(hazard_params={"time_scale": inv_lambda})
        self._window = deque([], maxlen=window_size)
        self._ts = 0
        self._inv_lambda = inv_lambda
        self._N = 0
        self._mu = 0

    def step(self, data_pt):
        super().step(data_pt)
        self._N += 1
        self._mu += data_pt
        self._window.append(data_pt)
        estimated_time_till_next = 0.0
        confidence = 0.0

        #avg = self._mu / self._N
        #self._detector.update(avg)
        #self._detector.update(data_pt - avg)
        self._detector.update(data_pt)
        #self._detector.update(data_pt - np.mean(self._window))
        prob = self._detector.get_probabilities(5)

        if (len(prob) >= 1) and np.any(prob[1:] > self._threshold):
            self._is_triggered = True
            self._detector.reset()
            return True, estimated_time_till_next, confidence
        return False, estimated_time_till_next, confidence

    def changed_in_window(self):
        if self._is_triggered:
            self._is_triggered = False
            return True
        return False


class DetectorManager:
    def __init__(self, threshold, min_samples, det_type="threshold", detector_map={}, **kwargs):
        self._detector_map = detector_map 
        self._threshold = threshold
        self._min_samples = min_samples
        self._detector_args = kwargs

        if det_type.lower().strip() not in ("threshold", "bayes", "pelt"): #, "rf", "gpc", ""):
            raise ValueError("invalid detector type")
        self._det = ThresholdDetector
        if det_type.lower() == "bayes":
            self._det = OnlineBayesDetector
        elif det_type.lower() == "pelt":
            self._det = PeltDetector

    def is_new_device(self, key):
        return (key not in self._detector_map)

    def add_detector(self, key):
        if key not in self._detector_map:
            self._detector_map[key] = self._det(self._threshold, self._min_samples, **self._detector_args)

    def step(self, key, data_pt):
        if key not in self._detector_map:
            raise ValueError(f"{key} not in detector")
        changed, eta, conf = self._detector_map[key].step(data_pt)
        return changed, eta, conf

    def remove_detector(self, key):
        if key not in self._detector_map:
            return
        del self._detector_map[key]

    def changed_in_window(self, key):
        if key in self._detector_map:
            return self._detector_map[key].changed_in_window()
        else:
            return False

det_manager = DetectorManager(0.7, 10, det_type="bayes")

if __name__ == "__main__":
    threshold = 0.75
    min_samples = 10
    grad_det = ThresholdDetector(threshold, min_samples)
    assert grad_det.threshold == threshold, "wrong threshold in ThresholdDetector"
    bayes_det = OnlineBayesDetector(threshold, min_samples)
    assert bayes_det.min_samples == min_samples, "wrong min_samples in BayesDetector"
    det_manager = DetectorManager(threshold, min_samples, det_type="bayes", inv_lambda=245)
    det_manager.add_detector("Thread-1")
    det_manager.add_detector("Thread-2")
    assert det_manager.is_new_device("Thread-1") == False, "is_new_device() wrong implementation"
    assert det_manager.is_new_device("Thread-200") == True, "is_new_dev() wrong implementation"

    big = False
    for i in range(1000):
        x = np.random.random() 

        if big:
            x = 6.0 * np.random.random()

        if i % 100 == 0:
            big = not big
        #print(x)
        changed, eta, confidence = det_manager.step("Thread-1", x)
        changed_in_window = det_manager.changed_in_window("Thread-1")
        if changed_in_window:
            print("changepoint at", i)
            time.sleep(1)
    det_manager.remove_detector("Thread-2")
    assert det_manager.is_new_device("Thread-2") == True, "wrong remove_detector"
