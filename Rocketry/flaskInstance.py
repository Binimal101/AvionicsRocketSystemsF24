
'''from flask import Flask, jsonify
from flask_socketio import SocketIO, emit
import requests

app = Flask(__name__)
socketio = SocketIO(app)

@app.route('/data', methods=['GET'])
def sendData():
    newData = {'message': "hi"}
    return jsonify(newData)

@app.route('/')
@socketio.on('get_data')
def recieveData():
    flaskData = requests.get('http://127.0.0.1:5000/data').json() #
    emit('recieveData', flaskData)

if __name__ == '__main__':
    app.run(debug = True)
    socketio.run(app, debug = True)

'''
from flask import Flask, render_template, request, url_for
from flask_socketio import SocketIO, send, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

password = 'securePass123'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/success')
def success():
      return render_template('success.html')

@socketio.on('check_password')
def checkPass(data):
    user_password = data.get('password', '')
    if user_password== password:
        emit('validation_result', {'success': True})
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
    print(f"Received message: {message}")
    send(f"Server received: {message}", broadcast=True)

@socketio.on('request_data')
def handle_request_data():
    data = get_payload_data()
    print('Sending Data: {}'.format(data) )
    emit('data_send', {'data': data})

# Custom event example
@socketio.on('custom_event')
def handle_custom_event(data):
    print(f"Custom event received: {data}")
    emit('custom_response', {'response': f"Server says: {data['message']}"})

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True)