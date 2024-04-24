from uuid import uuid4

from uagents import Agent, Context

from negotiation.messages import CounterProposal, Acceptance, Reject, Proposal

ALICE_TARGET_MIN_PRICE = 60.0
ALICE_TARGET_MAX_PRICE = 110.0
ALICE_TARGET_ITEM = 'widget'

alice = Agent(name='alice', seed='alices super secret seed phrase')
print('Alice address: ', alice.address)

bob_address = 'agent1qg5a9zvex0gy2amagpvadp6f9kcf8jxa3akrqd09lf8kk2frlxj7q7pu3yt'



@alice.on_message(Acceptance)
async def handle_acceptance(ctx: Context, sender: str, msg: Acceptance):
    ctx.logger.info(f'({msg.proposal_id}) accepted at price {msg.price}')


@alice.on_message(Reject)
async def handle_reject(ctx: Context, sender: str, msg: Reject):
    ctx.logger.info(f'({msg.proposal_id}) rejected because {msg.reason}')


@alice.on_message(CounterProposal)
async def handle_counter_proposal(ctx: Context, sender: str, msg: CounterProposal):
    ctx.logger.info(f'({msg.proposal_id}) counter offer for {msg.price}')

    # evaluate the counter proposal
    next_price = ((msg.price - ALICE_TARGET_MIN_PRICE) // 2) + ALICE_TARGET_MIN_PRICE

    # attempt to negotiate down
    await ctx.send(
        bob_address,
        Proposal(
            id=uuid4(),
            item=ALICE_TARGET_ITEM,
            price=next_price,
        )
    )


@alice.on_interval(10)
async def on_interval(ctx: Context):
    proposal_id = uuid4()
    starting_price = ALICE_TARGET_MIN_PRICE

    ctx.logger.info(f'({proposal_id}) proposing at price {starting_price}')

    # send the proposal to Bob
    await ctx.send(
        bob_address,
        Proposal(
            id=proposal_id,
            item=ALICE_TARGET_ITEM,
            price=starting_price
        )
    )
