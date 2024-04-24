import requests
import json

URI = ''
jsonRes = json.loads((requests.get(URI)).text)


