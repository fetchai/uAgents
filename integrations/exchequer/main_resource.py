"""resource dialogue example"""

from asyncio import sleep

from dialogue.resource_handling import (
    ResourceAvailability,
    ResourcePaymentDialogue,
    ResourceRequest,
    ResourceRerservation,
)
from uagents import Agent, Bureau, Context

from dialogue.exchequer import PaymentRequest


# # # # # # # # # # #
# Consumer Agent    #
# # # # # # # # # # #

consumer_agent = Agent(
    name="Consumer",
    seed="resource consumer dialogue demo",
    log_level="DEBUG",
)

consumer_dialogue = ResourcePaymentDialogue(
    version="v0.0.1",
    agent_address=consumer_agent.address,
)

consumer_agent.include(consumer_dialogue)


@consumer_agent.on_event("startup")
async def start_consumer(ctx: Context):
    await sleep(5)
    # TODO start_dialogue handler to add custom code to be run when a dialogue is started
    await consumer_dialogue.start_dialogue(
        ctx, provider_agent.address, ResourceRequest(quantity=1, type="fancy_stuff")
    )


@consumer_dialogue.on_availability(ResourceAvailability)
async def handle_availability(ctx: Context, sender: str, msg: ResourceAvailability):
    ctx.logger.info(f"User: received an offer for my request with price: {msg.price}")


@consumer_dialogue.on_payment_request(PaymentRequest)
async def handle_payment_request(ctx: Context, sender: str, msg: PaymentRequest):
    availability_msg = consumer_dialogue.get_conversation(ctx.session)[1]
    offered_price = availability_msg["price"]
    ctx.logger.info(
        f"User: got payment request over {msg.amount} (initially offered: {offered_price})"
    )


# # # # # # # # # # #
# Provider Agent    #
# # # # # # # # # # #

provider_agent = Agent(
    name="Provider",
    seed="resource provider dialogue demo",
    log_level="DEBUG",
)

provider_dialogue = ResourcePaymentDialogue(
    version="v0.0.1",
    agent_address=provider_agent.address,
)

provider_agent.include(provider_dialogue)


@provider_agent.on_event("startup")
async def setup_resources(ctx: Context):
    res_type = {"fancy_stuff": {"available": 2, "price": 5}}
    ctx.storage.set("resources", res_type)


@provider_dialogue.on_resource_request(ResourceRequest)
async def handle_resource_request(ctx: Context, sender: str, msg: ResourceRequest):
    ctx.logger.info(
        f"Got a resource request for type {msg.type}. Doing my business logic here"
    )


@provider_dialogue.on_resource_reserve(ResourceRerservation)
async def handle_reservation(ctx: Context, sender: str, msg: ResourceRerservation):
    ctx.logger.info("User: got rerservationt. Decide here whether to fulfill or not")


if __name__ == "__main__":
    bureau = Bureau(port=8080, endpoint="http://localhost:8080/submit")
    bureau.add(consumer_agent)
    print("Consumer Agent:", consumer_agent.address)
    bureau.add(provider_agent)
    print("Provider Agent:", provider_agent.address)
    bureau.run()
