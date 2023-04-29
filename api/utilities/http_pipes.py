import time
from utilities.general import fail, succ, check_token_existance
from flask import Response, jsonify
from werkzeug import Request
from main import app, clients, socketio, tasks, tokens
import secrets
from queue import Queue

class httpPipeline():
    def __init__(self,
                 auth: bool,
                 timeout: int = None) -> None:
        self.auth = auth
        self.timeout = timeout

        self.fail = fail
        self.succ = succ

        self.threads = {}
        self.tasks = tasks

        self.ip_timeouts = {}

    def authenticate(self, req: Request) -> bool:
        """
        Authenticate function

        Checks if there's `ACCESS_TOKEN` in headers or cookies

        If there is and it's valid, returns `True`

        If there is not or it's invalid, returns `False`
        """
        if "ACCESS_TOKEN" in req.headers:
            token = req.headers.get("ACCESS_TOKEN")
        elif "ACCESS_TOKEN" in req.cookies:
            token = req.cookies.get("ACCESS_TOKEN")
        else:
            return False
        return check_token_existance(token, tokens)
    
    def timelimit(self, req: Request) -> bool:
        """
        Timelimit function

        Checks if the IP (`request.remote_addr`) is in timeout or not.
        Timeout time is set by self.timeout configured at `__init__`

        If it is, returns `True`

        If not, returns `False`
        """
        client_ip = req.remote_addr
        now = time.time()

        if client_ip in self.ip_timeouts and now - self.ip_timeouts[client_ip] < self.timeout:
            return True
        else:
            self.ip_timeouts[client_ip] = now
            return False
    
    def __process__(self, req: Request) -> Response:
        pass
        
    def __call__(self, req: Request) -> Response:
        if self.auth is True:
            if self.authenticate(req=req) is False:
                return jsonify(self.fail("UNAUTHORIZED", "Failed to authenticate with provided token or failed to detect it.")), 401
        if self.timeout is not None:
            if self.timelimit(req=req) is True:
                return jsonify(self.fail("RATE_LIMIT", f"Too many requests, please wait at least {self.timeout} seconds.")), 429
        return self.__process__(req=req)

class deepfloydTemplate(httpPipeline):

    def get_least_busy_node(self, clients: dict, assign: bool):

        best_node = None
        best_node_tasks = float('inf')

        for node_id, node_data in clients.items():
            if node_data['tasks'] < best_node_tasks:
                best_node_tasks = node_data['tasks']
                best_node = node_data
                best_node_id = node_id
        
        if assign is True:
            best_node['tasks'] += 1

        return best_node_id, best_node
    
    def __send_to_nodes__(self, data: dict):
        node_id, node_data = self.get_least_busy_node(
            clients=clients['deepfloyd'],
            assign=True
        )

        node_response = None
        #add `with threads[node_id]` here
        job_key = secrets.token_urlsafe(8)
        self.tasks[job_key] = {
            "return_queue": Queue(maxsize=1),
        }

        socketio.emit('task', {
            "queue_pointer": job_key,
            "parameters": data
        }, to=node_data['entry_point'])
        queue_response = self.tasks[job_key]['return_queue'].get()
        del self.tasks[job_key]

        #TODO: make this responsive to errors (with exceptions and that sort of things)
        node_data['tasks'] -= 1
        node_response = queue_response['raw_response']
        return node_response
    
    def __paramProcessing__(self, resp: dict) -> tuple[bool, dict]:
        pass

    def __fileProcessing__(self, resp: dict) -> Response:
        pass
    
    def __process__(self, req: Request) -> Response:
            
        jsonreq = req.get_json()
        requiredparams, _response = self.__paramProcessing__(jsonreq)

        if requiredparams is False:
            return jsonify(self.fail(_response['reason'], _response['content'])), 406
        else:
            toSendParams = _response

        response = self.__send_to_nodes__(toSendParams)

        if response['status'] == 'fail':
            print(response)
            if 'reason' not in response:
                response['reason'] = 'UNKNOWN_ERROR' #<- critical
            return self.fail(response['reason'], response['content'])

        if jsonreq['mode'] == 'json':
            return jsonify(response), 200
        elif jsonreq['mode'] == 'file':
            return self.__fileProcessing__(response)