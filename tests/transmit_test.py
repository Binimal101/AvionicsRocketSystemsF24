import serial, time
import reyax_test as reyax

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

recipient_address = int(input("Enter recipient address:\n>>> "))
while input("Test transmission (Y,N)?\n>>> ").lower() == "y":
    lora.send_data(data = (time_sent := str(time.time())), recipient_address = recipient_address)
    print(f"message sent at {time_sent}")
