# -*- coding: utf-8 -*-
# import datetime
import serial
import sys
import time
# import time
# import configparser

PORT = 'COM11'
BAUDRATE = 9600

con = serial.Serial(port=PORT, baudrate=BAUDRATE)
while True:
	tic = time.time()
	line = con.readline()
	print(line)
	if len(line) < 2:
		toc = time.time()
		print('interval...', round(toc-tic,3))
		print("="*100)

	
