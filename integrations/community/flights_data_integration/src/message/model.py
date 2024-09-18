# Import librarires
from uagents import Model


# Model for flught_data request
class Code(Model):
    code: str


# Model for flught_data response
class Response(Model):
    response: str
