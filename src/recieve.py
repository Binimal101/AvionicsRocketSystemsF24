import reyax

class RYLR998_Recieve:
    def __init__(self):
        # Initialize UART using pyserial
        uart_port = "/dev/ttyAMA0" #RPI5 config
        baud_rate = 115200

        # Create the RYLR998 object
        RYLR998 = reyax.RYLR998(uart_port, baud_rate, 1, address=2, network_id=1)  # Assuming address 2 for receiving

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
