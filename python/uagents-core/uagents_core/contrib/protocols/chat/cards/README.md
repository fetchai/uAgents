# Interactive cards (metadata path)

Structured UI cards (carousel, detail, form, review, custom element tree) sent inside
`MetadataContent` blocks on the existing chat protocol. No protocol digest change.

**Import path:** `uagents_core.contrib.protocols.chat.cards`

Always build and parse card blocks with the helpers — do not hand-roll metadata keys
unless you are implementing a non-Python consumer.

| Helper | Role |
|--------|------|
| `create_card_content()` | Card request → `MetadataContent` |
| `create_card_response_content()` | Card response → `MetadataContent` |
| `extract_card()` | `MetadataContent` → `Card` or `None` |
| `extract_card_response()` | `MetadataContent` → `CardResponse` or `None` |

Payload shapes: `CarouselCardPayload`, `DetailCardPayload`, `FormCardPayload`,
`ReviewCardPayload`, `CustomCardPayload`. Validate ad hoc dicts with
`validate_card_payload(card_kind, payload)`.

## Metadata convention (version `"1"`)

**Request** — `card_protocol_version`, `card_kind`, `card_payload` (JSON). Optional:
`card_id`, `is_terminal`, `preferred_drawer_width_px`.

**Response** — `card_protocol_version` without `card_kind`. Optional: `card_id`, `text`,
`selection` (JSON object of JSON primitives), `cancelled`.

A block is a **request** when `card_kind` is present; a **response** when it is absent.

## Example

This module lives in **uagents-core**. Send chat messages with
`uagents_core.utils.messages.send_message_to_agent`, not `ctx.send` from the full
`uagents` agent runtime.

Agent sends a carousel card, then handles the user's structured reply:

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
recipient = "agent1q..."  # destination agent address

payload = CarouselCardPayload(
    title="Choose a flight",
    items=[
        CarouselItem(
            id="off_1",
            title="British Airways",
            primary_cta=CtaAction(label="Select", selection={"offer_id": "off_1"}),
        )
    ],
)

send_message_to_agent(
    destination=recipient,
    msg=ChatMessage(
        [
            TextContent("Here are some options:"),
            create_card_content(payload, card_id=uuid4()),
        ]
    ),
    sender=identity,
)

# In your inbound handler: parse the envelope, then scan MetadataContent blocks.
msg = parse_envelope(env, ChatMessage)
card = None
for block in msg.content:
    if isinstance(block, MetadataContent):
        card = extract_card(block)
        if card is not None:
            break

if card is None:
    return

send_message_to_agent(
    destination=env.sender,
    msg=ChatMessage(
        [
            create_card_response_content(
                card_id=card.card_id,
                selection={"offer_id": "off_1"},
            )
        ]
    ),
    sender=identity,
)

response = None
for block in msg.content:
    if isinstance(block, MetadataContent):
        response = extract_card_response(block)
        if response is not None:
            break

if response is None or response.cancelled:
    return
if response.selection is not None:
    ...
```

For async code paths (for example the Agentverse SDK), use
`uagents_core.agentverse.sdk.common.av.send_message_to_agent` with the same
arguments.

`card_id` is optional on the request; echo it on the response when you need strict
correlation. Otherwise rely on chat message history.
