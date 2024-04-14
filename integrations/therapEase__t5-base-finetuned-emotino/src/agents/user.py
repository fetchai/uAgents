from uagents import Model, Agent, Context, Protocol
from langchain.prompts.few_shot import FewShotPromptTemplate
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import LLMChain
import pandas as pd
from transformers import AutoTokenizer, AutoModelWithLMHead
import warnings
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from uagents.setup import fund_agent_if_low
from pydantic import Field

warnings.filterwarnings(
    "ignore", category=FutureWarning
)  # To suppress the first warning
warnings.filterwarnings("ignore", category=UserWarning)
tokenizer = AutoTokenizer.from_pretrained(
    "mrm8488/t5-base-finetuned-emotion", use_fast=False, legacy=False
)

model = AutoModelWithLMHead.from_pretrained("mrm8488/t5-base-finetuned-emotion")


def get_emotion(text):
    input_ids = tokenizer.encode(text + "</s>", return_tensors="pt")

    output = model.generate(input_ids=input_ids, max_length=2)

    dec = [tokenizer.decode(ids) for ids in output]
    label = dec[0]
    label = re.sub(r"<pad>", "", label)
    # return label
    return label


class user_message(Model):
    msg: str = Field(
        description="Hello, I am Leo. I'm here to listen to your concerns and help you in any way I can. Can you tell me a little bit about what's been troubling you?"
    )


class ai_message(Model):
    msg: str


# Set a unique identifier for your agent
SEED_PHRASE = "Gemini based emotion recognition model"

AGENT_MAILBOX_KEY = "d4d8db58-1a12-4549-92b9-51de6ea7662a"

assProtocol = Protocol("Assistant Protocol")

ass_agent = Agent(
    "Assistant",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

# Ensure the agent has enough funds to operate, if not, fund it
fund_agent_if_low(ass_agent.wallet.address())

THERAPY_AGENT_ADD = "agent1qd52csugatsjvzsm7xyfufqx940qe9cfu7f50chvm8z2dpama6a8vm7hjwd"


@assProtocol.on_message(model=user_message, replies={ai_message})
async def startup(ctx: Context, sender: str, message: ai_message):
    ctx.logger.info(message.msg)
    # derive user emotion using hugging face api
    emotion = get_emotion(message.msg)
    user_msg_store = f" User : {message.msg} ->[emotion prediction : {emotion}]"
    conversation = f"Assessment Agent: Hello, I am Leo. I'm here to listen to your concerns and help you in any way I can. Can you tell me a little bit about what's been troubling you? \n\n User: {user_msg_store}"

    await ctx.send(THERAPY_AGENT_ADD, ai_message(msg=conversation))


ass_agent.include(assProtocol)

if __name__ == "__main__":
    ass_agent.run()
