"""
This module handles the collection and logging of flight data from sensors.
It retrieves sensor data and writes it to a log file for later analysis.
"""

#built-in
import threading
import multiprocessing as mp
import json, time, os, datetime

#embedded stuff
import board, adafruit_bno055

#files
from altimeter import MS5611
from transmit import RYLR998_Transmit
from camera import start_camera

#sleep timers
data_collection_sleep_timer = 0.008 #TODO test

altimeter_update_sleep_timer = 0.01 #tested
sleep_timers = [data_collection_sleep_timer, altimeter_update_sleep_timer] # could be utilized to measure theoretical time deltas

def fixQuaternionRotatation(quaternion: list) -> list:
    """
    fixes axes so that data is wrt rocket, not sensor

    :param quaternion: [w,x,y,z] wrt sensor, through testing, 
    
    TODO test: quaternion should be [w,y,z,x] wrt rocket?
    """

    return quaternion

class FlightDataLogger:
    def __init__(self):
        print("Setting up measurement devices")

        # SETUP WITH THREADS THEN WAIT FOR EVERYTHING
        thread_queue = self.setup_hardware() #avoids b2b sleep hassle for setting up configs
        [x.join() for x in thread_queue]
        
        self.transmit_queue = mp.Queue()
        self.transmit_process = mp.Process(target=self._transmit_process, args=(self.transmit_queue,))
        self.transmit_process.start()

        self.flight_package = {
            "imageLocation": None,  # Location of the image (if captured during flight)
            "gyro": {},  # Dictionary to hold gyroscope data
            "altimeter": {},  # Dictionary to hold altimeter data
            "time": -1,  # Time elapsed since the start of data collection
        }

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
    
    def _transmit_process(self, qbuff: mp.Queue):
        while True:
            payload = qbuff.get() #will wait the process until an item is available to get

            time_delta, quaternion = payload
            self.radio.send(time_delta, quaternion)

    def transmit(self, time_delta, quaternion):
        try:
            self.transmit_queue.put((time_delta, quaternion))
        except:
            pass

    def wait_for_start_signal(self) -> float:
        response = self.radio.wait_for_start_message()
        return response #sea_level_pressure

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

        #when thread spawned, self.altimeter will modify these for pickens in event-loop
        global pressure, temperature, altitude
        pressure, temperature, altitude = 0, 0, 0

        def readAltimeterValues():
            while True:
                global pressure, temperature, altitude
                
                temperature = float(self.altimeter.returnTemperature()) * (9/5) + 32 #farenheight rocks
                pressure = self.altimeter.returnPressure()
                altitude = self.altimeter.return_altitude(sea_level_pressure)
                
                self.altimeter.update() #sends signal to device to ready new information

                threading.Event().wait(0.02) #tested to be reliable with altimeter values

        altimeter_read_thread = threading.Thread(target=readAltimeterValues)
        altimeter_read_thread.start()

        #create new logfile in ../flightLogs/logfileNM
        current_file_dir = os.path.dirname(__file__)

        # Navigate to the "main scope" directory (parent of 'outer/')
        main_scope_dir = os.path.abspath(os.path.join(current_file_dir, ".."))
        
        # Create a file in the "main scope"
        dir_path = os.path.join(main_scope_dir, f"flightLogs/{datetime.date.today().strftime('%m-%d-%Y')}")
        file_path = dir_path + "/logfile.txt"
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        #used to measure time delta
        start_payload_time = time.time() 
        self.start_time = time.time()

        start_camera() #Popen's a subprocess for recording data, t=0 ~ self.start_time

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
                self.flight_package["gyro"]["radialVelocity"] = fixQuaternionRotatation(list(self.gyroscope.gyro))
                self.flight_package["gyro"]["magnetic"] = list(self.gyroscope.magnetic)
                self.flight_package["gyro"]["gravity"] = list(self.gyroscope.gravity)
                self.flight_package["gyro"]["temperature"] = self.get_temperature()
                
                #updates in seperate thread as refresh rate is only 20hz, just count same values until ready to refresh
                self.flight_package["altimeter"]["temperature"] = temperature
                self.flight_package["altimeter"]["pressure"] = pressure
                self.flight_package["altimeter"]["altitude"] = altitude
   
                # Write the flight package as JSON to the log file
                json_data = json.dumps(self.flight_package) + ",\n"
                
                file.write(json_data)  # Append the JSON data to the log file
                            
                self.transmit(time_delta = (time.time()) - start_payload_time, quaternion = self.flight_package["gyro"]["quaternion"])

                time.sleep(data_collection_sleep_timer)
                
                start_payload_time = time.time()

if __name__ == "__main__":
    logger = FlightDataLogger()  # Create an instance of FlightDataLogger
    
    #will block main thread until recieved go command from base control
    try:
        sea_level_pressure = float(logger.wait_for_start_signal())
    except Exception as e:
        print(e, "ERR, defaulting to 101.7 for sea_level_pressure")
        sea_level_pressure = 101.7
    
    logger.log_flight_data(sea_level_pressure)  # Start logging flight data & begin sub process for transmission 