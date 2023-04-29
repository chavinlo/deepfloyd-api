from utilities.http_pipes import deepfloydTemplate
from utilities.paramverifs import noInputDeepfloyd
from flask import Response, send_file
import io
import base64
    
class deepfloyd(deepfloydTemplate):
    def __paramProcessing__(self, resp: dict) -> tuple[bool, dict]:
        return noInputDeepfloyd(req=resp)
    def __fileProcessing__(self, resp: dict) -> Response:
        image = resp['content']['image']
        image = base64.b64decode(image)
        img_io = io.BytesIO(image)
        img_io.seek(0)
        response = send_file(img_io, mimetype='image/png')
        return response