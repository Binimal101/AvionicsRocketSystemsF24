import serial
import time

class RYLR998:
    def __init__(self, port='/dev/serial0', baudrate=115200, timeout=1):
        """
        Initialize the serial connection
        """
        self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        time.sleep(1)  # Allow time for the serial connection to initialize

    def send_command(self, command):
        """
        Send an AT command and return the response.
        """
        full_command = f'{command}\r\n'
        self.ser.write(full_command.encode())
        time.sleep(0.1)
        response = ''
        while True:
            if self.ser.in_waiting:
                response += self.ser.read(self.ser.in_waiting).decode()
                if 'OK' in response or 'ERROR' in response:
                    break
            else:
                break
        return response.strip()

    def read_data(self):
        """
        reads line of data
        """

        while True:
            if self.ser.in_waiting:
                response = self.ser.readline().decode().strip()
                if response:
                    print(f'Received: {response}')
                    return response
            time.sleep(0.1)
   
    def pulse(self):
        """
        Check if the RYLR998 module is responsive by sending a basic AT command.
        Returns True if the module responds with 'OK'.
        """
        response = self.send_command('AT')
        return 'OK' in response

    def close(self):
        """
        Close the serial connection.
        """
        self.ser.close()

