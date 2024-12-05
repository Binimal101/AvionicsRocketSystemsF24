from hashlib import sha256
from pprint import pprint
from dotenv import load_dotenv
import os
import threading
from queue import Queue
from interpolation import interpolate_quaternions
from time import sleep

from flask import Flask, render_template, request, url_for
from flask_socketio import SocketIO, send, emit

from recieve import RYLR998_Recieve

load_dotenv(os.getcwd() + "/.env")
hashedPassword = os.environ.get("hashedPassword")

launchSequenceInitiated = False
isBroadcasting = False  # Tracks if data is currently being broadcasted

# Shared queue & radio for communication between threads while reducing proc overhead
data_queue, radio = None, None

def get_data_queue(): #lazy load
    global data_queue

    if data_queue is None:
        data_queue = Queue()
    
    return data_queue

def get_radio(): #lazy load
    global radio

    if radio is None:
        radio = RYLR998_Recieve()
    
    return radio


app = Flask(__name__)
socketio = SocketIO(app)

# ROUTES
@app.route("/")
def index():
    global radio
    radio = get_radio()

    return render_template("index.html")

@app.route("/visualize")
def visualize():
    return render_template("visualize.html")

# SOCKET-IO EVENTS
@socketio.on("check_password")
def checkPass(data):
    """
    Checks password emission from webapp homepage, if true, sends start sig & begins visualization.
    """
    global hashedPassword, radio, launchSequenceInitiated

    userpass = data.get("password", "")
    hashedInput = sha256(userpass.encode()).hexdigest()
    
    print(userpass, hashedInput, hashedPassword)
    
    # Compare hashed input to hashed password
    if hashedInput == hashedPassword:
        emit("validation_result", {"success": True})
        # Begin data collection & provide sea_level_pressure
        radio.send_start_command(float(data.get("sea_level_pressure", 101.7)))
        launchSequenceInitiated = True
    else:
        emit("validation_result", {"success": False})

@socketio.on("request_data")
def handle_request_data(data):
    """
    Initiates data handling only once during execution, ensuring proper coordination between threads.
    """
    global launchSequenceInitiated, isBroadcasting, data_queue

    if not launchSequenceInitiated:
        return

    # Prevent multiple instances of broadcasting
    if isBroadcasting:
        return

    isBroadcasting = True  # Mark broadcasting as active

    data_queue = get_data_queue()

    send_thread = threading.Thread(target=send_data)
    send_thread.start()
    
    read_data()

def read_data():
    """
    Thread to read data from the radio and add it to the queue.
    """
    global radio, launchSequenceInitiated, data_queue

    while launchSequenceInitiated:
        data = radio.recieve()  # Assume this returns a dictionary
        if data:
            data_queue.put(data)
            print("Data added to queue:", data)

def send_data():
    """
    Thread to emit data from the queue to the client.
    """
    global launchSequenceInitiated, data_queue

    while launchSequenceInitiated:
        if not data_queue.empty():
            data = data_queue.get()
            
            all_interpolated = interpolate_quaternions(data) #[[w1, x1, y1, z1], [w2, x2, y2, z2], ... , [wn, xn, yn, zn]]
            
            #for loop thru combined and emit that way we avoid deadlock
            print("Sending data:", data)
            for interpolated_quaternion in all_interpolated:
                socketio.emit("data_send", interpolated_quaternion) #[x, x, y, z]
                sleep(.1)
                
        else:
            # Small sleep to avoid busy-waiting
            threading.Event().wait(0.01)

if __name__ == "__main__":
    # Shared queue for communication between threads
    socketio.run(app, host="127.0.0.1", debug=True, allow_unsafe_werkzeug=True)