# -*- coding: utf-8 -*-
# import datetime
import serial
import sys
import configparser
import os

prj_path = os.getcwd()
conf = configparser.ConfigParser()

conf.read(prj_path +'/config/config.ini')
BAUDRATE=conf.get('CONNECTION', 'BAUDRATE')


def get_connection(port, baudrate=BAUDRATE):
	try:
		con = serial.Serial(port=port, baudrate=baudrate)
		print("Connected to arduino: ", port)
		return con
	except Exception as e:
		print('Fail to connection: ', port)
		print(e)
		return None

if __name__ == '__main__':
	port_input = sys.argv[1]
	con = get_connection(port=port_input)
	while True:
		if con.readable():
			input_raw = con.readline()
			print(input_raw)
		

