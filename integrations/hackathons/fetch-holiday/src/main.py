from uagents import Bureau

from agents.activities.top_activities import agent as top_activities_agent
from agents.destinations.top_destinations import agent as top_destinations_agent
from agents.flights.flights import agent as flights_agent


if __name__ == "__main__":
    bureau = Bureau(endpoint="http://127.0.0.1:8000/submit", port=8000)
    print(f"Adding top activities agent to Bureau: {top_activities_agent.address}")
    bureau.add(top_activities_agent)
    print(f"Adding top destinations agent to Bureau: {top_destinations_agent.address}")
    bureau.add(top_destinations_agent)
    print(f"Adding flights agent to Bureau: {flights_agent.address}")
    bureau.add(flights_agent)
    bureau.run()