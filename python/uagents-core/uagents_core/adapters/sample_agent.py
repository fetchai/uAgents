import os
from fastapi import FastAPI
from adapters import attach_adapter, MsgCallback


app = FastAPI()

@app.get("/status")
async def healthcheck():
    return {"status": "OK - My FastAPI app is running"}


@app.post("/predict")
async def predict(payload: dict):
    text = payload.get("text", "")
    reply = await run_my_logic(text)
    return {"reply": reply}


async def run_my_logic(user_text: str) -> str:
    return f"Mesage received: {user_text}"


async def chat_callback(text: str) -> str:
    return await run_my_logic(text)


attach_adapter(
    app,
    msg_callback=chat_callback,
    msg_route="/chat",   
)