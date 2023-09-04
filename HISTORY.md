# Release History


## 0.6.0

New features:
- Better exception handling across the project
- Added extensive API documentation
- Almanac registration is now performed before startup tasks
- [Experimental] Broadcast to all agents supporting protocol
- Refactor: all contract interactions moved to `uagents.network`

Integrations:
- [Fetch] Holiday (flights, destinations, activities) 
- [Contributed] Mobility: EV charging station and mapping agents
- [Contributed] DistilGPT-2


## 0.5.1

Updates:
- Minor updates to name service integration
- Adds `Context.send_raw(...)` function


## 0.5.0

New features:
- Python 3.11 support
- Envelopes now include protocol digest when appropriate
- Agents can now support queries for their protocol manifests
- Envelope session ID is now used to keep track of dialogues between agents


## 0.4.1

Updates:
- Update CosmPy dependency for better compatibility with other projects.


## 0.4.0

New features:
- Add mailbox support to Bureau agents
- Update and reorganize examples


## 0.3.2

Updates:
- Protocol manifests
- Better startup task management
- Agentverse mailbox integration


## 0.3.1

Updates:
- Includes required API key in mailbox server authentication flow


## 0.3.0

New features:
- support for mailbox service
- better logging output


## 0.2.0

Initial release:
- Core framework with interval tasks, message, and event handlers
- Initial exchange protocol implementation
- Signed and unsigned message handlers
- Supports sync (wait for response) and async message exchange
- Interface with Almanac smart contract on Fetch.ai ledger
- Optional Tortoise-ORM integration
- 10 examples
- Initial docs and test cases
