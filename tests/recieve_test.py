import serial
import reyax_test as reyax
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

data_points_taken = 0
time_deltas = []  # List to store time deltas
data_point_numbers = [] #List to store number of data points at each time delta

try:
    plt.ion()  # Turn on interactive plotting
    fig, ax = plt.subplots() #Create plot only once
    line, = ax.plot(data_point_numbers, time_deltas)  # Initialize plot line, comma is important
    ax.set_xlabel("Data Point Number")
    ax.set_ylabel("Time Delta (seconds)")
    ax.set_title("Time to Travel vs. Message Count")

    while True:
        received_data = lora.read_data()
        if received_data:
            received_time = time.time()
            try:
                sent_time = float(received_data.split(",")[2]) 
                time_delta = received_time - sent_time
                
                data_points_taken += 1
                time_deltas.append(time_delta)
                data_point_numbers.append(data_points_taken)

                # Update plot data
                line.set_xdata(data_point_numbers)
                line.set_ydata(time_deltas)

                # Autoscale axis and redraw the plot
                ax.relim()
                ax.autoscale_view()
                fig.canvas.draw()
                fig.canvas.flush_events()
                print(f"Time Delta: {time_delta:.4f} seconds")
            except ValueError:
                print("Could not parse sent time from received data.")

        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nExiting receiver script.")

finally:
    lora.close()
    plt.ioff() # Turn off interactive plotting
    plt.show() # Keep plot open after program ends