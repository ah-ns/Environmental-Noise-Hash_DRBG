#!/usr/bin/env python3

import os
import logging
import time
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from decimal import Decimal
from PIL import (Image, ImageDraw)

from bme280 import BME280
from smbus2 import SMBus
from st7735 import ST7735
from ltr559 import LTR559
from pms5003 import PMS5003
from pms5003 import ReadTimeoutError as pmsReadTimeoutError
from enviroplus import gas

def check_sensors(
	temperature: float,
	pressure: float,
	humidity: float,
	light: float,
	proximity: float,
	oxidized: float,
	reduced: float,
	nh3: float
	):
	# CPU temp /sys/class/thermal/thermal_zone0/temp
	raise NotImplementedError()

def get_cpu_temperature():
	raise NotImplementedError()
	
def main():
	# Make dataframe for distribution graph
	columns = [
		"temperature",
		"pressure",
		"humidity",
		"light",
		"proximity",
		"oxidized_gas",
		"reduced_gas",
		"nh3_gas",
		]
	sensor_data = {"temperature":[]}
	#sensor_data = {column: [] for column in columns}
	
	# Extra logging information
	extra_info = {"user": os.getlogin()}
	
	# Create a log file to store numbers in
	logging.basicConfig(
		format="%(asctime)s %(user)-8s %(message)s",
		filename="noise-log.log", 
		level=logging.INFO,
		filemode="a",
		)
	
	# LCD instance
	display = ST7735(
		port=0,
		cs=1,
		dc="GPIO9",
		backlight="GPIO12",
		rotation=270,
		spi_speed_hz=10000000
		)
	display.begin() # initialize display
	image = Image.new(
				"RGB", 
				(display.width, display.height),
				color=(0,0,0)
				)
	draw = ImageDraw.Draw(image)
	back_color = (200, 200, 0) # Set to yellow to indicate setup
	draw.rectangle((0, 0, 160, 80), back_color)
	display.display(image)
	
	# Transfers information from sensor to RPi
	# 	using the directory /dev/i2c-{bus}
	# Temp, humidity, pressure sensors
	bus = SMBus(bus=1)
	bme280 = BME280(i2c_dev=bus)
	
	# Light/proximity sensor
	ltr559 = LTR559()
	
	# Ensure sensors are reading stable
	'''
	check_sensors(
		temperature=Decimal(bme280.get_temperature()),
		pressure=Decimal(bme280.get_pressure()),
		humidity=Decimal(bme280.get_humidity()),
		light=Decimal(ltr559.get_lux()),
		proximity=Decimal(ltr559.get_proximity()),
		oxidized=Decimal(0),
		reduced=Decimal(0),
		nh3=Decimal(0),
		)'''
	
	flag = False
	count = 1
	try:
		back_color = (0, 200, 25) # Green to indicate working
		draw.rectangle((0, 0, 160, 80), back_color)
		display.display(image)
		while not flag:
			# Decimal ensures all decimal places are displayed
			temperature = bme280.get_temperature()
			pressure = bme280.get_pressure()
			humidity = bme280.get_humidity()
			light = ltr559.get_lux()
			proximity = ltr559.get_proximity()
		
			# Prevent something interfering with data collection
			if -10 > temperature > 50:
				flag = True
			elif proximity > 1:
				back_color = (200, 0, 25) # Red to indicate error
				draw.rectangle((0, 0, 160, 80), back_color)
				display.display(image)
				while proximity > 0:
					# Warn that there is something interfering
					prox_warning = (
						"Something is near the sensor. "
						f"Prox: {proximity}. "
						"Please remove to continue."
						)
					print(prox_warning)
					logging.warning(
						prox_warning,
						extra=extra_info
						)
					
					time.sleep(5)
					proximity = ltr559.get_proximity()
					
				# Warn when restarting collecting
				logging.warning(
					"Resuming data collection", 
					extra=extra_info
					)
				back_color = (0, 200, 25) # Green to indicate working
				draw.rectangle((0, 0, 160, 80), back_color)
				display.display(image)
			# If there is nothing wrong
			else:
				if temperature > 30:
					
					sensor_data["temperature"].append(temperature)

					logging.info(
						Decimal(temperature),
						extra=extra_info
						)
			time.sleep(.9) # The avg. response time is about .88 seconds
	
	except KeyboardInterrupt:
		sensor_dataframe = pd.DataFrame(sensor_data)
		print(sensor_dataframe["temperature"].value_counts())
		sns.displot(data=sensor_dataframe, x="temperature", kde=True)
		plt.show()
		
if __name__ == '__main__':
	main()
