# Bureau Interaction Example
Welcome to the Bureau Interaction example! here we cover two examples demonstrating how agents can communicate using messaging systems. The first example focuses on sending custom messages between agents in a bureau, while the second example introduces Fetch.ai wallet messaging

To set up your environment for running the examples, navigate to the example directory and execute the following commands:

```
poetry install --extras wallet
poetry shell
```

## Standard Agent Messaging

### Key Concepts

#### Sending Custom Messages

- **Description**: Agents can send and receive custom messages, allowing for flexible communication between them. This is achieved by defining a model to structure the content and utilizing event handlers to process incoming and outgoing messages.
- **Example Usage**: Alice sends a greeting to Bob every 3 seconds. Bob, upon receiving this message, sends a greeting back to Alice. This interaction is facilitated by the `send_message` and `message_handler` functions defined in both agents.

#### Bureau for Agent Management

- **Description**: A `Bureau` is used to manage and run multiple agents concurrently. It enables the agents to operate within the same environment and communicate with each other as defined by their message handlers.
- **Example Usage**: Both Alice and Bob agents are added to a bureau and run, facilitating the exchange of messages between them as per the defined intervals and handlers.

## Fetch.ai Wallet Messaging

### Wallet Messaging

- **Description**: Wallet messaging is a feature of Fetch.ai that allows agents to send messages via their Fetch wallets. This method offers an additional layer of security and integration, leveraging the blockchain infrastructure for communication.
- **Example Usage**: Alice and Bob, with `enable_wallet_messaging` set to `True`, exchange greetings using their Fetch wallets. This is managed through the `send_wallet_message` and `on_wallet_message` event handlers, showcasing how agents can communicate securely using their blockchain identities.

### Running the Examples

To observe how agents interact through standard messaging, run:

```
python messaging.py
```
Or run:

```
python wallet-messaging.py
```

for wallet messaging interaction

## Experimentation

These examples serve as a foundation for exploring the capabilities of agent-based messaging. Consider experimenting with different model structures or message contents, altering the timing of message exchanges, or incorporating additional agents to simulate complex interactions and communication networks.
