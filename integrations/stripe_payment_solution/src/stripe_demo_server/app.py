import asyncio
from typing import List

from flask import Flask, render_template, request, jsonify
from pydantic import Field
from uagents import Model
from uagents.communication import send_sync_message


app = Flask(__name__)

class KeyValue(Model):
    currency: str
    product_name: str
    unit_price: int
    units: int

class QueryPaymentStatus(Model):
    client_reference_id: str

class StripePaymentRequest(Model):
    item_in_cart: list[KeyValue]
    customer_email: str
    order_id: str


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/test', methods=['GET'])
def test():
    return jsonify({"message": "Flask server is running"}), 200


def run_async(coro):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@app.route('/query', methods=['POST'])
async def query_agent():
    payment_status = QueryPaymentStatus(
        client_reference_id='123456'
    )
    response = await send_sync_message(
        'agent1qtehcv05d2yfdxgyhk8wnk9pavl7yxyzg2m05gvqwgggwtxas99nugry6xk',
        payment_status
    )
    print(response)

    return jsonify(response)


@app.route('/process', methods=['POST'])
async def process():
    data = request.json

    # Create a StripePaymentRequest object
    payment_request = StripePaymentRequest(
        item_in_cart=data['item_in_cart'],
        customer_email=data['customer_email'],
        order_id=data['order_id']
    )
    print("sending the payment request to Stripe agent")

    response = await send_sync_message(
        'agent1qtehcv05d2yfdxgyhk8wnk9pavl7yxyzg2m05gvqwgggwtxas99nugry6xk',
        payment_request
    )
    print(response)

    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True, port=9000, host='0.0.0.0')
