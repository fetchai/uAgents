# Elderly Assistant Agent

The Elderly Assistant agent enhances the safety of vulnerable individuals (e.g. with reduced mobility), utilising Natural Language Processing (NLP) to scrutinise incoming telephone calls and analysing audio captured by an loT device (e.g. Smart doorbell), providing an evaluation of potential security risks posed by callers on the phone / visitors to the property - essentially whether to reject the call or allow the person in to the house, with the assumption that it may be difficult to reach the phone / door. 

Langchain is set up to ingest multi-format information (documents, calendar, emails etc.) about the state of the home (uploaded via a .zip file in Delta-V) to inform the decisions the AI makes.
## Features

- **Call Analysis**: Evaluates incoming calls to determine their legitimacy.
- **Visitor Assessment**: Analyzes audio from IoT devices to judge the intent of visitors.
- **Contextual Decision Making**: Utilizes documents, calendars, and emails to inform decision-making, enhancing the system's ability to accurately assess safety risks.

## Installation

To set up the Elderly Assistant agent, follow these steps:

1. **Clone the Repository**

   Clone the uAgents repository to your local machine:

   ```bash
   git clone https://github.com/fetchai/uAgents.git
   cd fetch-hackathon
   ```

2. **Navigate to this directory fetch-hackathon/integrations/nlp-elderly-assistant**
   ```bash
   cd elderly-assistant
   ```


3. **Install Dependencies**

   Ensure Poetry is installed on your system. If not, install it following the [official instructions](https://python-poetry.org/docs/#installation). Then, install the project dependencies:

   ```bash
   poetry install
   ```

4. **Configure Environment Variables**

   Create a `.env` file in the root directory of the project and specify the following environment variables:

   - `OPENAI_API_KEY`: Your OpenAI API key for accessing GPT models.
   - `SEED_PHRASE`: A secure [seed phrase](https://fetch.ai/docs/guides/agent-courses/introductory-course#agent-interactions-and-interval-tasks) for your agent's identity.
   - `AGENT_MAILBOX_KEY`: Your agent's mailbox key, obtained after registering your agent in [Agentverse](https://agentverse.ai).

   Example `.env`:

   ```plaintext
   OPENAI_API_KEY=<your_openai_api_key>
   SEED_PHRASE=<your_secure_seed_phrase>
   AGENT_MAILBOX_KEY=<your_agent_mailbox_key>
   ```

## Running the Agent

To activate the Elderly Assistant agent:

```bash
poetry run python agent.py
```

This command initializes the agent, setting up the necessary protocols for call and visitor analysis, and begins monitoring for incoming requests.

## Project Structure

- `main.py`: The entry point of the application, orchestrating the setup and execution of the agent.
- `analyser.py`: Contains the logic for analyzing and assessing the safety based on audio and contextual data (documents, emails, schedule etc.).
- `summariser.py`: Handles the summarization of audio data for further analysis.
- `utils.py`: Provides utility functions, including data parsing and helper methods.
