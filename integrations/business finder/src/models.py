#importing models module from uagents library
from uagents import Model

#defining classes for handling request and response
class Location(Model):
    city: str
    category : str

class Response_list(Model):
    city: str
    category : str
    name_list : list

class Response(Model):
    response : str