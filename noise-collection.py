#!/usr/bin/env python3

import os
import logging
import time
import math
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


class Sensors:
	""" Sets up all specified sensors and includes all reused functions"""

	def __init__(
			self, 
			sensor_list=[
				"temperature",
				"pressure",
				"humidity",
				"light",
				"proximity",
				"oxidized_gas",
				"reduced_gas",
				"nh3_gas",
				],
			):
		self.sensor_list = sensor_list
		self.__ltr559 = LTR559() # Proximity sensor is always used
		
		sensor_set = set(sensor_list)
		if "temperature" in sensor_set \
		or "pressure" in sensor_set \
		or "humidity" in sensor_set:				
			# Transfers information from sensor to RPi
			# 	using the directory /dev/i2c-{bus}
			# Temp, humidity, pressure sensors
			bus = SMBus(bus=1)
			self.__bme280 = BME280(i2c_dev=bus)
	
	def check_entropy(self, input: str, symbol_space_size: int):
		""" Ensures a level of entropy in the random input
		
		:param input:				The string that the entropy will be calculated for
		:param symbol_space_size:	The number of possible options per character
		:return:					Bits of entropy
		"""
		return len(input) * math.log(symbol_space_size, 2)

	def get_cpu_temperature(self):
		""" To compensate for changes in hardware temperature"""
		# CPU temp /sys/class/thermal/thermal_zone0/temp
		raise NotImplementedError()

	def get_prox(self):
		return self.__ltr559.get_proximity()
	
	def get_light(self):
		return self.__ltr559.get_lux()

	def get_temp(self):
		return self.__bme280.get_temperature()
	
	def get_pres(self):
		return self.__bme280.get_pressure()

	def get_humi(self):
		return self.__bme280.get_humidity()


def main():
	# Basic logging information
	extra_info = {"user": os.getlogin()}
	
	# Create a log file to store numbers in
	logging.basicConfig(
		format="%(asctime)s %(user)-8s %(message)s",
		filename="new-noise-log.log", 
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
				color=(200, 200, 0) # Set to yellow to indicate setup
				)
	draw = ImageDraw.Draw(image) # Initiate draw object 

	sensors = Sensors(["temperature",]) # Initialize the desired sensors
	
	sensor_data = {sensor: [] for sensor in sensors.sensor_list}
	current_sensor_data = {sensor: 0 for sensor in sensors.sensor_list}

	try:
		# Set display to green to indicate working
		back_color = (0, 200, 25)
		draw.rectangle((0, 0, 160, 80), back_color)
		display.display(image)
		# The first reading seems to be the same every time
		current_sensor_data["temperature"] = 	sensors.get_temp()
		current_sensor_data["pressure"] = 		sensors.get_pres()
		current_sensor_data["humidity"] = 		sensors.get_humi()
		current_sensor_data["light"] = 			sensors.get_light()
		current_sensor_data["proximity"] = 		sensors.get_prox()

		flag = False
		while not flag: # While the temperature is within reasonable range
			# Get the current sensor data to check
			current_sensor_data["temperature"] = 	sensors.get_temp()
			current_sensor_data["pressure"] = 		sensors.get_pres()
			current_sensor_data["humidity"] = 		sensors.get_humi()
			current_sensor_data["light"] = 			sensors.get_light()
			current_sensor_data["proximity"] = 		sensors.get_prox()
		
			if -10 > current_sensor_data["temperature"] > 50: # Stops running if the temperature gets too hot
				flag = True
			elif current_sensor_data["proximity"] > 1: # Make sure nothing gets too close to interfere with readings
				back_color = (200, 0, 25) # Red to indicate error
				draw.rectangle((0, 0, 160, 80), back_color)
				display.display(image)
				while current_sensor_data["proximity"] > 0:
					# Warn that there is something interfering
					prox_warning = (
						"Something is near the sensor. "
						f"Prox: {current_sensor_data['proximity']}. "
						"Please remove to continue."
						)
					print(prox_warning)
					# Add the warning to the log
					logging.warning(
						prox_warning,
						extra=extra_info
						)
					# Wait 5 seconds before collecting the proximity again
					time.sleep(5)
					current_sensor_data["proximity"] = sensors.get_prox()
				# Warn when restarting collecting
				logging.warning(
					"Resuming data collection", 
					extra=extra_info
					)
				back_color = (0, 200, 25) # Green to indicate working
				draw.rectangle((0, 0, 160, 80), back_color)
				display.display(image)
			else: # If there is nothing wrong
				for sensor in sensors.sensor_list:
					# Take use decimal places 5-20 for a random string
					random_num = int(str(
						(Decimal(current_sensor_data[sensor])
						- int(current_sensor_data[sensor]))
						)[6:21]) % 100
					print(random_num)
					sensor_data[sensor].append(random_num)
				logging.info(
					random_num,
					extra=extra_info
					)
			time.sleep(1) # The avg. sensor refresh is about .88 seconds
	
	except KeyboardInterrupt: # When the data collection is manually stopped
		# Create a graph of the distribution data
		sensor_dataframe = pd.DataFrame(sensor_data)
		#sensor_dataframe.to_csv("./test_3", index=False)
		print(sensor_dataframe["temperature"].value_counts())
		sns.displot(data=sensor_dataframe, x="temperature", kde=True)
		plt.show()

main()
