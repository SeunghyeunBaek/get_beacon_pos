
import configparser
import numpy as np
import random

CONF_DIR = 'config/'
CONF_FILENAME = 'config.ini'
conf = configparser.ConfigParser()
conf.read(CONF_DIR+CONF_FILENAME)

TX_POWER = int(conf.get('PREPROCESS', 'tx_power'))
N = int(conf.get('PREPROCESS', 'n'))

def get_distance(tx_power, rssi):
    rssi = float(rssi)
    distance = 10**((TX_POWER - rssi) / (10 * N))
    return distance

# main.py line 161
def trilaterate(x1, x2, x3, y1, y2, y3, r1, r2, r3):

    s = (x3**2 - x2**2 + y3**2 - y2**2 + r2**2 - r3**2)/2
    t = (x1**2 - x2**2 + y1**2 - y2**2 + r2**2 - r1**2)/2

    y_now = ((t * (x2 - x3)) - (s * (x2 - x1))) / (((y1 - y2) * (x2-x3)) - ((y3-y2) * (x2 -x1)))
    try:
      x_now = ((y_now * (y1 - y2)) - t) / (x2 - x1)
    except:
      x_now = ((y_now * (y1 - y2)) - t) / .01

    return x_now, y_now


class KalmanFilterLinear:
  def __init__(self,_A, _B, _H, _x, _P, _Q, _R):
    self.A = _A                      # State transition matrix.
    self.B = _B                      # Control matrix.
    self.H = _H                      # Observation matrix.
    self.current_state_estimate = _x # Initial state estimate.
    self.current_prob_estimate = _P  # Initial covariance estimate.
    self.Q = _Q                      # Estimated error in process.
    self.R = _R                      # Estimated error idn measurements.
  def GetCurrentState(self):
    return self.current_state_estimate
  def Step(self,control_vector,measurement_vector):
    #---------------------------Prediction step-----------------------------
    predicted_state_estimate = self.A * self.current_state_estimate + self.B * control_vector
    predicted_prob_estimate = (self.A * self.current_prob_estimate) * np.transpose(self.A) + self.Q
    #--------------------------Observation step-----------------------------
    innovation = measurement_vector - self.H*predicted_state_estimate
    innovation_covariance = self.H*predicted_prob_estimate*np.transpose(self.H) + self.R
    #-----------------------------Update step-------------------------------
    kalman_gain = predicted_prob_estimate * np.transpose(self.H) * np.linalg.inv(innovation_covariance)
    self.current_state_estimate = predicted_state_estimate + kalman_gain * innovation
    # We need the size of the matrix so we can make an identity matrix.
    size = self.current_prob_estimate.shape[0]
    # eye(n) = nxn identity matrix.
    self.current_prob_estimate = (np.eye(size)-kalman_gain*self.H)*predicted_prob_estimate