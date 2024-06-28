"""Model definitions for the agents protocol."""

from uagents import Model


class RequestData(Model):
    prompt: str


class LlmResponse(Model):
    message: str
