
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
			is_atm = 0
			# encoding bytes to utf-8
			if b'LPF_DATA' in input_raw:
				# get atm data
				input_enc = input_raw[1:].decode('utf-8')
				is_atm = 1
			elif b'BASE' in input_raw:
				input_enc = input_raw.decode('utf-8')
				is_atm = 2
			else:
				# get beacon data
				input_enc = input_raw.decode('utf-8')
			
			# save to source log file
			now = time.localtime()
			timestamp = "%04d-%02d-%02d %02d:%02d:%02d" % (now.tm_year, now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
			log = timestamp + ' | ' + input_enc 
			with open(SCR_LOG_DIR, 'a', newline='') as f:
				f.write(log)

			# parsing
			input_sp = input_enc.split(':')

			if is_atm == 1:

				atm_value = float(input_sp[1].strip(' ').replace('\n', '').replace('\r', ''))
				return is_atm, atm_value

			elif is_atm == 2:
				base_atm = float(input_sp[1].strip(' ').replace('\n', '').replace('\r', ''))
				return is_atm, base_atm
				
			else:
				# 신호 받기
				input_factory_id = input_sp[1]
				input_beacon_id = input_sp[2]
				tx_power = input_sp[3][-2:]
				rssi = float(input_sp[5][:4])

				# 비콘 신호 선택
				select_cond = [factory_id == input_factory_id, input_beacon_id[8:] == "DFFB48D2B060D0F5A71096E0"]
				if all(select_cond):
					return is_atm, timestamp, input_factory_id, input_beacon_id, tx_power, rssi
					
		except Exception as e:
			# print(e)
			# print(input_raw)
			return -1

		else:
			# print('serial is not readable')
			return -1

			# print(e)
			# print(input_raw)


