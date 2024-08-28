#!/usr/bin/env python3

import os
import logging
import time
import math
import numpy as np
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
				"proximity",
				"oxidized_gas",
				"reduced_gas",
				"nh3_gas",
				"pm1",
				"pm2.5",
				"pm10",
				],
			):
		self.sensor_list = sensor_list
		self.__ltr559 = LTR559() # Proximity sensor is always used
		# Transfers information from sensor to RPi
		# 	using the directory /dev/i2c-{bus}
		# Temp, humidity, pressure sensors
		bus = SMBus(bus=1)
		self.__bme280 = BME280(i2c_dev=bus)
	
	def get_entropy(self, input: str, symbol_space_size: int):
		""" Ensures a level of entropy in the random input
		
		:param input:				The string that the entropy will be calculated for
		:param symbol_space_size:	The number of possible options per character
		:return:					Bits of entropy
		"""
		return len(input) * math.log(symbol_space_size, 2)

	def get_cpu_temperature(self):
		""" To compensate for changes in hardware temperature"""
		with open("/sys/class/thermal/thermal_zone0/temp", "r") as file:
			temp_celsius = file.read()
		return int(temp_celsius) / 1000.0

	def get_prox(self):
		return self.__ltr559.get_proximity()

	def get_temp(self, prev_temp: float) -> float:
		current_temp = self.__bme280.get_temperature()
		while current_temp == prev_temp:
			time.sleep(.1)
			current_temp = self.__bme280.get_temperature()
		return current_temp
	
	def get_pres(self, prev_pres: float) -> float:
		current_pres = self.__bme280.get_pressure()
		while current_pres == prev_pres:
			time.sleep(.1)
			current_pres = self.__bme280.get_pressure()
		return current_pres

	def get_humi(self, prev_humi: float) -> float:
		current_humi = self.__bme280.get_humidity()
		while current_humi == prev_humi:
			time.sleep(.1)
			current_humi = self.__bme280.get_humidity()
		return current_humi
	
	def get_gas(self, prev_gases: list) -> list:
		gas_data = gas.read_all()
		current_gases = [
			gas_data.oxidising, 
			gas_data.reducing, 
			gas_data.nh3]
		while current_gases == prev_gases:
			time.sleep(.1)
			gas_data = gas.read_all()
			current_gases = [
				gas_data.oxidising, 
				gas_data.reducing, 
				gas_data.nh3,]
		return current_gases
	
	def get_particles(self, prev_particles: list) -> list:
		def try_read():
			try:
				particle_data = pms5003.read()
				current_particles = [
					particle_data.pm_ug_per_m3(1.0),
					particle_data.pm_ug_per_m3(2.5),
					particle_data.pm_ug_per_m3(10),]
			except pmsReadTimeoutError:
				logging.warning("pms5003 read error")
				current_particles = None
			return current_particles
			
		current_particles = try_read() # priming read
		while current_particles == None \
			or current_particles == prev_particles:
			time.sleep(.1)
			current_particles = try_read()
		return current_particles


def collect_noise(min_bits_entropy: int):
	# Basic logging information
	extra_info = {"user": os.getlogin()}
	
	# Create a log file to store numbers in
	logging.basicConfig(
		format="%(asctime)s %(user)-8s %(message)s",
		filename="./logs/new-noise-log.log", 
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
	try:
		sensors = Sensors(["temperature", "pressure"]) # Initialize the desired sensors
	except Exception as e:
		return("Initialization Failed")

	sensor_data = {sensor: [] for sensor in sensors.sensor_list}
	current_sensor_data = {sensor: 0 for sensor in sensors.sensor_list}

	#try:
	# Set display to green to indicate working
	back_color = (0, 200, 25)
	draw.rectangle((0, 0, 160, 80), back_color)
	display.display(image)
	# The first reading seems to be the same every time
	current_sensor_data["temperature"] = 	sensors.get_temp(-999)
	current_sensor_data["pressure"] = 		sensors.get_pres(-999)
	current_sensor_data["humidity"] = 		sensors.get_humi(-999)
	current_sensor_data["oxidized_gas"], current_sensor_data["reduced_gas"], current_sensor_data["nh3_gas"] = sensors.get_gas([-999, -999, -999])
	current_sensor_data["pm1"], current_sensor_data["pm2.5"], current_sensor_data["pm10"] = sensors.get_gas([-999, -999, -999])
	current_sensor_data["proximity"] = 		sensors.get_prox()

	flag = False
	current_entropy_bits = 0
	entropy_output = ""
	while not flag and current_entropy_bits < min_bits_entropy: # While the temperature is within reasonable range
		# Get the current sensor data to check
		current_sensor_data["temperature"] = 	sensors.get_temp(current_sensor_data["temperature"])
		current_sensor_data["pressure"] = 		sensors.get_pres(current_sensor_data["pressure"])
		current_sensor_data["humidity"] = 		sensors.get_humi(current_sensor_data["humidity"])
		current_sensor_data["oxidized_gas"], current_sensor_data["reduced_gas"], current_sensor_data["nh3_gas"] = sensors.get_gas([current_sensor_data["oxidized_gas"], current_sensor_data["reduced_gas"], current_sensor_data["nh3_gas"]])
		current_sensor_data["pm1"], current_sensor_data["pm2.5"], current_sensor_data["pm10"] = sensors.get_gas([current_sensor_data["pm1"], current_sensor_data["pm2.5"], current_sensor_data["pm10"]])
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
				#random_num = Decimal(current_sensor_data[sensor])
				random_num = int(str(
					(Decimal(current_sensor_data[sensor])
					- int(current_sensor_data[sensor]))
					)[6:22])
				print(random_num)
				current_entropy_bits += sensors.get_entropy(str(random_num), 10)
				entropy_output += str(random_num)
				sensor_data[sensor].append(random_num)
			logging.info(
				random_num,
				extra=extra_info
				)
		time.sleep(0) # The avg. sensor refresh is about .88 seconds
	return entropy_output

	""" For testing entropy of the sensors
	except KeyboardInterrupt: # When the data collection is manually stopped
		# Create a graph of the distribution data
		sensor_dataframe = pd.DataFrame(sensor_data)
		print(sensor_dataframe.value_counts())
		for sensor in sensor_dataframe.columns:
			column = pd.DataFrame(sensor_dataframe[sensor])
			sns.displot(
				data=column, 
				x=sensor, 
				bins=100, #np.arange(0, 100), 
				kde=True)
			plt.show()
		sensor_dataframe.to_csv("./logs/test_current", index=False)
		#"""

collect_noise()
