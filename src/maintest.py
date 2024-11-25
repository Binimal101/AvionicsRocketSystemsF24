"""
This module handles the collection and logging of flight data from sensors.
It retrieves sensor data and writes it to a log file for later analysis.
"""
from pprint import pprint
import math, json, time, numpy, os
import board, adafruit_bno055

from altimeter import MS5611

class FlightDataLogger:
    """Class to collect and log flight data from sensors."""

    def __init__(self):
        """Initialize the FlightDataLogger with necessary setup."""

        # SETUP WITH THREADS THEN AWAIT EVERYTHING

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
        """Retrieve and process the temperature from the gyro.

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

        run_cycle = 0 # incremented
        transmit_cycles = 5 # used for modulo

        # Configure GPIO pins
        cs_pin = 24
        clock_pin = 11
        data_in_pin = 9
        data_out_pin = 10

        # Use the create method to instantiate MS5611
        time.sleep(0.1) # allows sensor to breathe

        #create new logfile in ../flightLogs/logfileNM
        current_file_dir = os.path.dirname(__file__)

        # Navigate to the "main scope" directory (parent of 'outer/')
        main_scope_dir = os.path.abspath(os.path.join(current_file_dir, ".."))

        # Create a file in the "main scope"
        file_path = os.path.join(main_scope_dir, f"flightLogs/{str(time.time())}.txt")

        # Open a log file to store flight data, using the current date for naming
        with open(f"{file_path}", "a", encoding="utf-8") as file:
            while True:  # Main loop for continuous data collection

                # Calculate the time elapsed since the start
                self.flight_package["time"] = time.time() - self.start_time

                # Collect sensor data and store in the flight package
                """
                formatted angles and quaternion data are respective to cardinal directions assigned at calibration
                """
            
                self.flight_package["gyro"]["quaternion"] = list(self.sensor.quaternion)

                if len([x for x in self.flight_package["gyro"]["quaternion"] if x is None]):
                    print("quant None encountered:")
                    pprint(self.flight_package["gyro"]["quaternion"])
                    continue #NoneType encountered in readloop
                
                file.write(f"{self.flight_package['gyro']['quaternion']}\n")
                
                self.flight_package["gyro"]["linearAcceleration"] = list(self.sensor.linear_acceleration)
                self.flight_package["gyro"]["radialVelocity"] = list(self.sensor.gyro)
                self.flight_package["gyro"]["magnetic"] = list(self.sensor.magnetic)
                self.flight_package["gyro"]["gravity"] = list(self.sensor.gravity)
                self.flight_package["gyro"]["temperature"] = self.get_temperature()

                # Capture altimeter pressure and calculate altitude.
                
                # Take a photo and add its path to 'imageLocation'.
                
                pprint(self.flight_package)  # Print the flight package to the console for debugging

                # Write the flight package as JSON to the log file
                json_data = json.dumps(self.flight_package) + ", "
                
                #file.write(json_data)  # Append the JSON data to the log file

                # Add radio transmission for flightPackage every n measurement cycles
                time.sleep(0.25)  # Delay between data collection cycles

if __name__ == "__main__":
    logger = FlightDataLogger()  # Create an instance of FlightDataLogger
    logger.log_flight_data()  # Start logging flight data