# Agent based Negotiation

This example is two locally running agents Alice and Bob.

Periodically, Alice will start a negotiation with Bob. Bob will respond with a counter offer. This will continue until a deal is reached or the negotiation times out.

This serves as an simple example of how to use the `Agent` class to create a simple negotiation.

## Running the agents

Install dependencies

```bash
poetry install
```

Enter the poetry shell

```bash
poetry shell
```

Start the agents

```bash
python3 main.py
```