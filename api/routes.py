from utilities.webui_pipes import deepfloyd
from flask import request
from main import app, clients
from flask import jsonify

#text2image_pipe = text2image(auth=False)
deepfloyd_pipe = deepfloyd(auth=False)

@app.route("/deepfloyd", methods=['post'])
def api_deepfloyd():
    return deepfloyd_pipe(request)

@app.route("/debug/clients")
def debug_clients():
    return jsonify(clients)