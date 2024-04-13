import requests
import io
from PIL import Image
import os

from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

def save_images_from_query(parts, folder='images', filename_prefix='generated_image'):
    API_URL = "https://api-inference.huggingface.co/models/digiplay/AbsoluteReality_v1.8.1"
    api_token = os.getenv('HF_API_TOKEN')
    headers = {"Authorization": f"Bearer {api_token}"}

    # Iterate over each part of the story
    for i, part in enumerate(parts, 1):
        payload = {"inputs": part}

        # Query the model
        response = requests.post(API_URL, headers=headers, json=payload)

        # Check if response content is not empty
        if response.content:
            # Load image data into a PIL image
            image = Image.open(io.BytesIO(response.content))

            # Create the folder to save images if it doesn't exist
            if not os.path.exists(folder):
                os.makedirs(folder)

            # Save the image to a file
            image_path = os.path.join(folder, f'{filename_prefix}_{i}.jpg')
            image.save(image_path)

            print(f"Image {i} saved successfully:", image_path)
        else:
            print(f"No image data received from the API for part {i}.")
