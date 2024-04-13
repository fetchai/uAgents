import asyncio
import os
import requests
from uagents import Agent
import nltk
from nltk.corpus import stopwords

class ResearchPaperQnA(Agent):
    def __init__(self, model_name="deepset/roberta-base-squad2"):
        super().__init__()
        self.model_name = model_name
        nltk.download('stopwords')
        self.stop_words = set(stopwords.words('english'))

    def tokenize_and_remove_stopwords(self, text):
        tokens = nltk.word_tokenize(text.lower())
        filtered_tokens = [token for token in tokens if token not in self.stop_words]
        return filtered_tokens

    async def handle_request(self, text: str, question: str):
        # Use the original text as the context
        context = text

        # Tokenize and remove stop words from the context and question
        context_tokens = set(self.tokenize_and_remove_stopwords(context))
        question_tokens = set(self.tokenize_and_remove_stopwords(question))

        # Check if the question is related to the context
        if not context_tokens.intersection(question_tokens):
            return "Sorry, I could not find an answer to your question in the given context."

        # Make an API call to the Hugging Face Transformers API
        url = f"https://api-inference.huggingface.co/models/{self.model_name}"
        headers = {"Authorization": f"Bearer {os.environ.get('HUGGING_FACE_API_TOKEN')}"}
        payload = {
            "context": context,
            "question": question,
        }
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        answer = result.get("answer", "")

        # Check if the answer is empty
        if not answer.strip():
            answer = "Sorry, I could not find an answer to your question in the given context."

        return answer