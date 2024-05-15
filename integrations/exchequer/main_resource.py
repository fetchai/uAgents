"""resource dialogue example"""

from asyncio import sleep

from dialogue.resource_handling import ResourcePaymentDialogue, ResourceRequest
from uagents import Agent, Bureau, Context

agent1 = Agent(
    name="Payer   ",
    seed="resource consumer dialogue demo",
    log_level="DEBUG",
)
agent2 = Agent(
    name="Receiver",
    seed="resource provider dialogue demo",
    log_level="DEBUG",
)

res_dialogue_1 = ResourcePaymentDialogue(
    version="v0.0.1",
    agent_address=agent1.address,
)
res_dialogue_2 = ResourcePaymentDialogue(
    version="v0.0.1",
    agent_address=agent2.address,
)

agent1.include(res_dialogue_1)
agent2.include(res_dialogue_2)


@agent1.on_event("startup")
async def setup_resources(ctx: Context):
    res_type = {"fancy_stuff": {"available": 2, "price": 5}}
    ctx.storage.set("resources", res_type)


@agent2.on_event("startup")
async def start_consumer(ctx: Context):
    await sleep(5)
    # TODO start_dialogue handler to add custom code to be run when a dialogue is started
    await res_dialogue_2.start_dialogue(
        ctx, agent1.address, ResourceRequest(quantity=1, type="fancy_stuff")
    )


if __name__ == "__main__":
    bureau = Bureau(port=8080, endpoint="http://localhost:8080/submit")
    bureau.add(agent1)
    print("Paying Agent:", agent1.address)
    bureau.add(agent2)
    print("Receiving Agent:", agent2.address)
    bureau.run()
