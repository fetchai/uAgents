# uAgents: AI Agent Framework
[![Official Website](https://img.shields.io/badge/Official%20Website-fetch.ai-blue?style=flat&logo=world&logoColor=white)](https://fetch.ai) [![Unit Tests](https://img.shields.io/github/actions/workflow/status/Fetchai/uAgents/ci.yml?label=unit%20tests)](https://github.com/Fetchai/uAgents/actions/workflows/ci.yml) [![GitHub Repo stars](https://img.shields.io/github/stars/Fetchai/uAgents?style=social)](https://github.com/Fetchai/uAgents/stargazers) [![Twitter Follow](https://img.shields.io/twitter/follow/fetch_ai?style=social)](https://twitter.com/fetch_ai)

uAgents is a library developed by Fetch.ai that allows for creating autonomous AI agents in Python. With simple and expressive decorators, you can have an agent that performs various tasks on a schedule or takes action on various events.

## 🚀 Features

- 🤖 **Easy creation and management**: Create any type of agent you can think of and put into code.
- 🔗 **Connected**: On startup, each agent automatically joins the fast growing network of uAgents by registering on the Almanac, a smart contract deployed on the Fetch.ai blockchain.
- 🔒 **Secure**: uAgent messages and wallets are cryptographically secured, so their identities and assets are protected.

## ⚡ Quickstart

### Installation
Get started with uAgents by installing it for Python 3.8, 3.9, 3.10, or 3.11:

    cd python
    poetry install
    poetry shell

### Running a Demo

#### Creating an Agent 
Build your first uAgent using the following script:

    from uagents import Agent, Context 
    alice = Agent(name="alice", seed="alice recovery phrase")

Include a seed parameter when creating an agent to set fixed addresses, or leave it out to generate random addresses each time.

#### Giving it a task
Give it a simple task, such as greeting:

    @alice.on_interval(period=2.0)
    async def say_hello(ctx: Context):
        ctx.logger.info(f'hello, my name is {ctx.name}')
    
    if __name__ == "__main__":
        alice.run()

#### Running the Agent 
So far, your code should look like this:

    from uagents import Agent, Context
    
    alice = Agent(name="alice", seed="alice recovery phrase")
    
    @alice.on_interval(period=2.0)
    async def say_hello(ctx: Context):
        ctx.logger.info(f'hello, my name is {ctx.name}')
    
    if __name__ == "__main__":
        alice.run()

Run it using:

    python agent.py

You should see the results in your terminal.

## 📖 Documentation

Please see the [official documentation](https://docs.fetch.ai/) for full setup instructions and advanced features.

* [👋 Introduction](https://docs.fetch.ai/uAgents/)
* [💻 Installation](https://docs.fetch.ai/uAgents/installation/)
* [🏃 Running an agent](https://docs.fetch.ai/uAgents/run-agent/)
* Tutorials
  * [🤖 Agent Interactions](https://docs.fetch.ai/uAgents/simple-interaction/)
  * [🛣️ Remote Agents](https://docs.fetch.ai/uAgents/remote-agents/)
  * [🍽️ Restaurant Booking Demo](https://docs.fetch.ai/uAgents/booking-demo/)
* Key Concepts:
  * [📍Addresses](https://docs.fetch.ai/uAgents/addresses/)
  * [💾 Storage](https://docs.fetch.ai/uAgents/storage/)
  * [📝 Interval Tasks](https://docs.fetch.ai/uAgents/interval-tasks/)
  * [🌐 Agent Protocols](https://docs.fetch.ai/uAgents/agent-protocols/)
  * [⚙️ Almanac Contracts](https://docs.fetch.ai/uAgents/almanac-overview/)
  * [🔁 Exchange Protocol](https://docs.fetch.ai/uAgents/protocol/)

## 🌱 Examples

The [`examples`](https://github.com/fetchai/uAgents/tree/main/python/examples) folder contains several examples of how to create and run various types of agents.

## Python Library

Go to the [`python`](https://github.com/fetchai/uAgents/tree/main/python) folder for details on the Python uAgents library.

## ✨ Contributing

All contributions are welcome! Remember, contribution includes not only code, but any help with docs or issues raised by other developers. See our [contribution guidelines](https://github.com/fetchai/uAgents/blob/main/CONTRIBUTING.md) for more details.

### 📄 Development Guidelines

Read our [development guidelines](https://github.com/fetchai/uAgents/blob/main/DEVELOPING.md) to learn some useful tips related to development.

### ❓ Issues, Questions, and Discussions

We use [GitHub Issues](https://github.com/fetchai/uAgents/issues) for tracking requests and bugs, and [GitHub Discussions](https://github.com/fetchai/uAgents/discussions) for general questions and discussion.

## 🛡 Disclaimer

This project, μAgent, is provided "as-is" without any warranty, express or implied. By using this software, you agree to assume all risks associated with its use, including but not limited to unexpected behavior, data loss, or any other issues that may arise. The developers and contributors of this project do not accept any responsibility or liability for any losses, damages, or other consequences that may occur as a result of using this

## License

The uAgents project is licensed under [Apache License 2.0](https://github.com/fetchai/uAgents/blob/main/LICENSE).
