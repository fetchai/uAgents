# Message handler for data requests sent to this agent
import os
import requests
from dotenv import load_dotenv
from uagents import Model, Context
import json

load_dotenv()

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


# Configuration for making requests to OPEN AI
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENAI_API_KEY}",
}


class Error(Model):
    text: str


class Text(Model):
    pdf: str
    success: bool
    question: str
    chapter: str
    subject: str
    standard: str


# class based on {"summary": "summary", "question_bank": ["question_1","question_2",...], answer_key:["answer_1","answer_2",...]}
class Summary(Model):
    summary: str
    question_bank: str
    answer_key: str


class Response(Model):
    text: str


class End(Model):
    msg: str


context = """    
    You are a helpful NCERT Tutor agent who will summarize a given chapter from NCERT and respond with a summary and a question bank with answers.
    
    Please follow these guidelines:
    1. Try to answer the question as accurately as possible, using only reliable sources like the ones provided as .
    2. Take in consideration the standard, subject, chapter, and question given.
    3. Provide a detailed summary of the chapter.
    4. Create a question bank with answers to the questions.
    5. Provide the information in the exact JSON format: {"summary": "summary", "question_bank": "question_1,question_2,...", answer_key:"answer_1,answer_2,..."}
        - summary is the summary of the chapter given
        - question bank is a newlined string of questions from the chapter
        - answer key is a newlined string of answers to the questions made from the chapter
    """

MODEL = "gpt-4-turbo"


# Send a prompt and context to the AI model and return the content of the completion
def query_openai_gpt(prompt):

    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": context},
            {"role": "user", "content": prompt},
        ],
    }

    # Make the POST request to the OpenAI API
    response = requests.post(OPENAI_URL, json=data, headers=HEADERS)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the JSON response
        response_json = response.json()
        # Retrieve the content from the first choice in the response
        return response_json["choices"][0]["message"]["content"]
    else:
        # Handle errors (e.g., invalid API key, rate limits)
        response.raise_for_status()


# Instruct the AI model to retrieve data and context for the data and return it in machine readable JSON format
def get_data(ctx: Context, prompt: str):

    response = query_openai_gpt(prompt)

    try:
        ## try to convert response to json
        data = json.loads(response)
        ##return json data
        return data
    except Exception as ex:
        ctx.logger.exception(
            f"An error occurred retrieving data from the AI model: {ex}"
        )
        return Error(
            text="Sorry, I wasn't able to answer your request this time. Feel free to try again."
        )


def send_shared_link_data(data: Summary) -> str:
    url = "http://localhost:8080/sharedlink"
    response = requests.post(url, json=data.dict())

    if response.status_code == 200:
        return response.json()
    else:
        return None
