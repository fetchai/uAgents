import json
import requests

api_url = "http://localhost:8080/send-pdf-content"
payload = {
            "standard": 3,
            "subject": "english",
            "chapter": 101,
        }
headers = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
response = requests.post(api_url, json=payload, headers=headers)
data = response.json()
print(data["content"])