from nexus import Agent

agent = Agent()


@agent.on_interval(period=1.0)
async def on_interval():
    print("User interval code")


if __name__ == "__main__":
    agent.run()
