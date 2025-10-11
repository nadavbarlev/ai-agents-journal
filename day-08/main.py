import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from openai.types.responses import ResponseTextDeltaEvent
from pydantic import BaseModel

from agents import Agent, ItemHelpers, Runner
from config import with_env

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/client", StaticFiles(directory="client"), name="client")


class ChatRequest(BaseModel):
    message: str
    agent_name: str = "Assistant"
    agent_instructions: str = "You are a helpful assistant."


@app.get("/", response_class=HTMLResponse)
async def index():
    with open("client/index.html") as f:
        return HTMLResponse(content=f.read())


@app.post("/chat")
async def chat(request: ChatRequest):
    return StreamingResponse(
        generate(request),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@with_env
async def generate(request: ChatRequest):
    agent = Agent(
        name=request.agent_name,
        instructions=request.agent_instructions,
    )

    result = Runner.run_streamed(
        agent,
        input=request.message,
    )

    # Send start signal
    data = json.dumps({"type": "start"})
    yield f"data: {data}\n\n"

    async for event in result.stream_events():
        if event.type == "raw_response_event":
            if not isinstance(event.data, ResponseTextDeltaEvent):
                continue
            token = event.data.delta
            if token:
                data = json.dumps({"type": "token", "content": token})
                yield f"data: {data}\n\n"

        elif event.type == "agent_updated_stream_event":
            data = json.dumps(
                {"type": "agent_update", "agent_name": event.new_agent.name}
            )
            yield f"data: {data}\n\n"

        elif event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
                data = json.dumps({"type": "tool_call", "message": "Tool was called"})
                yield f"data: {data}\n\n"
            elif event.item.type == "tool_call_output_item":
                data = json.dumps(
                    {"type": "tool_output", "content": str(event.item.output)}
                )
                yield f"data: {data}\n\n"

            elif event.item.type == "message_output_item":
                message_text = ItemHelpers.text_message_output(event.item)
                data = json.dumps({"type": "message_replace", "content": message_text})
                yield f"data: {data}\n\n"

    # Send completion signal
    data = json.dumps({"type": "complete"})
    yield f"data: {data}\n\n"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8080)
