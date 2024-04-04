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
