# A2A Outbound Adapter

A comprehensive Python module for integrating A2A (Agent-to-Agent) systems with uAgents, enabling intelligent multi-agent coordination and communication.

---

## 1. What is the A2A Outbound Adapter?
- A bridge between A2A agents and the uAgent ecosystem
- Enables:
  - Multi-agent orchestration
  - Intelligent query routing
  - Health monitoring
  - Robust error handling
  - Seamless chat protocol integration

---

## 2. Main Components & Responsibilities (Agenda)
1. **A2AAgentConfig**: Define each agent's config (name, description, URL, port, specialties, etc.)
2. **a2a_servers**: Start one or more A2A agent servers, each with its own manifest and port
3. **SingleA2AAdapter**: For single-agent setups; wraps an agent executor and exposes it via uAgent chat/HTTP
4. **MultiA2AAdapter**: For multi-agent orchestration; manages configs, discovers agents, routes queries, handles fallback
5. **Message Flow**: Incoming message → Adapter → Routing/Selection → Agent Executor → Response → Back to sender

---

## 3. Installation

```shell
pip install "uagents-adapter[a2a-outbound]"
pip install "a2a-sdk[all]"
```

---

## 4. Configuration

### 4.1. Define Agent(s)
```python
config = A2AAgentConfig(
    name="SpecializedAgent",
    description="Agent description",
    url="http://localhost:9000",
    port=9000,
    specialties=["Machine Learning", "Data Science"],
    # skills, examples, keywords auto-generated if not provided
    priority=1
)
```

### 4.2. Routing Strategies
- **Keyword Matching** (default): Route by keyword/specialty
- **LLM-Based Routing**: Use AI to select best agent
- **Round Robin**: Distribute queries evenly

---

## 5. Step-by-Step Usage

### 5.1. Single Agent Setup
1. Define your agent config
2. Create the agent executor
3. Start the A2A server with `a2a_servers`
4. Create and run a `SingleA2AAdapter`

```python
from uagent_adapter import SingleA2AAdapter, A2AAgentConfig, a2a_servers
from brave.agent import BraveSearchAgentExecutor

def main():
    agent_config = A2AAgentConfig(
        name="brave_search_specialist",
        description="AI Agent for web and news search using Brave Search API",
        url="http://localhost:10020",
        port=10020,
        specialties=["web search", "news", "information retrieval", "local business", "site-specific lookup"],
        priority=3
    )
    executor = BraveSearchAgentExecutor()
    a2a_servers([agent_config], {agent_config.name: executor})
    print(f"AgentCard manifest URL: http://localhost:{agent_config.port}/.well-known/agent.json")
    adapter = SingleA2AAdapter(
        agent_executor=executor,
        name="brave",
        description="Routes queries to Brave Search AI specialists",
        port=8200,
        a2a_port=10030
    )
    adapter.run()

if __name__ == "__main__":
    main()
```

### 5.2. Multi-Agent Setup
1. Define multiple agent configs
2. Create executors for each
3. Start all A2A servers with `a2a_servers`
4. Create and run a `MultiA2AAdapter`

```python
from uagent_adapter import MultiA2AAdapter, A2AAgentConfig, a2a_servers
from agents.research_agent import ResearchAgentExecutor
from agents.coding_agent import CodingAgentExecutor
from agents.analysis_agent import AnalysisAgentExecutor

def main():
    agent_configs = [
        A2AAgentConfig(
            name="research_specialist",
            description="AI Research Specialist for research and analysis",
            url="http://localhost:10020",
            port=10020,
            specialties=["research", "analysis", "fact-finding", "summarization"],
            priority=3
        ),
        A2AAgentConfig(
            name="coding_specialist",
            description="AI Software Engineer for coding",
            url="http://localhost:10022",
            port=10022,
            specialties=["coding", "debugging", "programming"],
            priority=3
        ),
        A2AAgentConfig(
            name="analysis_specialist",
            description="AI Data Analyst for insights and metrics",
            url="http://localhost:10023",
            port=10023,
            specialties=["data analysis", "insights", "forecasting"],
            priority=2
        )
    ]
    executors = {
        "research_specialist": ResearchAgentExecutor(),
        "coding_specialist": CodingAgentExecutor(),
        "analysis_specialist": AnalysisAgentExecutor()
    }
    a2a_servers(agent_configs, executors)
    for config in agent_configs:
        print(f"AgentCard manifest URL: http://localhost:{config.port}/.well-known/agent.json")
    adapter = MultiA2AAdapter(
        name="coordinator---",
        description="Routes queries to AI specialists",
        llm_api_key="your_llm_api_key",
        base_url="your_llm_base_url"     #By default it selects the ASI1 LLM and expects the ASI1 API key
        model="your_llm_model"          #By default it selects the asi1-mini model
        port=8200,
        mailbox=True,
        agent_configs=agent_configs,
        routing_strategy="keyword_match"
    )
    adapter.run()

if __name__ == "__main__":
    main()
```

