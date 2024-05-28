from uagents.setup import fund_agent_if_low
from uagents import Agent, Context, Protocol, Model
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType
import os
from openai import OpenAI
import json

class Medi(Model):
    medicine_name: str = Field(description="Enter The Medicine Name")

SEED_PHRASE = "MED IQ"

print(f'My Agent Address Is {Agent(seed=SEED_PHRASE).address}')

AGENT_MAILBOX_KEY = "a8e4a022-49c6-476e-bb18-8868b5c9a71a"

MedIQ = Agent(
    name="MEDIQ",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

fund_agent_if_low(MedIQ.wallet.address()) #funding agent.


MedIQProtocol = Protocol("MEDIQ Protocol")

OPENAI_API_KEY = "OPENAI-YOUR-API_KEY"

async def output(prompt):
    client = OpenAI(
    api_key=os.environ.get("OPENAI-YOUR-API-KEY"),
    )

    medicine_name = prompt

    prompt = f"""
    Provide details about the medicine "{medicine_name}" in the following format:

    "usage": "{medicine_name} used for?",
    "contraindications": "Who should not take {medicine_name}?",
    "dosage": "How should I take {medicine_name}?",
    "general_info": "side effects of {medicine_name}.",
    "Storage Query": "How should I store my {medicine_name}",
    "expire": "When does my prescription for {medicine_name} expire?",
    "man": "Who manufactures {medicine_name}",
    "overdose": "What are the symptoms of an {medicine_name} overdose, and what should I do if it happens?",
    "what": "What is {medicine_name}",
    "before": "What should I tell my doctor before taking {medicine_name}?",
    "ingredients": "What are the ingredients in {medicine_name}?"
    """

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="gpt-3.5-turbo",
    )
    response_json = json.loads(chat_completion.choices[0].message.content)

    return response_json

@MedIQProtocol.on_message(model=Medi,replies={UAgentResponse})
async def load_model(ctx:Context,sender:str,mes:Medi):
    response = await output(f'What is the Use of {mes.medicine_name} and What are the Side effects of the {mes.medicine_name}')
    ctx.logger.info("The Model SuccessFully Run")
    result =''
    attributes = ['usage','contraindications','dosage','general_info','Storage Query','expire','man','overdose','what','before','ingredients']
    for i in attributes:
        result+=i.capitalize()
        result+=" : "
        result+=response.get(i,'')
        result+='\n\n'
    print(result)
    await ctx.send(sender,UAgentResponse(message=result,type=UAgentResponseType.FINAL))


MedIQ.include(MedIQProtocol,publish_manifest=True)
MedIQ.run()