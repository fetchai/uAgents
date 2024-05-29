import os
import json
import pyrebase

# Function to load configuration from a JSON file
def load_config(config_file):
    with open(config_file, 'r') as file:
        config = json.load(file)
    return config

# Load configuration from config.json
config = load_config('config.json')

config_db = {
    "apiKey": config.get("apiKey"),
    "authDomain": config.get("authDomain"),
    "projectId": config.get("projectId"),
    "storageBucket": config.get("storageBucket"),
    "messagingSenderId": config.get("messagingSenderId"),
    "appId": config.get("appId"),
    "measurementId": config.get("measurementId"),
    
    "serviceAccount": config.get("serviceAccount"),
    "databaseURL": config.get("databaseURL"),
}

firebase = pyrebase.initialize_app(config_db)

storage = firebase.storage()

def get_cloud_link(image_path:str, storage:object) -> str:
    """
    upload image to the cloud and returns the accessible link.
    """

    image_name = os.path.basename(image_path)
    # used as ---> storage.child("new_name_stored_in_firebase.jpg").put("local_name.jpg")
    storage.child(image_name).put(image_path)
    # Generate the download URL
    download_url = storage.child(image_name).get_url(None)

    print("Image link: ", download_url)

    return download_url

# get_cloud_link('img.png',storage=storage)
