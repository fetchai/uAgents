DEFAULT_LANGGRAPH_PORT = "2024"
DEFAULT_LANGGRAPH_INTERNAL_BASE_URL = "http://langgraph.internal"
DEFAULT_LANGGRAPH_ASSISTANT_ID = "agent"
DEFAULT_HTTP_TIMEOUT = 60.0

DEFAULT_ENV_VARS = {
    "LANGGRAPH_RUNTIME_EDITION": "inmem",
    "DATABASE_URI": "postgresql://postgres:postgres@127.0.0.1:5432/postgres?sslmode=disable",
    "REDIS_URI": "redis://127.0.0.1:6379/0",
}
