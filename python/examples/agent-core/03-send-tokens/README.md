
# Send Tokens Example

Welcome to the Send Tokens example! This guide illustrates how agents can trade tokens on the Fetch.ai blockchain, creating economic interactions within an agent-based system. This example also emphasizes the importance of using seeds for agent identity, as each agent possesses a Fetch wallet tied to its unique identity. Before you begin, make sure to navigate to the example directory and set up your environment with the following commands:

```
poetry install
poetry shell
```

## Key Concepts

### Trading Tokens between Agents

- **Description**: This example demonstrates how agents can send tokens using the Fetch.ai blockchain, showcasing the potential for economic interactions in agent systems. Agents use models to define the structure of payment requests and transaction information, facilitating clear communication about token transfers.
- **Example Usage**: Alice sends a `PaymentRequest` to Bob, specifying the wallet address, amount, and denomination of tokens she requests. Bob, upon receiving this request, sends the specified amount of tokens to Alice's address and informs her of the transaction's hash.

### Agent Uniqueness with Seeds

- **Description**: Each agent is initialized with a unique seed phrase, which is critical for securing and distinguishing their respective Fetch wallets. This uniqueness is essential for economic transactions to ensure that tokens are sent to and from the correct entities.
- **Example Usage**: Alice and Bob are initialized with their respective `ALICE_SEED` and `BOB_SEED`, linking them to distinct wallets on the Fetch.ai blockchain.

### Using `ctx.ledger` for Token Transactions

- **Description**: The context (`ctx`) provides access to the `ledger` object, which agents use to interact with the blockchain. This includes functionalities like sending tokens, checking transaction statuses, and accessing wallet addresses.
- **Example Usage**: Bob uses `ctx.ledger.send_tokens` to transfer tokens to Alice's wallet in response to her payment request. Alice then uses `wait_for_tx_to_complete` with `ctx.ledger` to check the status of the transaction using the transaction hash provided by Bob.

## Running the Agents

To observe the interaction between the agents, follow these steps:

### 1. Start Agent Bob
- Navigate to the directory named `bob`.
- Run the command:
  ```
  python agent.py 
  ```
- Upon starting, agent bob can print its address using `bob.address`. Make sure to copy this address.

### 2. Start Agent Alice
- Open the file alice/agent.py.
- Paste the copied address of agent bob into the specified location in the file to set up the communication link between Alice and Bob.
- Inside alice directory, run the command:
  ```
  python agent.py
  ```
Following these instructions will initiate agent alice, which will then connect to agent bob using the provided address. You will see them to communicate and execute token transactions as defined in the example. Observing the logs will show you the payment request from Alice, the transaction initiation by Bob, and the successful transaction confirmation.

## Experimentation

This example sets a foundation for exploring more economic interactions between agents. Consider modifying the amount of tokens requested, experimenting with different intervals for payment requests, or introducing more agents into the system to simulate a more dynamic economic environment.

