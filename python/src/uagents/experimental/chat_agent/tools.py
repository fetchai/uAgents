from typing import Any, Callable

from uagents_core.models import Model

from uagents.protocol import Protocol


class Tool:
    def __init__(
        self,
        name: str,
        description: str,
        model_cls: type[Model],
        handler: Callable[..., Any],
    ):
        self.name = name
        self.description = description
        self.model_cls = model_cls
        self.handler = handler

    def tool_spec(self) -> dict[str, Any]:
        schema = self.model_cls.schema()
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": schema,
            },
        }


def extract_tools_from_protocol(proto: Protocol) -> list[Tool]:
    tools: list[Tool] = []

    all_handlers: dict[str, Callable[..., Any]] = {
        **proto.signed_message_handlers,
        **proto.unsigned_message_handlers,
    }

    for digest, model_cls in proto.models.items():
        handler_fn = all_handlers.get(digest)
        if handler_fn is None:
            continue

        tool_name = model_cls.__name__
        description = (
            f"Handle a `{model_cls.__name__}` request for protocol "
            f"{proto.canonical_name}."
        )

        tools.append(
            Tool(
                name=tool_name,
                description=description,
                model_cls=model_cls,
                handler=handler_fn,
            )
        )

    return tools
