import os
import json
import cloud
import base64
import requests
import upload_insta
from cloud import storage


# Function to load configuration from a JSON file
def load_config(config_file):
    with open(config_file, 'r') as file:
        config = json.load(file)
    return config

# Load configuration from config.json
config = load_config('config.json')

engine_id = "stable-diffusion-v1-6"

api_key = config.get("stable_api_key")

if api_key is None:
    raise Exception("Missing Stability API key.")

def image_req(prompt,username):
    response = requests.post(
        f"https://api.stability.ai/v1/generation/{engine_id}/text-to-image",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "text_prompts": [
                {
                    "text": prompt
                }
            ],
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
        },
    )

    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    data = response.json()


    for i, image in enumerate(data["artifacts"]):
        with open(f"img.png", "wb") as f:
            f.write(base64.b64decode(image["base64"]))


    #upload to cloud
    file='img.png'
    link = cloud.get_cloud_link(file,storage=storage)

    #upload to insta
    status = upload_insta.upload(file,username)    

    return {"link": link}

# image_req(prompt='25 year old blue haired pretty girl enjoying her vacations in a snowy and grassy valley of Himalayas. Highly detailed, photo realistic. Accurate lighting. No inconsistencies',
#     username='seema.ai.2024')

