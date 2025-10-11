import asyncio

from openai.types.responses import ResponseTextDeltaEvent

from agents import Agent, ItemHelpers, Runner, function_tool
from config import with_env


@function_tool
def joke_issue_selector(topic: str):
    """
    Selects an issue for a joke
    """
    return "Dogs"


@with_env
async def main():
    agent = Agent(
        name="Joker",
        tools=[joke_issue_selector],
        instructions="Tell me a joke. Use the joke_issue_selector tool to pick topic",
    )

    result = Runner.run_streamed(
        agent,
        input="Hello",
    )

    async for event in result.stream_events():
        if event.type == "raw_response_event":
            if isinstance(event.data, ResponseTextDeltaEvent):
                print(f"[Token]: {event.data.delta}")
            else:
                print(event)

        # When the agent updates, print that
        elif event.type == "agent_updated_stream_event":
            print(f"Agent updated: {event.new_agent.name}")
            continue

        # When items are generated, print them
        elif event.type == "run_item_stream_event":
            if event.item.type == "tool_call_item":
                print("-- Tool was called")
            elif event.item.type == "tool_call_output_item":
                print(f"-- Tool output: {event.item.output}")
            elif event.item.type == "message_output_item":
                print(
                    f"-- Message output:\n {
                        (ItemHelpers.text_message_output(event.item),)
                    }"
                )
            else:
                print(f" -- Other Event: {event}")


if __name__ == "__main__":
    asyncio.run(main())
