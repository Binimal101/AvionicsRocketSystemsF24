from pprint import pprint
import json

import time
import board
import numpy

import adafruit_bno055
from altimeter import MS5611

#SETUP
i2c = board.I2C()  # uses board.SCL and board.SDA (wired config in the google sheet)
sensor = adafruit_bno055.BNO055_I2C(i2c)


last_val = 0xFFFF
def temperature():
    global last_val  # pylint: disable=global-statement
    result = sensor.temperature
    if abs(result - last_val) == 128:
        result = sensor.temperature
        if abs(result - last_val) == 128:
            return 0b00111111 & result
    last_val = result
    return result

#START
flightPackage = {
	"imageLocation" : None,
	"gyro" : {},
	"altimeter" : {},
	"time" : -1,
}

flightPackages = []

# Configure Altimeter
cs_pin = 24
clock_pin = 11
data_in_pin = 9
data_out_pin = 10

ms = MS5611(cs_pin, clock_pin, data_in_pin, data_out_pin)


startTime = time.time() #epoch secs
with open(f"flightLogs/{time.time()}.log", "a") as file:
	while True: #TODO end condition == (velocity == 0 for c seconds)
		flightPackage["time"] = time.time() - startTime
		flightPackage["gyro"]["temperature"] = temperature()
		flightPackage["gyro"]["linearAcceleration"] = list(sensor.linear_acceleration)
		flightPackage["gyro"]["radialVelocity"] = list(sensor.gyro)
		flightPackage["gyro"]["quaternion"] = list(sensor.quaternion)
		flightPackage["gyro"]["gravity"] = list(sensor.gravity)
		flightPackage["gyro"]["magnetic"] = list(sensor.magnetic)
		
		ms.update()
		temp = ms.returnTemperature()
		pres = ms.returnPressure()
		alt = ms.returnAltitude(101.7)
        
		flightPackage["altimeter"]["temperature"] = temp
		flightPackage["altimeter"]["pressure"] = pres
		flightPackage["altimeter"]["altitude"] = alt

		#TODO grab photo, save locally, add relPath to package (hopefully sending over lo-framerate compressed B32 images is plausible over radio)
		
		pprint(flightPackage) #TODO remove for deployment
		file.write(json.dumps(flightPackage) + ", ") #appends to logfile
		#TODO add radio transmission for flightPackage every n measurement cycles (put more priority on READING data than transmission); testing should be done for tradeoffs
		
		time.sleep(0.5)

#file will have extra ", " POST PROCESS IT
