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
        # get storage entry for current DeltaV session from agent storage
        # because another AI agent has already sent back its response to this Adapter via this message handler
        # so an entry for this DeltaV session has already been created before in agent storage
        ai_agents_responses_session = pending_ai_agents_responses[session_str]
    else:
        # Adapter hasn't got any messages from any of the AI Agents for this DeltaV session via this message handler so far
        # so let's create a new entry for this session
        ai_agents_responses_session = {}
    # add response of AI Agent to session dictionary
    ai_agents_responses_session[sender] = msg.response
    ctx.logger.info(
        f"""All AI Agent responses that belong to those DeltaV sessions
            for which we have got some of the responses but not all of them: {pending_ai_agents_responses}"""
    )

    # number of responses for current DeltaV session is equal to the number of AI Agents
    # it means we have received the response from all AI Agents
    if len(ai_agents_responses_session) == len(ctx.storage.get("ai_agent_addresses")):
        ctx.logger.info(
            f"Sending response back to DeltaV for session {session_str} since we have received the response from all AI Agents"
        )

        # concatenate all AI responses into a final response string
        final_ai_responses = ", ".join(
            [resp for resp in ai_agents_responses_session.values()]
        )
        # send final response back to DeltaV
        await ctx.send(
            ctx.storage.get("deltav-sender-address"),
            UAgentResponse(
                message=f"AI Agents' responses: {final_ai_responses}",
                type=UAgentResponseType.FINAL,
            ),
        )

        # we don't need the store responses for this session anymore
        # so we can remove those AI responses from agent storage the were collected for current DeltaV session
        pending_ai_agents_responses.pop(session_str)
        # save updated AI responses data (without current session responses) in agent storage
        ctx.storage.set("pending_ai_agents_responses", pending_ai_agents_responses)
        return

    # update all AI responses data with the one specific for this session
    pending_ai_agents_responses[session_str] = ai_agents_responses_session
    # save updated AI responses data in agent storage
    ctx.storage.set("pending_ai_agents_responses", pending_ai_agents_responses)


agent.include(adapter_protocol)
