# from uagents.experimental.mobility import MobilityAgent
from uagents import Agent

# agent = MobilityAgent(
#     seed="5813827564197286315342489173672541637287328671",
#     location=AgentGeoLocation(
#         latitude=52.507410,
#         longitude=13.378240,
#         radius=50,
#     ),
#     port=8000,
#     endpoint="http://localhost:8000/submit",
# )

agent = Agent(
    seed="5813827564197286315342489173672541637287328671",
    metadata={
        "latitude": 52.507410,
        "longitude": 13.378240,
        "radius": 50,
        "mobility": True,
        "useless_information": "This is a test",
    },
    port=8000,
    endpoint="http://localhost:8000/submit",
)

if __name__ == "__main__":
    print(agent.metadata)
    # agent.run()
