"""
This module handles the collection and logging of flight data from sensors.
It retrieves sensor data and writes it to a log file for later analysis.
"""
from pprint import pprint
import json
import time
import board
import adafruit_bno055
from sensors.altimeter import MS5611
import numpy

class FlightDataLogger:
    """Class to collect and log flight data from sensors."""

    def __init__(self):
        """Initialize the FlightDataLogger with necessary setup."""

        # SETUP
        self.i2c = board.I2C()  # Initializes the I2C interface for communication with the sensor

        # Create a sensor object for the BNO055 sensor
        self.sensor = adafruit_bno055.BNO055_I2C(self.i2c)

        # This variable holds the last temperature reading to prevent erroneous readings
        self.last_temperature_reading = 0xFFFF

        # Flight data package structure to be logged
        self.flight_package = {
            "imageLocation": None,  # Location of the image (if captured during flight)
            "gyro": {},  # Dictionary to hold gyroscope data
            "altimeter": {},  # Dictionary to hold altimeter data
            "time": -1,  # Time elapsed since the start of data collection
        }

        # Record the start time of data collection
        self.start_time = time.time()  # Get the current time in epoch seconds

    def get_temperature(self):
        """Retrieve and process the temperature from the sensor.

        Returns:
            int: The temperature reading from the sensor, processed to handle
                  specific edge cases where readings may roll over.
        """
        result = self.sensor.temperature  # Get the current temperature from the sensor

        # Check if the temperature reading differs from the last by a specific threshold
        if abs(result - self.last_temperature_reading) == 128:
            result = self.sensor.temperature  # Re-read if a threshold difference is detected
            # If still different, process the result to correct for roll-over
            if abs(result - self.last_temperature_reading) == 128:
                return 0b00111111 & result  # Mask the result to fit expected range

        self.last_temperature_reading = result  # Update the last temperature reading
        return result  # Return the processed temperature reading

    def log_flight_data(self):
        """Log the flight data to a file continuously."""

        # Configure GPIO pins
        cs_pin = 24
        clock_pin = 11
        data_in_pin = 9
        data_out_pin = 10

        # Use the create method to instantiate MS5611
        ms = MS5611.create(cs_pin, clock_pin, data_in_pin, data_out_pin)

        # Open a log file to store flight data, using the current date for naming
        with open(f"flightLogs/{time.time}.log", "a", encoding="utf-8") as file:
            while True:  # Main loop for continuous data collection
                # Calculate the time elapsed since the start
                self.flight_package["time"] = time.time() - self.start_time

                # Collect sensor data and store in the flight package
                self.flight_package["gyro"]["temperature"] = self.get_temperature()
                self.flight_package["gyro"]["linearAcceleration"] = list(
    			self.sensor.linear_acceleration)
                self.flight_package["gyro"]["radialVelocity"] = list(self.sensor.gyro)
                self.flight_package["gyro"]["quaternion"] = list(self.sensor.quaternion)
                self.flight_package["gyro"]["gravity"] = list(self.sensor.gravity)
                self.flight_package["gyro"]["magnetic"] = list(self.sensor.magnetic)

                ms.update()
                temp = ms.returnTemperature()
                pres = ms.returnPressure()
                alt = ms.returnAltitude(101.7)

                self.flightPackage["altimeter"]["temperature"] = temp
                self.flightPackage["altimeter"]["pressure"] = pres
                self.flightPackage["altimeter"]["altitude"] = alt

                # Capture altimeter pressure and calculate altitude.
                # Take a photo and add its path to 'imageLocation'.
                # Add radio transmission logic to send data at intervals.

                pprint(self.flight_package)  # Print the flight package to the console for debugging

                # Write the flight package as JSON to the log file
                json_data = json.dumps(self.flight_package) + ", "
                file.write(json_data)  # Append the JSON data to the log file

                # Add radio transmission for flightPackage every n measurement cycles

                time.sleep(0.5)  # Delay between data collection cycles to reduce load

if __name__ == "__main__":
    logger = FlightDataLogger()  # Create an instance of FlightDataLogger
    logger.log_flight_data()  # Start logging flight data
