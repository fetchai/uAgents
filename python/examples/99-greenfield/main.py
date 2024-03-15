from uagents import Agent, Context, Model

agent = Agent(
    name="stateful_agent_example",
    seed="feawuhfdajnvuiwahfuidsafmcwefuihwfuihufinhaufienwurazewufhdjsklfwhdkj",
    port=8080,
    endpoint="http://localhost:8080/submit",
)


class Message(Model):
    pass


def counter_logic(st_agent: Agent, ctx: Context):
    counter = ctx.storage.get("counter") or 0
    counter += 1
    if counter == 3:
        counter = 0
        st_agent.state = "new_state" if st_agent.state != "new_state" else "other_state"
        ctx.logger.info(f"State changed to {st_agent.state}")
    ctx.storage.set("counter", counter)


@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.storage.set("counter", 0)


@agent.on_interval(2)
async def another_interval_handler(ctx: Context):
    # ctx.logger.info("This handler will always be triggered.")
    counter_logic(agent, ctx)


# @agent.on_interval(2, state="new_state")
# async def interval_handler(ctx: Context):
#     ctx.logger.info("Only triggered when the agent is in the 'new_state'.")


@agent.on_message(Message, state="new_state")
async def handle_message(ctx: Context, sender: str, msg: Message):
    ctx.logger.info("Received a message!")


# print(agent.address)
# print(agent._protocol.manifest())
agent.run()
