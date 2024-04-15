from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts.prompt import PromptTemplate
from langchain.chains import LLMChain
from .therapist import get_top_5_therapists
from transformers import AutoTokenizer, AutoModelWithLMHead
import warnings
import re
import json


# To suppress the first warning shown on the terminal
warnings.filterwarnings(
    "ignore", category=FutureWarning
)
warnings.filterwarnings("ignore", category=UserWarning)
tokenizer = AutoTokenizer.from_pretrained(
    "mrm8488/t5-base-finetuned-emotion", use_fast=False, legacy=False
)

# t5 Model
model = AutoModelWithLMHead.from_pretrained(
    "mrm8488/t5-base-finetuned-emotion")

# get emotions


def get_emotion(text):
    input_ids = tokenizer.encode(text + "</s>", return_tensors="pt")
    output = model.generate(input_ids=input_ids, max_length=2)
    dec = [tokenizer.decode(ids) for ids in output]
    label = dec[0]
    label = re.sub(r"<pad>", "", label)
    return label


# Gemini Init
llm = ChatGoogleGenerativeAI(
    model="gemini-pro", google_api_key="YOUR_API_KEY"
)

# write to file


def append_to_file(filename, value):
    with open(filename, "a") as file:
        # Convert value to string and add newline
        file.write(str(value) + "\n")

# read from file


def read_file_as_string(filename):
    with open(filename, "r") as file:
        return file.read()


# generate response from gemini
def generate_gpt_response(user_message):
    user_message = user_message
    conversation_history = read_file_as_string(filename="app/utils/msgs.txt")

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


# generate report from conversation
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


# generate message response
def generate_response(response):
    user_resp = response
    if response.lower() == "hi" or response.lower() == "hello" or response.lower() == "hay":
        initial_msg = "Hello👋🏻, I am Leo. I'm here to listen to your concerns and help you in any way I can. Can you tell me a little bit about what's been troubling you? "
        return initial_msg
    elif response.lower() == "bye":
        conv_history = read_file_as_string("app/utils/msgs.txt")
        response = generate_final_report(conv_history)
        response = json.loads(response)
        if response["condition_of_patient"] == "severe":
            therapists = get_top_5_therapists(city="mumbai")
            resp = f"We have analysed your condition and we think that you should consult to a therapist. Here are top 5 therapists in Mumbai : \n {therapists}"
        else:
            resp = """ We have analysed your condition and we think that you can get back into shape easily with some self-care!
             Here are some resources for you :

1. https://www.verywellmind.com/ - *Blogs for self care*
2. https://www.psychcentral.com/ -*Blogs for Mental Health awareness*
3. https://www.amahahealth.com/therapy- *Website for booking mental health appointments*

Govt Helpline :
 24/7 toll-free mental health rehabilitation helpline is 1800-599-0019, also known as Kiran. This helpline is available in 13 languages and was launched by the Ministry of Social Justice and Empowerment to provide support to people with mental illness."""
        return resp
    else:
        response = generate_gpt_response(user_message=response)
        response_to_store = f"User : {user_resp}, AI Agent : {response}"
        append_to_file(filename="app/utils/msgs.txt", value=response_to_store)
    return response
