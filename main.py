from pprint import pprint
import json

import time
import board
import adafruit_bno055

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
	"gyro" : {},
	"altimeter" : {},
	"time" : -1,
}

flightPackages = []

startTime = time.time() #epoch secs
while True: #TODO end condition == (velocity == 0 for c seconds)
	flightPackage["time"] = time.time() - startTime
	flightPackage["gyro"]["temperature"] = temperature()
	flightPackage["gyro"]["linearAcceleration"] = list(sensor.linear_acceleration)
	flightPackage["gyro"]["radialVelocity"] = list(sensor.gyro)
	flightPackage["gyro"]["quaternion"] = list(sensor.quaternion)
	flightPackage["gyro"]["gravity"] = list(sensor.gravity)
	flightPackage["gyro"]["magnetic"] = list(sensor.magnetic)
	
	pprint(flightPackage) #TODO remove for deployment
	
	flightPackages.append(flightPackage)
	time.sleep(1)
