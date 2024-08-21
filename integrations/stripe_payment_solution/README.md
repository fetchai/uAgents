# Stripe Payment Solution

Have you ever considered using Stripe as a payment partner for your business? 
That's exactly what we've done by leveraging the power of Fetch.AI Agents and Stripe's cutting-edge payment technology. 
We’ve developed an integrated Stripe payment solution that simplifies and streamlines all your payment processes.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Introduction

Imagine a world where your payment requirements are effortlessly handled,
giving you more time to focus on what truly matters—growing your business. 
Our solution ensures
that transactions are not only fast and secure but also incredibly convenient for both you and your customers.

By integrating Fetch.AI's intelligent agent technology with Stripe’s robust payment infrastructure, we offer a seamless experience that adapts to your unique business needs. 
Whether you're handling subscriptions, one-time payments, or complex billing scenarios, our solution is designed to evolve with your business.

Take the next step in transforming your payment processes.
With our **Stripe Payment Solution**, you can expect reduced friction, 
enhanced security, and an overall superior payment experience.
Let’s simplify your payments, so you can focus on innovation and growth.

## Features

- Real Time Payment Link Generator.
- Real Time Payment Confirmation mechanism.
- Custom Multi Cart Item Payments.
- Simple UI.
- Automated Invoicing & Receipts
- One-Click Payments for Customers

## How It Works

Stripe Payment Solution few items to choose from, for testing purposes. 

1. Choose one of the items to initiate the payment.
2. Then a payment link from Stripe is generated for payment, Click it.
3. Fill it the Payment Details and click **Place Order**, wait for Payment Confirmation.

## Installation

To get started with **Stripe Payment Solution**, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/fetchai/uAgents.git
   cd stripe-agent
   
2. Get API Key and Endpoint Secret from [Stripe.com](https://dashboard.stripe.com/login).

3. **Set up .env file**:
   To run the demo, you need to add these API keys in .env file:
   ```bash
   STRIPE_API_KEY='YOUR_STRIPE_KEY'
   STRIPE_ENDPOINT_SECRET='YOUR_STRIPE_ENDPOINT_SECRET'
   STRIPE_WEBHOOK_URL='YOUR_STRIPE_WEBHOOK_URL'

4. **Open a shell**:
   ```bash
   poetry shell

5. **Install dependencies using Poetry**:
   ```bash
   poetry install --no-root

6. **Run the agent**:
   ```bash
   cd src/stripe_agent
   poetry run python agent.py

7. **Run the demo_server**:
   ```bash
   cd src/stripe_demo_server
   poetry run python app.py

8. **Run the webhook**:
   ```bash
   cd src/stripe_webhook
   poetry run python webhook.py