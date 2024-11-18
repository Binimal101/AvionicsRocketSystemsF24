import serial
import reyaxTransmit as reyax

# Initialize UART using pyserial
uart_port = "/dev/serial0"  # Update this to the correct port if needed
baud_rate = 115200

# Create the RYLR998 object
lora = reyax.RYLR998(uart_port, baud_rate, 1)

# Test if the module is connected
if lora.pulse:
    print("RYLR998 module is connected.")
else:
    print("RYLR998 module is not responding.")

# Get the network ID
try:
    print(f"Network ID: {lora.networkid}")
except AttributeError:
    print("Unable to retrieve network ID.")

# Get the address of the module
try:
    print(f"Address: {lora.address}")
except AttributeError:
    print("Unable to retrieve address.")

