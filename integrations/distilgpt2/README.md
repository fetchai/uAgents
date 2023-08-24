#  uAgent DistilGPT2 integrations Examples

### Step 1: Prerequisites
Before starting, you'll need the following:
* Python (3.10+ is recommended)
* Poetry (a packaging and dependency management tool for Python)

### Step 2: Set up .env file
To run the demo, you need API keys from:
* HuggingFaceAPI Token

##### HuggingFaceAPI Token
* Visit HuggingFace.
* Sign up or log in.
* Goto Profile -> Settings -> Access Tokens.
* Copy the old token or create new token.

Once you have token, create a .env file in the distilgpt2-integrations/src directory.
```bash
export HUGGIN_FACE_ACCESS_TOKEN="{HuggingFaceAPI Token}"
```
To use the environment variables from .env and install the project:
```bash
cd src
source .env
poetry intall
```
### Step 3: Run the main script
To run the project and its agents:
```bash
poetry run python main.py
```

Once you hit enter, a request will be sent to the agent every 10 mins, and you will be able to see your results in the console!
You need to look for the following output in the logs:
```
 Adding agent to Bureau: {agent_address}
```
Copy the {agent_address} value, and replace AI_MODEL_AGENT_ADDRESS with this value distilgpt2_user.py file

This example sends a request to distilgpt2 interface API to auto complete (in this example, Can you please let us know more details about your). You can change text by changing the COMPLETE_THIS variable in distilgpt2_user.py file.
