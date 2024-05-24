import os


API_KEY = os.environ.get("CLOUDINARY_API_KEY")
API_SECRET = os.environ.get("API_SECRET")

CLOUDINARY_URL = f"cloudinary://{API_KEY}:{API_SECRET}@du91akze5"


def print_api_key_secret():
    print("API Key:", API_KEY)
    print("API Secret:", API_SECRET)


#print_api_key_secret()
