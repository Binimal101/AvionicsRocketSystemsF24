import serial
import time

class RYLR998:
    def __init__(self, port='/dev/serial0', baudrate=115200, timeout=1, address=1, network_id=1999):
        """
        Initialize the serial connection and configure the module's address and network ID if provided.
        """
        self.ser = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
        time.sleep(1)  # Allow time for the serial connection to initialize

        self.send_command("AT+RESET")
        time.sleep(2) #Allow time for reset

        # Set configurations to optimal rocket telemetry settings
        self.configure_module()
        
        # Configure network ID if provided
        if network_id is not None:
            print("\nsetting NWID")
            self.set_network_id(network_id)
        
        # Configure address if provided
        if address is not None:
            print("\nsetting ADDR")
            self.set_address(address)

    def configure_module(self):
        """
        Configure the module with hardcoded settings.
        """
        print("Configuring RYLR998...")

        # Frequency band: 915 MHz (US ISM band)
        self.send_command('AT+FREQ=915000000')

        # Spreading factor: SF9
        self.send_command('AT+SF=9')

        # Bandwidth: 125 kHz
        self.send_command('AT+BW=125')

        # Coding rate: 4/5
        self.send_command('AT+CR=5')

        # Preamble length: 12
        self.send_command('AT+PREAMBLE=12')

        # Transmission power: 14 dBm
        self.send_command('AT+POWER=14')

        print("Config complete.")
    
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
        response = response.strip()
        if 'ERROR' in response:
            raise RuntimeError(f"Command failed: {command}, Response: {response}")
        
        return response

    def read_data(self):
        """
        Read a line of data.
        """
        while True:
            if self.ser.in_waiting:
                response = self.ser.readline().decode().strip()
                if response:
                    print(f'Received: {response}')
                    return response
            time.sleep(0.1)

    def send_data(self, data: str, recipient_address: int = 0):
        """
        Sends a *STRING* over the network "self.network_id" to be recieved by recipient_address 
        Not efficient for sending binary_floats
        Use struct in a NEW function to send hex_strings? more research needed
        """

        command = f"AT+SEND={recipient_address},{len(data)},{data}"
        self.send_command(command)

    def pulse(self):
        """
        Check if the RYLR998 module is responsive by sending a basic AT command.
        Returns True if the module responds with 'OK'.
        """
        response = self.send_command('AT')
        return response

    def set_network_id(self, network_id):
        """
        Set the network ID of the module.
        """

        command = f"AT+NETWORKID={network_id}"
        response = self.send_command(command)
        
        if 'OK' in response:
            print(f"Network ID set to {network_id}")
            self.network_id = network_id
        else:
            print(f"Failed to set Network ID: {response}")

    def set_address(self, address):
        """
        Set the address of the module.
        """
        
        command = f"AT+ADDRESS={address}"
        response = self.send_command(command)
        
        if 'OK' in response:
            print(f"Address set to {address}")
            self.address = address
        else:
            print(f"Failed to set Address: {response}")

    def close(self):
        """
        Close the serial connection.
        """
        self.ser.close()

