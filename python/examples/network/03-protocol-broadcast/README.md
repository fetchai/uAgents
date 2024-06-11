# Protocol Broadcast

Welcome to the Protocol Broadcast example! This guide focuses on a specific example that demonstrates how to broadcast messages to agents sharing the same protocol within a distributed agent system. This capability is pivotal for scenarios where a message needs to be sent to multiple agents simultaneously, such as updates, or requests for information.

To prepare for running the example, ensure you're in the proper directory and have configured your environment with the necessary dependencies:

```
poetry install
poetry shell
```

## Broadcasting Messages with Protocols

### Defining a Shared Protocol

- **Description**: A shared protocol specifies a common communication format and procedure that participating agents agree upon. It ensures that messages are understood and processed uniformly across different agents.
- **Example Usage**: The `hello_protocol` is defined with a simple `Request` and `Response` model. Agents using this protocol can send a greeting request and expect a greeting response.

### Including Protocols in Agents

- **Description**: For an agent to participate in protocol-based communication, it must include the protocol within its definition. This inclusion enables the agent to understand and respond to messages formatted according to the protocol.
- **Example Usage**: Alice and Bob include the `hello_protocol`, making them capable of receiving and responding to broadcast requests sent using this protocol.

### Broadcasting Messages

- **Description**: Broadcasting refers to sending a message to all agents that are capable of understanding it, based on the shared protocol. This is done without specifying individual recipients, allowing for efficient group communication.
- **Example Usage**: Charles periodically broadcasts a greeting using `hello_protocol`. All agents that have included this protocol (Alice and Bob) will receive and respond to the greeting.

## Running the Example

To observe protocol-based broadcasting in action, run:

```
python main.py
```


This command starts the bureau, initializing all three agents. Charles periodically broadcasts a greeting to Alice and Bob, who respond to each greeting, showcasing the broadcasting functionality.

## Key Points

- Ensure that all agents meant to communicate share the same protocol by including it in their definitions.
- Use broadcasting for scenarios where a message needs to be sent to multiple agents without specifying each recipient.

By following this example, you can implement efficient and scalable communication patterns in distributed agent systems, leveraging the power of protocol broadcasting.
