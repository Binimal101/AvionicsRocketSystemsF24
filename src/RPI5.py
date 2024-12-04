
from hashlib import sha256
from pprint import pprint
from dotenv import load_dotenv
import os

from flask import Flask, render_template, request, url_for
from flask_socketio import SocketIO, send, emit

from recieve import RYLR998_Recieve

#RYLR998 | If multiple instances progress, load lazily
radio = RYLR998_Recieve()

load_dotenv(os.getcwd() + ".env")
hashedPassword = os.environ.get("hashedPassword")

isBroadcasting = False
launchSequenceInitiated = False

app = Flask(__name__)
socketio = SocketIO(app)

#ROUTES
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/visualize")
def success():
    return render_template("visualize.html")

#SOCKET-IO EVENTS
@socketio.on("check_password")
def checkPass(data):
    """
    checks password emission from webapp homepage, if true, sends start sig & begins visualization
    """
    global hashedPassword, radio, launchSequenceInitiated

    userpass = data.get("password", "")
    hashedInput = sha256(userpass.encode()).hexdigest()
    
    print(userpass, hashedInput, hashedPassword)
    
    # compare hashed input to hashed password
    if hashedInput == hashedPassword: # double blind
        emit("validation_result", {"success": True})
        #begin data collection & provide sea_level_pressure
        radio.send_start_command(float(data.get("sea_level_pressure", 101.7)))
        launchSequenceInitiated = True
        
    else:
        emit("validation_result", {"success": False})

#TODO refactor to have seperate process read data, globally access from global queue for emissions
@socketio.on("request_data")
def handle_request_data(data):
    """
    Write code to only run this once, EVER during execution
    sends data continuously to client for WebGL visualization, TODO integrate handlers on /visualize to
    access emissions AND enable the event loop from that scope
    """

    global radio
    global isBroadcasting
    global launchSequenceInitiated

    if not launchSequenceInitiated:
        return


    if isBroadcasting: #only one instance of this should EVER run; discards others
        return
    
    isBroadcasting = True #the one true client!

    while True:
        data = radio.recieve() #type(data) == dict, can be emitted normally
        print("reading data...")
        print(data, flush=True)
        emit("data_send", data)

if __name__ == "__main__":
    socketio.run(app, host="127.0.0.1", debug=True, allow_unsafe_werkzeug=True)