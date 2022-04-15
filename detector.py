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


class ThresholdDetector(BaseDetector):
    def __init__(self, threshold, min_samples, smoother=None, window=[], window_size=128):
        super().__init__(threshold, smoother=smoother, window=window, window_size=window_size, min_samples=min_samples)
        self._sum = 0.0
        self._sumsq = 0.0
        self._is_reset = False

    def step(self, data_pt):
        super().step(data_pt)
        self._N += 1
        self._sum += data_pt
        self._sumsq += data_pt**2
        estimated_time_till_next = 0.0
        confidence = 0.99

        self._mu = self._sum / self._N

        if self._N > self._min_samples: #or self._is_reset:
            var = (self._sumsq - self._N * self._mu ** 2) / (self._N) # or self.N - 1 
            window_mu = sum(self._window) / len(self._window)

            ratio = np.exp(window_mu) / np.exp(self._mu)
            if (ratio > 1.0 + self._threshold) or (ratio < 1.0 - self._threshold):
                self.reset()
                return True, estimated_time_till_next, confidence
        return False, estimated_time_till_next, confidence

    def reset(self):
        self._mu = 0.0
        self._sum = 0.0
        self._sumsq = 0.0
        self._N = 0
        self._is_reset = True



class OnlineBayesDetector(BaseDetector):
    def __init__(self, threshold, min_samples, smoother=None, window=[], window_size=128):
        super().__init__(threshold, smoother=smoother, window=window, window_size=window_size, min_samples=min_samples)
        self._detector = sdt.changepoint.BayesOnline()

    def step(self, data_pt):
        super().step(data_pt)
        self._N += 1
        estimated_time_till_next = 0.0
        confidence = 0.0

        if self._N > self._min_samples:
            self._detector.update(data_pt)
            prob = self._detector.get_probabilities(self._window_size)

            if len(prob) > 1 and np.any(prob[1:] > 0.8):
                return True, estimated_time_till_next, np.max(prob[1:])
        return False, estimated_time_till_next, confidence
        

class DetectorManager:
    def __init__(self, threshold, min_samples, det_type="threshold", detector_map={}):
        self._detector_map = detector_map 
        self._threshold = threshold
        self._min_samples = min_samples

        if det_type.lower().strip() not in ("threshold", "bayes"):
            raise ValueError("invalid detector type")
        self._det = ThresholdDetector
        if det_type.lower() == "bayes":
            self._det = OnlineBayesDetector

    def is_new_device(self, key):
        return (key not in self._detector_map)

    def add_detector(self, key):
        if key not in self._detector_map:
            self._detector_map[key] = self._det(threshold, min_samples)

    def step(self, key, data_pt):
        if key not in self._detector_map:
            raise ValueError(f"{key} not in detector")
        changed, eta, conf = self._detector_map[key].step(data_pt)
        return changed, eta, conf

    def remove_detector(self, key):
        if key not in self._detector_map:
            return
        del self._detector_map[key]

det_manager = DetectorManager(0.1, 100)

if __name__ == "__main__":
    threshold = 0.1
    min_samples = 45
    grad_det = ThresholdDetector(threshold, min_samples)
    assert grad_det.threshold == threshold, "wrong threshold in ThresholdDetector"
    bayes_det = OnlineBayesDetector(threshold, min_samples)
    assert bayes_det.min_samples == min_samples, "wrong min_samples in BayesDetector"
    det_manager = DetectorManager(threshold, min_samples)
    det_manager.add_detector("Thread-1")
    det_manager.add_detector("Thread-2")
    assert det_manager.is_new_device("Thread-1") == False, "is_new_device() wrong implementation"
    assert det_manager.is_new_device("Thread-200") == True, "is_new_dev() wrong implementation"

    for i in range(250):
        x = np.random.normal(loc=0.5, scale=0.2)

        if i > 105:
            x = np.random.normal(loc=4.5, scale=0.01)
        changed, eta, confidence = det_manager.step("Thread-1", x)
        if changed:
            print("changepoint at", i)
        #b_changed, b_eta, b_confidence = bayes_det.step(x)
        #print("grad_detector=", changed, eta, confidence, x)
        #print("bayes_detector=", b_changed, b_eta, b_confidence, x)
    det_manager.remove_detector("Thread-2")
