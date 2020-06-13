
import time
import csv
import configparser
import os

SCR_LOG_DIR = 'log/source_log/src_log.txt'
PARSE_LOG_DIR = 'log/parse_log/'
CONF_DIR = 'config/config.ini'
PARSE_LOG_HEADER = ['TIME', 'FACTORY_ID', 'BEACON_ID', 'TX_POWER', 'RSSI']

def get_data(con):

	# load config file
	conf = configparser.ConfigParser()
	conf.read(CONF_DIR)

	# beacon_id = conf.get('BEACON', 'b1_id')
	factory_id = conf.get('BEACON', 'factory_id')

	# get data
	if con.readable():
		input_raw = con.readline()
		try:
			# encoding to utf-8
			input_enc = input_raw.decode('utf-8')

			# print('src: ', input_enc)

			# save to source log file
			now = time.localtime()
			timestamp = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
			log = timestamp + ' | ' + input_enc 
			with open(SCR_LOG_DIR, 'a', newline='') as f:
				f.write(log)

			# print('log: ', log)
			# parsing
			input_sp = input_enc.split(':')
			if len(input_sp) == 1:
				pass # OK_DISC
			else:
				# 신호 받기
				input_factory_id = input_sp[1]
				input_beacon_id = input_sp[2]
				tx_power = input_sp[3][-2:]
				rssi = input_sp[5][:4] 

				# 비콘 신호 선택
				select_cond = [factory_id == input_factory_id, input_beacon_id[8:] == "DFFB48D2B060D0F5A71096E0"]
				if all(select_cond):
					return timestamp, input_factory_id, input_beacon_id, tx_power, rssi
					
		except Exception as e:
			# print(e)
			# print(input_raw)
			return -1

		else:
			# print('serial is not readable')
			return -1

			# print(e)
			# print(input_raw)

