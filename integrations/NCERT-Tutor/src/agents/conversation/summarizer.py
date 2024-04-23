from uagents import Agent, Context, Model, Protocol
from ai_engine import UAgentResponse, UAgentResponseType
from uagents.setup import fund_agent_if_low
import requests
import json
from openai import (
    get_data,
    send_shared_link_data,
    Summary,
    Response,
    Error,
    OPENAI_API_KEY,
)


class Question(Model):
    question: str
    chapter: int
    subject: str
    standard: int


class Text(Model):
    pdf: str
    success: bool
    question: str
    chapter: str
    subject: str
    standard: str


async def send_pdf_content(ctx: Context, sender: str, query: Question):
    if query.question and query.chapter and query.subject and query.standard:
        ctx.logger.info(
            f"Question received: {query.question} {query.chapter} {query.subject} {query.standard}"
        )

        ##change to local host if running locally
        api_url = "http://localhost:8080/send-pdf-content"
        # api_url = "https://ncert-tutor-dev-dbkt.3.us-1.fl0.io/send-pdf-content"

        payload = {
            "standard": query.standard,
            "subject": query.subject,
            "chapter": query.chapter,
        }
        headers = {"accept": "application/json", "Content-Type": "application/json"}
        response = requests.post(api_url, json=payload, headers=headers)
        data = response.json()["content"]
        ctx.logger.info(f"{data}")

        request = Text(
            pdf=data,
            success=True,
            question=query.question,
            chapter=query.chapter,
            subject=query.subject,
            standard=query.standard,
        )

        request_json = json.dumps(request.dict())
        ctx.logger.info(f"Request: {request_json}")

        data = get_data(ctx, f"{request_json}")

        # ctx.logger.info(f'Summary: {data["summary"]}')
        # ctx.logger.info(f'Question Bank: {data["question_bank"]}')
        # ctx.logger.info(f'Answer Key: {data["answer_key"]}')

        msg = Summary(
            summary=data["summary"],
            question_bank=data["question_bank"],
            answer_key=data["answer_key"],
        )
        url = send_shared_link_data(msg)
        if url is not None:
            message = f'{msg.summary}\n{msg.question_bank}\n<a href="{url}">Link to answers</a>'
            ctx.logger.info(message)
        else:
            message = f"{msg.summary}\n{msg.question_bank}\n{msg.answer_key}"
        return message
    else:
        ctx.logger.info("Invalid request")
        return
