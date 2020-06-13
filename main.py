from preproc import KalmanFilterLinear
import arduino_connector
import arduino_parser
import arduino_logger
import configparser
import numpy as np
import preproc
import time
import csv
import os
import sys

# TEST_LOG_DIR = 'test_log/'
# header = ['factory_id', 'beacon_id', 'tx_power', 'rssi', 'distance']

PREPROC_LOG_DIR = 'log/preproc_log/'
PREPROC_LOG_FILENAME = 'preproc_log.csv'
PREPROC_HEADER = ['TIME', 'FACTORY_ID', 'BEACON_ID', 'TX', 'RSSI', 'KM_RSSI', 'DISTANCE', 'KM_DISTANCE']
CONF_DIR = 'config/'
CONF_FILENAME = 'config.ini'

conf = configparser.ConfigParser()
conf.read(CONF_DIR + CONF_FILENAME)

b1_id = conf.get('BEACON', 'b1_id')
b2_id = conf.get('BEACON', 'b2_id')
b3_id = conf.get('BEACON', 'b3_id')

b1_coord = [int(i) for i in conf.get('BEACON', 'b1_coord').split(',')]
b2_coord = [int(i) for i in conf.get('BEACON', 'b2_coord').split(',')]
b3_coord = [int(i) for i in conf.get('BEACON', 'b3_coord').split(',')]

# set kalman filter
A = np.matrix([1])
H = np.matrix([1])
B = np.matrix([0])
Q = np.matrix([0.00001])
R = np.matrix([0.008])
xhat = np.matrix([3])
P    = np.matrix([1])

km_filter1 = KalmanFilterLinear(A,B,H,xhat,P,Q,R)
km_filter2 = KalmanFilterLinear(A,B,H,xhat,P,Q,R)
km_filter3 = KalmanFilterLinear(A,B,H,xhat,P,Q,R)

fiter_dict = {
	b1_id: km_filter1
	, b2_id: km_filter2
	, b3_id: km_filter3
}

def main(exec_time):
	con = arduino_connector.get_connection()

	start = time.time()
	el = 0


	dist_dict = {
		b1_id: list()  
		, b2_id: list()
		, b3_id: list() 
	}

	rciv_idx = 0

	while el < int(exec_time):


		end = time.time()

		result = arduino_parser.get_data(con)

		if result != -1:
			print(result)
			## preprocessor
			timestamp, input_factory_id, input_beacon_id, tx_power, rssi = result

			km_filter = fiter_dict[input_beacon_id]
			tx_power = -59
			rssi = float(rssi)

			km_rssi = km_filter.GetCurrentState()[0,0]
			km_filter.Step(np.matrix([0]),np.matrix([rssi]))
			fiter_dict[input_beacon_id] = km_filter

			distance = preproc.get_distance(tx_power, rssi)
			km_distance = preproc.get_distance(tx_power, km_rssi)

			dist_dict[input_beacon_id].append(km_distance)

			cal_cond = [rciv_idx < len(dist_dict[b1_id]), rciv_idx < len(dist_dict[b2_id]), rciv_idx < len(dist_dict[b3_id])] 

			if all(cal_cond):

				# trilaterate
				r1 = dist_dict[b1_id][rciv_idx]
				r2 = dist_dict[b2_id][rciv_idx]
				r3 = dist_dict[b3_id][rciv_idx]

				x1, y1, x2, y2, x3, y3 = b1_coord + b2_coord+ b3_coord

				s = (x3**2 - x2**2 + y3**2 - y2**2 + r2**2 - r3**2)/2
				t = (x1**2 - x2**2 + y1**2 - y2**2 + r2**2 - r1**2)/2

				y_now = ((t * (x2 - x3)) - (s * (x2 - x1))) / (((y1 - y2) * (x2-x3)) - ((y3-y2) * (x2 -x1)))
				x_now = ((y_now * (y1 - y2)) - t) / (x2 - x1)

				print('-------------------------------')
				print(rciv_idx)
				print('coord: ', b1_coord, b2_coord, b3_coord)
				print('r :', r1, r2, r3)
				print("내가 여기 있다", x_now, y_now)

				# if all beacons have distance value
				# print('삼각측량시작')
				# print(dist_dict[b1_id][rciv_idx], dist_dict[b2_did][rciv_idx], dist_dict[b3_id][rciv_idx])
				row = [timestamp, r1, r2, r3, x_now, y_now]
				header = ['TIME', 'R1', 'R2', 'R3', 'X', 'Y']
				arduino_logger.save_csv(PREPROC_LOG_DIR, PREPROC_LOG_FILENAME, header, row)
				
				rciv_idx += 1



			# preproc_row = [timestamp, input_factory_id, input_beacon_id, tx_power, rssi, km_rssi, distance, km_distance]
			# arduino_logger.save_csv(PREPROC_LOG_DIR, PREPROC_LOG_FILENAME, PREPROC_HEADER, preproc_row)

			# DIST_DICT[input_beacon_id].append(distance)
			# Kalman filtering

			# save csv

			# preproc_row = [timestamp, input_factory_id, input_beacon_id, tx_power, rssi, km_rssi, distance, km_distance]
			# arduino_logger.save_csv(PREPROC_LOG_DIR, PREPROC_LOG_FILENAME, PREPROC_HEADER, preproc_row)

			# Kalma Filter

		el = end - start

	# print(DIST_DICT)


if __name__ == '__main__':
	exec_time = sys.argv[1]
	main(exec_time)