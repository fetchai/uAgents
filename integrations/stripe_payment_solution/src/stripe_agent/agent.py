import os
import uuid

import requests
from ai_engine import UAgentResponse, UAgentResponseType
from dotenv import load_dotenv
from uagents import Agent, Protocol, Context, Model
from uagents.setup import fund_agent_if_low

class KeyValue(Model):
    currency: str
    product_name: str
    unit_price: int
    units: int

class StripePaymentRequest(Model):
    item_in_cart: list[KeyValue]
    customer_email: str
    order_id: str

class QueryPaymentStatus(Model):
    client_reference_id: str



class PaymentStatus(Model):
    client_reference_id: str
    data: dict

load_dotenv()

agent = Agent(
    name="Stripe Agent",
    seed="Stripe Agent secret seed phrase",
    log_level="DEBUG",
    endpoint="http://localhost:8001/submit",
    port=8001
)
fund_agent_if_low(str(agent.wallet.address()))

print("Agent Address:", agent.address)


stripe_payment_protocol = Protocol("Stripe Payment Protocol", "1.00")

API_KEY = os.getenv('STRIPE_API_KEY', "")
ENDPOINT_SECRET = os.getenv('STRIPE_ENDPOINT_SECRET', "")
WEBHOOK_URL = os.getenv('STRIPE_WEBHOOK_URL', "")
STRIPE_API_URL = os.getenv('STRIPE_API_URL', "")


@stripe_payment_protocol.on_message(model=StripePaymentRequest, replies={UAgentResponse})
async def create_checkout_session(ctx: Context, sender: str, msg: StripePaymentRequest):
    ctx.logger.info(
        f"Received Request from {msg.customer_email} for Payment Link.")
    try:
        print(agent.address)
        payload = {
            'customer_creation': 'always',
            'customer_email': msg.customer_email,
            'mode': 'payment',
            'payment_intent_data[metadata][order_id]': msg.order_id,
            'success_url': f"{WEBHOOK_URL}/order/success?session_id={{CHECKOUT_SESSION_ID}}",
            'cancel_url': f"{WEBHOOK_URL}/cancel"
        }

        for index, item in enumerate(msg.item_in_cart):
            payload[f'line_items[{index}][price_data][currency]'] = item.currency
            payload[f'line_items[{index}][price_data][product_data][name]'] = item.product_name
            payload[f'line_items[{index}][price_data][unit_amount]'] = item.unit_price
            payload[f'line_items[{index}][quantity]'] = item.units

        headers = {
            'Authorization': f'Bearer {API_KEY}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        # encoded_payload = urllib.parse.urlencode(payload, doseq=True)
        response = requests.post(f"{STRIPE_API_URL}/checkout/sessions", headers=headers, data=payload)
        session = response.json()
        request_id = str(uuid.uuid4())
        if response.status_code == 200 and 'url' in session:
            resp = await ctx.send(
                sender,
                UAgentResponse(
                    message=str(session['url']),
                    type=UAgentResponseType.FINAL,
                    request_id=request_id
                ),
            )

            ctx.storage.set(msg.order_id, {'address': sender})
        else:
            await ctx.send(
                sender,
                UAgentResponse(
                    message="Can't generate payment link, please try again after some time.!",
                    type=UAgentResponseType.FINAL,
                    request_id=request_id
                ),
            )
    except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(
            sender, UAgentResponse(message=str(exc), type=UAgentResponseType.ERROR)
        )


@stripe_payment_protocol.on_message(model=QueryPaymentStatus, replies={UAgentResponse})
async def payment_status(ctx: Context, sender: str, msg: QueryPaymentStatus):
    ctx.logger.info(
        f"Received query request from {msg.client_reference_id}.")
    try:
        payment_details = ctx.storage.get(msg.client_reference_id) or None
        if 'payment_data' in payment_details:
            await ctx.send(
                sender, UAgentResponse(message="Payment Succeeded", type=UAgentResponseType.FINAL)
            )
        else:
            await ctx.send(
                sender, UAgentResponse(message="Payment confirmation awaited", type=UAgentResponseType.FINAL)
            )
    except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(
            sender, UAgentResponse(message=str(exc), type=UAgentResponseType.ERROR)
        )


@stripe_payment_protocol.on_message(model=PaymentStatus, replies={UAgentResponse})
async def payment_status(ctx: Context, sender: str, msg: PaymentStatus):
    ctx.logger.info(
        f"Received Payment Update of Customer {msg.client_reference_id}.")
    try:
        payment_details = ctx.storage.get(msg.client_reference_id) or None
        if payment_details:
            payment_details['payment_data'] = msg.data
            ctx.storage.set(msg.client_reference_id, payment_details)

            await ctx.send(
                payment_details['address'], UAgentResponse(message="Payment Succeeded", type=UAgentResponseType.FINAL)
            )
            print(f"Notified {payment_details['address']} of payment confirmation")
        else:
            print('Weird...')

    except Exception as exc:
        ctx.logger.error(exc)
        await ctx.send(
            sender, UAgentResponse(message=str(exc), type=UAgentResponseType.ERROR)
        )


agent.include(stripe_payment_protocol, publish_manifest=True)

if __name__ == "__main__":
    agent.run()
