"""Simple AI-Engine integration example.

This example demonstrates how to use the AI-Engine message types
for creating structured responses in uAgents.
"""

from typing import Optional
from uagents import Agent, Context, Model

# Import AI-Engine types
try:
    from ai_engine.messages import UAgentResponse, UAgentResponseType, KeyValue
    AI_ENGINE_AVAILABLE = True
except ImportError:
    # Fallback if AI-Engine is not installed
    AI_ENGINE_AVAILABLE = False
    print("AI-Engine not available. This is a structure example only.")


class QueryMessage(Model):
    """Simple query message."""
    query: str
    user_id: Optional[str] = None


class SimpleResponseMessage(Model):
    """Simple response message for fallback."""
    response: str
    success: bool = True


# Create agent
agent = Agent(name="ai_engine_example", seed="ai_engine_demo_seed")


@agent.on_startup()
async def startup(ctx: Context):
    """Agent startup handler."""
    ctx.logger.info("AI-Engine example agent started!")
    ctx.logger.info(f"Agent address: {ctx.address}")
    if AI_ENGINE_AVAILABLE:
        ctx.logger.info("AI-Engine types are available")
    else:
        ctx.logger.info("AI-Engine types not available - using fallback")


@agent.on_message(QueryMessage)
async def handle_query(ctx: Context, sender: str, msg: QueryMessage):
    """Handle incoming queries using AI-Engine response format when available."""
    ctx.logger.info(f"Received query from {sender}: {msg.query}")
    
    if AI_ENGINE_AVAILABLE:
        # Use AI-Engine structured response
        if "options" in msg.query.lower():
            # Provide options response
            options = [
                KeyValue(key="option1", value="First Option"),
                KeyValue(key="option2", value="Second Option"),
                KeyValue(key="option3", value="Third Option")
            ]
            
            response = UAgentResponse(
                type=UAgentResponseType.SELECT_FROM_OPTIONS,
                request_id=msg.user_id,
                agent_address=ctx.address,
                message="Please select one of the following options:",
                options=options,
                verbose_message="This is a detailed explanation of the available options."
            )
        elif "error" in msg.query.lower():
            # Provide error response
            response = UAgentResponse(
                type=UAgentResponseType.ERROR,
                request_id=msg.user_id,
                agent_address=ctx.address,
                message="An error occurred while processing your query.",
                verbose_message="The system encountered an error due to invalid input parameters."
            )
        else:
            # Provide final response
            response = UAgentResponse(
                type=UAgentResponseType.FINAL,
                request_id=msg.user_id,
                agent_address=ctx.address,
                message=f"Processed your query: {msg.query}",
                verbose_message=f"The agent successfully processed the query '{msg.query}' and generated this response."
            )
        
        await ctx.send(sender, response)
        ctx.logger.info(f"Sent AI-Engine structured response of type: {response.type}")
    
    else:
        # Fallback to simple response
        response = SimpleResponseMessage(
            response=f"Processed your query: {msg.query}",
            success=True
        )
        await ctx.send(sender, response)
        ctx.logger.info("Sent simple fallback response")


@agent.on_interval(period=30.0)
async def periodic_status(ctx: Context):
    """Periodic status update."""
    ctx.logger.info("AI-Engine example agent is running...")
    if AI_ENGINE_AVAILABLE:
        ctx.logger.info("Ready to handle queries with AI-Engine structured responses")


if __name__ == "__main__":
    print("AI-Engine Integration Example")
    print("============================")
    print(f"Agent address: {agent.address}")
    print()
    
    if AI_ENGINE_AVAILABLE:
        print("Features available:")
        print("- Structured AI-Engine responses")
        print("- Options selection responses")
        print("- Error handling responses")
        print("- Verbose message support")
    else:
        print("Running in fallback mode (AI-Engine not installed)")
    
    print()
    print("Send a QueryMessage to test:")
    print("- Query with 'options' for selection response")
    print("- Query with 'error' for error response")
    print("- Any other query for final response")
    print()
    
    # Run the agent
    agent.run()