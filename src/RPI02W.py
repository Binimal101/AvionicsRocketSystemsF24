import threading
import multiprocessing as mp
import json, time, os, datetime
import board, adafruit_bno055
from altimeter import MS5611
from transmit import RYLR998_Transmit
from camera import start_camera

data_collection_sleep_timer = 0.008
altimeter_read_update_timer = 0.05

class FlightDataLogger:
    def __init__(self):
        print("Setting up measurement devices")
        
        # Initialize lock for sensor reading
        self.sensor_lock = threading.Lock()
        
        self.setup_hardware()
        
        self.transmit_queue = mp.Queue()
        self.transmit_process = mp.Process(target=self._transmit_process, args=(self.transmit_queue,))
        self.transmit_process.start()

        # Data structure updated by the sensor thread
        self.flight_package = {
            "gyro": {}, 
            "altimeter": {}, 
            "time": -1
        }

        self._sea_level_pressure = 101.7  # Default until set by wait_for_start_signal
        self._stop_event = threading.Event()

        # Start the dedicated sensor reading thread
        self.altimeter_thread = threading.Thread(target=self._altimeter_update_loop, daemon=True)
        self.altimeter_thread.start()

    def setup_hardware(self):
        # Initialize radio, gyro, altimeter
        self.radio = RYLR998_Transmit()

        self.i2c = board.I2C()
        self.gyroscope = adafruit_bno055.BNO055_I2C(self.i2c)
        self.gyro_last_temperature_reading = 0xFFFF

        cs_pin = 22
        clock_pin = 11
        data_in_pin = 9
        data_out_pin = 10

        self.altimeter = MS5611(cs_pin, clock_pin, data_in_pin, data_out_pin, data_collection_sleep_timer)
        time.sleep(0.1)

    def _transmit_process(self, qbuff: mp.Queue):
        while True:
            payload = qbuff.get() # Wait until item is available
            time_delta, quaternion = payload
            self.radio.send(time_delta, quaternion)

    def transmit(self, time_delta, quaternion):
        try:
            self.transmit_queue.put((time_delta, quaternion))
        except:
            pass

    def wait_for_start_signal(self) -> float:
        response = self.radio.wait_for_start_message()
        self._sea_level_pressure = response
        return response

    def get_temperature(self):
        # Acquire lock if you do any reads from the gyroscope that may conflict with other ops
        result = self.gyroscope.temperature

        if abs(result - self.gyro_last_temperature_reading) == 128:
            result = self.gyroscope.temperature
            if abs(result - self.gyro_last_temperature_reading) == 128:
                return 0b00111111 & result

        self.gyro_last_temperature_reading = result
        return result

    def _altimeter_update_loop(self):
        """
        Dedicated thread for safely updating the altimeter and reading values.
        This ensures the altimeter is only touched by one thread.
        """
        while not self._stop_event.is_set():
            with self.sensor_lock:
                self.altimeter.update()
                # After update, read current values
                temperature = float(self.altimeter.returnTemperature())
                pressure = float(self.altimeter.returnPressure())
                altitude = float(self.altimeter.return_altitude(self._sea_level_pressure))

            # Store them in class variables (protected by lock)
            # In main loop we will read them out under the same lock or just trust that
            # reading them without modification is safe if they're simple data types.
            self._current_temperature = temperature
            self._current_pressure = pressure
            self._current_altitude = altitude

            time.sleep(altimeter_read_update_timer)

    def log_flight_data(self, sea_level_pressure: float):
        self._sea_level_pressure = sea_level_pressure
        start_camera() 
        self.start_time = time.time()
        current_file_dir = os.path.dirname(__file__)
        main_scope_dir = os.path.abspath(os.path.join(current_file_dir, ".."))
        dir_path = os.path.join(main_scope_dir, f"flightLogs/{datetime.date.today().strftime('%m-%d-%Y')}")
        file_path = dir_path + "/logfile.txt"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        start_payload_time = time.time()

        while True:
            # Acquire lock before reading sensor data
            with self.sensor_lock:
                # Build flight_package from current sensor data
                self.flight_package["time"] = time.time() - self.start_time

                quaternion = list(self.gyroscope.quaternion)
                euler = list(self.gyroscope.euler)
                if any(x is None for x in (quaternion + euler)):
                    # If sensor reading is incomplete, skip this iteration
                    continue

                self.flight_package["gyro"]["quaternion"] = quaternion
                self.flight_package["gyro"]["euler"] = euler
                self.flight_package["gyro"]["linearAcceleration"] = list(self.gyroscope.linear_acceleration)
                self.flight_package["gyro"]["radialVelocity"] = list(self.gyroscope.gyro)
                self.flight_package["gyro"]["magnetic"] = list(self.gyroscope.magnetic)
                self.flight_package["gyro"]["gravity"] = list(self.gyroscope.gravity)
                self.flight_package["gyro"]["temperature"] = self.get_temperature()

                # Use data from altimeter_thread
                self.flight_package["altimeter"]["temperature"] = self._current_temperature
                self.flight_package["altimeter"]["pressure"] = self._current_pressure
                self.flight_package["altimeter"]["altitude"] = self._current_altitude

            # Write flight data to file
            with open(file_path, "a") as file:
                json_data = json.dumps(self.flight_package) + ",\n\n"
                file.write(json_data)

            # Transmit quaternion
            self.transmit((time.time() - start_payload_time), quaternion)

            time.sleep(data_collection_sleep_timer)
            start_payload_time = time.time()


if __name__ == "__main__":
    logger = FlightDataLogger()

    try:
        sea_level_pressure = float(logger.wait_for_start_signal())
    except Exception as e:
        print(e, "ERR, defaulting to 101.7 for sea_level_pressure")
        sea_level_pressure = 101.7

    logger.log_flight_data(sea_level_pressure)
