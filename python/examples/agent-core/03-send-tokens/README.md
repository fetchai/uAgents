
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

To see how agents interact and perform token transactions, run the following command in your terminal:

```
python main.py
```


This command starts both Alice and Bob agents within a `Bureau`, allowing them to communicate and execute token transactions as defined in the example. Observing the logs will show you the payment request from Alice, the transaction initiation by Bob, and the successful transaction confirmation.

## Experimentation

This example sets a foundation for exploring more complex economic interactions between agents. Consider modifying the amount of tokens requested, experimenting with different intervals for payment requests, or introducing more agents into the system to simulate a more dynamic economic environment.

