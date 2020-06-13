# -*- coding: utf-8 -*-
# import datetime
import serial
# import time
# import configparser

PORT = 'COM11'
BAUDRATE = 9600

def get_connection(port=PORT, baudrate=BAUDRATE):
	con = serial.Serial(port=port, baudrate=baudrate)
	return con

if __name__ == '__main__':
	try:
		con = get_connection()
		print("Connected to arduino")
	except Exception as e:
		print('Fail to connection')
		print(e)

	# print('get_connection')
	# tic = time.time()
	# while True:
	# 	toc = time.time()
	# 	get_data(con)
	# 	if toc - tic > 10:
	# 		break

