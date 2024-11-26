from reyax import RYLR998, getPackFormat, getStartMessage, quaternion_to_short, time_delta_to_short
import struct, time

class RYLR998_Transmit:
    def __init__(self):
        # Initialize UART using pyserial
        uart_port = "/dev/serial0" #RPI02W
        baud_rate = 115200

        # Create the RYLR998 object
        self.lora = RYLR998(uart_port, baud_rate, 1, address=1, network_id=1)
        self.ser = self.lora.ser # for more direct access to device

    def wait_for_start_message(self):
        print("WAITING FOR START COMMAND FROM BASE CONTROL...")
        while True: #blocks data collection execution in outer scope
            received_data = self.read_data()
            
            if received_data and getStartMessage() in received_data: #start message here soley to lessen error potential in comms
                #DECODE and return to Flask scope
                print("RECIEVED, ENTERING DATA COLLECTION AND TRANSMISSION...")
                pressure = received_data.split("|")[1] #float of pressure

                return pressure 

    def read_data(self):
        """
        Read a line of data.
        """
        while True:
            if self.ser.in_waiting:
                response = self.ser.readline().decode().strip()
                if response:
                    print(response)
                    if "," in response:
                        return response.split(",")[2] #TODO check if always <data> block
            
    def send(self, time_delta, data_points: list) -> bool:
        bytestr = self.encode(time_delta, data_points)
        return self.lora.send_data(data = bytestr + "\r\n".encode(), dataSize = struct.calcsize(getPackFormat))

    def encode(time_delta: int, data_points: list) -> bytes:
        """
        Through calculations we expect len(datapoints) == 9, although there are ONLY 8 data points
        
        data_points == [
            dp0, dp1, ... dp11,
        ]
        
        time_delta: estimated time between quaternions in seconds

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

        payload = struct.pack(getPackFormat(), time_delta_to_short(time_delta), *encodable_array)

        print(payload)
        return payload
