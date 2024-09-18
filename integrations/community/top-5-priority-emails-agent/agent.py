import imaplib
import email
import datetime
from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
import ast

from uagents import Agent, Context, Protocol, Model
import os
from pydantic import Field
from ai_engine import UAgentResponse, UAgentResponseType
from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
import re


class EmailAssistant(Model):
    email: str = Field(
        description="Email of interest to the user to login to Gmail. Always request this field since it can be different from the actual user email."
    )
    password: str = Field(description="Password of the user to login to Gmail")


OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SEED_PHRASE = os.getenv("SEED_PHRASE")
AGENT_MAILBOX_KEY = os.getenv("AGENT_MAILBOX_KEY")


chat = ChatOpenAI(model="gpt-3.5-turbo-0125", api_key=OPENAI_API_KEY)

email_assistant_agent = Agent(
    name="Email Assistant Agent",
    seed=SEED_PHRASE,
    mailbox=f"{AGENT_MAILBOX_KEY}@https://agentverse.ai",
)

email_assistant_protocol = Protocol("Email Assistant Protocol")

PROMPT = "Given that you are a mail assistant and you help in choosing  top 5 urgent mails for user \
that should answer right away. Your goal is to understand based on various factor how urgent \
is an email. The criteria could be: \
- sentiment analysis \
- context of the email (work's deadline, CEO asking  for specific info asap) \
- urgency of the tone \
Also make sure to understand if a email is a possible spam, if yes don't include it in your answer. \
You will need to choose emails from below context and your answer should be just the position \
inside the list given in the context \
e.g. \
emails =[email1, email2, email3] \
top_urgent_emails=[2, 3, 1] (this might be your answer ALWAYS based on how urgent emails are)"


def get_gpt_response(emails_content: List[Dict[str, str]]):
    system_message_prompt = SystemMessagePromptTemplate.from_template(PROMPT)
    human_template = "{context}"
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)
    chat_prompt = ChatPromptTemplate.from_messages(
        [system_message_prompt, human_message_prompt]
    )
    try:
        answer = chat.invoke(
            chat_prompt.format_prompt(context=str(emails_content)).to_messages()
        )
    except Exception as e:
        print(e)
        return []

    answer = answer.content
    if str(answer).startswith("[") and str(answer).endswith("]"):
        list_answer = ast.literal_eval(answer)
    else:
        possible_init_answer = str(answer).find("[")
        possible_end_answer = str(answer).find("]")
        if possible_init_answer != -1 and possible_end_answer != -1:
            list_answer = ast.literal_eval(
                answer[possible_init_answer : possible_end_answer + 1]
            )
        else:
            # retry
            try:
                answer = chat.invoke(
                    chat_prompt.format_prompt(context=str(emails_content)).to_messages()
                )
            except Exception as e:
                print(e)
                return []

            if str(answer).startswith("[") and str(answer).endswith("]"):
                list_answer = ast.literal_eval(answer)
            else:
                list_answer = []

    return list_answer


def retrieve_emails(unread_emails: List, mail: imaplib.IMAP4_SSL):
    emails_content = []
    for e_id in unread_emails:
        status, response = mail.fetch(e_id, "(RFC822)")
        msg_json = {}
        if status == "OK":
            email_msg = response[0][1].decode()
            msg_data = email.message_from_string(email_msg)

            msg_json["subject"] = msg_data["subject"]
            msg_json["from"] = msg_data["from"]
            if isinstance(msg_json["subject"], bytes):
                msg_json["subject"] = msg_json["subject"].decode()

            if msg_data.is_multipart():
                for part in msg_data.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    try:
                        body = part.get_payload(decode=True).decode()
                    except:
                        pass
                    if (
                        content_type == "text/plain"
                        and "attachment" not in content_disposition
                    ):
                        msg_json["body"] = body
            else:
                content_type = msg_data.get_content_type()

                body = msg_data.get_payload(decode=True).decode()
                if content_type == "text/plain":
                    msg_json["body"] = body

            mail.store(e_id, "-FLAGS", "\\Seen")
            emails_content.append(msg_json)
    return emails_content


@email_assistant_protocol.on_message(model=EmailAssistant, replies={UAgentResponse})
async def suggest_top_priority_emails(ctx: Context, sender: str, msg: EmailAssistant):
    ctx.logger.info(msg.email)

    username = msg.email
    password = msg.password

    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(username, password)

    mail.select("inbox")

    date = (datetime.date.today() - datetime.timedelta(days=0)).strftime("%d-%b-%Y")
    status, response = mail.search(None, "(UNSEEN)", f'(SINCE "{date}")')

    if status == "OK":
        unread_msg_nums = response[0].split()

        print(f"There are {len(unread_msg_nums)} unread emails for today.")

        emails_content = retrieve_emails(unread_msg_nums, mail)

        list_answer = get_gpt_response(emails_content=emails_content)

        if list_answer == []:
            await ctx.send(
                sender,
                UAgentResponse(
                    message="There was an unexpected error",
                    type=UAgentResponseType.ERROR,
                ),
            )

        final_answer = ""
        for index, answer in enumerate(list_answer):
            data = emails_content[answer - 1]
            parsed_sender = re.sub(r"<[^>]+>", "", data["from"])
            final_answer += (
                f"""●{index} sender: {parsed_sender} subject: {data['subject']}\n"""
            )

        mail.close()
        mail.logout()

        ctx.logger.info(final_answer)
        await ctx.send(
            sender, UAgentResponse(message=final_answer, type=UAgentResponseType.FINAL)
        )

    else:
        print("Failed to retrieve emails.")
        await ctx.send(
            sender,
            UAgentResponse(
                message="Failed to retrieve emails", type=UAgentResponseType.ERROR
            ),
        )


email_assistant_agent.include(email_assistant_protocol, publish_manifest=True)
email_assistant_agent.run()
