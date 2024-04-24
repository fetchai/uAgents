from uagents import Model


class LightsRequest(Model):
    on: int

class LightsResponse(Model):
    success_str: str

class ACRequest(Model):
    on: int
    temperature: int = 25

class ACResponse(Model):
    success_str: str

class WindowRequest(Model):
    open : int
    put_curtains: int

class WindowResponse(Model):
    success_str: str


request_keys = {
    "lights": {'on': int},
    "ac": {'on': int, 'temperature': int},
    "window": {'open': int, 'put_curtains': int}
}

request_description = {
    "lights" : {"on": "0 for off, 1 for on"},
    "ac" : {"on": "0 for off, 1 for on",  "temperature": "temperature to set"},
    "window" : {"open": "0 for close, 1 for open", "put_curtains": "0 for remove, 1 for put"}
}