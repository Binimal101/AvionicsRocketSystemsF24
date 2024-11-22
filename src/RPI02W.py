"""
This module handles the collection and logging of flight data from sensors.
It retrieves sensor data and writes it to a log file for later analysis.
"""
from pprint import pprint
import math, json, time, numpy, os
import threading, multiprocessing, queue
import board, adafruit_bno055

from altimeter import MS5611
from transmit import RYLR998_Transmit

class FlightDataLogger:
    """Class to collect and log flight data from sensors."""

    def __init__(self):
        """Initialize the FlightDataLogger with necessary setup."""

        # SETUP WITH THREADS THEN WAIT FOR EVERYTHING
        print("Setting up measurement devices")

        thread_queue = self.setup_hardware() #avoids b2b sleep hassle for setting up configs
        [x.join() for x in thread_queue]

        self.flight_package = {
            "imageLocation": None,  # Location of the image (if captured during flight)
            "gyro": {},  # Dictionary to hold gyroscope data
            "altimeter": {},  # Dictionary to hold altimeter data
            "time": -1,  # Time elapsed since the start of data collection
        }

        self.measurement_cycle = 0 # incremented when measurements are taken locally
        self.measurement_modulo = 5 # used to add every nth measurement to transmission payload

        #for when data collection is faster than data transmission, put items in a buffer to get sent over
        self.transmit_buffer = queue.Queue() #Holds all packets which, in order, will be sent to RPI5
        self.transmit_buffer_limit = 2 # IF PASSED, LOGIC WILL BE SETUP TO INCREASE MEASUREMENT_MODULO

        self.transmit_payload = [] # contains one packet to send to RPI5
        self.transmit_payload_limit = 8 # small enough payload that will allow for less time spent wt preamble

    def setup_hardware(self):
        #****RADIO****
        def init_radio():
            self.radio = RYLR998_Transmit()

        #****GYROSCOPE****
        def init_gyro():
            self.i2c = board.I2C()  # Initializes the I2C interface for communication with the sensor
            self.gyroscope = adafruit_bno055.BNO055_I2C(self.i2c)
        
        #****ALTIMETER****
        def init_altimeter():
            # Configure GPIO pins
            cs_pin = 24
            clock_pin = 11
            data_in_pin = 9
            data_out_pin = 10

            # This variable holds the last temperature reading to prevent erroneous readings
            self.gyro_last_temperature_reading = 0xFFFF
            
            # Use the create method to instantiate MS5611
            self.altimeter = MS5611.create(cs_pin, clock_pin, data_in_pin, data_out_pin)

            self.ms.update()
            time.sleep(0.1) # allows sensor to breathe

        threads = [threading.Thread(target=x) for x in (init_radio, init_gyro, init_altimeter)]
        #works through the sleepiness of the configurations for each module to lessen start timer
        [x.start() for x in threads]
        return threads
    
    def transmitFromBuffer(self, qbuff: queue.Queue):
        while True:
            time.sleep(0.1) #TODO manage sleep counters on program scope
            if qbuff.empty():
                # -= 1 to narrow into an "ideal value" given that the pattern for control-flow
                # execution may oscillate 
                self.measurement_modulo -= 1 #make modulo buffer smaller for faster data collection to sync with speed of transmission
                continue

            timestamp, quaternions = qbuff.get()
            self.radio.send(timestamp=timestamp, data_points=quaternions)

    def transmit(self, timestamp: int, quaternion: list): #will change layout in the future when we get better radios
        """
        doesn't actually transmit, but takes quaternion and adds it to a payload to be sent later
        if payload is full, gets put into a queue for transmission from a separate process
        
        sends to RPI5_encode in format:
        [ts, qt1: list, qt2: list, ... qt8: list]
        """

        if not len(self.transmit_payload): #first quaternion in the first payload
            self.transmit_payload.append(timestamp)
        
        if len(self.transmit_payload) > self.transmit_payload_limit: #len(quaternions) == 8    
            if self.transmit_buffer.qsize() > self.transmit_buffer_limit:
                #dynamically resize the modulus for collecting data points to uniformly slow 
                #transmission while allowing for smooth interpolation
                self.measurement_modulo += 2 

            #attempt to transmit and reset payload for next data
            self.transmit_buffer.put(self.transmit_payload)
            self.transmit_payload = [timestamp, quaternion]
        else:
            #add to payload
            self.transmit_payload.append(quaternion)

    def get_temperature(self):
        result = self.gyroscope.temperature  # Get the current temperature from the sensor

        # Check if the temperature reading differs from the last by a specific threshold
        if abs(result - self.gyro_last_temperature_reading) == 128:
            result = self.gyroscope.temperature  # Re-read if a threshold difference is detected
            # If still different, process the result to correct for roll-over
            if abs(result - self.gyro_last_temperature_reading) == 128:
                return 0b00111111 & result  # Mask the result to fit expected range

        self.gyro_last_temperature_reading = result  # Update the last temperature reading
        return result  # Return the processed temperature reading

    def log_flight_data(self):
        """Log the flight data to a file continuously."""

        #create new logfile in ../flightLogs/logfileNM
        current_file_dir = os.path.dirname(__file__)

        # Navigate to the "main scope" directory (parent of 'outer/')
        main_scope_dir = os.path.abspath(os.path.join(current_file_dir, ".."))

        # Create a file in the "main scope"
        self.start_time = time.time()
        file_path = os.path.join(main_scope_dir, f"flightLogs/{str(int(self.start_time))}/logfile.txt")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        #begin data transmission process to run concurrently and more efficiently than in the downtime of GIL 
        self.transmit_process = multiprocessing.Process(target=self.transmitFromBuffer, args=(self.transmit_buffer))
        self.transmit_process.start()     

        # Open a log file to store flight data, using the current date for naming
        with open(f"file_path", "a") as file:
            while True:  # Main loop for continuous data collection

                # Calculate the time elapsed since the start
                self.flight_package["time"] = time.time() - self.start_time

                # Collect sensor data and store in the flight package
                """
                euler and quaternion data are respective to cardinal directions assigned at calibration
                """
            
                self.flight_package["gyro"]["quaternion"] = list(self.gyroscope.quaternion)
                self.flight_package["gyro"]["euler"] = list(self.gyroscope.euler)
                
                if not all(self.flight_package["gyro"]["quaternion"], self.flight_package["gyro"]["euler"]):
                    continue #NoneType encountered in readloop
                
                self.flight_package["gyro"]["linearAcceleration"] = list(self.gyroscope.linear_acceleration)
                self.flight_package["gyro"]["radialVelocity"] = list(self.gyroscope.gyro)
                self.flight_package["gyro"]["magnetic"] = list(self.gyroscope.magnetic)
                self.flight_package["gyro"]["gravity"] = list(self.gyroscope.gravity)
                self.flight_package["gyro"]["temperature"] = self.get_temperature()

                # Capture altimeter pressure and calculate altitude.

                self.flight_package["altimeter"]["temperature"] = float(self.altimeter.returnTemperature()) * (9/5) + 32
                self.flight_package["altimeter"]["pressure"] = self.altimeter.returnPressure()
                self.flight_package["altimeter"]["altitude"] = self.altimeter.returnAltitude(101.7)
                
                self.altimeter.update()
                
                # Take a photo and add its path to 'imageLocation'.
                
                pprint(self.flight_package)  # Print the flight package to the console for debugging

                # Write the flight package as JSON to the log file
                json_data = json.dumps(self.flight_package) + ", "
                
                file.write(json_data)  # Append the JSON data to the log file

                # Add radio transmission for flightPackage every n measurement cycles (self.measurement_modulo is dynamic)
                if self.measurement_cycle % self.measurement_modulo == 0:
                    self.transmit(self.flight_package["gyro"]["quaternion"]) #abstracted for actual payload transmission 
                
                time.sleep(0.25)  # TODO change sleep cycle for deployment | Delay between data collection cycles

if __name__ == "__main__":
    logger = FlightDataLogger()  # Create an instance of FlightDataLogger
    
    #will block main thread until recieved go command from base control
    logger.wait_for_start()

    logger.log_flight_data()  # Start logging flight data & begin sub process for transmission 
