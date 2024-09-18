from ai_engine import UAgentResponse, UAgentResponseType
import requests


# Define the Invoice Data Request model
class InvoiceDataRequest(Model):
    url: str  # URL of the invoice PDF
    query: str = None  # Optional query about the invoice


# Define the protocol for Invoice Data Retrieval
invoice_data_protocol = Protocol("Invoice Data Retrieval")


def upload_pdf(url, ctx):
    """Uploads a PDF from a URL and returns the document ID."""
    endpoint = "https://pdf.ai/api/v1/upload/url"
    headers = {"X-API-Key": API_KEY}
    payload = {"url": url, "isPrivate": False, "ocr": False}

    ctx.logger.info(f"Uploading invoice PDF for URL: {url}")
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        response.raise_for_status()
        docId = response.json().get("docId")
        ctx.logger.info(f"Invoice PDF uploaded successfully, docId: {docId}")
        return docId
    except Exception as e:
        ctx.logger.error(f"Error during invoice PDF upload: {e}")
        return None


def get_invoice_data(doc_id, query, ctx):
    """Retrieves invoice data in JSON format using the docId."""
    endpoint = "https://pdf.ai/api/v1/invoice"
    headers = {"X-API-Key": API_KEY}
    payload = {"docId": doc_id, "message": query} if query else {"docId": doc_id}

    ctx.logger.info(f"Retrieving invoice data with docId: {doc_id}")
    try:
        response = requests.post(endpoint, json=payload, headers=headers)
        ctx.logger.info(f"Response Status: {response.status_code}")
        ctx.logger.info(f"Response Body: {response.text}")
        response.raise_for_status()
        content = response.json().get("content")
        ctx.logger.info(f"content: {content}")
        return content
    except Exception as e:
        ctx.logger.error(f"Error retrieving invoice data: {e}")
        return None


@invoice_data_protocol.on_message(model=InvoiceDataRequest, replies=UAgentResponse)
async def on_message(ctx: Context, sender: str, msg: InvoiceDataRequest):
    ctx.logger.info(f"Received invoice data request from {sender} for URL: {msg.url}")

    try:
        doc_id = upload_pdf(msg.url, ctx)
        if not doc_id:
            raise Exception("Failed to upload invoice PDF.")

        invoice_data = get_invoice_data(doc_id, msg.query, ctx)
        if invoice_data is None:
            raise Exception("Failed to retrieve invoice data.")

        invoice_data_str = str(invoice_data)

        await ctx.send(
            sender,
            UAgentResponse(message=invoice_data_str, type=UAgentResponseType.FINAL),
        )

    except Exception as exc:
        ctx.logger.error(f"An error occurred: {exc}")
        await ctx.send(
            sender,
            UAgentResponse(message=f"Error: {exc}", type=UAgentResponseType.ERROR),
        )


# Include the Invoice Data Retrieval protocol in your agent
agent.include(invoice_data_protocol)
