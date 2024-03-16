import requests
import json

URI = 'https://dev.virtualearth.net/REST/v1/LocalSearch/?query=Hospitals&userLocation=40.785091,-73.968285,20000&key=Ar2PnnN71Ber0cEAkzbL41ForcU9ZPl-rEdO6MnMkvQNht9C8Buz8XQrcKTWlral'
jsonRes = json.loads((requests.get(URI)).text)


