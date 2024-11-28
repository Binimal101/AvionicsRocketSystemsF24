from reyax import RYLR998, getStartMessage
import time

class RYLR998_Recieve:
    def __init__(self):
        # Initialize UART using pyserial
        uart_port = "/dev/ttyAMA0" #RPI5 config
        baud_rate = 115200

        # Create the RYLR998 object
        self.RYLR998 = RYLR998(uart_port, baud_rate, 1, address=2, network_id=1)  # Assuming address 2 for receiving

    def send_start_command(self, RPI02W_address: int = 1):
        """
        Send message to rocket to begin data_logging
        """

        message = f"AT+SEND={RPI02W_address},{len(getStartMessage())},{getStartMessage()}\r\n"
        response = self.RYLR998.send_command(message)
        
        #TODO deliver visual in outer scope to let people know launch is ready
        return response

    def recieve(self):
        """
        reads a payload of a time delta, and 8 quaternions
        timeDelta, {
            "rotation_w" : short_to_quaternion(data[i]),
            "rotation_x" : short_to_quaternion(data[i+1]),
            "rotation_y" : short_to_quaternion(data[i+2]),
            "rotation_z" : short_to_quaternion(data[i+3])
        }, {
            "rotation_w" : short_to_quaternion(data[i]),
            "rotation_x" : short_to_quaternion(data[i+1]),
            "rotation_y" : short_to_quaternion(data[i+2]),
            "rotation_z" : short_to_quaternion(data[i+3])
        }, ...
        """
        return self.RYLR998.read_decoded_data()
