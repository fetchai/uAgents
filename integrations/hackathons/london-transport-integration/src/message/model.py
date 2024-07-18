# Importing model from uagents libraru
from uagents import Model

# defining model to take input form user
class Location(Model):
    from_loc : str
    to_loc : str

# defining model to give response to user.
class Response(Model):
    response : str