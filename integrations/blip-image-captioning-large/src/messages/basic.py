from uagents import Model


class UARequest(Model):
    image_data: str


class Error(Model):
    error: str


class UAResponse(Model):
    generated_text: str
