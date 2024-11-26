from flask import Flask, render_template, request, url_for
from flask_socketio import SocketIO, send, emit
from recieve import RYLR998_Recieve

from hashlib import sha256
from pprint import pprint

app = Flask(__name__)
socketio = SocketIO(app)

hashedPassword = "a31b7f27cc7496ec97fffa9518737d5565e3474c4b7a0bc503eb195cf6f6d65d"

#RYLR998
lora = RYLR998_Recieve()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/visualize")
def success():
    return render_template("success.html")

@socketio.on("check_password")
def checkPass(data):
    """
    checks password emission from webapp homepage, if true, sends start sig & begins visualization
    """
    userpass = data.get("password", "")

    # compare hashed input to hashed password
    if sha256(userpass.encode()).hexdigest() == hashedPassword: # double blind
        emit("validation_result", {"result": True})
        
        #begin data collection & provide sea_level_pressure
        lora.send_start_command(float(data.get("sea_level_pressure", 101.7)))
        
    else:
        emit("validation_result", {"success": False})

@socketio.on("request_data")
def handle_request_data():
    """
    Write code to only run this once, EVER during execution
    sends data continuously to client for WebGL visualization, TODO integrate handlers on /visualize to
    access emissions AND enable the event loop from that scope
    """
    data = lora.recieve()
    
    while True:
        pprint(data)
        emit("data_send", {"data": data})

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", debug=True)