---

## 6. Message Flow

1. **Incoming Message**: External uAgent sends chat message
2. **Agent Discovery**: Adapter discovers and health-checks available agents
3. **Query Routing**: Router selects best agent based on strategy
4. **Message Forwarding**: Query sent to selected A2A agent
5. **Response Processing**: Agent response processed and formatted
6. **Reply**: Response sent back to original sender
7. **Acknowledgment**: Confirmation sent to complete the cycle

---

## 7. Advanced Usage

- **Custom Fallback Executor**: Provide a fallback for unrouted queries
- **Dynamic Agent Registration**: Add agents at runtime
- **Health Monitoring**: Automatic health checks and exclusion of unhealthy agents

---

### Health Monitoring

The adapter automatically monitors agent health and excludes unhealthy agents from routing:

- Health status is checked on startup and periodically
- Unhealthy agents are automatically excluded from routing
- Health checks include:
  - Agent card availability at /.well-known/agent.json
  - HTTP response status
  - Response time monitoring

## Error Handling

The adapter includes comprehensive error handling:

- **Agent Unavailable**: Automatically routes to alternative agents
- **Network Timeouts**: Configurable timeout settings with graceful degradation
- **Invalid Responses**: Fallback to error messages or alternative agents
- **Health Check Failures**: Automatic agent exclusion and retry logic

---


## 9. Notes
- Use `A2AAgentConfig` for all agent configuration
- Start A2A servers with `a2a_servers` for manifest and server management
- Use `SingleA2AAdapter` or `MultiA2AAdapter` for orchestration and chat integration
- After starting, inspect manifest URLs at `http://localhost:{port}/.well-known/agent.json`

---

## 10. Full Example: Single Agent (Brave Search)

