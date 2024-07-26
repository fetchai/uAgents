# Block Time agent

This integration provides to agent. One agent is able to collect blockchain data, create a CVS with the data and upload to Google Cloud Storage. Other agent expects a URL to a CSV file, using the data it can do average block time calculation.

These two agents can be chained together using AI Engine.

In order to do that, you need to register these agents in [https://agentverse.ai](https://agentverse.ai) under services tab.

Example descriptions:

Generate data agent:
```This task can create CSV file with blockchain data. Provides a url to CSV file.```

Analyse block time:
```This task can provide average block time analysis of the fetch network.```
