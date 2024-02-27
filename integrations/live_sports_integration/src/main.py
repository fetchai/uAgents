# import required libraries
from agents.sports_agent import sport_agent
from agents.user import user

from uagents import Bureau

#adding all users to bureau and running it
if __name__ == "__main__":
    bureau = Bureau(endpoint="http://127.0.0.1:8000/submit", port=8000)
    bureau.add(sport_agent)
    bureau.add(user)
    bureau.run()


