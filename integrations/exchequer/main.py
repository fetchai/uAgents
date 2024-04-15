"""exchequer dialogue example"""

from asyncio import sleep

from dialogue.clients import get_client
from dialogue.exchequer import ExchequerDialogue, PaymentRequest
from uagents import Agent, Bureau, Context

agent1 = Agent(
    name="Payer   ",
    seed="exchequer payer dialogue demo",
    log_level="DEBUG",
)
agent2 = Agent(
    name="Receiver",
    seed="exchequer payee dialogue demo",
    log_level="DEBUG",
)

ex_dialogue_1 = ExchequerDialogue(
    version="v0.0.1",
    agent_address=agent1.address,
)
ex_dialogue_2 = ExchequerDialogue(
    version="v0.0.1",
    agent_address=agent2.address,
)

agent1.include(ex_dialogue_1)
agent2.include(ex_dialogue_2)


@agent2.on_event("startup")
async def start_payee(ctx: Context):
    await sleep(5)
    await ctx.send(
        agent1.address,
        PaymentRequest(
            requester_id=get_client("client_3")["id"],
            amount=50,
            subject="Invoice #2984537817894 for ebook",
        ),
    )


if __name__ == "__main__":
    bureau = Bureau(port=8080, endpoint="http://localhost:8080/submit")
    bureau.add(agent1)
    print("Paying Agent:", agent1.address)
    bureau.add(agent2)
    print("Receiving Agent:", agent2.address)
    bureau.run()
