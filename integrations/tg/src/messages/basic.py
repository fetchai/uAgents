from uagents import Model


class TelegramRequest(Model):
    text: str
    chat_id: int


class Error(Model):
    error: str


class TelegramResponse(Model):
    text: str
