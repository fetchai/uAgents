from uagents.experimental.mobility import MobilityAgent
from uagents.types import AgentGeoLocation

agent = MobilityAgent(
    seed="5813827564197286315342489173672541637287328671",
    location=AgentGeoLocation(
        latitude=52.507410,
        longitude=13.378240,
        radius=50,
    ),
    port=8000,
    endpoint="http://localhost:8000/submit",
)

if __name__ == "__main__":
    print(agent.location)
    agent.run()
