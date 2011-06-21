import json
import io

class InvalidResponse(Exception):
    def __init__(self, httpresp):
        self.httpresp = httpresp
    
    def __str__(self):
        return "Invalid response"

class Couch(Exception):
    def __init__(self, body):
        data = json.load(body)
        self.message = data["error"] + ": " + data["reason"]
    
    def __str__(self):
        return self.message

class NotFound(Couch):
    pass
class BadRequest(Couch):
    pass
class PreconditionFailed(Couch):
    pass
class InternalServerError(Couch):
    pass
class ResourceNotAllowed(Couch):
    pass
class Conflict(Couch):
    pass
