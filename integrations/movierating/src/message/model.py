# import required libraries
from uagents import Model
# taking request as sports name
class Message(Model):
    message : str
# getting response as live scores
class Response(Model):
    response : str
