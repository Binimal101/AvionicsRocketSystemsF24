import serial
import reyax
import time

# Initialize UART using pyserial
uart_port = "/dev/serial0"  # Update this to the correct port if needed
baud_rate = 115200

# Create the RYLR998 object
lora = reyax.RYLR998(uart_port, baud_rate, 1, address=2, network_id=1)  # Assuming address 2 for receiving

# Test if the module is connected
if (pulseResponse := lora.pulse()):
    print(f"RYLR998 module is connected. Response = {pulseResponse}")
else:
    print(f"RYLR998 module is not responding. Response = '{pulseResponse}'")

print("\nListening for incoming transmissions...")

try:
    while True:
        # Continuously read data from the module
        received_data = lora.read_data()
        if received_data:
            print(f"Received message: {received_data}")
        time.sleep(0.1)  # Add a slight delay to reduce CPU usage
except KeyboardInterrupt:
    print("\nExiting receiver script.")
finally:
    lora.close()