Please add your [A2A Agents](https://a2aproject.github.io/A2A/latest/) in the agents directory to import the Agent Executor. For more details, please refer [here](https://github.com/fetchai/innovation-lab-examples/tree/main/a2a-uAgents-Integration/a2a-Outbound-Communication/braveagent).


```python
from typing import Dict, List
from uagent_adapter import SingleA2AAdapter, A2AAgentConfig, a2a_servers
from brave.agent import BraveSearchAgentExecutor  

class BraveSearchAgent:
    def __init__(self):
        self.coordinator = None
        self.agent_configs: List[A2AAgentConfig] = []
        self.executors: Dict[str, any] = {}
        self.running = False

    def setup_agents(self):
        print("Setting up Brave Search Agent")
        self.agent_configs = [
            A2AAgentConfig(
                name="brave_search_specialist",
                description="AI Agent for web and news search using Brave Search API",
                url="http://localhost:10020",
                port=10020,
                specialties=["web search", "news", "information retrieval", "local business", "site-specific lookup"],
                priority=3
            )
        ]
        self.executors = {
            "brave_search_specialist": BraveSearchAgentExecutor()
        }
        print("Brave Search Agent configuration created")

    def start_individual_a2a_servers(self):
        print("Starting Brave Search server...")
        a2a_servers(self.agent_configs, self.executors)
        print("Brave Search server started!")

    def create_coordinator(self):
        print("Creating Brave Coordinator...")
        brave_executor = self.executors.get("brave_search_specialist")
        if brave_executor is None:
            raise ValueError("BraveSearchAgentExecutor not found in executors dictionary.")
        self.coordinator = SingleA2AAdapter(
            agent_executor=brave_executor,
            name="brave_coordin",
            description="Coordinator for routing Brave Search queries",
            port=8200,
            mailbox=True
        )
        print("Brave Coordinator created!")
        return self.coordinator

    def start_system(self):
        print("Starting Brave Search System")
        try:
            self.setup_agents()
            self.start_individual_a2a_servers()
            coordinator = self.create_coordinator()
            self.running = True
            print(f"Starting Brave coordinator on port {coordinator.port}...")
            if self.agent_configs and hasattr(self.agent_configs[0], "port"):
                agent_card = self.agent_configs[0].port
                print(f"AgentCard manifest URL: http://localhost:{agent_card}/.well-known/agent.json")
            else:
                print("AgentCard manifest URL: [unknown port]")
            coordinator.run()
        except KeyboardInterrupt:
            print("Shutting down Brave Search system...")
            self.running = False
        except Exception as e:
            print(f"Error: {e}")
            self.running = False

def main():
    try:
        system = BraveSearchAgent()
        system.start_system()
    except KeyboardInterrupt:
        print("Brave system shutdown complete!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
```

---

## 11. Full Example: Multi-Agent Orchestrator

Please add your [A2A Agents](https://a2aproject.github.io/A2A/latest/) in the agents directory to import the Agent Executor. For more details, please refer [here](https://github.com/fetchai/innovation-lab-examples/tree/main/a2a-uAgents-Integration/a2a-Outbound-Communication/Multiagent).

```python
from typing import Dict, List
from uagent_adapter import MultiA2AAdapter, A2AAgentConfig, a2a_servers
from agents.research_agent import ResearchAgentExecutor
from agents.coding_agent import CodingAgentExecutor
from agents.analysis_agent import AnalysisAgentExecutor

class MultiAgentOrchestrator:
    def __init__(self):
        self.coordinator = None
        self.agent_configs: List[A2AAgentConfig] = []
        self.executors: Dict[str, any] = {}
        self.running = False

    def setup_agents(self):
        print("Setting up Multi-Agent System")
        self.agent_configs = [
            A2AAgentConfig(
                name="research_specialist",
                description="AI Research Specialist for research and analysis",
                url="http://localhost:10020",
                port=10020,
                specialties=["research", "analysis", "fact-finding", "summarization"],
                priority=3
            ),
            A2AAgentConfig(
                name="coding_specialist",
                description="AI Software Engineer for coding",
                url="http://localhost:10022",
                port=10022,
                specialties=["coding", "debugging", "programming"],
                priority=3
            ),
            A2AAgentConfig(
                name="analysis_specialist",
                description="AI Data Analyst for insights and metrics",
                url="http://localhost:10023",
                port=10023,
                specialties=["data analysis", "insights", "forecasting"],
                priority=2
            )
        ]
        self.executors = {
            "research_specialist": ResearchAgentExecutor(),
            "coding_specialist": CodingAgentExecutor(),
            "analysis_specialist": AnalysisAgentExecutor()
        }
        print("Agent configurations created")

    def start_individual_a2a_servers(self):
        print("Starting servers...")
        a2a_servers(self.agent_configs, self.executors)
        print("Servers started!")

    def create_coordinator(self):
        print("Creating Coordinator...")
        self.coordinator = MultiA2AAdapter(
            name="MultiAgent",
            description="Routes queries to AI specialists",
            llm_api_key="your_llm_api_key",
            base_url="your_llm_base_url"     #By default it selects the ASI1 LLM and expects the ASI1 API key
            model="your_llm_model"          #By default it selects the asi1-mini model
            port=8200,
            mailbox=True,
            agent_configs=self.agent_configs,
            routing_strategy="keyword_match"
        )
        print("Coordinator created!")
        return self.coordinator

    def start_system(self):
        print("Starting Multi-Agent System")
        try:
            self.setup_agents()
            self.start_individual_a2a_servers()
            coordinator = self.create_coordinator()
            self.running = True
            print(f"Starting coordinator on port {coordinator.port}...")
            coordinator.run()
        except KeyboardInterrupt:
            print("Shutting down...")
            self.running = False
        except Exception as e:
            print(f"Error: {e}")
            self.running = False

def main():
    try:
        system = MultiAgentOrchestrator()
        system.start_system()
    except KeyboardInterrupt:
        print("Shutdown complete!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
```