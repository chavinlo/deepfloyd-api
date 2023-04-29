from queue import Queue
from threading import Lock, Thread
import json
import os
import socketio
from socketio.exceptions import ConnectionRefusedError
import uuid
from deepfloyd_node import image_generator
from os.path import join, abspath, dirname
import time
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--gpu', type=int, default=0, help='Index of GPU to use')
args = parser.parse_args()

gpu_index = args.gpu

CONFIG_PATH = join(dirname(abspath(__file__)), "config.json")

sio = socketio.Client(reconnection=True, reconnection_attempts=0, reconnection_delay=0, reconnection_delay_max=0, randomization_factor=0)

NODE_KEY = 'sh4JfXt6hwBkqjK6K8BGqju4'

ex_uuid = str(uuid.uuid4())

with open(CONFIG_PATH) as f:
    config = json.load(f)
    config['gpu'] = gpu_index

hfd = config['HF_HOME'] 
if hfd is not None:
    os.makedirs(hfd, exist_ok=True)

request_queue = Queue()
image_queue = Queue()
queue_lock = Lock()

@sio.event
def connect():
    print("Connected to manager")
    sio.emit('join', data={'node_id': ex_uuid, 'work': "deepfloyd"})
    time.sleep(2)
    data_to_update = {
        "node_id": ex_uuid,
        "work": "deepfloyd",
        "new_records": {
            "status": "ready",
            "tasks": 0,
        }
    }
    sio.emit("update_records", data=data_to_update)

@sio.on('task')
def on_task(data):
    queue_pointer = data['queue_pointer']
    parameters = data['parameters']
    with queue_lock:
        request_queue.put(parameters)
    response = image_queue.get()
    sio_response = {
        "queue_pointer": queue_pointer,
        "raw_response": response
    }
    sio.emit('post_task', sio_response)

# Image Generator Engine
image_generator_thread = Thread(
    target=image_generator, 
    args=(
        config,
        request_queue,
        image_queue
        )
    )
image_generator_thread.start()

@sio.on('*')
def catch_all(event, data):
    print("Catched some event:", event)
    print("data:", data)

print("Connecting...")
sio.connect(config['server'], auth={'KEY': NODE_KEY}, wait_timeout=5)

image_generator_thread.join()