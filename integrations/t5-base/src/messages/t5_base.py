from uagents import Model


class TranslationRequest(Model):
    text: str


class TranslationResponse(Model):
    translated_text: str


class Error(Model):
    error: str
