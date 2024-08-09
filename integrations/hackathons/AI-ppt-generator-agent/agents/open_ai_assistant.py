import time
from openai import OpenAI


assistant_id="asst_qG3nAPr1A1o4pIIXO5x8v27o"

class OpenAIProcessor:
    def __init__(self, api_key):
        self.client = OpenAI(api_key=api_key, default_headers={"OpenAI-Beta": "assistants=v2"})


    def get_assistant_response(self, topic, description, slides_number):
        thread = self.client.beta.threads.create()
        thread_id = thread.id

        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=f'topic: {topic}\ndescription: {description}\nslides_number: {slides_number}'
        )

        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=assistant_id,
            model='gpt-4o',
            tools=[],
        )

        def check_status(run_id, thread_id):
            run = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run_id
            )
            return run.status

        status = check_status(run.id, thread_id)
        while status != "completed":
            time.sleep(1)
            status = check_status(run.id, thread_id)

        messages = self.client.beta.threads.messages.list(
            thread_id=thread_id
        )

        response_content = ""
        for msg in messages.data:
            response_content = msg.content[0].text.value
            return response_content.strip()


