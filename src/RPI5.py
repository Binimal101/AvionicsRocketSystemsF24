from hashlib import sha256
from pprint import pprint
from dotenv import load_dotenv
import os
import threading
from queue import Queue
from interpolation import Interpolate
from time import sleep

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask_cors import CORS

from recieve import RYLR998_Recieve

FPS = 30

load_dotenv(os.getcwd() + "/.env")
hashedPassword = os.environ.get("hashedPassword")

launchSequenceInitiated = False
isBroadcasting = False  # Tracks if data is currently being broadcasted

# Shared queue & radio for communication between threads while reducing proc overhead
data_queue, radio, interpolator = None, None, None

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

def get_interpolation_medium(): #lazy load
    global interpolator
    if interpolator is None:
        interpolator = Interpolate(FPS)
    
    return interpolator

app = Flask(__name__)

CORS(app) #for the singulate JS http request on the frontend for downloading the model of the rocket
socketio = SocketIO(app, cors_allowed_origins="*") #inappropriate, but we don't have a domain or internet access so it's fine FTMP

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
    
    if not launchSequenceInitiated:
        radio = get_radio()

    # Compare hashed input to hashed password
    if hashedInput == hashedPassword:
        launchSequenceInitiated = True
        
        sleep(0.01) #race condition if emits before flag checks, the one request_data socket flag will NEVER send

        emit("validation_result", {"success": True})
        # Begin data collection & provide sea_level_pressure
        radio.send_start_command(float(data.get("sea_level_pressure", 101.7)))

    else:
        emit("validation_result", {"success": False})

@socketio.on("request_data")
def handle_request_data(_):
    """
    Initiates data handling only once during execution, ensuring proper coordination between threads
    Emits quaternions 1 by 1 to EVERY client in the root namespace
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

    if data_queue is None:
        data_queue = get_data_queue()

    while launchSequenceInitiated:
        data = radio.recieve()  # this returns a serializable dictionary
        
        if data:
            data_queue.put(data)

def send_data():
    """
    Thread to emit data from the queue to the client.
    """

    global launchSequenceInitiated, data_queue, interpolator

    data_queue = get_data_queue()
    interpolator = get_interpolation_medium()

    while launchSequenceInitiated:
        if not data_queue.empty():
            data = data_queue.get()

            all_interpolated = interpolator.interpolate_quaternion(data[0], data[1]) #[0]time_delta, [1]only one quaternion type==dict

            print("interpolated DP's:", flush=True)
            pprint(all_interpolated)

            if type(all_interpolated[0]) == float: #1d [], first iter
                socketio.emit("data_send", all_interpolated) #send data to ALL connected clients
                
                print(f"Sent! Left in queue {data_queue.qsize()}", flush=True)
                
                sleep(0.01) #works well, in future add PID loop
                continue

            for interpolated_quaternion in all_interpolated:

                if not isinstance(interpolated_quaternion, list): #if is np.array, make list
                    interpolated_quaternion = interpolated_quaternion.tolist()

                socketio.emit("data_send", interpolated_quaternion) #[w, x, y, z] #send data to ALL connected clients
                print(f"Sent! Left in queue {data_queue.qsize()}", flush=True)
                sleep(0.01) #works well, in future add PID loop

        else:
            # Small sleep to avoid busy-waiting
            sleep(0.01)
            
if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", debug=True, allow_unsafe_werkzeug=True)