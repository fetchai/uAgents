# Experimental ChatAgent

`ChatAgent` is a thin wrapper around `Agent` that:
- Plugs in an LLM (ASI1, OpenAI, Anthropic, …)
- Exposes your protocol handlers as **tools**
- Keeps **message history** by default for multi-turn chat

---

## Quickstart

Install uAgents with:
```bash
pip install uagents[llm]
```
or
```bash
pip install uagents[all]
```

Build your agent from protocols as usual:

```python
from uagents.experimental.chat_agent import ChatAgent

agent = ChatAgent(name="MathChat")
proto = Protocol(name="Calculator", version="0.1.0")


class CalculateRequest(Model):
    expression: str = Field(..., description="Mathematical expression to calculate")


class CalculateResponse(Model):
    result: float = Field(..., description="Calculation result")


@proto.on_message(CalculateRequest)
async def handle_calculate_request(ctx: Context, sender: str, msg: CalculateRequest):
    ctx.logger.info(f"Received calculate request from {sender}: {msg.expression}")
    await ctx.send(
        sender, CalculateResponse(result=eval(msg.expression))
    )


agent.include(proto, publish_manifest=True)


if __name__ == "__main__":
    agent.run()
```

## LLM Configuration
LLM behavior is configured via LLMParams and LLMConfig:

```python
from uagents.experimental.chat_agent import ChatAgent, LLMParams, LLMConfig

asione_config = LLMConfig.asi1() # default

openai_config = LLMConfig(
    provider="openai",
    api_key="YOUR_OPENAI_API_KEY",
    model="gpt-5-mini",
    url="https://api.openai.com/v1",
    parameters=LLMParams(temperature=1),
)

claude_config = LLMConfig(
    provider="anthropic",
    api_key="YOUR_ANTHROPIC_API_KEY",
    model="claude-4-5-haiku",
    url="https://api.anthropic.com/v1/messages",
    parameters=LLMParams(),
)

agent = ChatAgent(name="MathChat", llm_config=asione_config)
```

## LLMParams defaults:

* `temperature` = 0.0: make the model as deterministic as possible (no randomness in choices).
* `max_tokens` = 1024: upper bound on how long each model response can be.
* `tool_choice` = "required": whenever tools are available, the model must pick one instead of answering directly in the first step.
* `parallel_tool_calls` = False: at most one tool call per turn (no parallel / multi-tool execution).
* `system prompt`: global “rules of the game”: use tools, pick exactly one, base reasoning on the latest user message, etc.
* And because LLMParams uses extra="allow", you can add any extra provider-specific params (e.g. top_p, frequency_penalty, stop, etc.) to tailor behavior for your model without changing the core code.
