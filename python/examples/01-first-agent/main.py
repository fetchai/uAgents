from uagents import Agent, Context

agent = Agent(name="alice")
a = "agent1blahblahblah"
b = "some-prefix://agent1blahblahblah"
c = "some-prefix://some_agent_name/agent1blahblahblah"

print(a.split("://")[-1].split("/")[-1])
print(b.split("://")[-1].split("/")[-1])
print(c.split("://")[-1].split("/")[-1])


@agent.on_event("startup")
async def introduce_agent(ctx: Context):
    ctx.logger.info(f"Hello, I'm agent {ctx.name} and my address is {ctx.identifier}.")


if __name__ == "__main__":
    agent.run()
