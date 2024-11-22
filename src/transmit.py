from reyax import RYLR998, getPackFormat, getStartMessage, quaternion_to_short, short_to_quaternion, timestamp_to_short
import struct

class RYLR998_Transmit:
    def __init__(self):
        # Initialize UART using pyserial
        uart_port = "/dev/serial0" #RPI02W
        baud_rate = 115200

        # Create the RYLR998 object
        self.lora = RYLR998(uart_port, baud_rate, 1, address=1, network_id=1)
        
    def wait_for_start_message(self):
        print("WAITING FOR START COMMAND FROM BASE CONTROL...")
        while True: #blocks data collection execution in outer scope
            received_data = self.read_data()
            if received_data and received_data == getStartMessage():
                #DECODE and return to Flask scope
                print("RECIEVED, ENTERING DATA COLLECTION AND TRANSMISSION...")
                return True

    def send(self, timestamp, data_points: list) -> bool:
        #GATHER DATAPOINTS
        bytestr = self.encode(timestamp, data_points)
        return self.lora.send_data(data = bytestr + "\r\n".encode(), dataSize = struct.calcsize(getPackFormat))

    def encode(original_timestamp: int, data_points: list) -> bytes:
        """
        Through calculations we expect len(datapoints) == 13, although there are ONLY 12 data points
        
        data_points == [
            dp0, dp1, ... dp11,
        ]
        """
        
        """
        original_timestamp: delta-epoch time in seconds

        Param dp: will have...
        (
            rotation_w | (-1, 1) | WRT gyro NOT rocket | radians
            rotation_x | (-1, 1) | WRT gyro NOT rocket | radians
            rotation_y | (-1, 1) | WRT gyro NOT rocket | radians
            rotation_z | (-1, 1) | WRT gyro NOT rocket | radians
        )

        REWRITE DATA TO INTEGERS FOR SENDING | DIVIDE EQUALLY FOR RECIEVING

        [
            time_stamp:16bit, 
            (w:16bit, x:16bit, y:16bit, z:16bit), 
            (w2:16bit, x2:16bit, y2:16bit, z2:16bit), 
            (w3:16bit, x3:16bit, y3:16bit, z3:16bit), 
            (w4:16bit, x4:16bit, y4:16bit, z4:16bit),
            ...
            (w8:16bit, x8:16bit, y8:16bit, z8:16bit)
        ]
        """

        #build encodable array
        encodable_array = []
        for dp in data_points:
            encodable_array.extend([quaternion_to_short(x) for x in dp])

        payload = struct.pack(getPackFormat(), timestamp_to_short(original_timestamp), *encodable_array)

        print(payload)
        return payload