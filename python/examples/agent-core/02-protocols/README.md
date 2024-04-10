# Protocols Example

Welcome to the Protocols example! This guide delves into the concept of protocols within agents, demonstrating how to define and incorporate them for inter-agent communication. Before proceeding, ensure you navigate to the example directory then run the following commands to set up your environment with the necessary dependencies:

```
poetry install
poetry shell
```


## Key Concepts

### Protocols

- **Description**: A protocol in this context defines a set of rules or procedures for data exchange between agents. By defining a protocol, you establish a structured way for agents to communicate, ensuring they understand each other's messages.
- **Example Usage**: In the example, the `square_protocol` is defined to handle messages related to squaring a number. It specifies the message format for requests and responses, allowing agents to communicate this specific type of information reliably.

### Incorporating Protocols into Agents

- **Description**: Once a protocol is defined, it can be incorporated into an agent. This makes the agent aware of the protocol and enables it to send and receive messages that conform to the protocol's definitions.
- **Example Usage**: Both Alice and Bob agents include the `square_protocol`, which means they can participate in exchanges defined by this protocol, such as sending a number to square and receiving the squared result.

### Agent Seeds

- **Description**: A seed can be used to generate a unique identity for an agent. This is crucial in scenarios where agents need to be distinguishable from each other, for example, in a network of agents communicating over a protocol.
- **Example Usage**: Alice and Bob are given unique seeds (`ALICE_SEED` and `BOB_SEED`), ensuring their identities are distinct in the system.

### Running Multiple Agents with Bureau

- **Description**: The `Bureau` is a container for running multiple agents simultaneously. It facilitates the management and execution of several agents, allowing them to operate concurrently within the same environment.
- **Example Usage**: A bureau is created and both Alice and Bob agents are added to it. Running the bureau starts both agents, allowing them to communicate with each other using the defined protocol.

## Starting the Agents

To run the agents and observe the protocol in action, set your agents seeds and execute:

```
python main.py
```


This command starts the bureau, which in turn runs both Alice and Bob agents. You will see logs indicating that Alice is asking Bob what 7 squared is, and Bob responding with the answer. 

## Experimentation

Now that you understand how the protocol works and how it's incorporated into agents, try reversing the roles. Instead of Alice asking Bob to square a number, modify the code to have Bob ask Alice. This change will help you grasp the flexibility of protocols

Protocols are a powerful concept in agent-based systems, enabling structured and reliable communication. By defining a protocol and incorporating it into agents, you create a foundation for complex interactions.
