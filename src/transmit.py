import reyax

class RYLR998_Recieve:
    def __init__(self):
        # Initialize UART using pyserial
        uart_port = "/dev/serial0" #RPI02W
        baud_rate = 115200

        # Create the RYLR998 object
        lora = reyax.RYLR998(uart_port, baud_rate, 1, address=1, network_id=1)

    def encode(data: dict) -> str: #might return bytestring, research
        """
        Param data: will have...
        {
            rotation : [(-pi, pi), (-pi, pi), (-pi, pi)], #roll, pitch, yaw | WRT gyro NOT rocket | radians
            rotation_velocity : [s_float_32, s_float_32, s_float_32], #roll, pitch, yaw | WRT gyro NOT rocket | radians/sec
            lin_acceleration : [s_float_32, s_float_32, s_float_32], #x, y, z | WRT gyro NOT rocket | m/s^2
            temperature : us_float_32, #degrees F
            pressure : us_float_32, #pascals
            altitude : float_32, #meters

        }
        """
        pass
