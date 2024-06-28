from agents.tfl_agent import london_transport
from agents.user import user
from uagents import Bureau

#adding all users to bureau and running it
if __name__ == "__main__":
    bureau = Bureau(endpoint="http://127.0.0.1:8000/submit", port=8000)
    bureau.add(london_transport)
    bureau.add(user)
    bureau.run()