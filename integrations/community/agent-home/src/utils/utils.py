from dotenv import load_dotenv, find_dotenv
import google.generativeai as genai
import os
from src.utils.prompts import PREFIX, INSTRUCTIONS, SUFFIX, FUNCTION_PARAMETER_PROMPT
from src.messages.models import LightsRequest, ACRequest, WindowRequest

load_dotenv(find_dotenv())  # read local .env file

genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
llm_model = genai.GenerativeModel("gemini-pro")

requests_template = "\n\n".join([PREFIX, INSTRUCTIONS, SUFFIX])


def plan_requests(inp):
    prompt = requests_template.format(user_input=inp)
    response = llm_model.generate_content(prompt)
    print("Inside plan_requests", response.text)
    return response.text


parameters_template = "\n\n".join([FUNCTION_PARAMETER_PROMPT])


async def create_message(sub_task, request_key, request_description, protocol):
    # EXTRACTED PARAMETERS
    prompt = parameters_template.format(
        function_parameters=request_key,
        parameter_description=request_description,
        user_input=sub_task,
    )
    response = llm_model.generate_content(prompt)
    print("Inside create_message", response.text)
    params = eval(response.text)

    if protocol == "lights":
        return LightsRequest(**params)
    elif protocol == "ac":
        if "temperature" not in params.keys() or params["temperature"] is None:
            params["temperature"] = 25
        return ACRequest(**params)
    elif protocol == "window":
        if "put_curtains" not in params.keys() or params["put_curtains"] is None:
            params["put_curtains"] = 1
        return WindowRequest(**params)
