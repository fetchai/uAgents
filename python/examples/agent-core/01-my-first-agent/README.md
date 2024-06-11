# My First Agent Example

Welcome to My First Agent example! This guide will help you understand key concepts used in creating an agent that can perform tasks based on certain events and intervals. Before diving into the concepts, ensure you navigate to the example directory, then run the following commands to set up your environment with the necessary dependencies:

```
poetry install
poetry shell
```

## Key Concepts

### @on_event("startup")

- **Description**: The `@on_event("startup")` decorator is used to define a function that should be executed when the agent starts up. This is particularly useful for initialization tasks such as setting up logging, initializing storage, or performing a desired initial action.
- **Example Usage**: In our example, the `introduce_agent` function is executed at startup, where the agent logs its name and address and initializes a count in its storage.

### @on_event("shutdown")

- **Description**: Similarly, the `@on_event("shutdown")` decorator defines a function to be executed when the agent is shutting down. This can be used for cleanup tasks like closing database connections, saving state, or simply logging that the agent process is finished.
- **Example Usage**: The `goodbye` function logs a message indicating that the agent process has finished.

### @on_interval()

- **Description**: The `@on_interval` decorator is used to schedule a function to run at a fixed interval, specified by the `period` parameter (in seconds). This is useful for tasks that need to be repeated periodically, such as polling a service, updating a dashboard, or in this case, incrementing a counter.
- **Example Usage**: The `counter` function is called every 2 seconds, incrementing and logging a count stored in the agent's storage.

### Storage set and get

- **Description**: Storage operations like `set` and `get` allow the agent to save and retrieve data across event handlers. This persistent storage can be used to maintain state, cache results, or store configuration settings.
- **Example Usage**: In the `introduce_agent` function, the count is initialized to 0 using `ctx.storage.set("count", 0)`. The `counter` function then retrieves this count, increments it, and stores it back using `ctx.storage.get("count")` and `ctx.storage.set("count", current_count + 1)`.

## Start the Agent

To start the agent and see the above-mentioned functionalities in action, simply run:

```
python agent.py
```

You'll see logs corresponding to the agent's startup process, periodic counter updates, and the shutdown message if you terminate the process. This will give you a practical view of how the agent operates and responds to events and intervals as described.


While none of these components are strictly necessary for an agent to function, they enable the development of more complex, stateful, and responsive agents. By leveraging events, intervals, and storage, you can create agents capable of handling a wide range of tasks in an efficient and organized manner.
