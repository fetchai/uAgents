# Remote Agents Example

Welcome to the Remote Agents example! This will guide you through setting up and running remote agents that can communicate over the internet using `ngrok`. `Ngrok` is a tool that exposes local servers behind NATs and firewalls to the public internet over secure tunnels. This example demonstrates how to use `ngrok` to expose an agent, enabling it to interact with other agents regardless of their location.

To get started, ensure you are in the project's directory and have configured your environment correctly:

```
poetry install --extras remote-agents
poetry shell
```


## Using `ngrok` to Expose Agents

### Obtaining an `ngrok` Auth Token

- **Description**: To use `ngrok`, you first need to sign up for an account on the [ngrok website](https://ngrok.com/). Once registered, you can find your auth token on the dashboard. This token allows you to authenticate with `ngrok` and create secure tunnels.
- **Example Usage**: After obtaining your auth token, paste it into the script where indicated: `ngrok.set_auth_token("put_your_NGROK_AUTH_TOKEN_here")`.

### Configuring `ngrok` in the Script

- **Description**: `ngrok` is integrated into the agent script to expose the agent's local server to the internet. This setup involves specifying the local port the agent server is running on and configuring `ngrok` to tunnel traffic to this port.
- **Example Usage**: The example configures `ngrok` to expose Alice's agent running on `PORT = 8000`. The public URL provided by `ngrok` is then used as the endpoint in the agent's configuration.

### Running Remote Agents

- **Process**:
  1. **Start the Exposed Agent**: Run the script for Alice first. This starts the agent and uses `ngrok` to expose it. Note the agent's address and the `ngrok` public URL printed in the console.
  2. **Configure and Run the Remote Agent**: In Bob's script, replace `ALICE_ADDRESS` with Alice's agent address. Running Bob's script initiates communication with Alice via her `ngrok`-exposed endpoint.

## Communication Flow

- Alice's agent, once exposed by `ngrok`, can receive messages from any agent that knows its public URL.
- Bob sends a message to Alice's public URL. Alice processes this message and can respond if the logic is implemented for a response.

## Key Points

- `ngrok` enables local agents to be accessible from the internet, facilitating remote interactions between agents.
- It is essential to secure your `ngrok` tunnels with auth tokens and to manage access to your public URLs carefully.
- This example highlights the basics of setting up remote agent communication, providing a foundation for more complex, distributed agent-based applications.

The Remote Agents example demonstrates a practical approach to enabling agent interactions over the internet, breaking down barriers to communication in distributed systems.
