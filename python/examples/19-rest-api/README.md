## Example of how to add custom REST endpoints to your agent

By using one of the two new decorators: `on_rest_get()` and `on_rest_post()` you are able to define custom endpoints that your agent can act upon.

The usage is similar to a message handler in that you define:

- a custom endpoint in string format, e.g. `"/my_rest_endpoint"`,
- a Request Model (inheriting from uagents.models) for `POST` endpoints, and
- a Response Model for `GET` endpoints

The difference to a message handler is that you actually have to invoke `return` for the value to be returned to the REST client. The format can either be `Dict[str, Any]` or the `Model` itself but either way the output will be validated against the predefined response model.

**GET request example**

```python
@agent.on_rest_get("/custom_get_route", Response)
async def handle_get(ctx: Context) -> Dict[str, Any]:
    return {
        "field": <value>,
    }
```

**POST request example**

```python
@agent.on_rest_post("/custom_post_route", Request, Response)
async def handle_post(ctx: Context, req: Request) -> Response:
    ctx.logger.info(req)  # access to the request
    return Response(...)
```

For querying the agent you have to make sure that:

1. You use the correct REST method ("GET" or "POST"), and
2. You address the agent endpoint together with its route (`http://localhost:8000/custom_route`)

### Run the example

1. Run the agent:

```bash
python agent.py
```

2. Query the agent directly through your predefined interfaces:

```bash
curl -d '{"text": "test"}' -H "Content-Type: application/json" -X POST http://localhost:8000/rest/post
```
