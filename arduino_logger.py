import csv
import os

def save_csv(save_dir, filename, header, row):
	if filename not in os.listdir(save_dir):
		with open(save_dir + filename, 'w', newline='') as f:
			writer = csv.writer(f)
			writer.writerow(header)
	else:
		with open(save_dir + filename, 'a', newline='') as f:
			writer = csv.writer(f)
			writer.writerow(row)
	pass