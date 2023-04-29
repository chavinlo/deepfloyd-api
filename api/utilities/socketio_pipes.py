from main import socketio, NODE_KEY, clients, tasks
from flask import request
from flask_socketio import join_room, leave_room, send, emit, ConnectionRefusedError, disconnect
import utilities
import logging
from utilities.general import fail, succ

@socketio.on('connect')
def connect(auth):
    valid = auth['KEY'] == NODE_KEY
    if valid is False:
        emit('CONNECTION_HEALTH', fail("AUTH_CONN_FAILED", "Authentication failed during connection process"))
        disconnect(request.sid)
        raise ConnectionRefusedError('unauthorized!')
    else:
        emit('CONNECTION_HEALTH', succ("AUTH_CONN_SUCCESS", "Authentication success"))

clients['deepfloyd'] = dict()

@socketio.on('join')
def on_join(data):
    print("Join triggered")
    print(f"Node joined: {data}")
    node_id = data['node_id']
    node_work = data['work']

    if node_work not in clients:
        emit('GROUP_HEALTH', fail("GROUP_JOIN_NONEXISTENT", f"Group to join doesn't exists: {node_work}"))
        return

    clients[node_work][node_id] = {
        "entry_point": request.sid,
        "status": "boot",
        "tasks": None
    }

    print("Added as:", clients[node_work][node_id])

    emit('GROUP_HEALTH', succ("GROUP_JOIN_SUCCESS", f"Joined group {node_work} successfully"))

@socketio.on('update_records')
def on_update_records(data):
    print("update_records triggered:", data)
    node_id = data['node_id']
    node_work = data['work']

    if node_work not in clients:
        emit('GROUP_HEALTH', fail("GROUP_UPDT_NONEXISTENT", f"Group to update doesn't exists: {node_work}"))

    for key, value in data['new_records'].items():
        clients[node_work][node_id][key] = value
    emit('RECORDS', succ("RECORDS_UPDT_SUCCESS", f"Updated node_id {node_id} at group {node_work} with new configuration: {data['new_records']}"))

@socketio.on('post_task')
def on_post_task(data):
    queue_pointer = data['queue_pointer']
    if queue_pointer in tasks:
        queue_posted_dict = {
            "raw_response": data['raw_response']
        }
        tasks[queue_pointer]['return_queue'].put(queue_posted_dict)
        tasks[queue_pointer]['status'] = 'done'
    else:
        emit('POST_TASK', fail('QUEUE_POINTER_NOT_FOUND', f'Queue pointer {queue_pointer} is not in task list'))

@socketio.on('disconnect')
def disconnect():
    delete_primary = None
    delete_secondary = None
    for key1, value1 in clients.items():
        for key2, value2 in value1:
            if value2['entry_point'] == request.sid:
                delete_primary = key1
                delete_secondary = key2
    del clients[delete_primary][delete_secondary]