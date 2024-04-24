from uagents import Model


class PredictionRequest(Model):
    masked_text: str


class PredictionResponse(Model):
    data: str


class Error(Model):
    error: str
