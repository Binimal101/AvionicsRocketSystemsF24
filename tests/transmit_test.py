import serial, time, struct
import reyax

# Initialize UART using pyserial
uart_port = "/dev/serial0" #RPI02W
baud_rate = 115200

# Create the RYLR998 object
lora = reyax.RYLR998(uart_port, baud_rate, 1, address=1, network_id=1) 

# Test if the module is connected
if (pulseResponse := lora.pulse()):
    print(f"RYLR998 module is connected. Response = {pulseResponse}")
else:
    print(f"RYLR998 module is not responding. Response = '{pulseResponse}'")

# Get the network ID
try:
    print(f"Network ID: {lora.network_id}")
except AttributeError:
    print("Unable to retrieve network ID.")

# Get the address of the module
try:
    print(f"Address: {lora.address}")
except AttributeError:
    print("Unable to retrieve address.")

recipient_address = int(input("Enter recipient address (this device addr = 1):\n>>> "))

payload = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA".encode()
for i in range(50):
    lora.send_data(payload, len(payload), recipient_address=recipient_address)
