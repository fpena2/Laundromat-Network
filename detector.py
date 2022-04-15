from abc import ABC, abstractmethod
from collections import deque

import sdt.changepoint
import numpy as np

class BaseDetector:
    def __init__(self, threshold, smoother=None, window=[], window_size=128, min_samples=150):
        self._window = deque(window, maxlen=window_size)
        self._window_size = window_size
        self._smoother = smoother
        self._triggered = False
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
    def __init__(self, threshold, min_samples, inv_lambda = 25.0, smoother=None, window=[], window_size=128):
        super().__init__(threshold, smoother=smoother, window=window, window_size=window_size, min_samples=min_samples)
        self._detector = sdt.changepoint.BayesOnline(hazard_params={"time_scale": inv_lambda})
        self._ts = 0
        self._next_check = 0
        self._changepoints = []

    def step(self, data_pt):
        super().step(data_pt)
        self._N += 1
        self._ts += 1
        estimated_time_till_next = 0.0
        confidence = 0.0

        #if self._N > self._min_samples:
        self._detector.update(data_pt)
            #prob = self._detector.get_probabilities(self._window_size)

            #if len(prob) > 1 and np.any(prob[1:] > 0.8):
            #    return True, estimated_time_till_next, np.max(prob[1:])
        #return False, estimated_time_till_next, confidence
        return True, estimated_time_till_next, confidence

    def changed_in_window(self):
        if self._N > self._min_samples:
            window = np.array(self._window)
            changes = self._detector.find_changepoints(window, past=4, prob_threshold=self._threshold)
       
            if len(changes) > 0:
                self._changepoints.append(changes[-1])
                #self._N = 0
                self._detector.reset()
                return True
        return False

class DetectorManager:
    def __init__(self, threshold, min_samples, det_type="threshold", detector_map={}):
        self._detector_map = detector_map 
        self._threshold = threshold
        self._min_samples = min_samples

        if det_type.lower().strip() not in ("threshold", "bayes", "pelt"):
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
            self._detector_map[key] = self._det(self._threshold, self._min_samples)

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
        #if key in self._detector_map:
        #    return self._detector_map[key].changed_in_window()
        return self._detector_map[key].changed_in_window()
        #else:
        #    print("no key")
        #    return False

det_manager = DetectorManager(0.7, 10, det_type="threshold")

if __name__ == "__main__":
    threshold = 0.7
    min_samples = 1
    grad_det = ThresholdDetector(threshold, min_samples)
    assert grad_det.threshold == threshold, "wrong threshold in ThresholdDetector"
    bayes_det = OnlineBayesDetector(threshold, min_samples)
    assert bayes_det.min_samples == min_samples, "wrong min_samples in BayesDetector"
    det_manager = DetectorManager(threshold, min_samples, det_type="pelt")
    det_manager.add_detector("Thread-1")
    det_manager.add_detector("Thread-2")
    assert det_manager.is_new_device("Thread-1") == False, "is_new_device() wrong implementation"
    assert det_manager.is_new_device("Thread-200") == True, "is_new_dev() wrong implementation"

    big = False
    for i in range(1000):
        x = 0.5 

        if big:
            x = 6.0 

        if i % 100 == 0:
            big = not big
        changed, eta, confidence = det_manager.step("Thread-1", x)
        changed_in_window = det_manager.changed_in_window("Thread-1")
        if changed_in_window:
            print("changepoint at", i)
    det_manager.remove_detector("Thread-2")
    assert det_manager.is_new_device("Thread-2") == True, "wrong remove_detector"
