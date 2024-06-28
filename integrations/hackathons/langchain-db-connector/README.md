# Dynamic / intelligent database connector and query builder

With this agent integration you'll be able to provide your users with an easy way of accessing information in your database and without the hassle of designing a UI or specific interfaces.

A user can (through DeltaV or another agent) ask a natural language question about your dataset and will get a natural language response.

You'll also be able to have multiple databases configured in your agent and the LLM will pick the correct dataset based on the given prompt.

![Architecture](assets/architecture.jpg?raw=true)

How it works:

1. The user provides a prompt through either DeltaV or another agent.
2. An LLM will pick the correct database based on the users' prompt. The key point here is to provide a detailed description of the database, so the LLM can match the prompt to the database easily.
3. Another LLM then analyses the prompt and transforms it into a SQL query, which will then be used to query the database.
4. The result of the SQL query will again be chained through the LLM to generate a natural language response.
5. The Response is sent back to the requesting agent and then forwarded to the user.

## Demo:

For the demo, we used two databases similar to what we have in Agentverse. (The fields and names have been altered)

The first database holds information about agents.
The second database holds information about mailboxes and users of the Agentverse.

The first LLM chain will analyse a question like: `How many agents do you have?` and returns `agentverse` as a result since the first database is for agent data.
This information will be used and forwarded to the second LLM.

The second LLM then creates the query: `SELECT COUNT(*) from agents_by_user`. The query syntax is automatically derived from the configuration (just from the host URI) of the database and uses SQLAlchemy as a wrapper. Finally the function executes the query, feeds the response back into the LLM (enriching the context) and transforms the result into a human readable text.

The agent then receives the human readable text and returns it to the requester.

### Demo Log "Agent to Agent Communication":

In this demo the sigmar agent is calling our main agent to receive information about the agentverse.

```log
poetry run python project/main.py

INFO:     [project]: Manifest published successfully: deltav
INFO:     [project]: Almanac registration is up to date!
INFO:     [project]: Connecting to mailbox server at agentverse.ai
INFO:     [project]: Mailbox access token acquired

--- Num. of databases loaded: 2
--- Agent address: agent1q0wshdnsrghtpff3nacjztpeuyt34va2a8gjx063saecnhx9jgm3v944000

#######################################################
------------------ FIRST QUESTION --------------------
#######################################################

INFO:     [project]: How many agents do you have?

---------------------------------------
Using the following database:  agentverse
---------------------------------------

QUERY:
SELECT COUNT(*) AS total_agents
FROM agents_by_user;

[CORRECT ANSWER TO SIGMAR AGENT]
I currently have 4 agents.


#######################################################
------------------ SECOND QUESTION --------------------
#######################################################

INFO:     [project]: Give me all agent names, please.

---------------------------------------
Using the following database:  agentverse
---------------------------------------

MY QUERY:
SELECT "name" FROM agents_by_user;

[CORRECT ANSWER TO SIGMAR AGENT]
Here are all the agent names: Near Restaurant Booking, Spam Agent Alice, Flight Offer and Booking Execution, I am a blank agent.


#######################################################
------------------ THIRD QUESTION --------------------
#######################################################

INFO:     [project]: How many mailboxes do you have?

---------------------------------------
Using the following database:  mailbox
---------------------------------------

QUERY:
SELECT COUNT(*) AS total_mailboxes
FROM mailboxes;

[CORRECT ANSWER TO SIGMAR AGENT]
I have 1 mailbox.

#######################################################
------------------ FOURTH QUESTION --------------------
#######################################################

INFO:     [project]: How many users do you have?

---------------------------------------
Using the following database:  mailbox
---------------------------------------

QUERY:
SELECT COUNT(*) AS total_users
FROM users;

[CORRECT ANSWER TO SIGMAR AGENT]
I currently have 1 user.

#######################################################
------------------ FIFTH QUESTION --------------------
#######################################################

INFO:     [project]: Which agents have no description?

---------------------------------------
Using the following database:  agentverse
---------------------------------------

QUERY:
SELECT "id", "name"
FROM agents_by_user
WHERE "readme" IS NULL OR "readme" = '';
LIMIT 5;

[CORRECT ANSWER TO SIGMAR AGENT]
I am a blank agent.

```

### Demo "Delta V interaction":

Question: `I want some information about the agentverse. Tell me how much agents are currently running.` (agentverse related)
Response: `There are currently 3 agents running in the Agentverse.`

![DeltaV-Agentverse](assets/dv_agentverse.png?raw=true)

Question: `How many mailboxes do you have?` (mailbox related)
Response: `There is 1 mailbox in the database.`

![DeltaV-Mailbox](assets/dv_mailbox.png?raw=true)

## How to test the demo?

### Run Postgres DB

```sh
# Build and run the agentverse mock db:
docker build -t hackathon-sample .
docker run -p 5499:5432 hackathon-sample

# Build and run the mailbox mock db:
docker build -t hackathon-mailbox-sample -f Dockerfile-mailbox .
docker run -p 5498:5432 hackathon-mailbox-sample
```

The initial connection settings of the databases are configured [here](./project/databases.json_). If you want to use other sql databases, just change the settings there. Make sure that you also provide a detailed description of the purpose of the database, as the LLM will pick the correct databsae based on this description.

## Run main agent

The main agent is responsible to connect to the databases and is accessible via a mailbox also from DeltaV.

Please create a `.env` file with the following contents and populate accordingly:

```env
OPENAI_API_KEY=""
AGENT_SEED=""
MAILBOX_KEY=""
```

Rename the `databases.json_` file to `databases.json` (the repo ignores .json files)

```bash
mv /project/databases.json_ /project/databases.json
```

After that, install the environment with `poetry` and run the agent.

```sh
poetry install
poetry run python project/main.py
```

## Run sigmar agent

The sigmar agent is the local testing agent. It needs to register on the Almanac Smart Contract but does not need to have its own mailbox. It is responsible for calling the endpoint of the main agent and asking questions about the data the main agent is providing.

```sh
poetry run python project/sigmar.py
```

## Caveat

When setting up your database please consider creating a separate user for the LLM to use to restrict potential damaging SQL insertions. Damage can also be mitigated by providing a structurally identical database which is otherwise empty for the LLM to generate the query from.
Always be mindful of what data you give to an LLM.
