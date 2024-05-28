import os
import tempfile

from dotenv import load_dotenv, find_dotenv
from langchain.chains.llm import LLMChain
from langchain.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_openai import OpenAI
from openai import OpenAI as MyOpenAIClient
import utils
import requests


class SafetySummariser:
    def __init__(self):
        load_dotenv(find_dotenv())
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key is None:
            raise Exception("OPENAI_API_KEY not exposed in environment")

        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        self.openai_client = MyOpenAIClient(api_key=api_key)
        self.chat = ChatOpenAI(model="gpt-3.5-turbo")
        self.sys_prompt = (
            "You are an AI trained to provide a summary of an input event."
            "For example, a cold call or a person at the door."
            "Provide all of the information required to form a security decision, and no more."
            "Make the output of your response into a rigid structure such as:"
            "Summary:abc\nDate:day/month/year\nTime:hour:minutePM"
            "Do not deviate from this structure."
            "Respond to this request: {REQUEST}"
        )
        self.prompt_template = PromptTemplate(
            input_variables=["REQUEST"], template=self.sys_prompt
        )

    def download_and_summarise(self, audio_url):
        with tempfile.TemporaryDirectory() as tempdir:
            audio_path = os.path.join(tempdir, "audio.mp3")
            response = requests.get(audio_url)
            with open(audio_path, "wb") as audio_file:
                audio_file.write(response.content)

            # Use Whisper to transcribe audio
            audio_file = open(audio_path, "rb")
            transcription = self.openai_client.audio.transcriptions.create(
                model="whisper-1", file=audio_file, response_format="text"
            )
            transcribed_text = transcription
            return self.summarise(transcribed_text)

    def getChain(self):
        chain = LLMChain(llm=self.chat, prompt=self.prompt_template)
        return chain

    def summarise(self, msg):
        chain = self.getChain()
        summary = chain.run(msg)
        return utils.parse_summary(summary)
