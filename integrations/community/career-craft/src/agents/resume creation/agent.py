from uagents import Context, Model, Protocol
from ai_engine import UAgentResponse, UAgentResponseType
from pydantic import Field
import requests


class Request(Model):
    name: str = Field(description="Full name of the person.", default="Mustafa")
    email: str = Field(description="Email address of the person.")
    phone: str = Field(description="Contact phone number.")
    address: str = Field(description="Physical address of the person.")
    skills: str = Field(
        description="Comma-separated list of skills the person has acquired."
    )
    certifications: str = Field(
        description="Comma-separated list of certifications the person holds."
    )
    awards: str = Field(
        description="Comma-separated list of awards the person has received."
    )
    experiences: str = Field(
        description="Comma-separated list of professional experiences."
    )


simples = Protocol(name="Resume Creation Agent", version="1.1")


async def fetch_data_from_rapidapi(
    name, email, phone, address, skills, certifications, awards, experiences
):
    try:
        url = "https://webweaver-model.onrender.com/generation"

        body = {
            "name": name,
            "email": email,
            "phone": phone,
            "address": address,
            "skills": skills,
            "certifications": certifications,
            "awards": awards,
            "experiences": experiences,
        }

        headers = {
            "Content-Type": "application/json",
        }

        response = await requests.post(url, json=body, headers=headers)
        print("got response")
        fact = response.json()["response"]
        print(fact)
        return fact
    except:
        print("An error occurred")
        return "An error occurred"


@simples.on_message(model=Request, replies={UAgentResponse})
async def handle_message(ctx: Context, sender: str, msg: Request):
    response = await fetch_data_from_rapidapi(
        msg.name,
        msg.email,
        msg.phone,
        msg.address,
        msg.skills,
        msg.certifications,
        msg.awards,
        msg.experiences,
    )
    await ctx.send(
        sender, UAgentResponse(message=response, type=UAgentResponseType.FINAL)
    )


agent.include(simples)
