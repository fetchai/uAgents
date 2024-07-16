#  uAgent Holiday integrations Examples
### Step 1: Prerequisites
Before starting, you'll need the following:
* Python (3.8+ is recommended)
* Poetry (a packaging and dependency management tool for Python)

### Step 2: Set up .env file
To run the demo, you need API keys from:
* RapidAPI
* OpenAI
* SerpAPI

##### RapidAPI Key
* Visit RapidAPI.
* Sign up or log in.
* Search for the Skyscanner API and subscribe.
* Once subscribed, copy your X-RapidAPI-Key

##### OpenAI API Key
* Visit OpenAI.
* Sign up or log in.
* Navigate to the API section to obtain your API key.

Note that if you’ve run out of OpenAI credits, you will not be able to get results for this example.

##### SerpAPI Key

* Visit SerpAPI.
* Sign up or log in.
* Your API key will be available on the dashboard.

Once you have all three keys, create a .env file in the holiday-integrations/src directory.
```bash
export RAPIDAPI_API_KEY="{GET THE API KEY}"
export OPENAI_API_KEY="{GET THE API KEY}"
export SERPAPI_API_KEY="{GET THE API KEY}"
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
You need to look for the following output in the logs:
```
Adding top destinations agent to Bureau: {top_dest_address}
```
Copy the {top_dest_address} value and paste it somewhere safe. You will need it in the next step.
### Step 4: Set up the client script
Now that we have set up the integrations, let’s run a client script that will showcase the ‘top destinations’. To do this, create a new Python file in the src folder called top_dest_client.py, and paste the following:
```python
from messages import TopDestinations, UAgentResponse
from uagents import Agent, Context
from uagents.setup import fund_agent_if_low
import os
​
TOP_DESTINATIONS_CLIENT_SEED = os.getenv("TOP_DESTINATIONS_CLIENT_SEED", "top_destinations_client really secret phrase :)")
​
top_dest_client = Agent(
    name="top_destinations_client",
    port=8008,
    seed=TOP_DESTINATIONS_CLIENT_SEED,
    endpoint=["http://127.0.0.1:8008/submit"],
)
fund_agent_if_low(top_dest_client.wallet.address())
​
top_dest_request = TopDestinations(preferences="new york")
​
@top_dest_client.on_interval(period=10.0)
async def send_message(ctx: Context):
    await ctx.send("{top_dest_address}", top_dest_request)
​
@top_dest_client.on_message(model=UAgentResponse)
async def message_handler(ctx: Context, _: str, msg: UAgentResponse):
    ctx.logger.info(f"Received top destination options from: {msg.options}")
​
if __name__ == "__main__":
    top_dest_client.run()
```
Remember to replace the address in ctx.send with the value you received in the previous step. 

This code sends a request to get the top destinations (in this example, from New York). To do this, it sends a request to the ‘top destinations agent’ every 10 seconds and displays the options in the console.
### Step 5: Run the client script
Open a new terminal (let the previous one be as is), and navigate to the src folder to run the client.
```bash
cd src
poetry run python top_dest_client.py
```
Once you hit enter, a request will be sent to the top destinations agent every 10 seconds, and you will be able to see your results in the console!