import RPi.GPIO as GPIO
import time
import numpy

class MS5611(object):
    
    # MS5611 commands and addresses
    __MS5611_RESET             = 0x1E        # 
    
    __MS5611_CONVERT_D1_256    = 0x40        #
    __MS5611_CONVERT_D1_512    = 0x42        #
    __MS5611_CONVERT_D1_1024   = 0x44        #
    __MS5611_CONVERT_D1_2048   = 0x46        #
    __MS5611_CONVERT_D1_4096   = 0x48        #
    
    __MS5611_CONVERT_D2_256    = 0x50        #
    __MS5611_CONVERT_D2_512    = 0x52        #
    __MS5611_CONVERT_D2_1024   = 0x54        #
    __MS5611_CONVERT_D2_2048   = 0x56        #
    __MS5611_CONVERT_D2_4096   = 0x58        #
    
    __MS5611_ADC_READ          = 0x00        #

    __MS5611_C1                = 0xA2
    __MS5611_C2                = 0xA4
    __MS5611_C3                = 0xA6
    __MS5611_C4                = 0xA8
    __MS5611_C5                = 0xAA
    __MS5611_C6                = 0xAC
    __MS5611_D1                = 0xAC
    __MS5611_D2                = 0xAE
        
    def __init__(self, cs_pin, clock_pin, data_in_pin, data_out_pin, update_sleep_timer, board = GPIO.BCM):

        '''Initialize Soft (Bitbang) SPI bus
        Parameters:
        - cs_pin:    Chip Select (CS) / Slave Select (SS) pin (Any GPIO)  
        - clock_pin: Clock (SCLK / SCK) pin (Any GPIO)
        - data_in_pin:  Data input (SO / MOSI) pin (Any GPIO)
	    - data_out_pin: Data output (MISO) pin (Any GPIO)
        - board:     (optional) pin numbering method as per RPi.GPIO library (GPIO.BCM (default) | GPIO.BOARD)
        '''        

        self.board = board
        self.cs_pin = cs_pin
        self.clock_pin = clock_pin
        self.data_in_pin = data_in_pin
        self.data_out_pin = data_out_pin

        self.update_sleep_timer = update_sleep_timer
                
        # Default compensation parameters for MS5611
        self.C1 = 40127         # UINT16
        self.C2 = 36924         # UINT16
        self.C3 = 23317         # UINT16
        self.C4 = 23282         # UINT16
        self.C5 = 33464         # UINT16
        self.C6 = 28312         # UINT16        
        self.D1 = 9085466       # UINT32
        self.D2 = 8569150       # UINT32
        
        self.dT = 0          # INT32
        self.TEMP = 0        # INT32
        self.OFF = 0   # INT64
        self.SENS = 0  # INT64
        self.P = 0         # INT32  
                
        self.ground_pressure = None #initialized on first call to returnAltitude

        # Initialize needed GPIO
        GPIO.setmode(self.board)
        GPIO.setup(self.cs_pin, GPIO.OUT)
        GPIO.setup(self.clock_pin, GPIO.OUT)
        GPIO.setup(self.data_in_pin, GPIO.IN)
        GPIO.setup(self.data_out_pin, GPIO.OUT)

        # Pull chip select high to make chip inactive
        GPIO.output(self.cs_pin, GPIO.HIGH)
                      
        # Reset sensor
        self._send_command(self.__MS5611_RESET)
        time.sleep(0.03)

        # Load compensation parameters
        print("reading coeffs")
        self._read_coefficients()
        time.sleep(1.0)
        
        # Updating data                
        self.update()   

    def _spixfer(self, x):
        '''SPI send/recieve function'''
        reply = 0
        for i in range(7,-1,-1):
            reply <<= 1
            GPIO.output(self.clock_pin, GPIO.LOW)
            GPIO.output(self.data_out_pin, x & (1<<i))
            GPIO.output(self.clock_pin, GPIO.HIGH)
            if (GPIO.input(self.data_in_pin)):
                reply |= 1
        return reply
       
    def _read16(self, register):
        '''Reads 16-bits from specified register'''
        GPIO.output(self.cs_pin, GPIO.LOW)  
        self._spixfer(register)    # send request to read from register
        value = (self._spixfer(0) << 8) | self._spixfer(0) 
        GPIO.output(self.cs_pin, GPIO.HIGH)
        
        """
        # Add validation
        if value == 0xFFFF:  # Invalid read
            raise IOError(f"Failed to read register {hex(register)}")
        """

        return value

    def _read24(self, register):
        '''Reads 24-bits from specified register'''
        GPIO.output(self.cs_pin, GPIO.LOW)
        self._spixfer(register)    # send request to read from register
        value = (self._spixfer(0) << 16) | (self._spixfer(0) << 8) | self._spixfer(0)  
        GPIO.output(self.cs_pin, GPIO.HIGH)
        return value
    
    def _send_command(self, command):
        '''Sends command via SPI'''
        GPIO.output(self.cs_pin, GPIO.LOW)
        self._spixfer(command) 
        GPIO.output(self.cs_pin, GPIO.HIGH)     

    def _read_coefficients(self):
        '''Reads the factory-set coefficients'''
        self.C1 = self._read16(self.__MS5611_C1)   # UINT16
        self.C2 = self._read16(self.__MS5611_C2)   # UINT16
        self.C3 = self._read16(self.__MS5611_C3)   # UINT16
        self.C4 = self._read16(self.__MS5611_C4)   # UINT16
        self.C5 = self._read16(self.__MS5611_C5)   # UINT16
        self.C6 = self._read16(self.__MS5611_C6)   # UINT16

        """
        if self.C1 == 0 or self.C6 == 0:
            raise ValueError("Invalid calibration coefficients read from MS5611")
        """

        print('C1 = {0:10d}'.format(self.C1))
        print('C2 = {0:10d}'.format(self.C2))
        print('C3 = {0:10d}'.format(self.C3))
        print('C4 = {0:10d}'.format(self.C4))
        print('C5 = {0:10d}'.format(self.C5))
        print('C6 = {0:10d}'.format(self.C6))
       
            
    def _read_adc(self):
        GPIO.output(self.cs_pin, GPIO.LOW)
        dump = self._spixfer(self.__MS5611_ADC_READ)    # send request to read from register
        time.sleep(0.1)
        byteH = self._spixfer(0)    # send request to read from register
        byteM = self._spixfer(0)    # send request to read from register
        byteL = self._spixfer(0)    # send request to read from register
        value = (byteH << 16) | (byteM << 8) | byteL 
        GPIO.output(self.cs_pin, GPIO.HIGH)
        return value  
      
    def _refreshPressure(self, OSR = __MS5611_CONVERT_D1_4096):
        self._send_command(OSR)
        
        
    def _refreshTemperature(self, OSR = __MS5611_CONVERT_D2_4096):
        self._send_command(OSR)
               
    def _readPressure(self):
        self.D1 = self._read_adc()
        
    def _readTemperature(self):
        self.D2 = self._read_adc()
        
    def update(self):
        self._refreshPressure()
        time.sleep(self.update_sleep_timer / 2)
        self._readPressure()
        
        self._refreshTemperature()
        time.sleep(self.update_sleep_timer / 2)
        self._readTemperature()
        
        self.calculatePressureAndTemperature()

    def returnPressure(self):
        return '{:.3f}'.format(self.PRES)		    
        
    def returnTemperature(self):
        return '{:.2f}'.format(self.TEMP)
    
    def calculatePressureAndTemperature(self):
        dT = self.D2 - self.C5 * 2**8
        self.TEMP = 2000 + dT * self.C6 / 2**23
        
        OFF = self.C2 * 2**16 + (self.C4 * dT) / 2**7
        SENS = self.C1 * 2**15 + (self.C3 * dT) / 2**8
        
        if (self.TEMP >= 2000):
            T2 = 0
            OFF2 = 0
            SENS2 = 0
        elif (self.TEMP < 2000):
            T2 = dT * dT / 2**31
            OFF2 = 5 * ((self.TEMP - 2000) ** 2) / 2
            SENS2 = OFF2 / 2
        elif (self.TEMP < -1500):
            OFF2 = OFF2 + 7 * ((self.TEMP + 1500) ** 2)
            SENS2 = SENS2 + 11 * (self.TEMP + 1500) ** 2 / 2
        
        self.TEMP = self.TEMP - T2
        OFF = OFF - OFF2
        SENS = SENS - SENS2
        
        self.PRES = (self.D1 * SENS / 2**21 - OFF) / 2**15
        
        self.TEMP = self.TEMP / 100.0 # Temperature, C
        self.PRES = self.PRES / 1000.0 # Pressure, kPa
         
    def returnAltitude(self):

        if not type(self.PRES) == float or self.PRES < 0:
            print("pressure syncing, skipping valuation")
            return 0
        
        if not self.ground_pressure:
            self.ground_pressure = self.PRES
        
        altitude = 44330 * (1.0 - numpy.power(self.PRES / self.ground_pressure, 0.1903))
        return altitude