import serial
import reyax

# Initialize UART using pyserial
uart_port = "/dev/serial0"  # Update this to the correct port if needed
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

transmission_recipient = int(input("Enter recipient address:\n>>> "))
if input("Test transmission (Y,N)?\n>>> ").lower() == "y":
    lora.send_data(data=input("Enter message:\n>>> "), transmission_recipient=transmission_recipient)

