from uagents import Agent, Context

from negotiation.messages import Proposal, CounterProposal, Acceptance, Reject

BOB_TARGET_MIN_PRICE = 100.0
BOB_TARGET_MAX_PRICE = 150.0
BOB_TARGET_ITEM = 'widget'

bob = Agent(name='bob', seed='bobs super secret seed phrase')
print('Bob address: ', bob.address)


@bob.on_message(Proposal)
async def handle_proposal(ctx: Context, sender: str, msg: Proposal):
    ctx.logger.info(f'({msg.id}) proposal at price {msg.price}')

    # if the proposal is not for the target item then it will be rejected
    if msg.item != BOB_TARGET_ITEM:
        await ctx.send(sender, Reject(proposal_id=msg.id, reason='I am not interested in that item'))
        return

    # sanity check
    assert msg.item == BOB_TARGET_ITEM

    # if the price is right then accept the proposal
    if BOB_TARGET_MIN_PRICE <= msg.price:
        await ctx.send(sender, Acceptance(proposal_id=msg.id, item=msg.item, price=msg.price))
        return

    # if the price is not right then counter with a proposal
    await ctx.send(sender, CounterProposal(proposal_id=msg.id, item=msg.item, price=BOB_TARGET_MAX_PRICE))
