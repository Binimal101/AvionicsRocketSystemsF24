from reyax import RYLR998, getStartMessage
import time

class RYLR998_Recieve:
    def __init__(self):
        # Initialize UART using pyserial
        uart_port = "/dev/ttyAMA0" #RPI5 config
        baud_rate = 115200

        # Create the RYLR998 object
        RYLR998 = RYLR998(uart_port, baud_rate, 1, address=2, network_id=1)  # Assuming address 2 for receiving

    def send_start_command(self):
        """
        Send message to rocket to begin data_logging
        """

        message = f"AT+SEND={1},{len(getStartMessage())},{getStartMessage()}\r\n"
        self.ser.write(message.encode())

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
            raise RuntimeError(f"Command failed: {message}, Response: {response}")
        
        #TODO deliver visual in outer scope to let people know launch is ready
        return response

    def recieve(self):
        while True:
            received_data = self.read_data()
            if received_data:
                #DECODE and return to Flask scope
                return self.decode(received_data)
            
    def decode(data: str) -> dict:
        """
        Param data: full RYLR998 response ->
        +RCV=<Address>,<Length>,<Data>,<RSSI>,<SNR>
        <Address> Transmitter Address ID
        <Length> Data Length
        **<Data> ASCll Format Data**
        <RSSI> Received Signal Strength Indicator
        <SNR> Signal-to-noise ratio

        Return dict of full transmission data 
        """
        pass
