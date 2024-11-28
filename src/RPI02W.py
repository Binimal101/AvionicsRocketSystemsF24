"""
This module handles the collection and logging of flight data from sensors.
It retrieves sensor data and writes it to a log file for later analysis.
"""

#built-in
from pprint import pprint
import threading, multiprocessing, queue
import json, time, os, datetime

#embedded stuff
import board, adafruit_bno055

#files
from altimeter import MS5611
from transmit import RYLR998_Transmit
from reyax import getNumQuaternions

#sleep timers
data_collection_sleep_timer = 0.01
altimeter_update_sleep_timer = 0.05
sleep_timers = [data_collection_sleep_timer, altimeter_update_sleep_timer] # could be utilized to measure theoretical time deltas

class FlightDataLogger:
    def __init__(self):
        print("Setting up measurement devices")

        # SETUP WITH THREADS THEN WAIT FOR EVERYTHING
        thread_queue = self.setup_hardware() #avoids b2b sleep hassle for setting up configs
        [x.join() for x in thread_queue]

        #needs to be here after init_altimeter is joined
        self.altimeter_update_thread = threading.Thread(target=self.altimeter.update()) #starts variable in this scope so that it is initialized in read-scope
        self.altimeter_update_thread.start() #joined in main readloop
        
        self.flight_package = {
            "imageLocation": None,  # Location of the image (if captured during flight)
            "gyro": {},  # Dictionary to hold gyroscope data
            "altimeter": {},  # Dictionary to hold altimeter data
            "time": -1,  # Time elapsed since the start of data collection
        }

        self.measurement_cycle = 0 # incremented when measurements are taken locally
        self.measurement_modulo = 5 # used to add every nth measurement to transmission payload
        self.measurement_modulo_modifier = 0 #will modify measurement_modulo after last payload finishes

        #for when data collection is faster than data transmission, put items in a buffer to get sent over
        self.transmit_buffer = queue.Queue() #Holds all packets which, in order, will be sent to RPI5
        self.transmit_buffer_limit = 2 # IF PASSED, LOGIC WILL BE SETUP TO INCREASE MEASUREMENT_MODULO

        self.transmit_payload = [] # contains one packet to send to RPI5
        self.transmit_payload_limit = getNumQuaternions() # small enough payload that will allow for less time spent wt preamble

    def setup_hardware(self) -> list:
        
        #****RADIO****
        def init_radio():
            self.radio = RYLR998_Transmit()

        #****GYROSCOPE****
        def init_gyro():
            self.i2c = board.I2C()  # Initializes the I2C interface for communication with the sensor
            self.gyroscope = adafruit_bno055.BNO055_I2C(self.i2c)
            
            # This variable holds the last temperature reading to prevent erroneous readings
            self.gyro_last_temperature_reading = 0xFFFF
        
        #****ALTIMETER****
        def init_altimeter():
            cs_pin = 22
            clock_pin = 11
            data_in_pin = 9
            data_out_pin = 10

            self.altimeter = MS5611(cs_pin, clock_pin, data_in_pin, data_out_pin, data_collection_sleep_timer)

            self.altimeter.update()
            time.sleep(0.1) # allows sensor to breathe

        #works through the sleepiness of the configurations for each module to lessen start timer
        threads = [threading.Thread(target=x) for x in (init_altimeter, init_radio, init_gyro)]
        [x.start() for x in threads]
        
        return threads #joined in outer scope
    
    def wait_for_start_signal(self) -> float:
        response = self.radio.wait_for_start_message()
        return response #sea_level_pressure
    
    def transmitFromBuffer(self, qbuff: queue.Queue): #multiprocessed
        while qbuff.empty():
            time.sleep(0.01)

        while True: #queue buffer starts nonempty

            if qbuff.empty():
                # -= 1 to narrow into an "ideal value" given that the pattern for control-flow
                # execution may oscillate 

                time.sleep(0.1) #TODO test optimal value to avoid overflowing oscillatory patterns
                self.measurement_modulo_modifier -= 1 #make modulo buffer smaller for faster data collection to sync with speed of transmission
                continue
            
            time_delta, quaternions = qbuff.get()
            self.radio.send(time_delta=time_delta, data_points=quaternions)

    def transmit(self, time_delta: int, quaternion: list): #will change layout in the future when we get better radios
        """
        doesn't actually transmit, but takes quaternion and adds it to a payload to be sent later
        if payload is full, gets put into a queue for transmission from a separate process
        
        sends to RPI5_encode in format:
        [td, qt1: list, qt2: [w,x,y,z], ... qt8: [w,x,y,z]]

        time delta is for specific data point, average the running time deltas for better approximations
        """

        if not len(self.transmit_payload): #first quaternion in the first payload
            self.transmit_payload.append(time_delta)
        
        if len(self.transmit_payload) > self.transmit_payload_limit: #payload full, prepare 2 send  
            if self.transmit_buffer.qsize() > self.transmit_buffer_limit:
                #dynamically resize the modulus for collecting data points to uniformly slow 
                #transmission while allowing for smooth interpolation

                self.measurement_modulo += 2

            #modifications to modulo from RYLR998 process-scope
            #doesn't allow changes larger than 2, and that will bring modulo below two
            #TODO look into temperature-based modulo calibration
            self.measurement_modulo = max(2, self.measurement_modulo + max(-2, self.measurement_modulo_modifier))
            self.measurement_modulo_modifier = 0 

            #attempt to transmit and reset payload for next data
            self.transmit_buffer.put(self.transmit_payload)
            print(f"TIME DELTA: {self.transmit_payload[0]}, QUEUE SIZE: {self.transmit_buffer.qsize()}")
            self.transmit_payload = [time_delta, quaternion]
        else:
            #add to payload
            self.transmit_payload.append(quaternion)
            
            #average existing time delta (theoretically equivalent, experimentally variable)
            #will be redundant on first transmit() of each payload as 2*time_delta/2 is silly logic 
            self.transmit_payload[0] = (self.transmit_payload[0] + time_delta) / 2

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

    def log_flight_data(self, sea_level_pressure: float):
        """Log the flight data to a file continuously."""

        #create new logfile in ../flightLogs/logfileNM
        current_file_dir = os.path.dirname(__file__)

        # Navigate to the "main scope" directory (parent of 'outer/')
        main_scope_dir = os.path.abspath(os.path.join(current_file_dir, ".."))

        # Create a file in the "main scope"
        dir_path = os.path.join(main_scope_dir, f"flightLogs/{datetime.date.today().strftime('%m-%d-%Y')}")
        file_path = dir_path + "/logfile.txt"
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        #begin data transmission process to run concurrently and more efficiently than in the downtime of GIL 
        self.transmit_process = multiprocessing.Process(target=self.transmitFromBuffer, args=(self.transmit_buffer,))
        self.transmit_process.start()     

        #used to measure time delta
        start_payload_time = time.time() 
        self.start_time = time.time()
        
        # Open a log file to store flight data, using the current date for naming
        with open(f"{file_path}", "a") as file:
            while True:  # Main loop for continuous data collection

                # Calculate the time elapsed since the start
                self.flight_package["time"] = time.time() - self.start_time

                # Collect sensor data and store in the flight package
                """
                euler and quaternion data are respective to cardinal directions assigned at calibration
                """
            
                self.flight_package["gyro"]["quaternion"] = list(self.gyroscope.quaternion)
                self.flight_package["gyro"]["euler"] = list(self.gyroscope.euler)
                
                if len([x for x in [*self.flight_package["gyro"]["quaternion"], *self.flight_package["gyro"]["euler"]] if x is None]):
                    continue #NoneType encountered in readloop
                
                self.flight_package["gyro"]["linearAcceleration"] = list(self.gyroscope.linear_acceleration)
                self.flight_package["gyro"]["radialVelocity"] = list(self.gyroscope.gyro)
                self.flight_package["gyro"]["magnetic"] = list(self.gyroscope.magnetic)
                self.flight_package["gyro"]["gravity"] = list(self.gyroscope.gravity)
                self.flight_package["gyro"]["temperature"] = self.get_temperature()

                # Capture altimeter pressure and calculate altitude.
                self.altimeter_update_thread.join() #hacky, but since update takes .2 seconds to sleep, thread it and join here
                
                self.flight_package["altimeter"]["temperature"] = float(self.altimeter.returnTemperature()) * (9/5) + 32 #farenheight rocks
                self.flight_package["altimeter"]["pressure"] = self.altimeter.returnPressure()
                self.flight_package["altimeter"]["altitude"] = self.altimeter.returnAltitude(sea_level_pressure)
                
                self.altimeter_update_thread = threading.Thread(target=self.altimeter.update())
                self.altimeter_update_thread.start()
                
                # pprint(self.flight_package)  # Print the flight package to the console for debugging

                # Write the flight package as JSON to the log file
                json_data = json.dumps(self.flight_package) + ",\n"
                
                file.write(json_data)  # Append the JSON data to the log file

                # Add radio transmission for flightPackage every n measurement cycles (self.measurement_modulo is dynamic)
                if self.measurement_cycle % self.measurement_modulo == 0:
                    #time delta (for one measurement in payload), data
                    self.transmit(start_payload_time - (start_payload_time := time.time()), self.flight_package["gyro"]["quaternion"]) #abstracted for actual payload transmission 
                
                self.measurement_cycle += 1  # Increment the measurement cycle counter

                #Delay between data collection cycles to allow gyro refresh
                time.sleep(data_collection_sleep_timer)

if __name__ == "__main__":
    logger = FlightDataLogger()  # Create an instance of FlightDataLogger
    
    #will block main thread until recieved go command from base control
    try:
        sea_level_pressure = float(logger.wait_for_start_signal())
    except Exception as e:
        print(e, "ERR, defaulting to 101.7 for sea_level_pressure")
        sea_level_pressure = 101.7
    logger.log_flight_data(sea_level_pressure)  # Start logging flight data & begin sub process for transmission 
