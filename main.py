from module import arduino_connector, arduino_logger, arduino_parser, preproc
from module.preproc import KalmanFilterLinear
# from preproc import KalmanFilterLinear
# import arduino_connector
# import arduino_parser
# import arduino_logger
import configparser
import numpy as np
import operator
# import preproc
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

# set kalman filter
A = np.matrix([1])
H = np.matrix([1])
B = np.matrix([0])
Q = np.matrix([0.00001])
R = np.matrix([0.008])
xhat = np.matrix([3])
P    = np.matrix([1])

bid_dict = dict(conf.items('BEACON_ID'))  # 비콘번호: 비콘아이디
bcoord_dict = {bid: [float(i) for i in coord.split(',')] \
	 for bid, coord in dict(conf.items('BEACON_COORD')).items()}  # 비콘번호: 비콘좌표
bdist_dict = {bid: list() for bid in bid_dict.keys()}  # 비콘번호: 거리
bfilt_dict = {bid: KalmanFilterLinear(A, B, H, xhat, P,Q,R) for bid in bid_dict.keys()}  # 비콘번호: 칼만필터

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

	
	rciv_bnum = list()
	while el < int(exec_time):

		cal_cond = [rciv_idx < len(bdist_dict[bid]) for bid in bid_dict.keys()]
		cal_cond.append(rciv_idx < len(atm_list))
		cal_cond.append(rciv_idx < len(atm_base_list))

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
			elif result[0] == 0:
				# If reciver got beacon value

				is_atm, timestamp, input_factory_id, input_beacon_id, tx_power, raw_rssi = result

				raw_rssi = float(raw_rssi)
				bnum = [bnum for bnum, bid in bid_dict.items() if bid == input_beacon_id][0]
				km_filter = bfilt_dict[bnum]  # 현재 비콘 ID 에 해당하는 칼만 필터
				km_rssi = km_filter.GetCurrentState()[0,0]  # 현재 비콘 ID에 해당하는 칼만 필터 현재 상태
				km_filter.Step(np.matrix([0]),np.matrix([raw_rssi]))  # 현재 비콘 ID에 해당하는 칼만 필터 업데이트

				raw_distance = preproc.get_distance(tx_power, raw_rssi)  # 현재 비콘과 수신기 사이의 거리 산출
				km_distance = preproc.get_distance(tx_power, km_rssi)  # 칼만 필터 적용 후 거리 산출

				bdist_dict[bnum].append(km_distance)  # 현재 비콘에 해당하는 거리 리스트에 산출 거리 업데이트
				rciv_bnum.append(bnum)  # 들어온 비콘 번호 저장

			# ISDISI 한번 끝
			elif (result[0] == 3):
				if len(rciv_bnum) < 4:
					rciv_bnum = list()
					continue
				elif ((len(atm_base_list) == 0) | (len(atm_list) == 0)):
					rciv_bnum = list()
					continue 
				else:
					print(rciv_bnum)

					atm_base_selected = atm_base_list[-1]
					atm_selected = atm_list[-1]
					atm_diff = abs(atm_selected - atm_base_selected)
					alert = 1 if min_diff <= atm_diff < max_diff else 0  # 고소 작업 여부

					now_dist_dict = {bnum: bdist_dict[bnum][-1] for bnum in bid_dict.keys() if bnum in rciv_bnum}
					now_dist_dict = sorted(now_dist_dict.items(), key=operator.itemgetter(1))
					now_dist_list = now_dist_dict[:3]  # 가까운 순으로 3개 선택
					bnum_selected = [bnum for bnum, val in now_dist_list]  # 비콘 ID 추출

					# trilaterate
					r1 = bdist_dict[bnum_selected[0]][-1]
					r2 = bdist_dict[bnum_selected[1]][-1]
					r3 = bdist_dict[bnum_selected[2]][-1]

					x1, y1 = bcoord_dict[bnum_selected[0]]
					x2, y2 = bcoord_dict[bnum_selected[1]]
					x3, y3 = bcoord_dict[bnum_selected[2]]

					x_now, y_now = preproc.trilaterate(x1, x2, x3, y1, y2, y3, r1, r2, r3)
					
					print(f"""
					[Selected Beacons]
					{bnum_selected[0]}
						- R: {r1}
						- coord: {x1, y1}

					{bnum_selected[1]}
						- R: {r2}
						- coord: {x2, y2}

					{bnum_selected[2]}
						- R: {r3}
						- coord: {x3, y3}

					[Not selected Beacons]
					{now_dist_dict[3:]}
					""")
			
					print('-------------------------------')
					print("Result coord: ", x_now, y_now)
					print("ATM_DIFF: ", atm_diff, "ALERT: ", alert)

					row = [timestamp, atm_base_selected, atm_selected, atm_diff, r1, r2, r3, x_now, y_now, alert]
					print(row)
					header = ['TIME', 'BASE_ATM', 'ATM', 'ATM_DIFF', 'R1', 'R2', 'R3', 'X', 'Y', 'ALERT']
					arduino_logger.save_csv(PREPROC_LOG_DIR, PREPROC_LOG_FILENAME, header, row)

					rciv_bnum = list()

		

		# 실행시간 업데이트
		end = time.time()
		el = end - start

if __name__ == '__main__':
	exec_time = sys.argv[1]
	# exec_time = 30
	main(exec_time)