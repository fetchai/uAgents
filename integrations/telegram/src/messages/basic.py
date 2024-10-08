from uagents import Model


class TelegramRequest(Model):
    text: str
    chat_id: int
