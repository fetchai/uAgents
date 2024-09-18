from uagents import Context, Model, Protocol
from ai_engine import UAgentResponse, UAgentResponseType
from pydantic import Field
import requests


class Request(Model):
    job_description: str = Field(description=" Enter the Job Description")
    link: str = Field(description="Enter the Link of your Resume")


simples = Protocol(name="simples", version="1.1")


async def send_mail_request(job_description, link):
    url = "https://webweaver-model.onrender.com/compare"

    payload = {"job_description": job_description, "resume_url": link}

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Request successful. Response body:")
        print(response.json())
        return response.json()
    else:
        print(f"Error: {response.status_code}. Failed to send mail request.")


@simples.on_message(model=Request, replies={UAgentResponse})
async def handle_message(ctx: Context, sender: str, msg: Request):
    response = await send_mail_request(msg.job_description, msg.link)
    await ctx.send(
        sender,
        UAgentResponse(message=response["response"], type=UAgentResponseType.FINAL),
    )


agent.include(simples)
