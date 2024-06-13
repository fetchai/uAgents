import random

from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType

import requests

def interact_with_gemini(prompt, api_key):
  """Sends a prompt to Gemini's API and returns the response.

  Args:
      prompt: The user-provided prompt to send to Gemini.
      api_key: Your Gemini API key.

  Returns:
      The API response as a dictionary, or None if an error occurs.
  """

  # Base URL for Gemini's REST API
  base_url = "https://generativelanguage.googleapis.com/v1/projects"

  # Endpoint for text generation
  endpoint = "/locations/global/models/embedding-001:generateContent"

  # Construct the full URL
  url = f"{base_url}{endpoint}"

  # Request body with the prompt and API key
  data = {
      "requests": [
          {
              "model": "models/embedding-001",
              "content": {"text": prompt},
          }
      ]
  }

  headers = {"Authorization": f"Bearer {api_key}"}

  # Send request and get response
  response = requests.post(url, headers=headers, json=data)

  # Check for successful response
  if response.status_code == 200:
    return response.json()
  else:
    print(f"Error: API request failed with status code {response.status_code}")
    return None

class Story(Model):
    description: str = Field(description="Generate story using the above details?")

story_protocol = Protocol("Story")


@story_protocol.on_message(model=Story, replies={UAgentResponse})
async def generate_story(ctx: Context, sender: str, msg: Story):

    API_URL = "https://api-inference.huggingface.co/models/google/gemma-7b"
    headers = {"Authorization": "Bearer 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"}

    def query(payload):
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()
        
    output = query({
        "inputs": """
        Given below is the description of a character. Generate a mimimum 500 word story of the given character and its description. The story should be of minimum 500 words\n
        """ + msg.description,
    })
    print("REACHED "+msg.description)
    print(output[0]['generated_text'])
    message = """
    Here's the story we generated: \n""" + output[0]['generated_text'] + "\n\nHope it's helpful"

    await ctx.send(
        sender, UAgentResponse(message=message, type=UAgentResponseType.FINAL)
)

agent.include(story_protocol, publish_manifest=True)