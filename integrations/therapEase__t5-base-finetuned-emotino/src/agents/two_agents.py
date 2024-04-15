from langchain_google_genai import ChatGoogleGenerativeAI
import pandas as pd
from uagents import Model, Agent, Bureau, Context

# import os
# from dotenv import load_dotenv

from langchain.prompts.prompt import PromptTemplate
from langchain.chains import LLMChain

import json

from transformers import AutoTokenizer, AutoModelWithLMHead
import warnings
import re

warnings.filterwarnings(
    "ignore", category=FutureWarning
)  # To suppress the first warning
warnings.filterwarnings("ignore", category=UserWarning)
tokenizer = AutoTokenizer.from_pretrained(
    "mrm8488/t5-base-finetuned-emotion", use_fast=False, legacy=False
)

model = AutoModelWithLMHead.from_pretrained(
    "mrm8488/t5-base-finetuned-emotion")


def get_emotion(text):
    input_ids = tokenizer.encode(text + "</s>", return_tensors="pt")

    output = model.generate(input_ids=input_ids, max_length=2)

    dec = [tokenizer.decode(ids) for ids in output]
    label = dec[0]
    label = re.sub(r"<pad>", "", label)
    # return label
    return label


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
    model="gemini-pro", google_api_key="YOUR_API_KEY"
)
# conversation_history=""


def append_to_file(filename, value):
    """Appends a value to the given text file.

    Args:
        filename: The name of the text file.
        value: The value to be appended (can be any data type that can be converted to a string).
    """
    with open(filename, "a") as file:
        # Convert value to string and add newline
        file.write(str(value) + "\n")


def read_file_as_string(filename):
    with open(filename, "r") as file:
        return file.read()


def generate_response(user_message, filename):
    user_message = user_message
    filename = filename
    conversation_history = read_file_as_string(filename=filename)

    conv_prompt = PromptTemplate.from_template(
        """You are an expert mental therapist./
        Your task is to confront the user for his problems and ask critical questions to understand his mental health. You have to somehow ask the user about his symptoms, possible causes(relationship issues, health issues, sad demise) and carry on the conversation. The following is the conversation so far, continue asking questions. \
        Speak with the user in a very assistive and helpful manner.

    **Conversation History:**

    {conversation_history}

    **User Input:**

    {user_input}

    **Respond:**"""
    )

    conv_chain = LLMChain(llm=llm, prompt=conv_prompt, verbose=False)
    # conversation_history=""
    response = conv_chain.run(
        conversation_history=conversation_history, user_input=user_message
    )
    return response


def generate_final_report(data):
    # filename=filename
    data = data
    # conversation_history=read_file_as_string(filename=filename)
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
    # conversation_history=""
    response = conv_chain.run(conversation_history=data)
    return response


# Example usage
filename = "src/agents/msgs.txt"
# value1 = "This is the first value"
# value2 = 42  # Integer value

# append_to_file(filename, "hello")
# append_to_file(filename, value2)


class user_message(Model):
    msg: str


class ai_message(Model):
    msg: str


ass_agent = Agent("Assistant", seed="I am here to help")
user_agent = Agent("User", seed="I am a stressed user")
therapy_agent = Agent("Therapy", seed="I give therapy")


@ass_agent.on_event("startup")
async def startup(ctx: Context):
    # global conversation_history
    ctx.storage.set("filename", "src/agents/msgs.txt")

    initial_msg = "Hello, I am Leo. I'm here to listen to your concerns and help you in any way I can. Can you tell me a little bit about what's been troubling you? "
    ctx.logger.info(initial_msg)

    # initial_msg_store=f"Assessment Agent : {initial_msg}"

    # filename=ctx.storage.get("filename")

    # append_to_file(filename=filename,value=initial_msg_store)
    user_input = input("User : ")
    emotion = get_emotion(user_input)
    user_msg_store = f" User : {user_input} ->[emotion prediction : {emotion}]"
    conversation = f"Assessment Agent: {initial_msg} \n\n User: {user_msg_store}"

    await ctx.send(therapy_agent.address, ai_message(msg=conversation))


# @user_agent.on_message(ai_message)
# async def handle_message(ctx: Context, sender:str, message: ai_message):
#     #take user input
#     if ctx.storage.has("filename"):
#        filename=ctx.storage.get("filename")
#     else:
#        filename = "src/agents/msgs.txt"
#        ctx.storage.set("filename",'src/agents/msgs.txt')


#     user_input = input("User: ")
#     if user_input=="bye":
#        print("inside exit")
#        await ctx.send(therapy_agent.address, user_message(msg=filename))
#     else :
#         emotion=get_emotion(user_input)
#         user_msg_store = f" User : {user_input} -> [Emotion Detection : {emotion}]"

#         #append user message to file
#         # print(filename)
#         append_to_file(filename=filename, value=user_msg_store)
#         # print("appended to txt file")

#         await ctx.send(ass_agent.address, user_message(msg=user_input))

# @ass_agent.on_message(user_message)
# async def handle_user_message(ctx: Context, sender:str, message: user_message):
#     # user_message=message.msg
#     # filename=ctx.storage.get("filename")

#     response=generate_response(user_message=message.msg,filename=filename)

#     ctx.logger.info(response)
#     append_to_file(filename=filename, value=f"Assessment Agent : {response}")
#     await ctx.send(user_agent.address, ai_message(msg=response))


@therapy_agent.on_message(ai_message)
async def user_message_handler(ctx: Context, sender: str, message: ai_message):
    ctx.logger.info("generating final report")
    # data=read_file_as_string(filename=message.msg)
    response = generate_final_report(message.msg)
    print(response)
    response = json.loads(response)
    ctx.logger.info(ctx.address)
    ctx.logger.info(response)
    if response["condition_of_patient"] == "severe":
        ctx.logger.info(
            "We have analysed your condition and we think that you should consult to a therapist. \n Please enter your city : "
        )
        city = input("City: ")
        therapists = get_top_5_therapists(city)
        ctx.logger.info(
            f"Here are top 5 therapists in {city} : \n {therapists}")

    else:
        ctx.logger.info(
            """We have analysed your condition and we think that you can get back into shape easily! We have analysed your condition and we think that you can get back into shape easily with some self-care!
             Here are some resources for you :

1. https://www.verywellmind.com/ - *Blogs for self care*
2. https://www.psychcentral.com/ -*Blogs for Mental Health awareness*
3. https://www.amahahealth.com/therapy- *Website for booking mental health appointments*

Govt Helpline :
 24/7 toll-free mental health rehabilitation helpline is 1800-599-0019, also known as Kiran. This helpline is available in 13 languages and was launched by the Ministry of Social Justice and Empowerment to provide support to people with mental illness."""
        )


b = Bureau()
b.add(user_agent)
b.add(ass_agent)
b.add(therapy_agent)

if __name__ == "__main__":
    b.run()
