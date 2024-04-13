#  import required libraries
from uagents import Model
from pydantic import Field
class Message(Model):
    message : str
class Response(Model):
    response : str

class Movie(Model):
    title : str = Field(description="Enter the movie name")
