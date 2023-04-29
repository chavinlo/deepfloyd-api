from flask import Flask
from flask_socketio import SocketIO
import json

config = json.load(open('config.json'))
tokens = json.load(open('tokens.json'))

NODE_KEY = config['node_key']
SECRET_KEY = config['secret_key']
app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
socketio = SocketIO(app, ping_timeout=120, ping_interval=10, logger=True, max_http_buffer_size=1024*1024*30)
tasks = {}
clients = {}
job_id = 0

from routes import *
from utilities.socketio_pipes import *

if __name__ == '__main__':
    socketio.run(app, port=config['port'], debug=True)