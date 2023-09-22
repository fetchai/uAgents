from uagents import Model


class CaptionRequest(Model):
    image_data: str


class Error(Model):
    error: str


class CaptionResponse(Model):
    generated_text: str
