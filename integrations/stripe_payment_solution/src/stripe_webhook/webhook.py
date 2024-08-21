import asyncio
import json
import os

import stripe
from flask import Flask, request, jsonify, render_template_string
from uagents import Agent
from uagents import Model
from uagents.communication import send_sync_message

class PaymentStatus(Model):
    client_reference_id: str
    data: dict

app = Flask(__name__)

agent = Agent()

stripe.api_key = os.getenv('STRIPE_API_KEY')
webhook_secret = os.getenv('STRIPE_ENDPOINT_SECRET')


@app.route('/order/success', methods=['GET'])
async def order_success():
    session = stripe.checkout.Session.retrieve(request.args.get('session_id'))
    customer = stripe.Customer.retrieve(session.customer)
    retries = 5
    for attempt in range(retries):
        try:
            return render_template_string(
                '<html><body><h1>Thanks for your order, {{customer.name}}!</h1></body></html>',
                customer=customer)
        except Exception as e:
            print(f"Attempt {attempt + 1} failed with error: {e}")
            if attempt < retries - 1:
                print("Retrying...")
                await asyncio.sleep(5)  # Add a delay before retrying


@app.route('/webhook', methods=['POST'])
async def webhook_received():
    # You can use webhooks to receive information about asynchronous payment events.
    # For more about our webhook events, check out https://stripe.com/docs/webhooks.
    webhook_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    request_data = json.loads(request.data)

    if webhook_secret:
        # Retrieve the event by verifying the signature using the raw body and secret if webhook signing is configured.
        signature = request.headers.get('stripe-signature')
        try:
            event = stripe.Webhook.construct_event(
                payload=request.data, sig_header=signature, secret=webhook_secret)
            data = event['data']
        except Exception as e:
            return e
        # Get the type of webhook event sent - used to check the status of PaymentIntents.
        event_type = event['type']
    else:
        data = request_data['data']
        event_type = request_data['type']
    data_object = data['object']
    print(data_object, "Payment")
    print('event ' + event_type)

    if event_type == 'charge.updated':
        print("Event Details:", data_object)
        response = await send_sync_message('agent1qtehcv05d2yfdxgyhk8wnk9pavl7yxyzg2m05gvqwgggwtxas99nugry6xk',
                                           PaymentStatus(
                                               client_reference_id=data_object['metadata']['order_id'],
                                               data=data_object
                                           ))
        print(response)

    return jsonify({'status': 'success'})


if __name__ == '__main__':
    app.run(port=4242, debug=True)
