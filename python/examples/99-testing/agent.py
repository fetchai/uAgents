from uagents.experimental.mobility import MobilityAgent

agent = MobilityAgent(
    seed="5813827564197286315342489173672541637287328671",
    metadata={
        "geolocation": {
            "latitude": 52.507411,
            "longitude": 13.37824628,
            "radius": 50,
        },
        "mobility": True,
        "useless_information": "This is a test",
    },
    port=8000,
    endpoint="http://localhost:8000/submit",
)

if __name__ == "__main__":
    print(agent.metadata)
    agent.run()
