from preproc import KalmanFilterLinear
import arduino_connector
import arduino_parser
import arduino_logger
import configparser
import numpy as np
import operator
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

port1 = conf.get('CONNECTION', 'PORT1')
port2 = conf.get('CONNECTION', 'PORT2')

min_diff = float(conf.get('ALERT', 'min_diff'))
max_diff = float(conf.get('ALERT', 'max_diff'))

############################################################################
############# 비콘 추가시 수정 필요 부분######################################
############################################################################

"""
1 ID
2 coord
3 km filter
4 filter_dict
5 dist_dict
6 coord_dict
7 cal_cond (line 112)
"""
b1_id = conf.get('BEACON', 'b1_id')
b2_id = conf.get('BEACON', 'b2_id')
b3_id = conf.get('BEACON', 'b3_id')
b4_id = conf.get('BEACON', 'b4_id')

b1_coord = [int(i) for i in conf.get('BEACON', 'b1_coord').split(',')]
b2_coord = [int(i) for i in conf.get('BEACON', 'b2_coord').split(',')]
b3_coord = [int(i) for i in conf.get('BEACON', 'b3_coord').split(',')]
b4_coord = [int(i) for i in conf.get('BEACON', 'b4_coord').split(',')]

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
km_filter4 = KalmanFilterLinear(A,B,H,xhat,P,Q,R)

# BT ID - Filter
fiter_dict = {
	b1_id: km_filter1
	, b2_id: km_filter2
	, b3_id: km_filter3
	, b4_id: km_filter4
}

# BT ID - 거리
dist_dict = {
	b1_id: list()  
	, b2_id: list()
	, b3_id: list() 
	, b4_id: list()
}

# BT ID - 좌표

coord_dict = {
	b1_id: b1_coord
	, b2_id: b2_coord
	, b3_id: b3_coord
	, b4_id: b4_coord
}


############################################################################
############# 비콘 추가시 수정 필요 부분######################################
############################################################################

def main(exec_time):

	print('Start..', min_diff, max_diff)
	con = arduino_connector.get_connection(port=port1)  # 블루투스 수신 모듈 연결
	atm_base_con = arduino_connector.get_connection(port=port2) # 기준기압센서 연결

	start = time.time()  # 시작시간
	el = 0  # 경과 시간

	rciv_idx = 0  # 수신 순번
	atm_list = list()  # 기압 센서 값
	atm_base_list = list()  # 기압 센서 베이스 값

	while el < int(exec_time):

		# 거리 계산 조건 업데이트: 해당 수신 순번에 모든 비콘 수신 값과 기압 센서 값이 존재
		# 비콘 추가 시 아래 리스트에 추가해야함
		cal_cond = [rciv_idx < len(dist_dict[b1_id]),
					rciv_idx < len(dist_dict[b2_id]),
					rciv_idx < len(dist_dict[b3_id]),
					rciv_idx < len(dist_dict[b4_id]),
					# rciv_idx < len(dist_dict[b5_id]),
					rciv_idx < len(atm_list), 
					rciv_idx < len(atm_base_list)] 

		result = arduino_parser.get_data(con)  # get data from arduino
		atm_base = arduino_parser.get_data(atm_base_con)  # get data from base atm

		if ((result != -1) & (atm_base != -1)):
			print('Recived: ', result)
			print('BASE: ', atm_base)

			# IF reciver got no error
			if atm_base[0] == 2:
				is_atm, atm_base = atm_base
				atm_base_list.append(atm_base)

			if result[0] == 1:
				# IF reciver got atm value
				is_atm, atm_value = result
				atm_list.append(atm_value) 
			else:
				# If reciver got beacon value

				is_atm, timestamp, input_factory_id, input_beacon_id, tx_power, raw_rssi = result

				raw_rssi = float(raw_rssi)

				km_filter = fiter_dict[input_beacon_id]  # 현재 비콘 ID 에 해당하는 칼만 필터
				km_rssi = km_filter.GetCurrentState()[0,0]  # 현재 비콘 ID에 해당하는 칼만 필터 현재 상태
				km_filter.Step(np.matrix([0]),np.matrix([raw_rssi]))  # 현재 비콘 ID에 해당하는 칼만 필터 업데이트

				raw_distance = preproc.get_distance(tx_power, raw_rssi)  # 현재 비콘과 수신기 사이의 거리 산출
				km_distance = preproc.get_distance(tx_power, km_rssi)  # 칼만 필터 적용 후 거리 산출

				dist_dict[input_beacon_id].append(km_distance)  # 현재 비콘에 해당하는 거리 리스트에 산출 거리 업데이트
			
			# 수신 순번(rciv_idx)에 모든 비콘 신호가 들어왔을 때 좌표 계산
			if all(cal_cond):
				
				# Select atm value
				atm_selected = atm_list[rciv_idx]
				atm_base_selected = atm_base_list[rciv_idx]
				atm_diff = abs(atm_selected - atm_base_selected)
				alert = 1 if min_diff <= atm_diff < max_diff else 0  # 고소 작업 여부
				
				# Select nearest 3 beacons
				now_dist_dict = {b_id: dist_dict[b_id][rciv_idx] for b_id in [b1_id, b2_id, b3_id, b4_id]}
				now_dist_dict = sorted(dist_dict.items(), key=operator.itemgetter(1))
				now_dist_list = now_dist_dict[:3]  # 가까운 순으로 3개 선택
				b_id_selected = [id for id, val in now_dist_list]  # 비콘 ID 추출
								
				# trilaterate
				r1 = dist_dict[b_id_selected[0]][rciv_idx]
				r2 = dist_dict[b_id_selected[1]][rciv_idx]
				r3 = dist_dict[b_id_selected[2]][rciv_idx]

				x1, y1 = coord_dict[b_id_selected[0]]
				x2, y2 = coord_dict[b_id_selected[1]]
				x3, y3 = coord_dict[b_id_selected[2]]

				x_now, y_now = preproc.trilaterate(x1, x2, x3, y1, y2, y3, r1, r2, r3)
				
				print(f"""
				[Selected Beacons]
				{b_id_selected[0]}
					- R: {r1}
					- coord: {x1, y1}

				{b_id_selected[1]}
					- R: {r2}
					- coord: {x2, y2}

				{b_id_selected[2]}
					- R: {r3}
					- coord: {x3, y3}

				[Not selected Beacons]
				{now_dist_dict[-1]}
				""")
		
				print('-------------------------------')
				print("Result coord: ", x_now, y_now)
				print("ATM_DIFF: ", atm_diff, "ALERT: ", alert)

				row = [timestamp, atm_base_selected, atm_selected, atm_diff, r1, r2, r3, x_now, y_now, alert]
				print(row)
				header = ['TIME', 'BASE_ATM', 'ATM', 'ATM_DIFF', 'R1', 'R2', 'R3', 'X', 'Y', 'ALERT']
				arduino_logger.save_csv(PREPROC_LOG_DIR, PREPROC_LOG_FILENAME, header, row)
				
				rciv_idx += 1  # 수신 순번 업데이트

		# 실행시간 업데이트
		end = time.time()
		el = end - start

if __name__ == '__main__':
	exec_time = sys.argv[1]
	main(exec_time)