## Example of how to query an agent using a proxy API

In separate terminals:

1. Run the FastAPI proxy:
```bash
uvicorn proxy:app
```

2. Run the agent:
```bash
python agent.py
```

3. Query the agent via the proxy:
```bash
curl -d '{"message": "test"}' -H "Content-Type: application/json" -X POST http://localhost:8000/endpoint
```
