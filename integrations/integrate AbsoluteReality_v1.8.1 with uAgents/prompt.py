import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env
load_dotenv()

def generate_summary(story, text_file):
    # Get API key from environment variable
    api_key = os.getenv('YOUR_API_KEY')

    # Configure Gemini AI
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    # Concatenate static text with the story
    static_text = "i want to break this story into multiple parts so tht i can make photo give prompts such that it gives each disciption of photo how it should be ,each prompts ending with [&&&] and say last prompt as last prompt"
    content = static_text + story

    # Generate content using Gemini AI with the concatenated text
    response = model.generate_content(content)

    # Extract prompts from the response
    prompts = response.text.split("[&&&]")

    # Save prompts to the text file
    with open(text_file, 'w') as file:
        file.write("\n".join(prompts))

    # Return the generated content
    return prompts
