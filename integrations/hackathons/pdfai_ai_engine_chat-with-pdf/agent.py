from ai_engine import UAgentResponse, UAgentResponseType

# Define the Chat With PDF Request model
class ChatWithPDFRequest(Model):
    url: str
    question: str

# Define the protocol for Chatting With PDF
chat_with_pdf_protocol = Protocol("Chat With PDF")

# Dictionary to store URL and corresponding docId
url_docId_map = {}

def upload_pdf_if_needed(url, ctx):
    """Uploads a PDF from a URL if it's not already uploaded, and returns the document ID."""
    if url in url_docId_map:
        ctx.logger.info(f"PDF is already uploaded")
        return url_docId_map[url]

    endpoint = "https://pdf.ai/api/v1/upload/url"
    headers = {"X-API-Key": API_KEY}
    payload = {"url": url, "isPrivate": False, "ocr": False}

    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        docId = response.json().get("docId")
        url_docId_map[url] = docId  # Store the docId for future reference
        return docId
    except Exception as e:
        ctx.logger.info(f"Error during PDF upload: {e}")
        return None

def chat_with_pdf(doc_id, question, ctx):
    """Sends a question to the PDF and returns the answer."""
    endpoint = "https://pdf.ai/api/v1/chat"
    headers = {"X-API-Key": API_KEY}
    payload = {"docId": doc_id, "message": question, "save_chat": False, "language": "english", "use_gpt4": False}

    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        ctx.logger.info(f"Chat with PDF Response Status: {response.status_code}")
        ctx.logger.info(f"Chat with PDF Response Body: {response.text}")
        response.raise_for_status()
        content = response.json().get("content", None)
        return content
    except Exception as e:
        ctx.logger.info(f"Error during chat with PDF: {e}")
        return None

@chat_with_pdf_protocol.on_message(model=ChatWithPDFRequest, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: ChatWithPDFRequest):
    ctx.logger.info(f"Received chat with PDF request from {sender}.")

    try:
        ctx.logger.info("Checking if PDF needs uploading")
        doc_id = upload_pdf_if_needed(msg.url, ctx)
        if not doc_id:
            raise Exception("Failed to upload or retrieve PDF.")

        ctx.logger.info("Chatting with the PDF")
        answer = chat_with_pdf(doc_id, msg.question, ctx)
        if not answer:
            raise Exception("Failed to chat with PDF.")

        await ctx.send(
            sender,
            UAgentResponse(
                message=answer,
                type=UAgentResponseType.FINAL
            )
        )

    except Exception as exc:
        ctx.logger.error(f"An error occurred: {exc}")
        await ctx.send(
            sender,
            UAgentResponse(
                message=f"Error: {exc}",
                type=UAgentResponseType.ERROR
            )
        )

# Include the Chat With PDF protocol in your agent
agent.include(chat_with_pdf_protocol)
