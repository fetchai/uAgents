### How to use Dialogues

#### Define a pattern (generic dialogue without models)
1. Define the intended behaviour / communication flow as a directed graph.
2. Create a new class inheriting from `Dialogue`.
3. Specify nodes and edges according to the graph.
4. Specify a concrete transition decorator for each transition (=edge).

See `chitchat.py` for an example.

#### Implement a pattern (attach models to transitions)
1. Instantiate a dialogue (e.g., `ChitChatDialogue`) with your agents address.
2. Define message models for each transition defined in the dialogue, according to the needs of your use case.
3. Implement all state transition decorators defined in the dialogue, similarly to the `on_message` handler and register the corresponding models with the respective transitions.

See `main.py` for an example implementation of the `ChitChatDialogue` defined in `chitchat.py`.
