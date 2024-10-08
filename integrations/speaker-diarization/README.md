# Speaker Diarization

This project uses the `pyannote/speaker-diarization-3.1` model from Hugging Face and Fetch.ai agent to perform speaker diarization, which is the process of partitioning an audio stream into homogeneous segments according to the speaker identity. Agent helps in identifying "who spoke when" in multi-speaker audio recordings, making it highly useful for applications such as meeting transcription, call center analytics, and media indexing.

## Features

- **Accurate Speaker Segmentation:** The Fetch.ai agent effectively segments audio streams, distinguishing between different speakers with high accuracy.
- **Easy Integration:** Seamlessly integrates with existing workflows using the Fetch.ai agent, making it accessible for developers and researchers.
- **Customizable:** Supports fine-tuning for specific use cases and environments, enhancing its adaptability to different scenarios.

## Installation

To get started with **Website Validation**, follow these steps:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/fetchai/uAgents.git
   cd speaker-diarization

2. **Set up .env file**:
   To run the demo, you need to add these API keys in .env file:
   ```bash
   AGENT_MAILBOX_KEY = "YOUR_MAILBOX_KEY"
   HUGGING_FACE_TOKEN="YOUR_HUGGING_FACE_TOKEN"
3. **Open a shell**:
   ```bash
   poetry shell

4. **Install dependencies using Poetry**:
   ```bash
   poetry install --no-root
5. **Run the agent**:
   ```bash
   poetry run python agent.py