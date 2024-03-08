from ai_engine import UAgentResponse, UAgentResponseType


class AIRequest(Model):
    prompt: str


class AIResponse(Model):
    response: str


adapter_protocol = Protocol(f"AI Agent Adapter protocol")


@agent.on_event("startup")
async def start_ai_adapter(ctx: Context):
    # TODO: SET YOUR AI AGENT ADDRESSES HERE!
    ctx.storage.set("ai_agent_addresses", [])
    ctx.storage.set("pending_ai_agents_responses", {})


@adapter_protocol.on_message(model=AIRequest, replies=UAgentResponse)
async def send_prompt_to_ai_agents(ctx: Context, sender: str, msg: AIRequest):
    # save sender (=DeltaV) address so that we can send back response later
    ctx.storage.set("deltav-sender-address", sender)
    ai_agent_addresses = ctx.storage.get("ai_agent_addresses")
    ctx.logger.info(
        f"AI Agent addresses which we are sending request to: {ai_agent_addresses}"
    )
    for address in ai_agent_addresses:
        ctx.logger.info(f"Forwarding prompt {msg.prompt} to AI Agent {address}")
        await ctx.send(address, msg)


@adapter_protocol.on_message(model=AIResponse)
async def process_response_from_ai_agent(ctx: Context, sender: str, msg: AIResponse):
    ctx.logger.info(f"Response from AI agent: {msg.response}")

    # get all AI Agent responses from storage that belong to those DeltaV sessions
    # for which we have already got some of the responses from our AI Agents but not all of them (= pending DeltaV sessions)
    pending_ai_agents_responses = ctx.storage.get("pending_ai_agents_responses")
    session_str = str(ctx.session)
    if session_str in pending_ai_agents_responses:
        # get storage entry because another AI agent has already created an entry for this DeltaV session
        ai_agents_responses_session = pending_ai_agents_responses[session_str]
    else:
        # adapter hasn't got any messages from AI Agents for this DeltaV session so far so let's create a new entry for this session
        ai_agents_responses_session = {}
    # add response of AI Agent to session dictionary
    ai_agents_responses_session[sender] = msg.response
    # update all AI responses data with the one specific for this session
    pending_ai_agents_responses[session_str] = ai_agents_responses_session
    ctx.logger.info(
        f"""All AI Agent responses that belong to those DeltaV sessions
            for which we have got some of the responses but not all of them: {pending_ai_agents_responses}"""
    )
    # store updated AI responses data in agent storage
    ctx.storage.set("pending_ai_agents_responses", pending_ai_agents_responses)

    if len(ai_agents_responses_session) == len(ctx.storage.get("ai_agent_addresses")):
        ctx.logger.info(
            f"Sending response back to DeltaV for session {session_str} since we have got responses from all AI Agents"
        )
        final_ai_responses = ", ".join(
            [resp for resp in ai_agents_responses_session.values()]
        )
        await ctx.send(
            ctx.storage.get("deltav-sender-address"),
            UAgentResponse(
                message=f"AI Agents' responses: {final_ai_responses}",
                type=UAgentResponseType.FINAL,
            ),
        )
        # we don't need this session anymore so we can remove AI responses collected for current DeltaV session
        pending_ai_agents_responses.pop(session_str)
        # save updated AI responses data in agent storage
        ctx.storage.set("pending_ai_agents_responses", pending_ai_agents_responses)


agent.include(adapter_protocol)
