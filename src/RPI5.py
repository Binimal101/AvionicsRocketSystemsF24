from flask import Flask, render_template, request, url_for
from flask_socketio import SocketIO, send, emit
from recieve import RYLR998_Recieve

from hashlib import sha256

app = Flask(__name__)
socketio = SocketIO(app)

password = 'securePass123' #TODO hash agreed-upon password

#RYLR998
lora = RYLR998_Recieve()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/success')
def success():
    return render_template('success.html')

@socketio.on('check_password')
def checkPass(data):
    """
    checks password emission from webapp homepage, if true, sends start sig & begins visualization
    """
    user_password = data.get('password', '')
    if user_password == password:
        emit('validation_result', {'success': True})
        print("sending start")
        lora.send_start_command(float(data.get('sea_level_pressure', 101.7)))
        print("ending send start")
        # TODO emit a second flag to let FE know to switch over to visualization that LoRa has successfully 
    else:
        emit('validation_result', {'success': False})

# Handle messages from the client
@socketio.on('message')
def handle_message(message):
    #TODO is this needed?
    print(f"Received message: {message}")
    send(f"Server received: {message}", broadcast=True)

@socketio.on('request_data')
def handle_request_data():
    #TODO probably better to EMIT data continuously, this is a hotfix
    #With constant emission instead of handling emissions, transmission time is cut in half
    #Also would avoid deadlocks if this runs async

    # data = get_payload_data()
    
    data = lora.recieve()
    print('Sending Data: {}'.format(data) )
    emit('data_send', {'data': data})

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True)