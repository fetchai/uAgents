# Interactive cards (metadata path)

Structured UI cards in `MetadataContent` on the chat protocol. No digest change.

**Import:** `uagents_core.contrib.protocols.chat.cards`

Use the helpers for metadata keys — do not hand-roll them in Python.

| Helper | Role |
|--------|------|
| `create_card_content()` | Request → `MetadataContent` |
| `create_card_response_content()` | Response → `MetadataContent` |
| `extract_card()` | Request block → `Card` or `None` |
| `extract_card_response()` | Response block → `CardResponse` or `None` |

Payload types: `CarouselCardPayload`, `DetailCardPayload`, `FormCardPayload`,
`ReviewCardPayload`, `CustomCardPayload`. Ad hoc dicts: `validate_card_payload(card_kind, payload)`.

## Wire format (version `"1"`)

**Request** — `card_protocol_version`, `requires_card_interaction` (`"true"`), `card_kind`,
`card_payload` (JSON). Optional: `card_id`, `is_terminal`, `preferred_drawer_width_px`.

**Response** — `card_protocol_version`, no `card_kind`. Optional: `card_id`, `text`,
`selection` (JSON primitives), `cancelled`.

Request blocks include `card_kind`; response blocks do not.

## Example

Send with `send_message_to_agent` (`uagents_core.utils.messages`). In the uAgents runtime
you may use `ctx.send` instead.

```python
from uuid import uuid4

from uagents_core.contrib.protocols.chat import ChatMessage, MetadataContent, TextContent
from uagents_core.contrib.protocols.chat.cards import (
    CarouselCardPayload,
    CarouselItem,
    CtaAction,
    create_card_content,
    create_card_response_content,
    extract_card,
    extract_card_response,
)
from uagents_core.identity import Identity
from uagents_core.utils.messages import parse_envelope, send_message_to_agent

identity = Identity.from_seed("your-seed-phrase", 0)

# Outbound card request
send_message_to_agent(
    destination="agent1q...",
    msg=ChatMessage(
        [
            TextContent("Pick one:"),
            create_card_content(
                CarouselCardPayload(
                    title="Snacks",
                    items=[
                        CarouselItem(
                            id="apple",
                            title="Apple",
                            primary_cta=CtaAction(
                                label="Order", selection={"item_id": "apple"}
                            ),
                        ),
                        CarouselItem(
                            id="banana",
                            title="Banana",
                            primary_cta=CtaAction(
                                label="Order", selection={"item_id": "banana"}
                            ),
                        ),
                    ],
                ),
                card_id=uuid4(),
            ),
        ]
    ),
    sender=identity,
)

# Inbound: prefer MetadataContent (standard)
msg = parse_envelope(env, ChatMessage)
for block in msg.content:
    if isinstance(block, MetadataContent):
        response = extract_card_response(block)
        if response and response.selection:
            ...
        card = extract_card(block)
        if card:
            send_message_to_agent(
                destination=env.sender,
                msg=ChatMessage(
                    [
                        create_card_response_content(
                            card_id=card.card_id,
                            selection={"item_id": "apple"},
                        )
                    ]
                ),
                sender=identity,
            )
```

**Replies:** Handle card responses with `extract_card_response()` on `MetadataContent`.
That is the standard path.

Some clients still send the CTA `selection` as JSON inside `TextContent` for backwards
compatibility. You may parse `msg.text()` if needed; new integrations should use
`create_card_response_content()` / `extract_card_response()`.

Runnable demo: `python/tests/examples/45-interactive-cards/`.

`card_id` is optional; echo it on the response when you need strict correlation.
