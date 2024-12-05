import serial
import reyax
import time

import matplotlib.pyplot as plt

data_points_taken = 0
data_point_numbers = []
time_deltas = []

# Initialize UART using pyserial
uart_port = "/dev/ttyAMA0" #RPI5 config
baud_rate = 115200

# Create the RYLR998 object
lora = reyax.RYLR998(uart_port, baud_rate, 1, address=2, network_id=1)  # Assuming address 2 for receiving

# Test if the module is connected
if (pulseResponse := lora.pulse()):
    print(f"RYLR998 module is connected. Response = {pulseResponse}")
else:
    print(f"RYLR998 module is not responding. Response = '{pulseResponse}'")

print("\nListening for incoming transmissions...")
while True:
    received_data = lora.read_data()
    if received_data:
        print("Data recieved: '{recieved_data}'")
    
    time.sleep(0.01)