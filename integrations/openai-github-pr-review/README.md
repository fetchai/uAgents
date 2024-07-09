# GitHub PR Review AI Assistant 🤖

## Overview

The GitHub PR Review AI Assistant is a AI agent designed to streamline the process of reviewing pull requests on GitHub.
Develop using fetch.ai agents and integrated with langchain and codedog, this AI Agent utilizes OpenAI's powerful LLM models to provide in-depth, automated reviews that improve code quality and collaboration efficiency.

## Features

- **Automated PR Reviews**: Quickly receive feedback on pull requests to improve code quality. 🚀
- **AI-Powered Insights**: Leverage GPT-3.5 and GPT-4 models for detailed code analysis. 🔍
- **Public Repository Support**: Currently supports reviewing pull requests on public GitHub repositories. 📖

## Installation

1. **Clone the Repository**: Start by cloning this repository to get the agent code, and then navigate to the project directory.

    ```bash
    git clone https://github.com/fetchai/uAgents.git
    cd github-pr-review-ai-assistant
    ```

2. **Install Required Libraries using Poetry**: This project uses Poetry for dependency management. If you haven't installed Poetry yet, follow the instructions on the [Poetry website](https://python-poetry.org/docs/#installation). Once Poetry is installed, set up the project dependencies by running:

    ```bash
    poetry install
    ```

## Agent Setup

Follow these steps to set up and run the GitHub PR Review AI Assistant:

1. **Running the Agent**: With dependencies installed, you can start the agent by running:

    ```bash
    poetry run python agent.py
    ```

    Upon launching, the agent's address will be displayed in the console. Initial errors can be ignored; just ensure to copy the address for configuring your agent in Agentverse.

2. **Deployment on Agentverse**:

    - **Create a Mailbox**: Log in to Agentverse and navigate to the Mailroom to create a mailbox for your agent, using the previously noted address.
    - **Copy Mailbox Key**: Once created, copy the mailbox key for the next step.

3. **Configure the Agent**: Edit the agent file, replacing placeholder values with your actual data:

    - `SEED_PHRASE`: Your secret seed phrase for agent creation.
    - `AGENT_MAILBOX_KEY`: The mailbox key obtained from Agentverse.
    - `OPENAI_API_KEY`: Your OpenAI API key.

4. **Re-run the Agent**: Restart the agent with the updated configuration:

    ```bash
    poetry run python agent.py
    ```

    This will initialize the agent, allowing it to receive and process messages.

## Interaction via DeltaV

After configuring your agent locally, proceed to create a service in Agentverse for user interaction.

### Create a Service for Your Agent

1. **Service Group Creation**
    - Go to "Services" in Agentverse.
    - Switch the tab to 'Service Groups' on the top, and click on 'New Service Group'
    - Create a new private service group (e.g., "GitHub PR Review AI Assistant") and save it.

2. **Add New Service**

   - Navigate back to the other tab ('Services').
   - Click on '+ New Service' and fill in the information.
   - Give it a very descriptive objective - this field is extremely helpful for Agent discovery on DeltaV.
   - For 'Service group', select the one you created in the previous step.
   - For 'Agent', select the mailbox agent you created before.
   - Add a field for "pull_request_url" that users will request to help in PR review.

Now you can head over to [DeltaV](https://deltav.agentverse.ai/) to start interacting with it.

## Access on DeltaV

When you are testing, remember to select 'Advanced Options', and click on the service group you created for this project.

1. **Initiate a Request**:
   - Use the sample prompt: "I need help in reviewing a Github PR."

2. **Provide Required Information**:
   - **PR URL**: When prompted, enter the whole PR URL. At this point only **\*public\*** GitHub repositories are supported.

The GitHub PR Review AI Assistant will process your request and return a comprehensive review of the specified pull request, offering valuable insights to improve your code quality.

## Libraries Used

This service incorporates several key libraries to provide its functionality:

- **fetch-uagents**
- **langchain**
- **codedog**
- **GPT-3.5 and GPT-4 Models**

## Future Scope

We're constantly looking to expand the capabilities of the GitHub PR Review AI Assistant. Future enhancements include:

- **Private Repository Reviews**: Integrate functionality to review pull requests on private repositories by securely using GitHub tokens. 🔒
- **GitLab Support**: Extend the service to support PR reviews on GitLab, catering to a wider audience. 🌐
- **Advanced AI Models**: Incorporate newer and more powerful LLM models as they become available, to improve the depth and accuracy of code reviews. 🧠

## Feedback and Contributions

We welcome feedback and contributions from the community! If you have suggestions, issues, or would like to contribute, please feel free to reach out or submit a pull request. 🤝
