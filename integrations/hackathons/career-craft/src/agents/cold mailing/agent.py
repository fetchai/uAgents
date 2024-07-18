from uagents import Context, Model, Protocol
from ai_engine import UAgentResponse, UAgentResponseType
from pydantic import Field
import json
import requests


class Request(Model):
    name : str= Field(description = "Enter your Full Name")
    recruiterEmail : str=Field(description = "Enter the Recruiter's Email")
    job_description : str=Field(description= " Enter the Job Description")
    mail_type : str = Field(description = "Do you want to Enquire or Apply")



simples = Protocol(name="simples", version="1.1")


async def send_mail_request(job_description, mail_type,sendTo,name):
    url = "https://webweaver-model.onrender.com/sendEmail"  

    payload = {
        "name":name,
        "sendTo": sendTo,
        "job_description": job_description,
        "mail_type": mail_type
    }
    
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Request successful. Response body:")
        print(response.json())
        return response.json()
    else:
        print(f"Error: {response.status_code}. Failed to send mail request.")

@simples.on_message(model=Request, replies={UAgentResponse})
async def handle_message(ctx: Context, sender: str, msg: Request):
    response = await send_mail_request(msg.job_description,msg.mail_type,msg.recruiterEmail,msg.name)
    await ctx.send(
        sender, UAgentResponse(message="Email Sent Successfully", type=UAgentResponseType.FINAL)
    )


agent.include(simples)

