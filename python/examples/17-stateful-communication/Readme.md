### How to use Dialogues

#### Define a pattern (generic dialogue without models)

1. Define the intended behaviour / communication flow as a directed graph.
2. Create a new class inheriting from `Dialogue`.
3. Specify nodes and edges according to the graph.
4. Specify a concrete transition decorator for each transition (=edge).

See `chitchat.py` for an example.

**Note:** The default state represents the state that the agent is in when a dialogue with another agent hasn't been started yet. This state is not shared but exists for each potential dialogue instance with other agents. The default state is included for completeness of the Dialogue graph and has no functional role.

#### Implement a pattern (attach models to transitions)

1. Instantiate a dialogue (e.g., `ChitChatDialogue`) with your agents address.
2. Define message models for each transition defined in the dialogue, according to the needs of your use case.
3. Implement all state transition decorators defined in the dialogue, similarly to the `on_message` handler and register the corresponding models with the respective transitions.

See `agent1.py` and `agent2.py` for an example implementation of the `ChitChatDialogue` defined in `chitchat.py`.

To use the example start `agent1` first, then `agent2` which will initiate the dialogue after 5 seconds. To exit the dialogue press `ctrl + d` on your keyboard.

### Examples

#### Open Dialogue (Agent 1 & 2)

Agent 1 and 2 make use of an implementation of the ChitChat Dialogue in which each step of the graph is exposed to the user. Both agents will be able to communicate as long as both define the same Models for the predefined graph (ChitChatDialogue class).

#### Predefined Dialogue (Agent 3 & 4)

Agent 3 and 4 are given a graph of the same ChitChat Dialogue but most of the interactions are automated and not exposed to the user. Only one interaction to start the dialogue and the cyclic ChitChat message is required to use the graph.
