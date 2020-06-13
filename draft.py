from preproc import KalmanFilterLinear
import numpy as np

A = np.matrix([1])
H = np.matrix([1])
B = np.matrix([0])
Q = np.matrix([0.00001])
R = np.matrix([0.008])
xhat = np.matrix([3])
P    = np.matrix([1])

meters_arr = []
kalman_arr = []
raw_arr = []
A0 = -75
n = 2
size = 50 # length of plot array

# bt_addr, rssi
filter = KalmanFilterLinear(A,B,H,xhat,P,Q,R)

for rssi in range(100):


	kalman_value = filter.GetCurrentState()[0,0]
	print ("Kalman : " + str(kalman_value))
	meters = 10**((kalman_value - A0)/(-10*n))
	meters_arr.append(meters)

	kalman_arr.append(filter.GetCurrentState()[0,0])
	raw_arr.append(rssi)
	print("RSSI : "  + str(rssi))
	# print("Packet : " + str(packet))

	# if len(kalman_arr) > size:
	#     counter = len(kalman_arr) -size
	#     del kalman_arr[:counter]
	# if len(raw_arr) > size:
	#     counter = len(raw_arr) - size
	#     del raw_arr[:counter]
	# if len(meters_arr) >size:
	#     counter = len(meters_arr) - size
	#     del meters_arr[:counter]

	filter.Step(np.matrix([0]),np.matrix([rssi]))