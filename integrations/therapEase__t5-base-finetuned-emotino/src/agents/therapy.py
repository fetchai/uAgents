from uagents import Model, Agent, Context, Protocol

"""
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import LLMChain
import json
from transformers import AutoTokenizer
import warnings
import re
import pandas as pd
"""
from uagents.setup import fund_agent_if_low
from ai_engine import UAgentResponse, UAgentResponseType
from pydantic import Field

'''
warnings.filterwarnings(
    "ignore", category=FutureWarning
)  # To suppress the first warning
warnings.filterwarnings("ignore", category=UserWarning)
tokenizer = AutoTokenizer.from_pretrained(
    "mrm8488/t5-base-finetuned-emotion", use_fast=False, legacy=False
)


df = pd.read_csv("src/agents/data.csv")


def get_top_5_therapists(city):
    # Filter therapists based on the input city
    therapists_in_city = df[df["city"].str.lower() == city.lower()]

    if therapists_in_city.empty:
        print("No therapists found in the specified city.")
        return

    # Sort therapists based on years_of_exp in descending order and get the top 5
    top_5_therapists = therapists_in_city.sort_values(
        by="years_of_exp", ascending=False
    ).head(5)

    return top_5_therapists


llm = ChatGoogleGenerativeAI(
    model="gemini-pro", google_api_key="AIzaSyA0SThtOf3QoNJLr12CiDwkiTtUafL1rXE"
)


def generate_final_report(data):
    data = data
    conv_prompt = PromptTemplate.from_template(
        """You are an expert mental therapist./
    We are providing you with the a conversational data between between a user and a assessment chatbot. /
    Based on the conversation history provided, you have to output a final assessment of the user. We have also tagged all the user sentences with emotions detection deep learning model, please consider the emotions while generating the response./
    Return the response only as a json object starting and ending with curly brackets with the following keys and value-/ condition_of_patient : basic/mediocre/severe/, possible_causes : [list of possible causes discussed],/
    
                                               
    **Conversation History:**

    {conversation_history}

    **Respond:** """
    )

    conv_chain = LLMChain(llm=llm, prompt=conv_prompt, verbose=False)
    response = conv_chain.run(conversation_history=data)
    return response

'''


class ai_message_city(Model):
    city: str = Field(
        description="City of the person, specifically ask the user the following: ENTER YOUR CITY: "
    )


filename = "src/agents/msgs.txt"

SEED_PHRASE = "Agent for suggesting therapists"
AGENT_MAILBOX_KEY = "c2761651-9175-438d-8a1e-86a4606d0be3"

therapy_protocol = Protocol("Therapy Protocol")


therapy_agent = Agent(
    name="Therapy",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

# Ensure the agent has enough funds to operate, if not, fund it
fund_agent_if_low(therapy_agent.wallet.address())


@therapy_agent.on_event("startup")
async def on_startup(ctx: Context):
    print(therapy_agent.address)


async def get_top_5_therapists(city):
    return "Good therapist"


@therapy_protocol.on_message(model=ai_message_city, replies={UAgentResponse})
async def user_message_handler(ctx: Context, sender: str, message: ai_message_city):
    ctx.logger.info("generating final report")

    therapists = await get_top_5_therapists(message.city)
    ctx.logger.info(f"Here are top 5 therapists in {message.city} : \n {therapists}")

    await ctx.send(
        sender,
        UAgentResponse(
            message=f"Here are top 5 therapists in {message.city} : \n {therapists}",
            type=UAgentResponseType.FINAL,
        ),
    )

    """
    response = generate_final_report(message.msg)
    print(response)
    response = json.loads(response)
    if response["condition_of_patient"] == "severe":
        ctx.logger.info(
            "We have analysed your condition and we think that you should consult to a therapist. \n Please enter your city : "
        )
        city = input("City: ")
        therapists = get_top_5_therapists(city)
        ctx.logger.info(f"Here are top 5 therapists in {city} : \n {therapists}")

    else:
        ctx.logger.info(
            "We have analysed your condition and we think that you can get back into shape by doing this course : "
        )
    """


# Include the therapy protocol in the agent's capabilities
therapy_agent.include(therapy_protocol)

if __name__ == "__main__":
    therapy_agent.run()
