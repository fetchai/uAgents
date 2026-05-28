# Interactive cards

Interactive cards over the chat protocol using
`uagents_core.contrib.protocols.chat.cards`. Card payloads travel in `MetadataContent`
blocks; the chat protocol digest is unchanged.

| Agent | Role |
|-------|------|
| `menu-host` | Receives `"menu"`, replies with a carousel card, confirms the selection |
| `menu-picker` | Asks for the menu, auto-selects the first carousel item, sends a card response |

Shared handlers live in `protocols.py`. Wire format and helpers are documented in
`uagents_core/contrib/protocols/chat/cards/README.md`.

## Setup

From the `python/` directory, `uv sync` installs `uagents` with an editable path
dependency on the local `uagents-core` tree (includes the cards module).

```bash
cd ../../../   # from this example → python/
uv sync
```

## Bureau (local, single process)

Both agents run in one process; the picker messages the host on startup.

```bash
uv run python tests/examples/45-interactive-cards/bureau.py
```

Watch the logs: the host prints `Order confirmed: apple` after the picker's
`MetadataContent` card response.

## Mailbox agents

Run each agent in its own terminal. They use `mailbox=True` and relay through Agentverse.

**Terminal 1 — menu host**

```bash
uv run python tests/examples/45-interactive-cards/menu_host.py
```

Copy the agent address from the startup logs.

**Terminal 2 — picker**

Set `MENU_HOST_ADDRESS` in `picker.py` to that address (picker uses port `8001` so it
does not clash with the host locally), then:

```bash
uv run python tests/examples/45-interactive-cards/picker.py
```

The picker sends `"menu"` on startup; the host replies with a carousel card; the picker
sends a structured `MetadataContent` card response.

## Messaging

- **Bureau:** agents use `ctx.send` for in-process delivery.
- **Mailbox / external:** use `send_message_to_agent` from `uagents_core.utils.messages`
  (see `uagents_core/contrib/protocols/chat/cards/README.md`).
- **Card responses:** prefer `MetadataContent` via `extract_card_response()`. The menu host
  also accepts legacy `TextContent` JSON for backwards compatibility.

Card types and wire helpers are imported from **uagents-core** in `protocols.py`.
