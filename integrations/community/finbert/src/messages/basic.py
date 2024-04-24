from uagents import Model


class UARequest(Model):
    text: str


class Error(Model):
    error: str


class UAResponse(Model):
    response: list
