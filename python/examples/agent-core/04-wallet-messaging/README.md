# Wallet Messaging Example

Welcome to the Wallet Messaging example! The Wallet Alert Agent is a simple example designed to demonstrate how you can program agents to send automated alerts directly to a Fetch Wallet. This particular example is configured to send a pre-defined message about Bitcoin's price status every 5 seconds. This template can be expanded to include real-time data queries from financial APIs to send timely and relevant financial alerts. Before you begin, make sure to navigate to the example directory and set up your environment with the following commands:

```
poetry install --extras wallet
poetry shell
```

Also make sure to have an active Fetch Wallet. You can install the Fetch Wallet extension from the Chrome Web Store: [Fetch Wallet Extension](https://chromewebstore.google.com/detail/fetch-wallet/ellkdbaphhldpeajbepobaecooaoafpg?hl=en-GB&pli=1). Make sure to set it to `Dorado`testnet and copy your `Wallet Address`

## Key Concepts

### Sending Wallet Messages

- **Description**: This example illustrates how agents can send wallet messages to communicate directly with wallets on the Fetch.ai network. It highlights the ability of agents to not only perform transactions but also send alerts or notifications directly to user wallets, enhancing interaction and user engagement in decentralized applications.
- **Example Usage**: In the given scenario, an agent named "alert agent" periodically sends a message "Bitcoin price is too low!" to a specified Fetch Wallet address. The message is sent using the `ctx.send_wallet_message` method, which leverages the agent's capabilities to interact directly with Fetch.ai wallets. This method requires the wallet address and the message content as parameters.

## Running the Agent

- Copy and paste your `Wallet Address` into agent.py

- Run the command:
  ```
  python agent.py 
  ```
- Upon starting, the agent will send a message alert to your `Fetch Wallet` every 5 seconds. You can observe this in your wallet Agents chat.

## Experimentation

Building on the initial setup, the Wallet Alert Agent can be enhanced to deliver more complex and actionable alerts by querying real-time data from financial APIs. By integrating with these APIs, you can program the agent to analyze cryptocurrency market trends or specific stock movements, enabling it to send personalized alerts when certain thresholds are met. This approach not only makes the alerts more relevant but also allows users to respond swiftly to market changes directly from their Fetch Wallet.