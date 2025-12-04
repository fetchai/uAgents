# Experimental ChatAgent

`ChatAgent` is a thin wrapper around `Agent` that:
- Plugs in an LLM (ASI1, OpenAI, Anthropic, …)
- Exposes your protocol handlers as **tools**
- Optionally keeps **message history** for multi-turn chat

---

## Quickstart

Minimal change from `Agent` → `ChatAgent`:

```python
from uagents.experimental.chatagent.agent import ChatAgent
from uagents.experimental.chatagent.ai import asione_config

AGENT_SEED = "chat-agent"
AGENT_NAME = "chat-agent"
PORT = 8000

agent = ChatAgent(
    name=AGENT_NAME,
    seed=AGENT_SEED,
    port=PORT,
    endpoint=f"http://localhost:{PORT}/submit",
    llm_config=claude_config,      # choose your LLM config
    store_message_history=True,    # enable session-aware chat
)

@proto.on_message(Prompt, replies={Response, ErrorMessage})
async def handle_request(ctx: Context, sender: str, msg: Prompt):
    # Your logic...

    # NEW: always return, ChatAgent will reply for you
    return Response(mean=..., median=...)

# include your protocols as usual
agent.include(my_proto, publish_manifest=True)
```

## LLM Configuration
LLM behavior is configured via LLMParams and LLMConfig:

```python
from uagents.experimental.chatagent.ai import LLMParams, LLMConfig

openai_config = LLMConfig(
    provider="openai",
    api_key="YOUR_OPENAI_API_KEY",
    model="gpt-4o-mini",
    url="https://api.openai.com/v1",
    parameters=LLMParams(),
)

claude_config = LLMConfig(
    provider="anthropic",
    api_key="YOUR_ANTHROPIC_API_KEY",
    model="claude-3-5-haiku-latest",
    url="https://api.anthropic.com/v1/messages",
    parameters=LLMParams(),
)

asione_config = LLMConfig(
    provider="openai",
    api_key="YOUR_ASIONE_API_KEY",
    model="asi1-mini",
    url="https://api.asi1.ai/v1",
    parameters=LLMParams(),
)
```

## LLMParams defaults:

* `temperature` = 0.0: make the model as deterministic as possible (no randomness in choices).
* `max_tokens` = 1024: upper bound on how long each model response can be.
* `tool_choice` = "required": whenever tools are available, the model must pick one instead of answering directly in the first step.
* `parallel_tool_calls` = False: at most one tool call per turn (no parallel / multi-tool execution).
* `system prompt`: global “rules of the game”: use tools, pick exactly one, base reasoning on the latest user message, etc.
* And because LLMParams uses extra="allow", you can add any extra provider-specific params (e.g. top_p, frequency_penalty, stop, etc.) to tailor behavior for your model without changing the core code.
