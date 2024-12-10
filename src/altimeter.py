# pylint: disable=invalid-name, consider-using-from-import, too-many-instance-attributes, too-many-arguments, E1101, unused-private-member
"""
This module contains the Altimeter class, which interfaces with the altimeter sensor
to read pressure and temperature values. It includes functions to calculate altitude, 
temperature, and pressure, and to handle sensor initialization and data updates.

It uses a variety of sensor coefficients to perform precise calculations and handle sensor 
readings, including error handling and data formatting.

Module components:
- Altimeter class with methods for pressure and temperature readings
- Sensor initialization and calibration
- Logging of data and errors during operation
"""
import time
import logging
import numpy
import RPi.GPIO as GPIO
import logging_config  # Import the logging configuration

# Call the setup function to configure logging
logging_config.setup_logging()

class MS5611:
    """
    Class representing the MS5611 Barometric Pressure and Temperature Sensor.
    Implements soft SPI communication and provides methods for sensor data reading and calculations.
    """

    # MS5611 commands and addresses
    __MS5611_RESET = 0x1E  # Reset command

    # Commands for converting pressure (D1) and temperature (D2)
    __MS5611_CONVERT_D1_256 = 0x40
    __MS5611_CONVERT_D1_512 = 0x42
    __MS5611_CONVERT_D1_1024 = 0x44
    __MS5611_CONVERT_D1_2048 = 0x46
    __MS5611_CONVERT_D1_4096 = 0x48

    __MS5611_CONVERT_D2_256 = 0x50
    __MS5611_CONVERT_D2_512 = 0x52
    __MS5611_CONVERT_D2_1024 = 0x54
    __MS5611_CONVERT_D2_2048 = 0x56
    __MS5611_CONVERT_D2_4096 = 0x58

    # Register to read ADC value
    __MS5611_ADC_READ = 0x00

    # PROM read commands for calibration coefficients
    __MS5611_C1 = 0xA2
    __MS5611_C2 = 0xA4
    __MS5611_C3 = 0xA6
    __MS5611_C4 = 0xA8
    __MS5611_C5 = 0xAA
    __MS5611_C6 = 0xAC

    # pylint: disable=R0917
    def __init__(self, cs_pin, clock_pin, data_in_pin, data_out_pin,
             update_sleep_timer, board=GPIO.BCM):
        """
        Initialize the MS5611 sensor with soft SPI communication.

        Args:
            cs_pin (int): Chip Select (CS) pin.
            clock_pin (int): Clock (SCK) pin.
            data_in_pin (int): Data input (MOSI) pin.
            data_out_pin (int): Data output (MISO) pin.
            update_sleep_timer (float): Time (seconds) to wait between updates.
            board (int): GPIO mode (default: GPIO.BCM).
        """
        try:
            # Set up GPIO pins
            self.board = board
            self.cs_pin = cs_pin
            self.clock_pin = clock_pin
            self.data_in_pin = data_in_pin
            self.data_out_pin = data_out_pin

            # Time (in seconds) to wait between updates to the sensor
            self.update_sleep_timer = update_sleep_timer

            # Default compensation parameters
            self.C1 = 40127
            self.C2 = 36924
            self.C3 = 23317
            self.C4 = 23282
            self.C5 = 33464
            self.C6 = 28312
            self.D1 = 9085466
            self.D2 = 8569150

            self.dT = 0
            self.TEMP = 0
            self.OFF = 0
            self.SENS = 0
            self.PRES = 0

            # Initialize GPIO
            GPIO.setmode(self.board)
            GPIO.setup(self.cs_pin, GPIO.OUT)
            GPIO.setup(self.clock_pin, GPIO.OUT)
            GPIO.setup(self.data_in_pin, GPIO.IN)
            GPIO.setup(self.data_out_pin, GPIO.OUT)

            # Pull chip select high to make chip inactive
            GPIO.output(self.cs_pin, GPIO.HIGH)

            # Reset the sensor
            self._send_command(self.__MS5611_RESET)
            time.sleep(0.03)

            # Read calibration coefficients
            logging.info("Reading calibration coefficients.")
            print("reading coeffs")
            self._read_coefficients()
            time.sleep(1.0)

            # Update sensor data
            self.update()

        except Exception as e:
            logging.error("Error initializing MS5611 sensor: %s", e)
            raise

    def _spixfer(self, x):
        """
        Perform SPI data transfer.
        
        Args:
            x (int): Data to send (8 bits).
        
        Returns:
            int: Received data (8 bits).
        """
        try:
            reply = 0
            for i in range(7, -1, -1):
                reply <<= 1
                GPIO.output(self.clock_pin, GPIO.LOW)
                GPIO.output(self.data_out_pin, x & (1 << i))
                GPIO.output(self.clock_pin, GPIO.HIGH)
                if GPIO.input(self.data_in_pin):
                    reply |= 1
            return reply
        except Exception as e:
            logging.error("Error in SPI transfer: %s", e)
            raise

    def _read16(self, register):
        """
        Read a 16-bit value from a given register.
        
        Args:
            register (int): Register address.
        
        Returns:
            int: 16-bit value read from the register.
        """
        try:
            GPIO.output(self.cs_pin, GPIO.LOW)
            self._spixfer(register)
            value = (self._spixfer(0) << 8) | self._spixfer(0)
            GPIO.output(self.cs_pin, GPIO.HIGH)
            return value
        except Exception as e:
            logging.error("Error reading 16-bit value from register %d: %s", register, e)
            raise

    def _read24(self, register):
        """
        Read a 24-bit value from a given register.
        
        Args:
            register (int): Register address.
        
        Returns:
            int: 24-bit value read from the register.
        """
        try:
            GPIO.output(self.cs_pin, GPIO.LOW)
            self._spixfer(register)
            value = (self._spixfer(0) << 16) | (self._spixfer(0) << 8) | self._spixfer(0)
            GPIO.output(self.cs_pin, GPIO.HIGH)
            return value
        except Exception as e:
            logging.error("Error reading 24-bit value from register %d: %s", register, e)
            raise

    def _send_command(self, command):
        """
        Send a command to the sensor.
        
        Args:
            command (int): Command to send.
        """
        GPIO.output(self.cs_pin, GPIO.LOW)
        self._spixfer(command)
        GPIO.output(self.cs_pin, GPIO.HIGH)

    def _read_coefficients(self):
        """
        Read the factory-set calibration coefficients.
        """
        try:
            self.C1 = self._read16(self.__MS5611_C1)
            self.C2 = self._read16(self.__MS5611_C2)
            self.C3 = self._read16(self.__MS5611_C3)
            self.C4 = self._read16(self.__MS5611_C4)
            self.C5 = self._read16(self.__MS5611_C5)
            self.C6 = self._read16(self.__MS5611_C6)

            # Logging coefficients
            for idx, coeff in enumerate(
                [self.C1, self.C2, self.C3, self.C4, self.C5, self.C6], start=1):
                logging.info("C%d = %d", idx, coeff)
                print(f'C{idx} = {coeff:10d}')
        except Exception as e:
            logging.error("Error reading calibration coefficients: %s", e)
            raise

    def _read_adc(self):
        """
        Read a 24-bit ADC value from the sensor.
        
        Returns:
            int: ADC value.
        """
        try:
            GPIO.output(self.cs_pin, GPIO.LOW)
            self._spixfer(self.__MS5611_ADC_READ)
            time.sleep(0.1)
            value = (self._spixfer(0) << 16) | (self._spixfer(0) << 8) | self._spixfer(0)
            GPIO.output(self.cs_pin, GPIO.HIGH)
            return value
        except Exception as e:
            logging.error("Error reading ADC value from sensor: %s", e)
            raise


    def _refresh_pressure(self, OSR=__MS5611_CONVERT_D1_4096):
        """
        Refresh pressure data by sending the corresponding conversion command.
        
        Args:
            OSR (int): Oversampling rate (default: 4096).
        """
        try:
            logging.info("Refreshing pressure with OSR = %d", OSR)
            self._send_command(OSR)
        except Exception as e:
            logging.error("Error refreshing pressure with OSR %s: %s", OSR, e)
            raise

    def _refresh_temperature(self, OSR=__MS5611_CONVERT_D2_4096):
        """
        Refresh temperature data by sending the corresponding conversion command.
        
        Args:
            OSR (int): Oversampling rate (default: 4096).
        """
        try:
            logging.info("Refreshing temperature with OSR = %s", OSR)
            self._send_command(OSR)
        except Exception as e:
            logging.error("Error refreshing temperature with OSR %s: %s", OSR, e)
            raise

    def _read_pressure(self):
        """
        Read the pressure data from the sensor ADC.
        """
        try:
            logging.info("Reading pressure data from ADC.")
            self.D1 = self._read_adc()
        except Exception as e:
            logging.error("Error reading pressure data: %s", e)
            raise

    def _read_temperature(self):
        """
        Read the temperature data from the sensor ADC.
        """
        try:
            logging.info("Reading temperature data from ADC.")
            self.D2 = self._read_adc()
        except Exception as e:
            logging.error("Error reading temperature data: %s", e)
            raise

    def update(self):
        """
        Update the pressure and temperature readings.
        """
        try:
            self._refresh_pressure()
            time.sleep(self.update_sleep_timer / 2)
            self._read_pressure()

            self._refresh_temperature()
            time.sleep(self.update_sleep_timer / 2)
            self._read_temperature()

            self._calculate_pressure_and_temperature()

        except Exception as e:
            logging.error("Error updating sensor data: %s", e)
            print(f"ALTIMETER UPDATE FAILURE, {e}", flush=True)

    def returnPressure(self):
        """
        Return the current pressure value, formatted to 3 decimal places.
        
        Returns:
            str: Formatted pressure value in kPa.
        """
        try:
            logging.info("Returning pressure value: %.3f kPa", self.PRES)
            return f'{self.PRES:.3f}'
        except Exception as e:
            logging.error("Error returning pressure value: %s", e)
            print(f"ALTIMETER RETURN PRESSURE FAILURE, {e}", flush=True)

    def returnTemperature(self):
        """
        Return the current temperature value, formatted to 2 decimal places.
        
        Returns:
            str: Formatted temperature value in degrees Celsius.
        """
        try:
            logging.info("Returning temperature value: %.2f °C", self.TEMP)
            return f'{self.TEMP:.2f}'
        except Exception as e:
            logging.error("Error returning temperature value: %s", e)
            print(f"ALTIMETER RETURN TEMPERATURE FAILURE, {e}", flush=True)


    def _calculate_pressure_and_temperature(self):
        """
        Perform compensation calculations for temperature and pressure.
        """
        dT = self.D2 - self.C5 * 2**8
        self.TEMP = 2000 + dT * self.C6 / 2**23

        T2 = 0
        OFF = self.C2 * 2**16 + (self.C4 * dT) / 2**7
        SENS = self.C1 * 2**15 + (self.C3 * dT) / 2**8

        if self.TEMP >= 2000:
            T2 = 0
            OFF2 = 0
            SENS2 = 0
        elif self.TEMP < 2000:
            T2 = dT * dT / 2**31
            OFF2 = 5 * ((self.TEMP - 2000) ** 2) / 2
            SENS2 = OFF2 / 2
        elif self.TEMP < -1500:
            T2 = dT * dT / 2**31
            OFF2 = OFF2 + 7 * ((self.TEMP + 1500) ** 2)
            SENS2 = SENS2 + 11 * (self.TEMP + 1500) ** 2 / 2

        self.TEMP = self.TEMP - T2
        OFF = OFF - OFF2
        SENS = SENS - SENS2

        self.PRES = (self.D1 * SENS / 2**21 - OFF) / 2**15

        self.TEMP = self.TEMP / 100.0 # Temperature, C
        self.PRES = self.PRES / 1000.0 # Pressure, kPa

    def return_altitude(self, sea_level_kPa=101.325):
        """
        Calculate altitude based on pressure readings.
        """

        if not type(self.PRES) == float or self.PRES < 0:
            return -1 #clean invalid data post-process
        
        altitude = 44330 * (1.0 - numpy.power(self.PRES / sea_level_kPa, 0.1903))
        return f'{altitude:.2f}'
