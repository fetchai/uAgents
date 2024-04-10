# Local Network Interactions

Welcome to the Local Network Interactions example! this document details how to set up and run two agents, Alice and Bob, for local network interactions. This example highlights the configuration of ports and endpoints to enable communication between agents running on the same machine but simulating a distributed environment.

To set up your environment for running the examples, navigate to the example directory and execute the following commands:

```
poetry install
poetry shell
```


## Configuration for Local Network Interaction

### Ports and Endpoints

- **Description**: For agents to interact over a local network, each agent must be assigned a unique port and endpoint. The port indicates where the agent is listening for messages, and the endpoint provides a URL for sending messages to the agent.
- **Example Usage**: 
  - Bob is configured to listen on port 8001 and has an endpoint `http://127.0.0.1:8001/submit`. 
  - Alice is set up to use port 8000, with her endpoint being `http://127.0.0.1:8000/submit`.

### Running Bob and Alice Agents

1. **Start Bob**: Run Bob's script first. This initializes Bob on his configured port and prints his address to the terminal.

```
python bob.py
```

Note Bob's address as it is printed in the terminal. This address is needed for Alice to send messages to Bob.

2. **Configure Alice with Bob's Address**: Before running Alice's script, replace `BOB_ADDRESS` in Alice's code with the address you noted from Bob's terminal output. This step is crucial for enabling Alice to correctly send messages to Bob.

3. **Start Alice**: Once Bob's address is configured in Alice's script, run Alice's script. This starts Alice on her configured port, allowing her to send messages to Bob and receive responses.

```
python alice.py
```


## Communication Flow

- Upon running both scripts with the correct configurations, Alice sends a message to Bob every 2 seconds.
- Bob, upon receiving a message from Alice, logs the message and responds with a greeting.
- Alice then receives Bob's response and logs it, demonstrating successful local network interaction between the two agents.

## Key Points

- Ensure that each agent has a unique port and endpoint configured for local network interactions.
- Start the receiving agent (Bob) first to ensure his address is available for configuring the sending agent (Alice).
- Update the sender's (Alice's) code with the receiver's (Bob's) address before starting the sender agent.

This example demonstrates a foundational setup for local network interactions between agents, enabling a wide range of distributed agent-based applications.




