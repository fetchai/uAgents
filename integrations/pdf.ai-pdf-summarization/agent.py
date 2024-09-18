import requests
from ai_engine import UAgentResponse, UAgentResponseType


# Define the PDF Summarization Request model
class PDFSummarizationRequest(Model):
    url: str


# Define the protocol for PDF Summarization
pdf_summarization_protocol = Protocol("PDF Summarization")

# Global counter for the number of summarizations
summarization_count = 0


def upload_pdf(url, ctx):
    """Uploads a PDF from a URL and returns the document ID."""
    endpoint = "https://pdf.ai/api/v1/upload/url"
    headers = {"X-API-Key": API_KEY}
    payload = {
        "url": url,
        "isPrivate": False,  # Assuming the file is not private
        "ocr": False,  # Enabling OCR
    }
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json().get("docId")
    except requests.RequestException as e:
        ctx.logger.info(f"Error during PDF upload: {e}")
        return None


def summarize_pdf(doc_id, ctx):
    """Summarizes the uploaded PDF and returns the summary."""
    endpoint = "https://pdf.ai/api/v1/summary"
    headers = {"X-API-Key": API_KEY}
    payload = {"docId": doc_id, "language": "english"}
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        ctx.logger.info(f"Error during PDF summarization: {e}")
        return None


def delete_pdf(doc_id, ctx):
    """Deletes the uploaded PDF."""
    endpoint = "https://pdf.ai/api/v1/delete"
    headers = {"X-API-Key": API_KEY}
    payload = {"docId": doc_id}
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
    except requests.RequestException as e:
        ctx.logger.info(f"Error during PDF deletion: {e}")


# Handler for PDF Summarization requests
@pdf_summarization_protocol.on_message(
    model=PDFSummarizationRequest, replies=UAgentResponse
)
async def on_message(ctx: Context, sender: str, msg: PDFSummarizationRequest):
    ctx.logger.info(f"Received PDF summarization request from {sender}.")
    global summarization_count

    try:
        ctx.logger.info("Upload the PDF")
        # Upload the PDF
        doc_id = upload_pdf(msg.url, ctx)
        if not doc_id:
            raise Exception("Failed to upload PDF.")

        # Summarize the PDF
        ctx.logger.info("Summarize the PDF")
        summary = summarize_pdf(doc_id, ctx)
        if not summary:
            delete_pdf(doc_id, ctx)
            raise Exception("Failed to summarize PDF.")

        # Delete the PDF
        ctx.logger.info("Delete the PDF")
        delete_pdf(doc_id, ctx)

        # Increment the summarization count
        summarization_count += 1
        ctx.logger.info(f"summarization count: {summarization_count}")

        # Send the summary response
        await ctx.send(
            sender,
            UAgentResponse(
                message=f"{summary.get('content')}",
                type=UAgentResponseType.FINAL,  # Assuming FINAL indicates a successful response
            ),
        )

    except requests.RequestException as req_exc:
        ctx.logger.error(f"Request failed: {req_exc}")
        await ctx.send(
            sender,
            UAgentResponse(
                message=f"Request error: {req_exc}",
                type=UAgentResponseType.ERROR,  # Assuming ERROR indicates an error response
            ),
        )
    except Exception as exc:
        # Catch other general exceptions
        ctx.logger.error(f"An error occurred: {exc}")
        await ctx.send(
            sender,
            UAgentResponse(
                message=f"Error: {exc}",
                type=UAgentResponseType.ERROR,  # Assuming ERROR indicates an error response
            ),
        )


# Include the PDF Summarization protocol in your agent
agent.include(pdf_summarization_protocol)
