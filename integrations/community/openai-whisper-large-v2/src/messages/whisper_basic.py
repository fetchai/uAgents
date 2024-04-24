from uagents import Model


class AudioTranscriptRequest(Model):
    audio_data: str


class Error(Model):
    error: str


class AudioTranscriptResponse(Model):
    transcript: str
