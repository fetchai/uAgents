import asyncio
import os
import requests
from uagents import Agent

class ResearchPaperSummarizer(Agent):
    def __init__(self, model_name="google/pegasus-xsum"):
        super().__init__()
        self.model_name = model_name

    async def handle_request(self, text: str):
        # Make an API call to the Hugging Face Transformers API
        url = f"https://api-inference.huggingface.co/models/{self.model_name}"
        headers = {"Authorization": f"Bearer {os.environ.get('HUGGING_FACE_API_TOKEN')}"}
        payload = {
            "inputs": text,
            "parameters": {
                "min_length": 60,
                "max_length": 150,
                "num_beams": 4,
                "early_stopping": True,
            },
        }
        response = requests.post(url, headers=headers, json=payload)
        summary = response.json()[0]["summary_text"]
        return summary