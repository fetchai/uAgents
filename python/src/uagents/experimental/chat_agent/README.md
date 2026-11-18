# Experimental ChatAgent

`ChatAgent` is a thin wrapper around `Agent` that:
- Plugs in an LLM (ASI1, OpenAI, Anthropic, …)
- Exposes your protocol handlers as **tools**
- Always includes an `AgentInfoRequest` tool (name, description, instructions, capabilities) for greetings and “who are you?” questions
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

agent = ChatAgent(
    name="MathChat",
    starter_prompts=[
        "What can you calculate?",
        "Help me solve 12 * 8",
    ],
)
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

### Starter prompts

`starter_prompts` are optional example chat messages for the agent's Agentverse profile. They only apply to `ChatAgent` (agents with Chat Protocol). Length limits are enforced by the Agentverse API when the profile is saved. They are published when the agent connects to Agentverse with `publish_agent_details=True` (the default for `ChatAgent`).

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

## Structured resources and ASI:One

The chat protocol can carry more than plain text. Use `TextContent` for UTF-8 text,
`ResourceContent` for a URI such as a PDF or image, and `MetadataContent` for
structured JSON-like metadata. A resource is referenced by URI; the protocol does
not upload the file or fetch the URI for you.

For example, an agent can accept a resource in a regular protocol handler:

```python
from uagents import Context
from uagents_core.contrib.protocols.chat import ChatMessage, ResourceContent
from uagents import Protocol

resource_protocol = Protocol(name="ResourceHandling", version="0.1.0")


@resource_protocol.on_message(ChatMessage)
async def handle_resource(ctx: Context, sender: str, msg: ChatMessage):
    for content in msg.content:
        if not isinstance(content, ResourceContent):
            continue

        resources = content.resource
        if not isinstance(resources, list):
            resources = [resources]

        for resource in resources:
            mime_type = resource.metadata.get("mime_type", "application/octet-stream")
            if mime_type == "application/pdf":
                ctx.logger.info("Received a PDF resource at %s", resource.uri)
            elif mime_type.startswith("image/"):
                ctx.logger.info("Received an image resource at %s", resource.uri)
```

`ResourceContent` is suitable for PDFs and images because it carries a URI and
metadata such as `mime_type`. `MetadataContent` is suitable for structured values
that are already part of the message, for example:

```python
from uagents_core.contrib.protocols.chat import MetadataContent

metadata = MetadataContent(
    metadata={"document_type": "invoice", "page_count": "3"}
)
```

The current `ChatAgent` LLM path extracts `TextContent` from `ChatMessage` before
calling the configured model. It does not automatically download, parse, OCR, or
send PDF and image resources to ASI:One. To make a resource available to an LLM,
the application must validate the URI, retrieve the resource through its own
trusted service, and convert it to text or a provider-specific multimodal request
before invoking the model. Do not place private files or credentials in a public
URI. Treat resource metadata and remote content as untrusted input.

## LLMParams defaults:

* `temperature` = 0.0: make the model as deterministic as possible (no randomness in choices).
* `max_tokens` = 1024: upper bound on how long each model response can be.
* `tool_choice` = "required": whenever tools are available, the model must pick one instead of answering directly in the first step.
* `parallel_tool_calls` = False: at most one tool call per turn (no parallel / multi-tool execution).
* `system prompt`: global “rules of the game”: use tools, pick exactly one, base reasoning on the latest user message, etc.
* And because LLMParams uses extra="allow", you can add any extra provider-specific params (e.g. top_p, frequency_penalty, stop, etc.) to tailor behavior for your model without changing the core code.
