# Stripe Payment Solution

Ever had an idea to use Stripe as a payment partner for your business, That's why I've harnessed the power of Fetch.AI
Agent and Stripe payment ecosystem to develop a **Stripe Payment Solution** integration, designed to transform all your
payment requirements, into a simple and convenient manner.

## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [How It Works](#how-it-works)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Introduction

**Stripe Payment Solution** is an innovative tool that leverages Fetch.AI's Agent technology to help anyone with a requirement to accept payment over the Internet. This System integrates Stripe as the Payment regulator for all the payment related services.

## Features

- Real Time Payment Link Generator.
- Real Time Payment Confirmation mechanism.
- Custom Multi Cart Item Payments.
- Simple UI.
- Automated Invoicing & Receipts
- One-Click Payments for Customers

## Working Diagram

![Working Diagram](./images/payment_system_overview.png "Working Diagram")

This Agent can work like a template and can be used in different organizations with their API keys from stripe A/c.


## Demo Video 

https://github.com/user-attachments/assets/3de86092-e2aa-43f1-b59d-73b725698600


## Detail Document

[Detail Document](https://github.com/user-attachments/files/16706323/Stripe_Agent_Integration.pdf)


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
   
2. **Open a shell**:
   ```bash
   poetry shell

3. **Install dependencies using Poetry**:
   ```bash
   poetry install --no-root
   
4. Get API Key and Endpoint Secret from [Stripe.com](https://dashboard.stripe.com/login).

5. **Run the webhook**:
   ```bash
   cd src/stripe_webhook
   poetry run python webhook.py
   
6. Using Ngrok or any Tunneling Software, Create secure https endpoint and set it up as a webhook in Stripe dashboard under the webhook section.

7. **Set up .env file**:
   To run the demo, you need to add these API keys and URLs in .env file:
   ```bash
   STRIPE_API_KEY='YOUR_STRIPE_KEY'
   STRIPE_ENDPOINT_SECRET='YOUR_STRIPE_ENDPOINT_SECRET'
   STRIPE_WEBHOOK_URL='YOUR_STRIPE_WEBHOOK_URL'

8. **Run the agent**:
   ```bash
   cd src/stripe_agent
   poetry run python agent.py

9. **Run the demo_server**:
   ```bash
   cd src/stripe_demo_server
   poetry run python app.py
