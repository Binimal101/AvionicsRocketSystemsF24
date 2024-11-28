from flask import Flask, render_template, request, url_for
from flask_socketio import SocketIO, send, emit
from recieve import RYLR998_Recieve


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
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
    if user_password== password:
        emit('validation_result', {'success': True})
        lora.send_start_command() #TODO, how to init 2 second delay for visuals

    else:
        emit('validation_result', {'success': False})

def get_payload_data():
    data = [
    {'ts': 1.00000000, 'x': 0.12345678, 'y': -0.87654321, 'w': 0.65432109, 'z': -0.43210987},
    {'ts': 2.00000000, 'x': -0.56789012, 'y': 0.34567891, 'w': -0.23456789, 'z': 0.98765432},
    {'ts': 3.00000000, 'x': 0.87654321, 'y': -0.12345678, 'w': 0.54321098, 'z': -0.67890123}
]
    return data

# Handle messages from the client
@socketio.on('message')
def handle_message(message):
    #TODO is this needed?
    print(f"Received message: {message}")
    send(f"Server received: {message}", broadcast=True)

@socketio.on('request_data')
def handle_request_data():
    #TODO probably better to EMIT data continuously, this is a hotfix
    #With constant emission instead of handling emissions, transmission time cut in half
    
    data = lora.recieve()
    print('Sending Data: {}'.format(data) )
    emit('data_send', {'data': data})

# Custom event example
@socketio.on('custom_event')
def handle_custom_event(data):
    #TODO is this needed?
    print(f"Custom event received: {data}")
    emit('custom_response', {'response': f"Server says: {data['message']}"})

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True)