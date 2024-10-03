from uagents import Context, Model, Protocol
from ai_engine import UAgentResponse, UAgentResponseType
from pydantic import Field
import requests


class Request(Model):
    resume_text: str = Field(description="Enter the resume text")


simples = Protocol(name="Resume Optimizer Agent", version="1.1")


async def send_file_request(filename, base64_string):
    url = "https://2070-2402-e280-3e1b-1b4-f59b-6603-9f90-845b.ngrok-free.app/upload"

    payload = {"filename": filename, "base64_string": base64_string}

    response = requests.post(url, json=payload)
    if response.status_code == 200:
        print("Request successful. Response body:")
        print(response.json())
        return response.json()
    else:
        print(f"Error: {response.status_code}. Failed to send file request.")
        return None


async def resume_optimiser(resume_text):
    try:
        url = "https://resumeoptimizerpro.p.rapidapi.com/optimize"

        payload = {
            "ResumeText": resume_text,
            "WritingStyle": "Professional",
            "FormattingOptions": {"TemplateStyle": "1"},
        }
        headers = {
            "content-type": "application/json",
            "X-RapidAPI-Key": "YOUR_API_KEY",
            "X-RapidAPI-Host": "resumeoptimizerpro.p.rapidapi.com",
        }

        response = requests.post(url, json=payload, headers=headers)

        response_json = response.json()
        print(response_json)

        if "OptimizedResumeAsBase64String" in response_json:
            return response_json["OptimizedResumeAsBase64String"]
        else:
            # If the response does not contain the expected key, return None
            return None

    except Exception as e:
        print("An error occurred:", e)
        return None


@simples.on_message(model=Request, replies={UAgentResponse})
async def handle_message(ctx: Context, sender: str, msg: Request):
    optimized_resume = await resume_optimiser(msg.resume_text)
    response = await send_file_request("Download1.docx", optimized_resume)
    await ctx.send(
        sender,
        UAgentResponse(
            message=f"We have created an optimized resume just for you\nYou can access the resume at this link: {response['response']}",
            type=UAgentResponseType.FINAL,
        ),
    )
